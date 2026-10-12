#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1: render the Scientific Reports Markdown into Springer Nature LaTeX.

Input : <OUT>/P0S1_SciRep_v1.md      (+ P0S1_SciRep_SI.md)
Output: <OUT>/P0S1_SciRep_v1.tex     (+ P0S1_SciRep_SI.tex)

Uses the official Springer Nature class (sn-jnl) with the Nature Portfolio
reference style. Scientific Reports is on the Nature Portfolio submission
system, whose template instructs authors to carry the reference list inside the
manuscript rather than in a separate .bib, so the bibliography is emitted as a
thebibliography block in citation order, which is the numbering Nature uses.

Heading labels travel with the Markdown as {@label@} markers, so a section can
be moved without silently breaking a cross reference.
"""
import os
import re
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get("S2DS_AUDIT_ROOT") or os.path.dirname(_HERE)
# Works in both layouts: locally the manuscripts live in <project>/out, in the
# published repository they live in <repo>/papers.
_CANDS = [os.environ.get("S2DS_OUT"), os.path.join(_ROOT, "papers"),
          os.path.join(os.path.dirname(_ROOT), "out")]
OUT = next((c for c in _CANDS
            if c and os.path.exists(os.path.join(c, "P0S1_SciRep_v1.md"))),
           _CANDS[-1])

FIG_FILES = {1: "fig1_noise_vs_testsize.pdf", 2: "fig2_effect_vs_noise.pdf"}

# Supplementary table order, matching the order written by s1_make_scirep_md.py
SI_ORDER = ["II", "V", "VI"]

# Roman table number as written in the Markdown -> its label
TAB_LABEL = {"I": "srbench", "II": "lines", "III": "conventions", "IV": "effect",
             "V": "seednoise", "VI": "anchor", "VII": "practice",
             "VIII": "gains", "IX": "scorecard"}

BACK = ["Acknowledgements", "Author contributions", "Data availability",
        "Additional Information"]

# ----------------------------------------------------------------- escaping
PIPE = "\x00P"
UNI = [("\u2014", "---"), ("\u2013", "--"), ("\u00d7", r"$\times$"),
       ("\u00b1", r"$\pm$"), ("\u0394", r"$\Delta$"), ("\u03c1", r"$\rho$"),
       ("\u2265", r"$\geq$"), ("\u2264", r"$\leq$"), ("\u2717", r"$\times$"),
       ("\u2192", r"$\rightarrow$"), ("\u00b7", r"$\cdot$"),
       ("\u2026", r"\ldots{}"), ("\u2212", r"$-$"), ("\u00b0", r"$^\circ$"),
       ("\u2018", "`"), ("\u2019", "'"), ("\u201c", "``"), ("\u201d", "''"),
       ("\u00a0", "~")]
TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[\[.+?\]\])", re.S)

# LaTeX control sequences that the Markdown already carries. They must survive
# escaping intact: the backslash in \ref{...} would otherwise be turned into
# \textbackslash{}, which silently converts a cross reference into literal text
# and leaves pdflatex with nothing to resolve.
LATEX_KEEP = re.compile(r"\\(?:ref|cite|label)\{[^}]*\}")


def smart_quotes(s):
    out, open_q = [], True
    for ch in s:
        if ch == '"':
            out.append("``" if open_q else "''")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)


def esc(s):
    prot = []

    def keep(m):
        prot.append(m.group(0))
        return "\x02%d\x02" % (len(prot) - 1)

    s = LATEX_KEEP.sub(keep, s)
    s = s.replace("\\|", PIPE)
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("{", r"\{").replace("}", r"\}")
    s = s.replace("$", r"\$").replace("&", r"\&").replace("%", r"\%")
    s = s.replace("#", r"\#").replace("_", r"\_")
    s = s.replace("^", r"\textasciicircum{}").replace("~", r"\textasciitilde{}")
    for a, b in UNI:
        s = s.replace(a, b)
    s = s.replace(PIPE, r"$|$")
    for i, v in enumerate(prot):
        s = s.replace("\x02%d\x02" % i, v)
    return s


def conv(s, allow_cite=True):
    out, pos = [], 0
    for m in TOKEN.finditer(s):
        out.append(cite_sub(esc(s[pos:m.start()])) if allow_cite else esc(s[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith("**"):
            out.append(r"\textbf{" + conv(tok[2:-2], allow_cite) + "}")
        elif tok.startswith("`"):
            out.append(r"\texttt{" + esc(tok[1:-1]).replace(r"\_", r"\_\allowbreak ") + "}")
        else:
            out.append(r"\textcolor{red}{[" + esc(tok[2:-2]) + "]}")
        pos = m.end()
    out.append(cite_sub(esc(s[pos:])) if allow_cite else esc(s[pos:]))
    return "".join(out)


def cite_sub(tex):
    """[n] in the Markdown becomes a numbered citation in order of appearance."""
    return re.sub(r"\[(\d{1,2})\]",
                  lambda m: r"\cite{ref%s}" % m.group(1), tex)


def line_tex(raw, allow_cite=True):
    return conv(smart_quotes(raw.strip()), allow_cite)


def strip_label(t):
    """Pull the {@label@} marker off a heading, returning (text, label)."""
    m = re.search(r"\s*\{@([^}]+)@\}\s*$", t)
    if m:
        return t[:m.start()].strip(), m.group(1)
    return t.strip(), None


# ------------------------------------------------------------------ preamble
PREAMBLE = r"""\documentclass[pdflatex,sn-nature]{sn-jnl}
% Scientific Reports submission, built on the official Springer Nature class.
% The class and the reference styles ship in out/sn/sn-article-template.
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\usepackage{url}
\graphicspath{{figures/}{../figures/}}
\newlength{\tblavail}

