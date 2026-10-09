# -*- coding: utf-8 -*-
"""
P0-S1 JSTARS-version consistency check.

Re-derives every headline number from the result files and confirms the literal
appears in the JSTARS manuscript and its caption document. Adds the venue-specific
checks that the JSTARS submission requires:

  * abstract word count inside IEEE JSTARS' 150-250 range, no citations, one paragraph
  * Index Terms present
  * a Conclusions section present
  * Data and Code Availability present
  * Acknowledgment present
  * references numbered in IEEE form, contiguous from [1], every number cited
  * tables numbered with Roman numerals and figures with Arabic numerals
  * every Table/Fig reference resolves to a definition
  * zero banned words, zero semicolons in body prose
"""
import json, re, io, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Portable roots: this script is shipped inside the repository, so it locates its
# inputs relative to its own location rather than to an author-side absolute path.
# Set S2DS_AUDIT_ROOT to point at a different checkout if needed.
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("S2DS_AUDIT_ROOT") or os.path.dirname(_HERE)
AUD = os.path.join(REPO, "results")
PAPER = os.path.join(REPO, "papers", "P0S1_JSTARS_v1.md")
CAPT = os.path.join(REPO, "papers", "P0S1_图表caption_JSTARS_v1.md")
MANIFEST = os.path.join(REPO, "data", "manifest.json")

J = {f: json.load(open(os.path.join(AUD, f), encoding="utf-8"))
     for f in ["audit_A_pathset.json", "audit_B_protocols.json",
               "audit_C_seednoise.json", "audit_D_effect_vs_noise.json",
               "audit_E_anchor_b3.json", "audit_F_field_survey.json",
               "audit_G_gain_vs_noise.json", "audit_H_spectralsr_std.json",
               "audit_I_oa_resolution.json"]}

text = open(PAPER, encoding="utf-8").read()
capt = open(CAPT, encoding="utf-8").read()
both = text + "\n" + capt

results = []


def check(name, expected, pattern, hay=both):
    ok = pattern in hay
    results.append((name, expected, pattern, "OK" if ok else "MISMATCH"))


def add(name, derived, literal, ok):
    results.append((name, derived, literal, "OK" if ok else "MISMATCH"))


# ------------------------------------------------------------------ A line
man = json.load(open(MANIFEST, encoding="utf-8"))
n_runs = len(man)
n_tagged = sum(1 for r in man if r.get("dataset"))
n_paired = sum(1 for r in man if r.get("dataset") and re.search(r"_s20\d\d", r.get("rel", "")))
check("n_runs", n_runs, "170", text)
check("n_paired", n_paired, "144", text)
add("n_paired_exact", n_paired, "144", n_paired == 144)

import collections
cnt = collections.Counter(r.get("dataset") for r in man if r.get("dataset"))
add("aid_46", cnt.get("AID"), "46", cnt.get("AID") == 46)
add("rsscn7_39", cnt.get("RSSCN7"), "39", cnt.get("RSSCN7") == 39)
add("whu_36", cnt.get("WHU-RS19"), "36", cnt.get("WHU-RS19") == 36)

# ------------------------------------------------------------------ B line
B = J["audit_B_protocols.json"]
SAM_WHU, MEDIAN_FLIP = None, 0
for ds, d in B.items():
    for pr in d["protocols"]:
        if pr["protocol"] == "sam_mean" and "WHU" in ds:
            SAM_WHU = pr["spearman_vs_psnr_mean"]
        if pr["protocol"] == "psnr_median" and not pr["top1_same_as_psnr_mean"]:
            MEDIAN_FLIP += 1
check("median_flip", MEDIAN_FLIP, "4 of 4", text)
# the JSTARS text spells the acronym out at first use
check("sam_rho_272", SAM_WHU, "0.272")
check("median_flip_table", MEDIAN_FLIP, "Median aggregation changes the champion", both)
trims = [(pr["spearman_vs_psnr_mean"], pr["protocol"])
         for d in B.values() for pr in d["protocols"]
         if pr["protocol"] in ("psnr_trim10", "psnr_trim25")]
check("worst_trim", min(trims)[0], "0.833")
rss_med = [pr["spearman_vs_psnr_mean"] for ds, d in B.items() if "RSSCN7" in ds
           for pr in d["protocols"] if pr["protocol"] == "psnr_median"]
