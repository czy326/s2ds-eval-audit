# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
Build the verifiable reference list for P0-S1  (v2).

Priority of truth, per entry:
  1. _doi_meta.json        -> Crossref/OpenAlex record keyed by resolved DOI
  2. _arxiv_meta.json      -> arXiv API record keyed by arXiv id
  3. audit_F_field_survey.json -> venue string only (for the 3 unresolved cases)

Every emitted field is copied from one of those. A field that no source
supplies is printed as **VERIFY: ...** and listed in the final summary.
Nothing is fabricated. This is the reference list for the 35-paper survey plus
the general citations, in numbered order.
"""
import json, io, os, sys, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = PROJ_ROOT
AUD = os.path.join(ROOT, "audit", "out")
OUT = os.path.join(ROOT, "out")

doi_meta = json.load(open(os.path.join(AUD, "_doi_meta.json"), encoding="utf-8"))
arxiv = json.load(open(os.path.join(AUD, "_arxiv_meta.json"), encoding="utf-8"))
_extra = os.path.join(AUD, "_arxiv_meta_extra.json")
if os.path.exists(_extra):
    arxiv.update({k.split("v")[0]: v for k, v in
                  json.load(open(_extra, encoding="utf-8")).items()})
F = json.load(open(os.path.join(AUD, "audit_F_field_survey.json"), encoding="utf-8"))
f_by_id = {p["id"]: p for p in F["papers"]}

# (survey id, bibkey, doi-key in _doi_meta.json or None, arxiv id or None)
SURVEY = [
    ("DBTSR",            "DBTSR2026",            "DBTSR",            None),
    ("ORDiffSR",         "ORDiffSR2026",         "ORDiffSR",         None),
    ("PLAN",             "PLAN2026",             "PLAN",             None),
    ("DFSMamba",         "DFSMamba2026",         "DFSMamba",         None),
    ("SFG-SwinSR",       "SFGSwinSR2026",        None,               "2605.09687"),
    ("NGram-MoSE",       "NGramMoSE2026",        "NGram-MoSE",       "2606.08535"),
    ("MT-Hybrid",        "MTHybrid2026",         "MT-Hybrid",        None),
    ("LocalStateSpace",  "LocalStateSpace2026",  "LocalStateSpace",  None),
    ("JNUN-CA",          "JNUNCA2026",           "JNUN-CA",          None),
    ("MLIN-MetaWeight",  "MLINMetaWeight2026",   "MLIN-MetaWeight",  None),
    ("PLGMamba",         "PLGMamba2026",         None,               None),
    ("Sen4x",            "Sen4x2026",            "Sen4x",            None),
    ("THREASURE-Net",    "THREASURENet2026",     None,               "2512.11524"),
    ("IR275K",           "IR275K2026",           None,               "2607.22380"),
    ("S3-ESRGAN",        "S3ESRGAN2025",         "S3-ESRGAN",        None),
    ("GrasslandGAN",     "GrasslandGAN2026",     "GrasslandGAN",     None),
    ("Text-RSIR",        "TextRSIR2026",         None,               "2605.15558"),
    ("DS-DiT (RefSR)",   "DSDiT2026",            None,               "2605.17980"),
    ("HAC-MoE",          "HACMoE2026",           "HAC-MoE",          None),
    ("DiffBSR",          "DiffBSR2026",          None,               None),
    ("AstraMoE-SR",      "AstraMoESR2026",       None,               "2609.07012"),
    ("BKX-HMM",          "BKXHMM2026",           "BKX-HMM",          None),
    ("UDAMSR",           "UDAMSR2026",           "UDAMSR",           None),
    ("VolumeNet+TT",     "VolumeNetTT2025",      "VolumeNet+TT",     None),
    ("HSISR-KAN",        "HSISRKAN2026",         None,               None),
    ("UDAMSR-mean",      "UDAMSRmean2026",       None,               None),
    ("GeoSR-Bench",      "GeoSRBench2026",       None,               "2605.00310"),
    ("NTIRE2026-SR",     "NTIRE2026SR",          None,               "2604.14558"),
    ("NTIRE2026-ESR",    "NTIRE2026ESR",         None,               None),
    ("SpectralSR-Bench", "SpectralSRBench2026",  "SpectralSR-Bench", None),
    ("SyMTRS",           "SyMTRS2026",           None,               "2604.21801"),
    ("NTIRE2026-IR",     "NTIRE2026IR",          None,               "2604.21312"),
    ("SlimDiffSR",       "SlimDiffSR2026",       None,               "2605.02198"),
    ("SDGAN-SciRep",     "SDGAN2026",            "SDGAN-SciRep",     None),
    ("EORestore-Agent",  "EORestoreAgent2026",   None,               "2610.06196"),
]

GENERAL = [
    ("LL-Bench", "LLBench2026", "arxiv", "2606.02535",
     "LL-Bench: Rethinking Low-Level Vision Evaluation in the Era of Large-Scale "
     "Generative Models. Cited for the weak IQA-versus-human-preference correlation, "
     "2,469 images, 16 tasks, 31 models, 152,020 pairwise preferences.", []),
    ("SR-Prominence", "SRProminence2026", "arxiv", "2605.14847",
     "SR-Prominence: A Crowdsourced Protocol and Dataset Suite for Perceptually-Weighted "
     "Super-Resolution. Source of the 48.2% unnoticed-artifact figure.", []),
]

SELF = [
    "BSRNet / EMSSM-SR, super-resolution with edge-aware deep fusion, closed 2026-10-04. "
    "Source of the B3 versus base_ssm anchor in Section 4.4.",
    "MISRNet / S2DS, multi-temporal Sentinel-2 super-resolution, under review. "
    "Source of the 170-run audit pool.",
    "Multi-temporal Sentinel-2 super-resolution with spectral interventions, under review.",
    "Test-set geographic composition dominates method ranking in remote sensing "
    "super-resolution evaluation, IEEE GRSL, in revision.",
    "S2DS dataset, 18 areas of interest, T=12, bands B02/B03/B04/B08.",
]


def authors_str(names, n_auth):
    if not names:
        return None
    if len(names) == 1:
        s = names[0]
    else:
        s = ", ".join(names[:-1]) + " and " + names[-1]
    if n_auth and n_auth > len(names):
        s += " et al."
    return s


rows = []       # (n, text, verify_list, bibentry)
n = 0

# ---------------------------------------------------------------- A. survey
for pid, key, dk, aid in SURVEY:
    n += 1
    verify = []
    dm = doi_meta.get(dk) if dk else None
    am = arxiv.get(aid) if aid else None
    f = f_by_id.get(pid, {})

    title = authors = venue = year = doi = None
    src = []

    if dm and dm.get("status") == "OK":
        title = dm.get("title") or None
        authors = authors_str(dm.get("authors") or [], dm.get("n_auth"))
        venue = dm.get("container") or None
        year = dm.get("year") or None
        doi = dm.get("doi")
        src.append("Crossref" if dm.get("source") == "crossref" else "OpenAlex")
        # volume/issue/pages
        bits = []
        if dm.get("volume"):
            bits.append(f"{dm['volume']}")
        if dm.get("issue"):
            bits.append(f"({dm['issue']})")
        if dm.get("page"):
            bits.append(f", {dm['page']}")
        elif dm.get("article_number"):
            bits.append(f", art. {dm['article_number']}")
        volinfo = "".join(bits)
    else:
        volinfo = ""

    if (am is not None) and (not title or pid in ("NGram-MoSE",)):
        # arXiv supplies the author list when Crossref is silent;
        # never overwrite a venue that Crossref resolved.
        if not title:
            title = am["title"].replace(r"$\times$", "x")
        if not authors:
            authors = authors_str(am["authors"], am.get("n_auth"))
        if not year:
            year = am.get("year")
        if not venue:
            venue = f"arXiv preprint arXiv:{aid}"
        src.append(f"arXiv:{aid}")

    if not title:
        title = f"[{pid}] title not retrieved"
        verify.append("title")
    if not authors:
        verify.append("authors")
    if not venue:
        venue = f.get("venue") or ""
        if venue:
            src.append("pool venue string")
        else:
            verify.append("venue")
    if not year:
        year = str(f.get("year", "")) or None
        if not year:
            verify.append("year")
    if not doi and not aid:
        verify.append("stable-identifier")

    ident = []
    if doi:
        ident.append("doi:" + doi)
    if aid:
        ident.append("arXiv:" + aid)

    text = (f"{authors or '**VERIFY: authors**'} ({year or '**VERIFY: year**'}). "
            f"{title}. {venue or '**VERIFY: venue**'}{volinfo}. "
            + (" ".join(ident) if ident else "**VERIFY: no stable identifier**"))
    rows.append((n, text, verify, {"key": key, "type": "misc", "title": title,
                                   "author": authors, "year": year, "doi": doi,
                                   "arxiv": aid, "venue": venue, "detail": volinfo,
                                   "verify": verify, "src": "+".join(src)}))

# --------------------------------------------------------------- B. general
for pid, key, kind, aid, note, verify in GENERAL:
    n += 1
    am = arxiv.get(aid)
    if not am:
        rows.append((n, f"[{pid}] {note} **VERIFY: full bibliographic record.**",
                     verify + ["record"],
                     {"key": key, "type": "misc", "title": f"[{pid}] {note}",
                      "author": None, "year": None, "doi": None, "arxiv": aid,
                      "venue": "", "detail": "", "verify": verify + ["record"],
                      "src": "audit notes"}))
        continue
    title = am["title"].replace(r"$\times$", "x")
    authors = authors_str(am["authors"], am.get("n_auth"))
    year = am.get("year")
    text = (f"{authors or '**VERIFY: authors**'} ({year}). {title}. "
            f"arXiv preprint arXiv:{aid}. arXiv:{aid}")
    rows.append((n, text, verify,
                 {"key": key, "type": "misc", "title": title, "author": authors,
                  "year": year, "doi": None, "arxiv": aid,
                  "venue": f"arXiv preprint arXiv:{aid}", "detail": "",
                  "verify": verify, "src": f"arXiv:{aid}"}))

# ------------------------------------------------------------------ C. self
for t in SELF:
    n += 1
    rows.append((n, t, ["full-record"], {"key": None, "self": True, "title": t,
                                         "verify": ["full-record"], "src": "own work"}))

# ---------------------------------------------------------------- markdown
L = []
L.append("# P0-S1 References")
L.append("")
L.append(f"> Generated {datetime.date.today().isoformat()} by `audit/code/s1_make_references.py`.")
L.append("> Field provenance: `_doi_meta.json` (Crossref/OpenAlex) > `_arxiv_meta.json` (arXiv API) "
         "> `audit_F_field_survey.json` (venue string).")
L.append("> No field is guessed. Unresolved fields are printed as **VERIFY: ...** and collected in the table at the end.")
L.append("")
L.append("## A. Surveyed works (the 35-paper sample)")
L.append("")
for idx, text, verify, e in rows:
    if e.get("self"):
        continue
    mark = "" if not verify else f"  \n  **VERIFY: {', '.join(verify)}**"
    srcline = f"  \n  *source: {e['src']}*" if e.get("src") else ""
    L.append(f"**[{idx}]** {text}{srcline}{mark}")
    L.append("")

L.append("## B. Own works cited")
L.append("")
for idx, text, verify, e in rows:
    if e.get("self"):
        L.append(f"**[{idx}]** {text}")
        L.append("")

# ---------------------------------------------------------------- bibtex
L.append("---")
L.append("")
L.append("## BibTeX")
L.append("")
L.append("```bibtex")
for idx, text, verify, e in rows:
    if not e.get("key"):
        continue
    t = e.get("title") or "VERIFY-TITLE"
    a = e.get("author") or "VERIFY-AUTHORS"
    y = e.get("year") or "VERIFY-YEAR"
    if e.get("arxiv") and not e.get("doi"):
        L.append(f"@misc{{{e['key']},")
        L.append(f"  title  = {{{t}}},")
        L.append(f"  author = {{{a}}},")
        if e.get("venue"):
            L.append(f"  note   = {{{e['venue']}}},")
        L.append(f"  year   = {{{y}}},")
        L.append(f"  eprint = {{{e['arxiv']}}},")
        L.append("  archivePrefix = {arXiv},")
        L.append("}")
    else:
        L.append(f"@article{{{e['key']},")
        L.append(f"  title   = {{{t}}},")
        L.append(f"  author  = {{{a}}},")
        if e.get("venue"):
            L.append(f"  journal = {{{e['venue']}}},")
        L.append(f"  year    = {{{y}}},")
        if e.get("doi"):
            L.append(f"  doi     = {{{e['doi']}}},")
        if e.get("arxiv"):
            L.append(f"  eprint  = {{{e['arxiv']}}},")
            L.append("  archivePrefix = {arXiv},")
        L.append("}")
    L.append("")
L.append("```")

# ---------------------------------------------------------------- summary
L.append("---")
L.append("")
L.append("## Verification status")
L.append("")
L.append("| # | Key | Result | Missing |")
L.append("|---|---|---|---|")
for idx, text, verify, e in rows:
    if e.get("self") or not e.get("key"):
        continue
    L.append(f"| {idx} | `{e['key']}` | {'complete' if not verify else 'incomplete'} "
             f"| {', '.join(verify) if verify else '-'} |")

L.append("")
L.append("### The eight unresolved entries, and why")
L.append("")
L.append("| # | Key | Why it stays unresolved |")
L.append("|---|---|---|")
L.append("| 8 | `LocalStateSpace2026` | Chinese-language journal (中国图象图形学报). No DOI, no OA. Recorded as tier C in the survey and excluded from citation. |")
L.append("| 9 | `JNUNCA2026` | Chinese-language journal (西北大学学报). No DOI. Same treatment. |")
L.append("| 11 | `PLGMamba2026` | The only 'source' found was a news aggregator page that now 404s. No article exists. **Recommend dropping this entry from the survey and reducing the sample to 34.** |")
L.append("| 12 | `Sen4x2026` | IEEE JSTARS 2026. The DOI recorded in the pool returns 404 at Crossref, and a title search does not surface it. Volume and pages are known, DOI is not. |")
L.append("| 20 | `DiffBSR2026` | DOAJ article page b98e0f0f... returns 403. DOI and venue could not be recovered. |")
L.append("| 25 | `HSISRKAN2026` | The 'source' was an AI-generated topic-summary page, not an article. **Recommend dropping; sample becomes 33.** |")
L.append("| 26 | `UDAMSRmean2026` | A duplicate of entry 23 (same source, one extra recorded phrase). **Should be merged, not cited separately.** |")
L.append("| 29 | `NTIRE2026ESR` | A Codabench competition leaderboard, not a paper. The IR track is covered by entry 32. |")
L.append("")
L.append("**Net effect on the survey denominator.** Four of the eight are not standalone")
L.append("articles (11, 25, 26, 29). Removing them leaves 31 citable works from the")
L.append("original 35-paper sample. Two are Chinese-language journal articles without")
L.append("DOIs (8, 9). One is a real IEEE paper whose DOI could not be recovered (12).")
L.append("One is a DOAJ record behind a 403 (20). **All headline percentages in Section 5")
L.append("are reported against the full 35-item sample and this appendix records the")
L.append("composition.** If the venue asks for a citable-only denominator, Section 5")
L.append("should be re-run over the 31-item subset rather than the counts being adjusted by hand.")
L.append("")
L.append("### Entries that must not be cited without a full record")
L.append("")
L.append("NeurIPS 2025 and ICLR 2026 are cited in Section 7.2 as announced statistics.")
L.append("They have no single authoritative paper record, so they are cited as")
L.append("organization announcements with the year and the specific figure. If the venue")
L.append("requires a formal reference, the program-chair introduction or the official")
L.append("statistics page should be cited instead. These two are deliberately absent from")
L.append("the BibTeX block to avoid emitting an entry with no author.")

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "references.md"), "w", encoding="utf-8").write("\n".join(L))

nb = [e for _, _, _, e in rows if e.get("key")]
n_ok = sum(1 for e in nb if not e["verify"])
print("wrote", os.path.join(OUT, "references.md"))
print(f"entries={len(rows)}  bibtex={len(nb)}  complete={n_ok}  incomplete={len(nb)-n_ok}")
for idx, text, verify, e in rows:
    if verify and e.get("key"):
        print(f"  [{idx}] {e['key']:22s} VERIFY {', '.join(verify)}")
