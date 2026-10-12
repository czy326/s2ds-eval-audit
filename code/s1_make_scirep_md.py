#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1: restructure the IEEE-format Markdown into a Scientific Reports master.

Input : <OUT>/P0S1_JSTARS_v1.md      (the existing source of truth)
Output: <OUT>/P0S1_SciRep_v1.md      (Introduction / Related work / Results /
                                      Discussion / Methods, Nature-style)
        <OUT>/P0S1_SciRep_SI.md       (the three tables moved out of the main text)

The restructuring is mechanical: sections are reordered and renamed, never
retyped, so the prose cannot drift away from the version whose numbers were
verified. Only three pieces of text are authored here, and they are marked
below: the Scientific Reports title, the 200-word abstract, and the keyword
list. The journal caps the abstract at 200 words and the display items at 8
combined, which is why three tables move to the supplementary information.
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
SRC = os.path.join(OUT, "P0S1_JSTARS_v1.md")
DST = os.path.join(OUT, "P0S1_SciRep_v1.md")
DST_SI = os.path.join(OUT, "P0S1_SciRep_SI.md")

# --------------------------------------------------------------- authored text
TITLE = ("Evaluation protocol choices, not method quality, decide the ranking in "
         "remote sensing super-resolution benchmarks")

ABSTRACT = (
    "Super-resolution papers for remote sensing routinely advertise gains as a "
    "single number, for instance that a method exceeds the state of the art by "
    "0.1 dB. Those numbers rest on protocol choices that are rarely reported: "
    "which images form the test set, how per-image metrics are aggregated, how "
    "many training seeds are run, and which baseline convention defines the "
    "endpoint. We audit these choices on 170 existing runs spanning four remote "
    "sensing super-resolution benchmarks, reusing stored per-image evaluation "
    "artifacts and training nothing. A path-level check confirms that every run "
    "within a benchmark evaluates an identical image set, so the instability we "
    "report is not a data-engineering artifact. Changing only the aggregation "
    "rule flips the top-ranked method on all four benchmarks. Across 327 method "
    "pairs, 25.4% reverse sign between training seeds and 52.6% have an effect "
    "smaller than the reference method's seed-to-seed standard deviation, whose "
    "median is 0.088 dB against method effects of 0.018 to 0.039 dB. A survey "
    "of 35 papers from 2026, with 18 full texts retrieved, finds that 7 state a "
    "verifiable dB gain, that no abstract mentions seeds, variance, or "
    "statistical testing, and that 4 disclose seed counts in the body. We close "
    "with a seven-item reproducibility scorecard."
)

KEYWORDS = ("Super-resolution; Benchmark evaluation; Reproducibility; "
            "Statistical significance; Model ranking; Earth observation")

# --------------------------------------------- label renames and table moves
# Explicit labels attached to headings as {@label@} markers. The LaTeX stage
# reads them, so reordering a section can never invalidate a cross reference.
LBL = {
    "1. Introduction": "sec:introduction",
    "2. Related work": "sec:related",
    "3. Results": "sec:results",
    "4. Discussion": "sec:discussion",
    "5. Methods": "sec:methods",
    "The leaderboard rests on unreported choices": "sec:unreported",
    "Opening evidence: a well-documented paper that still ranks by mean": "sec:opening",
    "What existing evaluation critiques address": "sec:prior",
    "Contributions": "sec:contributions",
    "Metric trustworthiness": "sec:metric",
    "Downstream correlation": "sec:downstream",
    "Protocol standardization": "sec:standard",
    "Cross-method fairness": "sec:fairness",
    "Statistical reporting norms": "sec:reporting",
    "Benchmark scale in remote sensing": "sec:scale",
    "Line A: the test sets are identical": "sec:testsets",
    "Line B: the champion changes on all four benchmarks": "sec:champion",
    "Lines C and D: effect size against seed noise": "sec:noise",
    "Line E: the pipeline reproduces a known result": "sec:anchor",
    "Report-practice statistics": "sec:survey",
    "Full texts change the seed count": "sec:fulltext",
    "Claimed gains against the noise floor": "sec:gains",
    "Positive exemplars": "sec:exemplars",
    "Two failure modes with names": "sec:failures",
    "Closed access limits external audit": "sec:closed",
    "The R1 to R7 reproducibility scorecard": "sec:scorecard",
    "This is a norm problem, not a capability problem": "sec:norm",
    "What the ranking instability means for remote sensing applications": "sec:applications",
    "The audit joins a shift already under way": "sec:shift",
    "Recommendations": "sec:recommend",
    "Consequences for reading a ranking": "sec:reading",
    "Limitations": "sec:limitations",
    "Conclusion": "sec:conclusion",
    "Data and assets": "sec:assets",
    "Four audit lines": "sec:lines",
    "Pairing discipline and a grouping bug": "sec:pairing",
    "Coding scheme and evidence tiers": "sec:coding",
}

