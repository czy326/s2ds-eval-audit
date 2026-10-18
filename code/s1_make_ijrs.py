# -*- coding: utf-8 -*-
"""
Render the Scientific Reports master into an International Journal of Remote
Sensing submission.

Input : <OUT>/P0S1_SciRep_v1.md
Output: <OUT>/P0S1_IJRS_v1.md and <OUT>/P0S1_IJRS_v1.tex

What the journal requires, and what this script therefore changes:

  * Order: Introduction, [Related work], Materials and methods, Results,
    Discussion. Methods moves ahead of Results.
  * References: Taylor & Francis Chicago author-date, alphabetical, cited as
    (Author Year) rather than by number. The numeric markers in the source are
    resolved to keys through the reference list, and the list is rebuilt.
  * Declarations: Acknowledgements, Disclosure of interest, Funding, Data
    availability statement, Author contributions in CRediT roles, and a
    declaration on generative AI use.
  * A word count must appear in the manuscript.
  * Interact document class (T&F), single column, typeset by the publisher.

The restructuring is mechanical so the prose cannot drift from the version whose
numbers were verified.
"""
import os
import re
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get("S2DS_AUDIT_ROOT") or os.path.dirname(_HERE)
_CANDS = [os.environ.get("S2DS_OUT"), os.path.join(_ROOT, "papers"),
          os.path.join(os.path.dirname(_ROOT), "out")]
OUT = next((c for c in _CANDS
            if c and os.path.exists(os.path.join(c, "P0S1_SciRep_v1.md"))),
           _CANDS[-1])

SRC = os.path.join(OUT, "P0S1_SciRep_v1.md")
DST_MD = os.path.join(OUT, "P0S1_IJRS_v1.md")
DST_TEX = os.path.join(OUT, "P0S1_IJRS_v1.tex")

FIG_FILES = {1: "fig1_noise_vs_testsize.pdf", 2: "fig2_effect_vs_noise.pdf"}
FIG_WIDTH = r"0.55\textwidth"
TAB_LABEL = {"I": "srbench", "II": "lines", "III": "conventions", "IV": "effect",
             "V": "seednoise", "VI": "anchor", "VII": "practice",
             "VIII": "gains", "IX": "scorecard"}
SI_ORDER = ["II", "V", "VI"]

# ---------------------------------------------------------------- escaping
PIPE = "\x00P"
UNI = [("\u2014", "---"), ("\u2013", "--"), ("\u00d7", r"$\times$"),
       ("\u00b1", r"$\pm$"), ("\u0394", r"$\Delta$"), ("\u03c1", r"$\rho$"),
       ("\u2265", r"$\geq$"), ("\u2264", r"$\leq$"), ("\u2717", r"$\times$"),
       ("\u2192", r"$\rightarrow$"), ("\u00b7", r"$\cdot$"),
       ("\u2026", r"\ldots{}"), ("\u2212", r"$-$"), ("\u00b0", r"$^\circ$"),
       ("\u2018", "`"), ("\u2019", "'"), ("\u201c", "``"), ("\u201d", "''"),
       ("\u00a0", "~")]
TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[\[.+?\]\])", re.S)
LATEX_KEEP = re.compile(r"\\(?:ref|cite|label|citep|citet)\{[^}]*\}")


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


CITE = {"map": {}}


def cite_sub(tex):
    def rep(m):
        key = CITE["map"].get(int(m.group(1)))
        return r"\citep{%s}" % key if key else m.group(0)
    return re.sub(r"\[(\d{1,2})\]", rep, tex)


def line_tex(raw, allow_cite=True):
    return conv(smart_quotes(raw.strip()), allow_cite)


# ------------------------------------------------------ Chicago author-date
def chicago(body):
    """Reformat one IEEE-style entry as Chicago author-date. Returns (text, key, label)."""
    q = body.index('"')
    authors_raw = body[:q].rstrip().rstrip(",").strip()
    rest = body[q:]

    stripped = re.sub(r"doi:\s*\S+", " ", body)
    stripped = re.sub(r"arXiv:\s*\S+", " ", stripped)
    years = re.findall(r"\b(20\d\d)\b", stripped)
    year = int(years[-1]) if years else 0

    # invert only the first author: "L. Liu" -> "Liu, L."
    parts = [p.strip() for p in authors_raw.split(",") if p.strip()]
    first = parts[0]
    toks = first.split()
    if len(toks) >= 2:
        parts[0] = "%s, %s" % (toks[-1], " ".join(toks[:-1]))
    authors = ", ".join(parts)

    # split title and venue
    m = re.match(r'^"(.+?)"\s*,?\s*(.*)$', rest, re.S)
    title, venue = (m.group(1), m.group(2).strip()) if m else (rest, "")

    # compact the venue towards Chicago
    venue = re.sub(r"\bvol\.\s*(\d+)", r"\1", venue)
    venue = re.sub(r"\bno\.\s*(\d+)", r"(\1)", venue)
    venue = re.sub(r"\bart\.\s*", r"", venue)
    venue = re.sub(r"\bpp\.\s*", r"", venue)
    venue = re.sub(r"\s*,\s*doi:\s*", ". doi:", venue)
    venue = venue.rstrip(".").rstrip(",")

    tail = (" " + venue) if venue else ""
    punct = "" if authors.endswith(".") else "."
    text = '%s%s %d. "%s."%s.' % (authors, punct, year, title, tail)

    surname = parts[0].split(",")[0] if parts else "Anon"
    surname = re.sub(r"[^A-Za-z\-]", "", surname) or "Anon"
    return text, surname, year


