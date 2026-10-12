#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1: render the JSTARS manuscript Markdown into an IEEEtran LaTeX source.

Input : <ROOT>/P0S1_JSTARS_v1.md      (the Markdown the audit checks)
Output: <ROOT>/P0S1_JSTARS_v1.tex     (IEEEtran, journal mode, two column)

The converter is deliberately rule-based and conservative. It emits no package
beyond what a stock TeX Live or Overleaf installation ships, so the .tex compiles
without bibtex and without a custom class. Section, table, and figure numbering
is left to IEEEtran, whose journal mode numbers sections, tables, and figures in
the same order the Markdown defines them.
"""
import os
import re
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = _os.path.join(PROJ_ROOT, "papers")
SRC = os.path.join(ROOT, "P0S1_JSTARS_v1.md")
DST = os.path.join(ROOT, "P0S1_JSTARS_v1.tex")

# ----------------------------------------------------------------- small helpers
PIPE = "\x00P"

UNI = [
    ("\u2014", "---"),          # em dash
    ("\u2013", "--"),           # en dash
    ("\u00d7", r"$\times$"),    # multiplication sign
    ("\u00b1", r"$\pm$"),
    ("\u0394", r"$\Delta$"),
    ("\u03c1", r"$\rho$"),
    ("\u2265", r"$\geq$"),
    ("\u2264", r"$\leq$"),
    ("\u2717", r"$\times$"),    # ballot cross used as "champion changes"
    ("\u2192", r"$\rightarrow$"),
    ("\u00b7", r"$\cdot$"),
    ("\u2026", r"\ldots{}"),
    ("\u2212", r"$-$"),         # minus sign
    ("\u00b0", r"$^\circ$"),
    ("\u2018", "`"),
    ("\u2019", "'"),
    ("\u201c", "``"),
    ("\u201d", "''"),
]

TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[\[.+?\]\])", re.S)


def smart_quotes(s):
    """Turn straight double quotes into TeX open/close pairs."""
    out, open_q = [], True
    for ch in s:
        if ch == '"':
            out.append("``" if open_q else "''")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)


def esc(s):
    s = s.replace("\\|", PIPE)
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("{", r"\{").replace("}", r"\}")
    s = s.replace("$", r"\$")
    s = s.replace("&", r"\&")
    s = s.replace("%", r"\%")
    s = s.replace("#", r"\#")
    s = s.replace("_", r"\_")
    s = s.replace("^", r"\textasciicircum{}")
    s = s.replace("~", r"\textasciitilde{}")
    for a, b in UNI:
        s = s.replace(a, b)
    s = s.replace(PIPE, r"$|$")
    return s


def conv(s):
    """Escape a text run, converting **bold**, `code`, and [[marker]] in place."""
    out, pos = [], 0
    for m in TOKEN.finditer(s):
        out.append(esc(s[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith("**"):
            out.append(r"\textbf{" + conv(tok[2:-2]) + "}")
        elif tok.startswith("`"):
            out.append(r"\texttt{" + esc(tok[1:-1]) + "}")
        else:
            out.append(r"\textcolor{red}{[" + esc(tok[2:-2]) + "]}")
        pos = m.end()
    out.append(esc(s[pos:]))
    return "".join(out)


def line_tex(raw):
    return conv(smart_quotes(raw.strip()))


ARABIC2ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
                6: "VI", 7: "VII", 8: "VIII", 9: "IX"}

FIG_FILES = {1: "fig1_noise_vs_testsize.pdf", 2: "fig2_effect_vs_noise.pdf"}

AUTHOR_NAMES = ("Zhengyang Chen", "Dawei Liu", "Zhiheng Liu")

PREAMBLE = r"""\documentclass[journal,twoside,10pt]{IEEEtran}
% IEEE JSTARS submission. Compile with pdflatex on a stock TeX Live or on Overleaf.
% IEEEtran is the journal's official template and ships with both.
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{xcolor}
\usepackage{url}
\graphicspath{{figures/}{../figures/}}
\hyphenation{re-pro-duc-ib-il-ity su-per-res-o-lu-tion bench-mark}
% width available to the p-columns of a table once the inter-column padding
% is subtracted, so that a full-width table cannot spill past the margin
\newlength{\tblavail}