# old Roman cross references  ->  labelled reference
SEC_REF_MAP = [
    ("Section VII-D", "Section~\\ref{sec:recommend}"),
    ("Section VII", "Section~\\ref{sec:discussion}"),
    ("Section VIII", "Section~\\ref{sec:limitations}"),
    ("Section IX", "Section~\\ref{sec:conclusion}"),
    ("Section VI", "Section~\\ref{sec:scorecard}"),
    ("Section V-C", "Section~\\ref{sec:fulltext}"),
    ("Section V-D", "Section~\\ref{sec:gains}"),
    ("Section V", "Section~\\ref{sec:survey}"),
    ("Section IV-C", "Section~\\ref{sec:noise}"),
    ("Section IV-D", "Section~\\ref{sec:anchor}"),
    ("Section IV", "Section~\\ref{sec:results}"),
    ("Section III", "Section~\\ref{sec:methods}"),
    ("Section II", "Section~\\ref{sec:related}"),
    ("Section I", "Section~\\ref{sec:introduction}"),
]

# old Roman table number  ->  (replacement token, destination). The supplementary
# tables are referred to by literal label, not by \ref, because they are printed
# in a separate document and a cross-document \ref cannot resolve.
TABLE_MAP = {
    "I":   ("Table~\\ref{tab:srbench}", "main"),
    "II":  ("Supplementary Table S1", "si"),
    "III": ("Table~\\ref{tab:conventions}", "main"),
    "IV":  ("Table~\\ref{tab:effect}", "main"),
    "V":   ("Supplementary Table S2", "si"),
    "VI":  ("Supplementary Table S3", "si"),
    "VII": ("Table~\\ref{tab:practice}", "main"),
    "VIII": ("Table~\\ref{tab:gains}", "main"),
    "IX":  ("Table~\\ref{tab:scorecard}", "main"),
}

# old TABLE heading -> new heading (label, destination, caption kept)
TABLE_ORDER = ["I", "III", "IV", "VII", "VIII", "IX", "II", "V", "VI"]