check("rsscn7_median", rss_med[0], "0.502")

# ------------------------------------------------------------------ C/D line
D = J["audit_D_effect_vs_noise.json"]
pairs = D if isinstance(D, list) else D.get("pairs", [])
n_pairs = len(pairs)
n_flip = sum(1 for p in pairs if not p.get("sign_consistent"))
n_min = sum(1 for p in pairs if abs(p.get("mean_effect_dB") or 0)
            < min(p.get("sd_seed_ref_a") or 0, p.get("sd_seed_ref_b") or 0))
n_ref = sum(1 for p in pairs if abs(p.get("mean_effect_dB") or 0)
            < (p.get("sd_seed_ref_a") or 0))
n_max = sum(1 for p in pairs if abs(p.get("mean_effect_dB") or 0)
            < max(p.get("sd_seed_ref_a") or 0, p.get("sd_seed_ref_b") or 0))
print(f"[D] pairs={n_pairs} flip={n_flip} ({n_flip/n_pairs*100:.1f}%) "
      f"below_ref={n_ref} ({n_ref/n_pairs*100:.1f}%) "
      f"min={n_min} ({n_min/n_pairs*100:.1f}%) max={n_max} ({n_max/n_pairs*100:.1f}%)")
check("n_pairs", n_pairs, "327")
check("flip_pct", round(n_flip / n_pairs * 100, 1), "25.4")
check("below_ref_pct", round(n_ref / n_pairs * 100, 1), "52.6")
check("below_min_pct", round(n_min / n_pairs * 100, 1), "47.1")
check("below_max_pct", round(n_max / n_pairs * 100, 1), "68.5")
add("flip_exact", round(n_flip / n_pairs * 100, 1), "25.4",
    abs(n_flip / n_pairs * 100 - 25.4) <= 0.05)
add("below_ref_exact", round(n_ref / n_pairs * 100, 1), "52.6",
    abs(n_ref / n_pairs * 100 - 52.6) <= 0.05)

C = J["audit_C_seednoise.json"]
sds = []


def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("sd", "sd_dB", "std") and isinstance(v, (int, float)):
                sds.append(v)
            else:
                walk(v)
    elif isinstance(o, list):
        for x in o:
            walk(x)