\begin{document}
"""


def build_table(num, caption, header, body, note_after=None):
    """Return the LaTeX for one Markdown table.

    Column widths are allocated in proportion to the longest cell, but every
    column is also given room for three times its longest single word. A word
    cannot be broken, so a column narrower than its longest word would spill
    past the margin however the paragraph is set.
    """
    ncol = len(header)
    cols = [[header[j]] + [r[j] if j < len(r) else "" for r in body]
            for j in range(ncol)]
    def longest_word(s):
        return max((len(w) for w in re.split(r"[\s/]+", s)), default=0)
    maxlen = [max(len(c) for c in col) for col in cols]
    maxword = [max(longest_word(c) for c in col) for col in cols]
    weights = [max(maxlen[j], 3 * maxword[j]) for j in range(ncol)]
    wide = max(maxlen) > 28
    base = r"\textwidth" if ncol >= 5 else r"\columnwidth"
    env = "table*" if ncol >= 5 else "table"
    if wide:
        tot = float(sum(weights))
        spec = "".join("p{%.3f\\tblavail}" % (0.97 * w / tot) for w in weights)
    else:
        spec = "l" + "c" * (ncol - 1)
    lab = "tab:%s" % num
    lines = []
    lines.append("\\begin{%s}[!t]" % env)
    lines.append(r"\caption{%s}" % conv(smart_quotes(caption)))
    lines.append(r"\label{%s}" % lab)
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\setlength{\tblavail}{\dimexpr%s-%d\tabcolsep\relax}"
                 % (base, 2 * ncol))
    lines.append(r"\begin{tabular}{%s}" % spec)
    lines.append(r"\hline")
    lines.append(" & ".join(conv(smart_quotes(c)) for c in header) + r" \\")
    lines.append(r"\hline")
    for row in body:
        row = (row + [""] * ncol)[:ncol]
        lines.append(" & ".join(conv(smart_quotes(c)) for c in row) + r" \\")
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append("\\end{%s}" % env)
    return "\n".join(lines)


def split_row(raw):
    inner = raw.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def main():
    src = open(SRC, encoding="utf-8").read()
    lines = src.split("\n")

    title = ""
    authors_tex = ""
    body = []
    i = 0
    n_tables = n_figs = n_refs = n_bios = 0

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        # ---- html comment blocks
        if s.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        if not s:
            i += 1
            continue

        # ---- title
        if s.startswith("# "):
            title = conv(smart_quotes(s[2:].strip()))
            i += 1
            continue

        # ---- author block: "Names<sup>1</sup>" then <sup>..</sup> footnotes
        if re.match(r"^[A-Za-z].*<sup>1</sup>", s) and not authors_tex:
            names = re.sub(r"<sup>.*?</sup>", "", s).strip()
            i += 1
            thanks, orcid = [], ""
            while i < len(lines):
                t = lines[i].strip()
                if t.startswith("<sup>"):
                    thanks.append(re.sub(r"^<sup>.*?</sup>", "", t).strip())
                    i += 1
                elif t.startswith("ORCID:"):
                    orcid = t
                    i += 1
                elif t == "":
                    i += 1
                else:
                    break
            chunks = []
            for t in thanks:
                if t.startswith("Corresponding author") and "This work was supported" in t:
                    a, _, b = t.partition(". This work was supported")
                    chunks.append(a.strip() + ".")
                    chunks.append("This work was supported" + b)
                else:
                    chunks.append(t)
            if orcid:
                chunks.append(orcid)
            th = "".join("\\thanks{%s}%%\n" % line_tex(c) for c in chunks)
            authors_tex = "\\author{%s%%\n%s}" % (line_tex(names).replace(", and", ",~and"), th)
            continue

        # ---- abstract
        if s == "## Abstract":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            body.append("\\begin{abstract}\n%s\n\\end{abstract}\n"
                        % line_tex(lines[j]))
            i = j + 1
            continue

        # ---- keywords
        if s.startswith("**Index Terms**"):
            kw = s.split("\u2014", 1)[-1] if "\u2014" in s else s
            body.append("\\begin{IEEEkeywords}\n%s\n\\end{IEEEkeywords}\n" % line_tex(kw))
            i += 1
            continue

        # ---- horizontal rule
        if s in ("---", "***", "___"):
            i += 1
            continue

        # ---- numbered sections
        m = re.match(r"^##\s+(\d+)\.\s*(.+)$", s)
        if m:
            body.append("\\section{%s}\n" % conv(smart_quotes(m.group(2).strip())))
            i += 1
            continue

        # ---- unnumbered sections
        if s.startswith("## "):
            name = s[3:].strip()
            if name == "References":
                refs = []
                j = i + 1
                while j < len(lines):
                    r = lines[j].strip()
                    if not r:
                        j += 1
                        continue
                    if r.startswith("##"):
                        break
                    rm = re.match(r"^\[(\d+)\]\s*(.+)$", r)
                    if rm:
                        n_refs += 1
                        refs.append("\\bibitem{ref%s}\n%s" % (rm.group(1), line_tex(rm.group(2))))
                    j += 1
                body.append("\\begin{thebibliography}{99}\n%s\n\\end{thebibliography}\n"
                            % "\n".join(refs))
                i = j
                continue
            if name == "Author Biographies":
                bios = []
                j = i + 1
                while j < len(lines):
                    r = lines[j].strip()
                    if not r:
                        j += 1
                        continue
                    if r.startswith("##"):
                        break
                    nm = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", r)
                    if nm and nm.group(1) in AUTHOR_NAMES:
                        n_bios += 1
                        bios.append("\\begin{IEEEbiographynophoto}{%s}\n%s\n\\end{IEEEbiographynophoto}\n"
                                    % (nm.group(1), line_tex(nm.group(2))))
                    else:
                        bios.append("%% biography note: %s\n" % r.replace("\n", " "))
                    j += 1
                body.append("\n".join(bios))
                i = j
                continue
            if name == "Figures and Tables":
                # internal checklist: keep it, but as an unnumbered non-floating table
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                rows = []
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append(lines[j])
                    j += 1
                cells = [split_row(r) for r in rows]
                hdr, data = cells[0], cells[2:]
                txt = [r"\begin{center}\small",
                       r"\setlength{\tabcolsep}{3pt}",
                       r"\setlength{\tblavail}{\dimexpr\columnwidth-6\tabcolsep\relax}",
                       r"\begin{tabular}{@{}l p{0.42\tblavail} p{0.32\tblavail}@{}}",
                       r"\hline",
                       " & ".join(conv(smart_quotes(c)) for c in hdr) + r" \\", r"\hline"]
                for r in data:
                    cells_r = [conv(smart_quotes(c)) for c in r]
                    # \texttt paths have no natural breakpoints, so give the
                    # narrow Source column one after every slash and underscore
                    if len(cells_r) >= 3:
                        s = cells_r[-1]
                        s = s.replace("/", "/\\allowbreak ").replace("\\_", "\\_\\allowbreak ")
                        cells_r[-1] = s
                    txt.append(" & ".join(cells_r) + r" \\")
                txt += [r"\hline", r"\end{tabular}", r"\end{center}"]
                body.append("\\section*{%s}\n%s\n" % (conv(name), "\n".join(txt)))
                i = j
                continue
            body.append("\\section*{%s}\n" % conv(smart_quotes(name)))
            i += 1
            continue

        # ---- subsections
        m = re.match(r"^###\s+([A-Z])\.\s*(.+)$", s)
        if m:
            body.append("\\subsection{%s}\n" % conv(smart_quotes(m.group(2).strip())))
            i += 1
            continue

        # ---- table caption + markdown table
        m = re.match(r"^\*\*TABLE\s+([IVX]+)\.\s*(.+?)\*\*$", s)
        if m:
            num, cap = m.group(1), m.group(2)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(lines[j])
                j += 1
            cells = [split_row(r) for r in rows]
            body.append(build_table(num, cap, cells[0], cells[2:]))
            n_tables += 1
            i = j
            continue

        # ---- figure caption (bold caption, remainder of the paragraph follows)
        m = re.match(r"^\*\*Fig\.\s+(\d+)\.\s*(.+?)\*\*\s*(.*)$", s)
        if m:
            num = int(m.group(1))
            cap = m.group(2)
            rest = m.group(3).strip()
            body.append("\n".join([
                "\\begin{figure}[!t]",
                r"\centering",
                r"\includegraphics[width=\columnwidth]{%s}" % FIG_FILES.get(num, "fig%d.pdf" % num),
                r"\caption{%s}" % conv(smart_quotes(cap)),
                r"\label{fig:%d}" % num,
                r"\end{figure}",
            ]))
            n_figs += 1
            if rest:
                body.append(line_tex(rest))
            i += 1
            continue

        # ---- numbered list run
        if re.match(r"^\d{1,2}\.\s", s):
            items = []
            while i < len(lines) and re.match(r"^\d{1,2}\.\s", lines[i].strip()):
                items.append("\\item %s" % line_tex(re.sub(r"^\d{1,2}\.\s", "", lines[i].strip())))
                i += 1
            body.append("\\begin{enumerate}\n%s\n\\end{enumerate}\n" % "\n".join(items))
            continue

        # ---- plain paragraph
        body.append(line_tex(s))
        i += 1

    doc = PREAMBLE
    doc += "\\title{%s}\n\n" % title
    doc += authors_tex + "\n\n\\maketitle\n\n"
    doc += "\n\n".join(body)
    doc += "\n\n\\end{document}\n"

    with open(DST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    # ------------------------------------------------------------------ report
    print("wrote %s (%d bytes)" % (DST, len(doc.encode("utf-8"))))
    print("tables=%d figures=%d bibitems=%d biographies=%d" % (n_tables, n_figs, n_refs, n_bios))
    leftover = sorted(set(ch for ch in doc if ord(ch) > 126))
    print("non-ascii remaining:", leftover if leftover else "none")
    print("begin/end env balance:",
          len(re.findall(r"\\begin\{", doc)), len(re.findall(r"\\end\{", doc)))


if __name__ == "__main__":
    main()