def build_references(lines):
    """Return (map n->key, ordered list of (key, label, chicago_text))."""
    refs = {}
    for s in lines:
        m = re.match(r"^\[(\d+)\]\s*(.+)$", s.strip())
        if m:
            refs[int(m.group(1))] = m.group(2)

    parsed = {}
    for n, body in refs.items():
        text, surname, year = chicago(body)
        parsed[n] = {"text": text, "surname": surname, "year": year}

    groups = {}
    for n in sorted(parsed):
        groups.setdefault((parsed[n]["surname"], parsed[n]["year"]), []).append(n)
    for (_, _y), ns in groups.items():
        for k, n in enumerate(ns):
            suffix = "abcdefgh"[k] if len(ns) > 1 else ""
            parsed[n]["ysuf"] = "%d%s" % (parsed[n]["year"], suffix)
            parsed[n]["label"] = "%s(%d%s)" % (parsed[n]["surname"], parsed[n]["year"], suffix)
            parsed[n]["key"] = re.sub(r"[^a-z]", "", parsed[n]["surname"].lower()) + parsed[n]["ysuf"]

    order = sorted(parsed, key=lambda n: (parsed[n]["surname"].lower(),
                                          parsed[n]["year"], n))
    CITE["map"] = {n: parsed[n]["key"] for n in parsed}
    return [parsed[n] for n in order]