DECLARATIONS = """
---

## Author contributions

Z.C. designed the audit, wrote the analysis code, ran all computations, and wrote the manuscript. D.L. supervised the study, defined the statistical evaluation protocol, and revised the manuscript. Z.L. assembled the survey corpus, verified the bibliographic records, and revised the manuscript. All authors reviewed and approved the final manuscript.

---

## Data availability

The audit code, the per-image evaluation records for all 170 runs, every result file, and both figures are available at `https://github.com/czy326/s2ds-eval-audit`. The repository is self-contained. Running `code/run_audit_chain.py` regenerates the audit result files from the shipped per-image records, and the regenerated files are identical to the shipped ones. The chain includes the anchor in the reproducibility check, which reproduces a known result before any negative finding is reported.

The four benchmark datasets (AID, RSSCN7, UCMerced, WHU-RS19) are public and are not redistributed, because the audit reads only stored metric values and image path strings, not pixels. Publisher PDFs and HTML retrieved during the 35-paper survey are not redistributed, because most are copyrighted. The derived codings are shipped in the repository, and an index recording which source files were read is included so the codings can be checked.

The reference list is shipped with the repository. Every bibliographic field is copied from a Crossref, arXiv or OpenAlex record, and the source is named for each entry. Eight entries could not be completed and are flagged. One of those eight is the case in which the DOI carried in the survey pool resolved at Crossref to a paper with an unrelated title. The true record was recovered by querying Crossref with the publisher's article identifier as an alternative-id.

---

## Additional Information

**Competing interests.** The authors declare no competing interests.

---

## Acknowledgements

The authors thank the maintainers of the AID, RSSCN7, UCMerced, and WHU-RS19 benchmarks, whose public release made this audit possible. The audit uses only released per-image evaluation artifacts and no restricted data. This work was supported by the National Natural Science Foundation of China under Grant 42502302.
"""

# section order in the new document, with new titles
ORDER = [
    ("1. Introduction", "1. Introduction"),
    ("2. Related Work", "2. Related work"),
    ("4. Results I: Controlled Audit of 170 Runs", "3. Results"),
    ("5. Results II: Report Practice in 35 Papers", None),   # folded into Results
    ("6. The R1 to R7 Reproducibility Scorecard", None),     # folded into Results
    ("7. Discussion", "4. Discussion"),
    ("8. Limitations", None),                                # folded into Discussion
    ("9. Conclusion", None),                                 # folded into Discussion
    ("3. Audit Design", "5. Methods"),
]


# A short call-out added to the paragraph that precedes a display item, for any
# item the manuscript never cites in its text. Without it a reader has no
# pointer to the item, and the journal's submission checklist requires the
# in-text citations and the supplied files to agree.
CALLOUT = {
    "IV": "Table~\\ref{tab:effect} collects these counts.",
    "VII": "Table~\\ref{tab:practice} reports the full breakdown.",
    "VIII": "Table~\\ref{tab:gains} lists the seven claims against the noise floor of their own benchmarks.",
    "IX": "Table~\\ref{tab:scorecard} states each check and the failure its omission produces.",
    "fig1": "Fig.~\\ref{fig:1} shows this relation.",
    "fig2": "Fig.~\\ref{fig:2} shows all 327 pairs.",
}


def split_sections(text):
    """Return {heading: body} for every '## ' section, plus any preamble."""
    parts = re.split(r"(?m)^## ", text)
    pre = parts[0]
    out = {}
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        out[head.strip()] = body
    return pre, out


def rewrite_xrefs(s):
    for old, new in SEC_REF_MAP:
        s = s.replace(old, new)
    # tables: longest Roman numeral first so 'Table III' is not hit by 'Table II'
    for old in sorted(TABLE_MAP, key=len, reverse=True):
        tok = TABLE_MAP[old][0]
        s = re.sub(r"Table %s\b" % old, tok.replace("\\", "\\\\"), s)
    # Figure caption definitions are turned into floats by the LaTeX stage, so
    # they must keep their 'Fig. N.' form. Only inline references are rewritten.
    out = []
    for ln in s.split("\n"):
        if not re.match(r"^\*\*Fig\. \d+\.", ln.strip()):
            ln = re.sub(r"Fig\. ?(\d)\b",
                        lambda m: "Fig.~\\ref{fig:%s}" % m.group(1), ln)
        out.append(ln)
    return "\n".join(out)