\begin{document}
"""

FRONT = r"""\title[Evaluation protocol choices decide the ranking]{%(title)s}

\author*[1]{\fnm{Zhengyang} \sur{Chen}}\email{1250368357@qq.com}

\author[1]{\fnm{Dawei} \sur{Liu}}\email{wjmicheal@163.com}

\author[2]{\fnm{Zhiheng} \sur{Liu}}\email{liuzhiheng@xidian.edu.cn}

\affil*[1]{\orgname{Engineering University of PAP}, \orgaddress{\city{Xi'an}, \postcode{710086}, \country{China}}}

\affil[2]{\orgname{Institute of Earth Environment, Chinese Academy of Sciences}, \orgaddress{\city{Xi'an}, \postcode{710061}, \country{China}}}

\abstract{%(abstract)s}

\keywords{%(keywords)s}

\maketitle

"""


def build_table(roman, caption, header, body):
    ncol = len(header)
    cols = [[header[j]] + [r[j] if j < len(r) else "" for r in body]
            for j in range(ncol)]

    def longest_word(s):
        return max((len(w) for w in re.split(r"[\s/]+", s)), default=0)

    maxlen = [max(len(c) for c in col) for col in cols]
    maxword = [max(longest_word(c) for c in col) for col in cols]
    weights = [max(maxlen[j], 3 * maxword[j]) for j in range(ncol)]
    if max(maxlen) > 28:
        tot = float(sum(weights))
        spec = "".join("p{%.3f\\tblavail}" % (0.97 * w / tot) for w in weights)
    else:
        spec = "l" + "c" * (ncol - 1)

    lab = TAB_LABEL.get(roman, roman.lower())
    lines = ["\\begin{table}[htbp]", r"\centering", r"\small",
             r"\setlength{\tabcolsep}{3pt}",
             r"\setlength{\tblavail}{\dimexpr\textwidth-%d\tabcolsep\relax}" % (2 * ncol),
             r"\begin{tabular}{%s}" % spec, r"\hline",
             " & ".join(xrefs(conv(smart_quotes(c))) for c in header) + r" \\",
             r"\hline"]
    for row in body:
        row = (row + [""] * ncol)[:ncol]
        lines.append(" & ".join(xrefs(conv(smart_quotes(c))) for c in row) + r" \\")
    lines += [r"\hline", r"\end{tabular}",
              r"\caption{%s}\label{tab:%s}" % (conv(smart_quotes(caption)), lab),
              r"\end{table}"]
    return "\n".join(lines)


def split_row(raw):
    inner = raw.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def xrefs(tex):
    tex = re.sub(r"Supplementary Table~\\ref\{tab:([a-z]+)\}",
                 lambda m: "Supplementary Table~\\ref{tab:%s}" % m.group(1), tex)
    return tex


def render(md_path, tex_path, supplementary=False):
    lines = open(md_path, encoding="utf-8").read().split("\n")

    title = abstract = keywords = ""
    body, back, figures, tables, refs = [], {}, [], [], []
    i = 0
    n_tab = n_fig = 0
    while i < len(lines):
        s = lines[i].strip()

        if s.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if not s:
            i += 1
            continue

        if s.startswith("# ") and not title:
            title = conv(smart_quotes(s[2:].strip()), False)
            i += 1
            continue

        if s == "## Abstract":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            # must be escaped: the abstract contains '%' signs, which LaTeX
            # would otherwise read as the start of a comment and swallow the
            # closing brace of \abstract{...}
            abstract = conv(smart_quotes(" ".join(lines[j].split())), False)
            i = j + 1
            continue

        if s.startswith("**Keywords**"):
            kw = re.split("[\u2014\u2013]", s, maxsplit=1)[-1].strip()
            keywords = ", ".join(k.strip() for k in kw.rstrip(".").split(";"))
            keywords = esc(keywords)
            i += 1
            continue

        if s == "## References":
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("##"):
                rm = re.match(r"^\[(\d+)\]\s*(.+)$", lines[j].strip())
                if rm:
                    refs.append("\\bibitem{ref%s}\n%s"
                                % (rm.group(1), conv(rm.group(2), False)))
                j += 1
            i = j
            continue

        if s == "## Figure legends":
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("##"):
                i += 1
            continue

        if s == "## Tables":
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("##"):
                m = re.match(r"^\*\*TABLE\s+([IVX]+)\.\s*(.+?)\*\*$", lines[j].strip())
                if m:
                    k = j + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    rows = []
                    while k < len(lines) and lines[k].strip().startswith("|"):
                        rows.append(lines[k])
                        k += 1
                    cells = [split_row(r) for r in rows]
                    tables.append(build_table(m.group(1), m.group(2), cells[0], cells[2:]))
                    n_tab += 1
                    j = k
                    continue
                j += 1
            i = j
            continue

        m = re.match(r"^## (.+)$", s)
        if m:
            same = m.group(1) == "Supplementary tables"
            t, lab = strip_label(m.group(1))
            if t in BACK:
                # collect the back-matter text under its heading
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("##"):
                    j += 1
                back[t] = conv(smart_quotes("\n".join(lines[i + 1:j]).strip()), False)
                i = j
                continue
            if t == "Supplementary tables":
                i += 1
                continue
            body.append("\\section{%s}%s" % (conv(smart_quotes(t), False),
                                             ("\\label{%s}" % lab) if lab else ""))
            i += 1
            continue

        m = re.match(r"^### (.+)$", s)
        if m:
            t, lab = strip_label(m.group(1))
            head = re.sub(r"^[A-Z]\.\s*", "", t)
            body.append("\\subsection{%s}%s" % (conv(smart_quotes(head), False),
                                                ("\\label{%s}" % lab) if lab else ""))
            i += 1
            continue

        m = re.match(r"^\*\*TABLE\s+(?:S(\d+)|([IVX]+))\.\s*(.+?)\*\*$", s)
        if m:
            if m.group(1):
                roman = SI_ORDER[int(m.group(1)) - 1]
                caption = m.group(3)
            else:
                roman, caption = m.group(2), m.group(3)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(lines[j])
                j += 1
            cells = [split_row(r) for r in rows]
            tables.append(build_table(roman, caption, cells[0], cells[2:]))
            n_tab += 1
            i = j
            continue

        m = re.match(r"^\*\*Fig\.\s+(\d+)\.\s*(.+?)\*\*\s*(.*)$", s)
        if m:
            num = int(m.group(1))
            figures.append("\n".join([
                "\\begin{figure}[htbp]", r"\centering",
                r"\includegraphics[width=\textwidth]{%s}" % FIG_FILES.get(num, "fig%d.pdf" % num),
                r"\caption{%s}" % conv(smart_quotes(m.group(2)), False),
                r"\label{fig:%d}" % num, r"\end{figure}"]))
            n_fig += 1
            if m.group(3).strip():
                body.append(line_tex(m.group(3).strip()))
            i += 1
            continue

        if re.match(r"^\d{1,2}\.\s", s):
            items = []
            while i < len(lines) and re.match(r"^\d{1,2}\.\s", lines[i].strip()):
                items.append("\\item %s"
                             % line_tex(re.sub(r"^\d{1,2}\.\s", "", lines[i].strip())))
                i += 1
            body.append("\\begin{enumerate}\n%s\n\\end{enumerate}" % "\n".join(items))
            continue

        if s in ("---", "***", "___"):
            i += 1
            continue

        body.append(line_tex(s))
        i += 1

    doc = [PREAMBLE]
    if not supplementary:
        doc.append(FRONT % {"title": title, "abstract": abstract,
                            "keywords": keywords})
    else:
        doc.append("\\title[Supplementary information]{Supplementary information}\n"
                   "\\author*[1]{}\\affil*[1]{}\n"
                   "\\renewcommand{\\thetable}{S\\arabic{table}}\n"
                   "\\maketitle\n")
    doc.append("\n\n".join(body))
    if refs:
        doc.append("\\begin{thebibliography}{99}\n" + "\n".join(refs)
                   + "\n\\end{thebibliography}")
    for name in BACK:
        if name in back:
            doc.append("\\bmhead{%s}\n\n%s" % (conv(name, False), back[name]))
    if figures:
        doc.append("\\clearpage\n" + "\n".join(figures))
    if tables:
        doc.append("\\clearpage\n" + "\n".join(tables))
    doc.append("\\end{document}")

    out = "\n\n".join(doc) + "\n"
    with open(tex_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)

    print("%-34s refs=%d tables=%d figures=%d sections=%d"
          % (os.path.basename(tex_path), len(refs), n_tab, n_fig,
             len(re.findall(r"\\section\{", out))))
    return out


def main():
    md = os.path.join(OUT, "P0S1_SciRep_v1.md")
    si = os.path.join(OUT, "P0S1_SciRep_SI.md")
    main_tex = render(md, os.path.join(OUT, "P0S1_SciRep_v1.tex"))
    si_tex = render(si, os.path.join(OUT, "P0S1_SciRep_SI.tex"), supplementary=True)

    for name, doc in (("main", main_tex), ("SI", si_tex)):
        labels = re.findall(r"\\label\{([^}]+)\}", doc)
        refs = set(re.findall(r"\\ref\{([^}]+)\}", doc))
        dup = sorted({l for l in labels if labels.count(l) > 1})
        print("%-5s labels=%d dangling=%s duplicate=%s"
              % (name, len(labels), sorted(refs - set(labels)) or "none", dup or "none"))
        cites = set(re.findall(r"\\cite\{([^}]+)\}", doc))
        bibs = set(re.findall(r"\\bibitem\{([^}]+)\}", doc))
        print("%-5s cites=%d undefined=%s" % (name, len(cites), sorted(cites - bibs) or "none"))
        left = re.findall(r"(?<![\w{*\\])\[\d+\]|Section [IVX]+|Table [IVX]+|\{@", doc)
        print("%-5s unconverted=%s" % (name, sorted(set(left)) or "none"))
        print("%-5s mangled_refs=%d refs=%d"
              % (name, doc.count("textbackslash"), len(re.findall(r"\\ref\{", doc))))
        nonascii = sorted({c for c in doc if ord(c) > 126})
        print("%-5s nonascii=%s" % (name, nonascii or "none"))


if __name__ == "__main__":
    main()