# ------------------------------------------------------------------ preamble
PREAMBLE = r"""\documentclass{interact}
%% International Journal of Remote Sensing submission.
%% Taylor & Francis Interact layout class (v1.05), single column for review.
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\usepackage{url}
\usepackage[authoryear,round]{natbib}
\bibpunct{(}{)}{;}{a}{}{,}
\graphicspath{{figures/}{../figures/}}
\newlength{\tblavail}
%% Floats may take a page top or a float page, never a page bottom: bottom
%% placement let a figure and a table collide, which drew the figure outside the
%% text block. The publisher redoes the page make-up at typesetting anyway.
\usepackage{float}
%% Tighten the reference list: the class default of 1em between 19 entries
%% spills a few lines onto a nearly empty final page.
\setlength{\bibsep}{0.35em}

\begin{document}

\articletype{Research Article}

\title{@@TITLE@@}

%% AUTHOR-BEGIN
\author{\name{Zhengyang Chen\textsuperscript{a}\thanks{ORCID: 0009-0003-3310-8077}
  and Dawei Liu\textsuperscript{a}\thanks{*CONTACT Dawei Liu. Email: wjmicheal@163.com}
  and Zhiheng Liu\textsuperscript{b}}
\affil{\textsuperscript{a}Engineering University of PAP, Xi'an 710086, China;
  \textsuperscript{b}Institute of Earth Environment, Chinese Academy of Sciences,
  Xi'an 710061, China}}
%% AUTHOR-END

\maketitle

\begin{abstract}
@@ABSTRACT@@
\end{abstract}

\begin{keywords}
@@KEYWORDS@@
\end{keywords}

\noindent\small Word count: @@WORDCOUNT@@ (main text, excluding abstract,
references and declarations).

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
    lines = ["\\begin{table}[tbp]", r"\centering", r"\footnotesize",
             r"\setlength{\tabcolsep}{3pt}",
             r"\setlength{\tblavail}{\dimexpr\textwidth-%d\tabcolsep\relax}" % (2 * ncol),
             r"\begin{tabular}{%s}" % spec, r"\hline",
             " & ".join(conv(smart_quotes(c)) for c in header) + r" \\",
             r"\hline"]
    for row in body:
        row = (row + [""] * ncol)[:ncol]
        lines.append(" & ".join(conv(smart_quotes(c)) for c in row) + r" \\")
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


# IJRS declaration block, in the journal's terminology
DECLS = [
    ("Acknowledgements", "ACK"),
    ("Disclosure of interest", "The authors report no conflict of interest."),
    ("Funding", "This work was supported by the National Natural Science Foundation of China under Grant 42502302."),
    ("Author contributions", "CREDIT"),
    ("Declaration of generative AI use", "The authors report generative AI was not used in their research or preparation of this manuscript."),
]


def main():
    text = open(SRC, encoding="utf-8").read()
    lines = text.split("\n")

    # --- harvest the pieces
    title = lines[0].lstrip("# ").strip()
    sec = {}
    cur = None
    for ln in lines[1:]:
        m = re.match(r"^## (.+)$", ln)
        if m:
            cur = m.group(1).strip()
            sec[cur] = []
            continue
        if cur:
            sec[cur].append(ln)

    def body_of(name):
        for k in sec:
            if k.startswith(name):
                return "\n".join(sec[k])
        return ""

    # the keyword line is not a heading, so it sits inside the abstract section;
    # take only the first non-empty line, which is the abstract itself
    abstract = next((l.strip() for l in sec.get("Abstract", []) if l.strip()), "")
    kwline = next((l for l in sec.get("Keywords", []) if l.strip()), "")
    keywords = re.split("[\u2014\u2013]", kwline, maxsplit=1)[-1].strip().rstrip(".")

    refs = build_references(sec.get("References", []))
    n_refs = len(refs)

    # data availability text is carried over; acknowledgements regenerate
    avail = body_of("Data availability").strip()
    avail = re.sub(r"(?m)^---\s*$", "", avail).strip()

    # --- assemble the body in IJRS order, demoting the subsection letters
    ORDER = [("1. Introduction", "Introduction", "sec:introduction"),
             ("2. Related work", "Related work", "sec:related"),
             ("5. Methods", "Materials and methods", "sec:methods"),
             ("3. Results", "Results", "sec:results"),
             ("4. Discussion", "Discussion", "sec:discussion")]

    chunks = []
    for old, new, lab in ORDER:
        body = body_of(old)
        body = re.sub(r"(?m)^### [A-Z]\.\s*", "### ", body)
        body = re.sub(r"(?m)^---\s*$", "", body)
        chunks.append("## %s {@%s@}\n%s" % (new, lab, body.strip("\n")))

    body_all = "\n\n".join(chunks)

    # --- word count over the prose only
    prose = [l for l in body_all.split("\n")
             if not l.strip().startswith("|")
             and not re.match(r"^\*\*(TABLE|Fig\.)", l.strip())]
    n_words = len(re.findall(r"[A-Za-z][A-Za-z'\-]*", " ".join(prose)))

    # --- references in the body: numeric markers become author-date citations
    body_all = cite_sub(body_all)

    # --- declarations
    decl_items = [
        ("Acknowledgements",
         "The authors thank the maintainers of the AID, RSSCN7, UCMerced, and "
         "WHU-RS19 benchmarks, whose public release made this audit possible. "
         "The audit uses only released per-image evaluation artifacts and no "
         "restricted data."),
        ("Disclosure of interest", "The authors report no conflict of interest."),
        ("Funding",
         "This work was supported by the National Natural Science Foundation of "
         "China under Grant 42502302."),
        ("Data availability statement", avail),
        ("Author contributions",
         "**Zhengyang Chen:** conceptualisation, methodology, software, formal "
         "analysis, investigation, writing - original draft. "
         "**Dawei Liu:** supervision, methodology, validation, writing - review "
         "and editing. "
         "**Zhiheng Liu:** data curation, resources, validation, writing - review "
         "and editing."),
        ("Declaration of generative AI use",
         "The authors report generative AI was not used in their research or "
         "preparation of this manuscript."),
    ]
    decl = ["## %s\n\n%s" % (h, b) for h, b in decl_items]

    md = ["# %s\n" % title,
          "<!-- International Journal of Remote Sensing submission master, generated "
          "by code/s1_make_ijrs.py from P0S1_SciRep_v1.md. -->\n",
          "## Abstract\n\n%s\n" % abstract,
          "**Keywords**\u2014%s\n" % keywords,
          "**Word count:** %d (main text, excluding abstract, references and "
          "declarations)\n" % n_words,
          body_all,
          "\n".join(decl),
          "## References\n\n" + "\n\n".join(r["text"] for r in refs)]
    md_out = "\n\n---\n\n".join(md) + "\n"
    with open(DST_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md_out)

    # ------------------------------------------------------------------ LaTeX
    tex = [PREAMBLE.replace("@@TITLE@@", conv(title, False))
           .replace("@@ABSTRACT@@", conv(abstract, False))
           .replace("@@KEYWORDS@@", esc(keywords.replace(";", r"\sep ")))
           .replace("@@WORDCOUNT@@", "{:,}".format(n_words))]

    lines_t = body_all.split("\n")
    i = 0
    while i < len(lines_t):
        s = lines_t[i].strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^## (.+?) \{@([^}@]*)@\}$", s)
        if m:
            tex.append("\\section{%s}\\label{%s}" % (conv(m.group(1), False), m.group(2)))
            i += 1
            continue
        m = re.match(r"^### (.+?)(?: \{@([^}@]*)@\})?$", s)
        if m:
            lab = ("\\label{%s}" % m.group(2)) if m.group(2) else ""
            tex.append("\\subsection{%s}%s" % (conv(m.group(1), False), lab))
            i += 1
            continue
        m = re.match(r"^\*\*TABLE\s+(?:S(\d+)|([IVX]+))\.\s*(.+?)\*\*$", s)
        if m:
            roman = SI_ORDER[int(m.group(1)) - 1] if m.group(1) else m.group(2)
            j = i + 1
            while j < len(lines_t) and not lines_t[j].strip():
                j += 1
            rows = []
            while j < len(lines_t) and lines_t[j].strip().startswith("|"):
                rows.append(lines_t[j])
                j += 1
            cells = [split_row(r) for r in rows]
            if len(cells) >= 2:
                tex.append(build_table(roman, m.group(3), cells[0], cells[2:]))
            i = j
            continue
        m = re.match(r"^\*\*Fig\.\s+(\d+)\.\s*(.+?)\*\*\s*(.*)$", s)
        if m:
            num = int(m.group(1))
            tex.append("\n".join([
                "\\begin{figure}[tbp]", r"\centering",
                r"\includegraphics[width=%s]{%s}" % (FIG_WIDTH,
                                                     FIG_FILES.get(num, "fig%d.pdf" % num)),
                r"\caption{%s}" % conv(smart_quotes(m.group(2)), False),
                r"\label{fig:%d}" % num, r"\end{figure}"]))
            if m.group(3).strip():
                tex.append(line_tex(m.group(3).strip()))
            i += 1
            continue
        if re.match(r"^\d{1,2}\.\s", s):
            items = []
            while i < len(lines_t) and re.match(r"^\d{1,2}\.\s", lines_t[i].strip()):
                items.append("\\item %s"
                             % line_tex(re.sub(r"^\d{1,2}\.\s", "", lines_t[i].strip())))
                i += 1
            tex.append("\\begin{enumerate}\n%s\n\\end{enumerate}" % "\n".join(items))
            continue
        tex.append(line_tex(s))
        i += 1

    # declarations
    for head, bodytxt in decl_items:
        tex.append("\\section*{%s}\n\n%s" % (conv(head, False), line_tex(bodytxt)))

    # references, alphabetical, author-date
    bib = ["\\begin{thebibliography}{%d}" % n_refs]
    for r in refs:
        bib.append("\\bibitem[%s]{%s}\n%s" % (r["label"], r["key"], esc(r["text"])))
    bib.append("\\end{thebibliography}")
    tex.append("\n".join(bib))
    tex.append("\\end{document}")

    doc = "\n\n".join(tex) + "\n"
    with open(DST_TEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    # ------------------------------------------------------------------ report
    print("wrote %s (%d bytes)" % (DST_MD, len(md_out.encode("utf-8"))))
    print("wrote %s (%d bytes)" % (DST_TEX, len(doc.encode("utf-8"))))
    print("title words   :", len(title.split()))
    print("abstract words:", len(abstract.split()), "(IJRS limit 300)")
    print("word count    :", n_words)
    print("references    :", n_refs, "| keys unique:",
          len({r["key"] for r in refs}) == n_refs)
    cites = set(re.findall(r"\\citep\{([^}]+)\}", body_all))
    keys = {r["key"] for r in refs}
    print("citations     :", len(re.findall(r"\\citep\{", body_all)),
          "| undefined:", sorted(cites - keys) or "none",
          "| unused:", sorted(keys - cites) or "none")
    left = re.findall(r"(?<![\w{*\\])\[\d+\]", doc)
    print("unconverted   :", sorted(set(left)) or "none")
    print("markers left  :", doc.count("{@"), "(must be 0 in the tex)")
    refs_tex = set(re.findall(r"\\ref\{([^}]+)\}", doc))
    labs = set(re.findall(r"\\label\{([^}]+)\}", doc))
    print("dangling refs :", sorted(refs_tex - labs) or "none")
    print("sections      :", re.findall(r"\\section\{([^}]+)\}", doc))
    print("bib sample    :", refs[0]["text"][:120])


if __name__ == "__main__":
    main()
