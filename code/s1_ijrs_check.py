# -*- coding: utf-8 -*-
"""
International Journal of Remote Sensing submission check.

Asserts what the journal's instructions specify and what the restructuring has
to get right: title and abstract limits, the prescribed section order, the
mandatory declarations, author-date rather than numeric citations, an
alphabetical reference list, a word count, and LaTeX integrity.

Exit status is non-zero if any check fails.
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
_OUT = next((c for c in _CANDS
             if c and os.path.exists(os.path.join(c, "P0S1_IJRS_v1.md"))),
            _CANDS[-1])

MD = os.path.join(_OUT, "P0S1_IJRS_v1.md")
TEX = os.path.join(_OUT, "P0S1_IJRS_v1.tex")
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def main():
    md = open(MD, encoding="utf-8").read()
    tex = open(TEX, encoding="utf-8").read() if os.path.exists(TEX) else ""

    # ------------------------------------------------------------- framing
    title = md.split("\n", 1)[0].lstrip("# ").strip()
    # take the first non-empty line under the heading: a multiline regex here
    # can run past the abstract into the keyword block
    lines = md.split("\n")
    abstract = ""
    if "## Abstract" in lines:
        i0 = lines.index("## Abstract")
        abstract = next((l.strip() for l in lines[i0 + 1:] if l.strip()), "")
    check("abstract_present", bool(abstract))
    check("abstract_le_300_words", len(abstract.split()) <= 300,
          "%d words" % len(abstract.split()))
    check("abstract_unstructured", not re.search(r"\*\*|\\textbf", abstract))
    check("abstract_uncited", not re.search(r"\[\d+\]|\\cite", abstract))
    check("title_present", 5 <= len(title.split()) <= 25, "%d words" % len(title.split()))
    kw = next((l for l in md.split("\n") if l.startswith("**Keywords**")), "")
    kw_text = re.sub(r"^\*\*Keywords\*\*\s*[\u2014\u2013-]\s*", "", kw).strip()
    check("keywords_present", "**Keywords**" in md)
    check("keywords_nonempty", bool(kw_text), "%d chars" % len(kw_text))
    check("keywords_count", 3 <= len([k for k in kw_text.split(";") if k.strip()]) <= 8,
          "%d terms" % len([k for k in kw_text.split(";") if k.strip()]))
    check("word_count_stated", "**Word count:**" in md, "required by the journal")

    # ------------------------------------------------------------- structure
    want = ["Introduction", "Related work", "Materials and methods",
            "Results", "Discussion"]
    have = re.findall(r"(?m)^## (\w[\w ]*?) \{@", md)
    check("section_order", have == want, " -> ".join(have))
    check("methods_before_results",
          md.find("## Materials and methods") < md.find("## Results"))

    # ---------------------------------------------------------- declarations
    for head in ["Acknowledgements", "Disclosure of interest", "Funding",
                 "Data availability statement", "Author contributions",
                 "Declaration of generative AI use"]:
        check("decl_%s" % head.split()[0].lower(), ("## " + head) in md)

    # ------------------------------------------------------------- citations
    body = re.sub(r"(?m)^\[\d+\]\s.*$", "", md)
    check("no_numeric_markers", not re.search(r"(?<![\w{*\\])\[\d+\]", body))
    check("author_date_citations", len(re.findall(r"\\citep\{", md)) > 0,
          "%d citations" % len(re.findall(r"\\citep\{", md)))
    check("no_numeric_in_tex", not re.search(r"(?<![\w*{])\[\d+\]", tex))

    # reference list alphabetical by surname
    sec = md.split("## References", 1)[-1]
    entries = [e for e in sec.split("\n") if e.strip()]
    surnames = [e.split(",")[0].strip().lower() for e in entries if "," in e]
    check("reference_count", len(entries) == 31, "%d entries" % len(entries))
    check("references_alphabetical", surnames == sorted(surnames),
          next((surnames[i] for i in range(1, len(surnames))
                if surnames[i] < surnames[i - 1]), ""))
    check("references_author_date",
          all(re.search(r"\.\s*(19|20)\d\d\.", e) for e in entries),
          "year follows the author list in every entry")
    check("no_ieee_vol_no",
          not any(re.search(r"\bvol\.\s*\d+|,\s*no\.\s*\d+", e) for e in entries))

    # ----------------------------------------------------------- latex health
    if tex:
        check("tex_class_interact", tex.startswith("\\documentclass{interact}"))
        check("tex_natbib_authoryear", "authoryear" in tex)
        labels = re.findall(r"\\label\{([^}]+)\}", tex)
        refs = set(re.findall(r"\\ref\{([^}]+)\}", tex))
        cites = {k.strip()
                 for grp in re.findall(r"\\cite[a-z]*\{([^}]+)\}", tex)
                 for k in grp.split(",")}
        bibs = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", tex))
        check("tex_labels_unique", len(labels) == len(set(labels)), "%d" % len(labels))
        check("tex_no_dangling_ref", not (refs - set(labels)), str(sorted(refs - set(labels))))
        check("tex_cites_defined", not (cites - bibs), str(sorted(cites - bibs)))
        check("tex_no_unused_bibitem", not (bibs - cites))
        check("tex_no_markers", "{@" not in tex)
        kwm = re.search(r"\\begin\{keywords\}(.*?)\\end\{keywords\}", tex, re.S)
        check("tex_keywords_nonempty", bool(kwm and kwm.group(1).strip()),
              "the class prints a KEYWORDS heading even when the block is empty")
        check("tex_no_mangled", "textbackslash" not in tex)
        check("tex_tables", tex.count(r"\begin{table}") == 6)
        check("tex_figures", tex.count(r"\begin{figure}") == 2)
        check("tex_declarations",
              tex.count(r"\section*{") >= 6, "%d" % tex.count(r"\section*{"))
    else:
        check("tex_exists", False, TEX)

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