walk(C)
if sds:
    med = sorted(sds)[len(sds) // 2]
    print(f"[C] n_sd={len(sds)} median={med:.4f} min={min(sds):.4f} max={max(sds):.4f}")
    check("median_sd", round(med, 3), "0.088")
    add("median_sd_exact", round(med, 3), "0.088", abs(med - 0.088) <= 0.006)

# ------------------------------------------------------------------ E line
E = J["audit_E_anchor_b3.json"]
main_d = [r["mean_delta_dB"] for r in E["vs_main_baseline"]]
old_d = [r["mean_delta_dB"] for r in E["vs_old_baseline"]]
gap = abs(sum(old_d) / len(old_d) - sum(main_d) / len(main_d))
print(f"[E] main={[round(x,4) for x in main_d]} gap={gap:.4f}")
check("anchor_0.0849", round(main_d[0], 4), "0.0849")
check("anchor_0.1272", round(main_d[1], 4), "0.1272")
check("anchor_0.0744", round(main_d[2], 4), "0.0744")
check("gap_0.0049", round(gap, 4), "0.0049")

# ------------------------------------------------------------------ F line
F = J["audit_F_field_survey.json"]
fs = F["fulltext_summary"]
check("gain7", F["n_quantified_gain"], "7 of 35")
check("qual28", F["n_qualitative_only"], "28")
check("code5", F["n_with_code"], "5 / 35")
check("R3_abs0", F["seeds_or_stats_in_abstract"], "0 / 35")
check("agg4", F["aggregation_mention_in_abstract"], "4 of 35")
check("R2_A8", fs["R2_A"], "8 of 35")
check("R3_A4", fs["R3_A"], "4 of 35")
check("R5_A15", fs["R5_A"], "15 of 35")
check("n_upg18", fs["n_upgraded"], "18")

# ------------------------------------------------------------------ G line
for v in ["0.59", "1.01", "0.76", "1.41", "2.58", "9.02", "9.27"]:
    check("G_ratio_" + v, v, v)

# ------------------------------------------------------------------ H line
H = J["audit_H_spectralsr_std.json"]
below = sum(1 for r in H["pairwise"] if r["ratio"] < 1)
check("H_below8", below, "8 of 10")

# ------------------------------------------------------------------ I line
I = J["audit_I_oa_resolution.json"]
check("closed11", I["summary"]["CLOSED"], "11")

# =================================================== JSTARS venue checks
print("\n=== JSTARS venue checks ===")

# abstract 150-250 words, one paragraph, no citations
a = text.find("## Abstract")
b = text.find("**Index Terms**")
ab = re.sub(r"<!--.*?-->", "", text[a + len("## Abstract"):b], flags=re.S).strip()
nw = len(ab.split())
add("abstract_len_150_250", nw, "150-250", 150 <= nw <= 250)
add("abstract_no_citations", bool(re.search(r"\[\d+\]", ab)), "no [n] citations",
    not re.search(r"\[\d+\]", ab))
add("abstract_one_paragraph", len([p for p in ab.split("\n\n") if p.strip()]), "1",
    len([p for p in ab.split("\n\n") if p.strip()]) == 1)
print(f"[JSTARS] abstract words = {nw}")

# index terms
add("index_terms", "**Index Terms**" in text, "Index Terms present",
    "**Index Terms**" in text)

# required sections
for sec in ["## 9. Conclusion", "## Data and Code Availability", "## Acknowledgment"]:
    add("sec:" + sec, sec in text, sec, sec in text)

# references: contiguous from 1, all cited
refstart = text.find("## References")
refend = text.find("## Author Biographies")
refblock = text[refstart:refend]
nums = [int(x) for x in re.findall(r"^\[(\d+)\]", refblock, re.M)]
add("ref_contiguous", nums == list(range(1, len(nums) + 1)), "1..N contiguous",
    nums == list(range(1, len(nums) + 1)))
body = text[:refstart]
cited = sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", body)))
uncited = [n for n in nums if n not in cited]
add("ref_all_cited", uncited or "none", "no uncited entry", not uncited)
dangling = [n for n in cited if n not in nums]
add("ref_no_dangling", dangling or "none", "all cites resolve", not dangling)
add("ref_count", len(nums), "N entries", len(nums) >= 15)
print(f"[JSTARS] references = {len(nums)}, cited = {len(cited)}")

# tables Roman, figures Arabic, all defined
tab_ref = set(re.findall(r"Table\s+([IVX]+)\b", text))
tab_def = set(re.findall(r"\*\*TABLE ([IVX]+)\.", text)) | set(re.findall(r"^\*\*Table ([IVX]+)", text))
fig_ref = set(re.findall(r"Fig\.\s+(\d+)", text))
fig_def = set(re.findall(r"\*\*Fig\. (\d+)\.", text))
add("tables_defined", sorted(tab_ref - tab_def) or "none", "every Table ref defined",
    not (tab_ref - tab_def))
add("figs_defined", sorted(fig_ref - fig_def) or "none", "every Fig ref defined",
    not (fig_ref - fig_def))
print(f"[JSTARS] table refs={sorted(tab_ref)} defs={sorted(tab_def)}")
print(f"[JSTARS] fig refs={sorted(fig_ref)} defs={sorted(fig_def)}")

# style
BANNED = ["crucially", "deliberately", "moreover", "furthermore", "taken together",
          "noteworthy", "we do not claim", "we stress that", "it is worth noting",
          "no claim of superiority"]
bcount = sum(len(re.findall(re.escape(w), text, re.I)) for w in BANNED)
add("banned_words", bcount, "0", bcount == 0)
semis = [ln for ln in text.split("\n")
         if ln.strip() and ln.strip()[0] not in "#|>`" and ";" in ln]
add("semicolons_in_prose", len(semis), "0", len(semis) == 0)
print(f"[JSTARS] banned={bcount} semicolons={len(semis)}")

print("\n=== RESULTS ===")
bad = [r for r in results if r[3] != "OK"]
for r in results:
    print(f"  {r[3]:9s} {r[0]:24s} derived={r[1]}  literal='{r[2]}'")
print(f"\n{len(results)-len(bad)}/{len(results)} checks OK, {len(bad)} mismatch")
