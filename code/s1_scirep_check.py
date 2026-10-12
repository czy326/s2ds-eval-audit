# -*- coding: utf-8 -*-
"""
Scientific Reports submission check.

Three groups of assertions:

  1. journal limits  - title <= 20 words, abstract <= 200 words and uncited,
                       <= 6 keywords, <= 8 display items, <= 60 references.
  2. structure       - Introduction / Related work / Results / Discussion /
                       Methods present, with Methods last, plus the mandatory
                       Author contributions, Data availability, Additional
                       Information and Acknowledgements statements.
  3. integrity       - no unconverted numeric citation, no dangling or mangled
                       cross reference, every reference cited, and every decimal
                       figure in the Scientific Reports text also present in the
                       IEEE text whose numbers code/s1_jstars_check.py verifies.

That last check is what keeps the two venue versions from drifting apart: the
Scientific Reports text is a restructured subset of the verified text, so any
number that appears in one and not the other is a transcription error.

Run from anywhere. Exit status is non-zero if any check fails.
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
_OUT = next((c for c in _CANDS
             if c and os.path.exists(os.path.join(c, "P0S1_SciRep_v1.md"))),
            _CANDS[-1])
MD = os.path.join(_OUT, "P0S1_SciRep_v1.md")
SI = os.path.join(_OUT, "P0S1_SciRep_SI.md")
TEX = os.path.join(_OUT, "P0S1_SciRep_v1.tex")
REF = os.path.join(_OUT, "P0S1_JSTARS_v1.md")   # the numerically verified source

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def words(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", s))


def main():
    md = open(MD, encoding="utf-8").read()
    si = open(SI, encoding="utf-8").read()
    tex = open(TEX, encoding="utf-8").read() if os.path.exists(TEX) else ""

    # ------------------------------------------------------- journal limits
    title = md.split("\n", 1)[0].lstrip("# ").strip()
    check("title_words_le_20", words(title) <= 20, "%d words" % words(title))
    check("title_one_sentence",
          title.count(".") <= 1 and "?" not in title, "no pun or two-clause claim")

    m = re.search(r"(?ms)^## Abstract\n\n(.+?)\n", md)
    abstract = " ".join(m.group(1).split()) if m else ""
    check("abstract_present", bool(abstract))
    check("abstract_words_le_200", words(abstract) <= 200, "%d words" % words(abstract))
    check("abstract_uncited", not re.search(r"\[\d+\]|\\cite", abstract))

    m = re.search(r"(?m)^\*\*Keywords\*\*\u2014(.+)$", md)
    kws = [k for k in (m.group(1).split(";") if m else []) if k.strip()]
    check("keywords_present", bool(kws), "%d keywords" % len(kws))
    check("keywords_le_6", len(kws) <= 6)

    n_tab = len(re.findall(r"(?m)^\*\*TABLE (?!S)", md))
    n_fig = len(re.findall(r"(?m)^\*\*Fig\. \d+\.", md))
    check("display_items_le_8", n_tab + n_fig <= 8,
          "%d tables + %d figures = %d" % (n_tab, n_fig, n_tab + n_fig))
    check("tables_in_main", n_tab == 6, "%d" % n_tab)
    check("figures_in_main", n_fig == 2, "%d" % n_fig)

    refs = re.findall(r"(?m)^\[(\d+)\]\s", md)
    check("references_le_60", len(refs) <= 60, "%d" % len(refs))
    check("references_contiguous",
          [int(x) for x in refs] == list(range(1, len(refs) + 1)))

    # ------------------------------------------------------------- structure
    for want in ["## 1. Introduction", "## 2. Related work", "## 3. Results",
                 "## 4. Discussion", "## 5. Methods"]:
        check("section%s" % want.split(" ", 1)[1].replace(" ", "_"),
              want in md)
    order = [md.find("## 1."), md.find("## 2."), md.find("## 3."),
             md.find("## 4."), md.find("## 5. Methods")]
    check("methods_last", order == sorted(order) and order[-1] > 0)

    for want in ["## Author contributions", "## Data availability",
                 "## Additional Information", "## Acknowledgements"]:
        check("backmatter_%s" % want.split(" ", 1)[1].replace(" ", "_"), want in md)

    # a Results section must carry subheadings; Methods must carry the coding
    check("results_has_subheads",
          len(re.findall(r"(?m)^### [A-Z]\. ", md.split("## 3. Results")[1]
                         .split("\n## ")[0])) >= 8)
    check("methods_has_coding", "Coding scheme and evidence tiers" in md)

    # ------------------------------------------------------------- integrity
    # The Markdown keeps numeric [n] markers on purpose; they are the source
    # format and are converted to \cite in the LaTeX stage. So the assertion is
    # that every marker resolves to a reference entry, and that no marker
    # survives into the compiled source.
    # drop the reference-list entries themselves, then look for markers anywhere
    # else, including inside the table cells that sit at the end of the file
    body = re.sub(r"(?m)^\[\d+\]\s.*$", "", md)
    used = {int(x) for x in re.findall(r"\[(\d{1,2})\]", body)}
    check("markers_resolve", used <= set(range(1, len(refs) + 1)),
          "unresolved %s" % sorted(used - set(range(1, len(refs) + 1))))
    check("all_references_used", set(range(1, len(refs) + 1)) <= used,
          "never cited %s" % sorted(set(range(1, len(refs) + 1)) - used))
    check("no_numeric_citation_in_tex",
          not re.search(r"(?<![\w*{])\[\d+\]", tex))
    check("no_unconverted_marker", "{@" not in tex)

    if tex:
        labels = re.findall(r"\\label\{([^}]+)\}", tex)
        refs_tex = set(re.findall(r"\\ref\{([^}]+)\}", tex))
        cites = set(re.findall(r"\\cite\{([^}]+)\}", tex))
        bibs = set(re.findall(r"\\bibitem\{([^}]+)\}", tex))
        check("tex_labels_unique", len(labels) == len(set(labels)),
              "%d labels" % len(labels))
        check("tex_no_dangling_ref", not (refs_tex - set(labels)),
              str(sorted(refs_tex - set(labels))))
        check("tex_all_cites_defined", not (cites - bibs), str(sorted(cites - bibs)))
        check("tex_no_unused_bibitem", not (bibs - cites))
        check("tex_no_mangled_ref", "textbackslash" not in tex,
              "count=%d" % tex.count("textbackslash"))
        check("tex_table_env", tex.count(r"\begin{table}") == n_tab)
        check("tex_figure_env", tex.count(r"\begin{figure}") == n_fig)
        check("tex_supp_refs_are_literal",
              len(re.findall(r"Supplementary Table S\d", tex)) >= 1)
        check("tex_classes", tex.startswith("\\documentclass[pdflatex,sn-nature]"))
    else:
        check("tex_exists", False, TEX)

    # supplementary document
    s_tab = len(re.findall(r"(?m)^\*\*TABLE S\d", si))
    check("si_tables", s_tab == 3, "%d" % s_tab)
    check("si_not_in_main", "TABLE S1." not in md)

    # --------------------------------- numerical agreement with the verified text
    # the submission is the main text plus the supplementary tables, so both are
    # compared against the IEEE text whose numbers s1_jstars_check.py verifies
    ver = open(REF, encoding="utf-8").read()
    ver_nums = set(re.findall(r"\d+\.\d+", ver))
    sub_nums = set(re.findall(r"\d+\.\d+", md + "\n" + si))
    check("no_new_decimals", not (sub_nums - ver_nums),
          "introduced %s" % sorted(sub_nums - ver_nums)[:6])

    both = md + "\n" + si
    HEADLINE = ["170", "327", "25.4", "52.6", "47.1", "68.5", "0.088", "0.272",
                "0.1202", "0.0728", "47.3", "0.0049", "0.0849", "0.1272",
                "0.0744", "9.27", "154", "172", "224", "83", "8 of 10",
                "7 of 35"]
    for h in HEADLINE:
        check("headline_%s" % h, h in both)

    # --------------------------------------------------------------- report
    bad = [(n, d) for n, ok, d in results if not ok]
    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print("%-6s %-*s %s" % ("OK" if ok else "FAIL", width, name, detail))
    print()
    print("%d/%d checks OK, %d mismatch" % (len(results) - len(bad),
                                            len(results), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