def main():
    text = open(SRC, encoding="utf-8").read()
    pre, sec = split_sections(text)

    # --- main tables stay where the manuscript discusses them; only the three
    # supplementary tables are lifted out into their own document.
    table_blocks = {}
    for head in list(sec):
        lines = sec[head].split("\n")
        out_lines, i = [], 0
        while i < len(lines):
            s = lines[i].strip()
            m = re.match(r"^\*\*TABLE\s+([IVX]+)\.\s*(.+?)\*\*$", s)
            if m and TABLE_MAP.get(m.group(1), ("", "main"))[1] == "si":
                roman, cap = m.group(1), m.group(2)
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                rows = []
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append(lines[j])
                    j += 1
                table_blocks[roman] = (cap, rows)
                i = j
                continue
            out_lines.append(lines[i])
            i += 1
        sec[head] = "\n".join(out_lines)

    if len(table_blocks) != 3:
        raise SystemExit("expected 3 supplementary tables, found %d" % len(table_blocks))

    # --- add a call-out before any display item the text never cites
    for head in list(sec):
        lines = sec[head].split("\n")
        out = []
        for idx, ln in enumerate(lines):
            m = re.match(r"^\*\*TABLE\s+([IVX]+)\.", ln.strip())
            f = re.match(r"^\*\*Fig\.\s+(\d+)\.", ln.strip())
            key = m.group(1) if m else ("fig%s" % f.group(1) if f else None)
            if key and key in CALLOUT:
                j = len(out) - 1
                while j >= 0 and not out[j].strip():
                    j -= 1
                if j >= 0 and not out[j].lstrip().startswith(("|", "#", ">")):
                    # attach to the paragraph that discusses the item
                    out[j] = out[j].rstrip() + " " + CALLOUT[key]
                else:
                    # the item opens a subsection, so it needs its own lead-in
                    out.append("")
                    out.append(CALLOUT[key])
                    out.append("")
            out.append(ln)
        sec[head] = "\n".join(out)

    # --- build the new body
    def emit(head_old, head_new, extra_bodies=()):
        chunks = ["## %s\n" % head_new]
        body = sec[head_old]
        chunks.append(rewrite_xrefs(body).strip("\n"))
        for e in extra_bodies:
            chunks.append(rewrite_xrefs(sec[e]).strip("\n"))
        return "\n\n".join(c for c in chunks if c.strip())

    # renumber the subsections of Results and Discussion contiguously
    def reletter(block, start=0):
        n = [start]

        def rep(m):
            letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[n[0]]
            n[0] += 1
            return "### %s. %s" % (letter, m.group(2))
        return re.sub(r"(?m)^### ([A-Z])\. (.+)$", rep, block), n[0]

    results = emit("4. Results I: Controlled Audit of 170 Runs", "3. Results")
    results, k1 = reletter(results)
    # the second results section is split: the coding scheme is a method, the
    # rest is results. Methods words are excluded from the 4,500-word count.
    subs = re.split(r"(?m)^### ", sec["5. Results II: Report Practice in 35 Papers"])
    coding = subs[1]                      # 'A. Coding scheme and evidence tiers'
    rest = "### " + "### ".join(subs[2:])
    tail = rewrite_xrefs(rest).strip("\n")
    tail, k2 = reletter(tail, k1)
    tail2 = rewrite_xrefs(sec["6. The R1 to R7 Reproducibility Scorecard"]).strip("\n")
    score_letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[k2]
    tail2 = "### %s. The R1 to R7 reproducibility scorecard\n\n%s" % (score_letter, tail2)
    results = "\n\n".join([results, tail, tail2])
    coding_block = "### " + rewrite_xrefs(coding).strip("\n")

    disc = emit("7. Discussion", "4. Discussion")
    disc, d1 = reletter(disc)
    lim = "### %s. Limitations\n\n%s" % ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[d1],
                                        rewrite_xrefs(sec["8. Limitations"]).strip("\n"))
    con = "### %s. Conclusion\n\n%s" % ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[d1 + 1],
                                        rewrite_xrefs(sec["9. Conclusion"]).strip("\n"))
    disc = "\n\n".join([disc, lim, con])

    intro = emit("1. Introduction", "1. Introduction")
    intro, _ = reletter(intro)
    rel = emit("2. Related Work", "2. Related work")
    rel, _ = reletter(rel)
    meth = emit("3. Audit Design", "5. Methods")
    meth, m1 = reletter(meth)
    coding_block, _ = reletter(coding_block, m1)
    meth = "\n\n".join([meth, coding_block])

    doc = ["# %s\n" % TITLE,
           "<!-- Scientific Reports submission master, generated by "
           "code/s1_make_scirep_md.py from P0S1_JSTARS_v1.md. -->\n",
           "## Abstract\n\n%s\n" % ABSTRACT,
           "**Keywords**\u2014%s\n" % KEYWORDS,
           intro, rel, results, disc, meth]

    # references, verbatim from the source
    doc.append("## References\n\n%s" % sec["References"].strip("\n"))

    doc.append(DECLARATIONS.strip("\n"))

    out = "\n\n---\n\n".join(doc) + "\n"

    # --- attach the label markers and refuse to emit an unlabelled heading
    def sub_heading(m):
        key = m.group(2).strip()
        if key not in LBL:
            raise SystemExit("subsection without a label: %r" % key)
        return "### %s. %s {@%s@}" % (m.group(1), key, LBL[key])

    def sec_heading(m):
        key = "%s. %s" % (m.group(1), m.group(2).strip())
        if key not in LBL:
            raise SystemExit("section without a label: %r" % key)
        return "## %s {@%s@}" % (key, LBL[key])

    out = re.sub(r"(?m)^### ([A-Z])\. (.+)$", sub_heading, out)
    out = re.sub(r"(?m)^## ([0-9])\. (.+)$", sec_heading, out)

    missing = sorted(t for t in LBL if ("{@%s@}" % LBL[t]) not in out)
    if missing:
        raise SystemExit("labels defined but never attached: %s" % missing)

    with open(DST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)

    # --- supplementary document
    slines = ["# Supplementary information",
              "<!-- Supplementary tables for the Scientific Reports submission. -->",
              "## Supplementary tables\n",
              "Tables S1 to S3 carry the supporting audit detail that would take "
              "the main text past the eight-display-item limit.\n"]
    for n, roman in enumerate(["II", "V", "VI"], start=1):
        cap, rows = table_blocks[roman]
        slines.append("**TABLE S%d. %s**\n" % (n, cap))
        slines.append("\n".join(rows))
        slines.append("")
    with open(DST_SI, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(slines) + "\n")

    # ------------------------------------------------------------------ report
    plain = len(re.findall(r"[A-Za-z][A-Za-z'-]*", ABSTRACT))
    print("wrote %s (%d bytes)" % (DST, len(out.encode("utf-8"))))
    print("wrote %s" % DST_SI)
    print("title words          :", len(TITLE.split()))
    print("abstract words       :", plain)
    print("main tables (inline) :", len(re.findall(r"(?m)^\*\*TABLE [IVX]+\.", out)))
    print("supplementary tables :", len(table_blocks))
    body_only = out.split("## References")[0]
    main_labels = ["tab:srbench", "tab:conventions", "tab:effect", "tab:practice",
                   "tab:gains", "tab:scorecard", "fig:1", "fig:2"]
    missing = [l for l in main_labels if ("\\ref{%s}" % l) not in body_only]
    print("display items with no in-text call-out:", missing or "none")
    # display items are not prose, so table rows and caption lines are excluded
    def prose(s):
        keep = [l for l in s.split("\n")
                if not l.strip().startswith("|")
                and not re.match(r"^\*\*(TABLE|Fig\.)", l.strip())]
        return " ".join(keep)

    main = sum(len(re.findall(r"[A-Za-z][A-Za-z'-]*", prose(b)))
               for b in [intro, rel, results, disc])
    print("approx main text     :", main, "(Methods excluded, target <= 4500)")
    left = re.findall(r"Section [IVX]+|Table [IVX]+", out)
    print("unconverted xrefs    :", sorted(set(left)) if left else "none")


if __name__ == "__main__":
    main()
