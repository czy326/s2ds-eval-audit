# -*- coding: utf-8 -*-
"""
Render the Scientific Reports cover letter from Markdown to PDF.

Input : <OUT>/P0S1_SciRep_CoverLetter.md
Output: <OUT>/P0S1_SciRep_CoverLetter.tex and .pdf

The journal accepts the cover letter as .doc, .docx or .pdf, so a plain PDF is
enough. This is a thin wrapper rather than a document pipeline: the letter is
static text, and only needs to be recompiled when it is edited.
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

SRC = os.path.join(OUT, "P0S1_SciRep_CoverLetter.md")
TEX = os.path.join(OUT, "P0S1_SciRep_CoverLetter.tex")

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=1in]{geometry}
\usepackage{xcolor}
\usepackage{parskip}
\pagestyle{plain}

\begin{document}
"""


def esc(s):
    s = s.replace("\\", r"\textbackslash{}")
    s = s.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    s = s.replace("_", r"\_").replace("$", r"\$")
    s = s.replace("\u2014", "---").replace("\u2013", "--")
    s = s.replace("``", "``").replace("'", "'")
    return s


def inline(s):
    # [[FILL: ...]] markers are shown in red so they cannot be missed
    s = re.sub(r"\[\[(.+?)\]\]",
               lambda m: r"\textcolor{red}{[" + esc(m.group(1)) + "]}", s)
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: r"\textbf{" + esc(m.group(1)) + "}", s)
    s = re.sub(r"`([^`]+)`", lambda m: r"\texttt{" + esc(m.group(1)) + "}", s)
    if not s.startswith("\\"):
        s = esc(s)
    return s


def convert(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s in ("---", "***"):
            out.append(r"\medskip\hrule\medskip")
            i += 1
            continue
        if s.startswith("# "):
            out.append("\\begin{center}{\\large\\bfseries %s}\\end{center}" % inline(s[2:]))
            i += 1
            continue
        if s.startswith("## "):
            out.append(r"\medskip\noindent\textbf{%s}" % inline(s[3:]))
            i += 1
            continue
        if re.match(r"^\d+\.\s", s):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(r"\item %s" % inline(re.sub(r"^\d+\.\s", "", lines[i].strip())))
                i += 1
            out.append("\\begin{enumerate}\n%s\n\\end{enumerate}" % "\n".join(items))
            continue
        out.append(inline(s))
        i += 1
    return "\n\n".join(out)


def main():
    md = open(SRC, encoding="utf-8").read()
    with open(TEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(PREAMBLE + convert(md) + "\n\n\\end{document}\n")
    print("wrote %s" % TEX)


if __name__ == "__main__":
    main()
