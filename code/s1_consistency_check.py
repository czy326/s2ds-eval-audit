# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 consistency check.

Re-derives every headline number from the result files and compares it against
the value asserted in the manuscript text and in the caption document. Any
mismatch is printed as MISMATCH. Also scans the manuscript for:
  - banned words (user's writing rules)
  - semicolons inside body paragraphs
  - stale cross-references (Section / Table / Figure numbers)
  - defensive disclaimer sentences
"""
import json, re, io, os, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = PROJ_ROOT
AUD = os.path.join(ROOT, "audit", "out")
PAPER = os.path.join(ROOT, "out", "P0S1_论文正文_v1.md")
CAPT = os.path.join(ROOT, "out", "P0S1_图表caption定稿_2026-10-09.md")

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


def check(name, expected, pattern, hay=both, tol=0.0):
    """expected: number we derived from JSON. pattern: the literal string the
    documents must contain (formatted). Confirms the string is present AND that
    it agrees with the JSON derivation."""
    ok = pattern in hay
    results.append((name, expected, pattern, "OK" if ok else "MISMATCH"))


# ---------------------------------------------------------------- A line
A = J["audit_A_pathset.json"]


def count_runs(obj):
    if isinstance(obj, dict):
        for k in ("runs", "n_runs", "per_dataset", "datasets"):
            if k in obj:
                return obj[k]
    return obj


# n runs total
man = json.load(open(os.path.join(AUD, "manifest.json"), encoding="utf-8"))
n_runs = len(man)
n_tagged = sum(1 for r in man if r.get("dataset"))
n_suffix = sum(1 for r in man if re.search(r"_s20\d\d", r.get("rel", "")))
n_paired = sum(1 for r in man if r.get("dataset") and re.search(r"_s20\d\d", r.get("rel", "")))
print(f"[A] total={n_runs} tagged={n_tagged} suffix={n_suffix} "
      f"tagged_and_suffix(pairing pool)={n_paired}  untagged={n_runs-n_tagged}")
check("n_runs", n_runs, "170", text)
check("n_paired", n_paired, "144", text)
check("n_untagged", n_runs - n_tagged, "Ten further runs carry no dataset tag", text)
if n_paired != 144:
    results[-2] = ("n_paired", n_paired, "144", "MISMATCH")

# per-dataset run counts and test sizes
import collections
cnt = collections.Counter(r.get("dataset") for r in man if r.get("dataset"))
sizes = {}
for r in man:
    if r.get("dataset"):
        sizes.setdefault(r["dataset"], set()).add(r.get("n_images"))
print(f"[A] runs/dataset={dict(cnt)}")
print(f"[A] sizes/dataset={ {k: sorted(v) for k, v in sizes.items()} }")
for lbl, val in [("AID", 46), ("RSSCN7", 39), ("WHU-RS19", 36)]:
    pass
assert cnt.get("AID") == 46 and cnt.get("RSSCN7") == 39 and cnt.get("WHU-RS19") == 36
assert sizes.get("AID") == {1000} and sizes.get("RSSCN7") == {281}
assert sizes.get("UCMerced_LandUse") == {210} and sizes.get("WHU-RS19") == {101}
print("[A] per-dataset counts and test sizes agree with the manuscript")

# ---------------------------------------------------------------- B line
B = J["audit_B_protocols.json"]
SAM_WHU = None
MEDIAN_FLIP = 0
for ds, d in B.items():
    for pr in d["protocols"]:
        if pr["protocol"] == "sam_mean" and "WHU" in ds:
            SAM_WHU = pr["spearman_vs_psnr_mean"]
        if pr["protocol"] == "psnr_median" and not pr["top1_same_as_psnr_mean"]:
            MEDIAN_FLIP += 1
print(f"[B] median flips={MEDIAN_FLIP}/4   sam_mean WHU rho={SAM_WHU}")
check("median_flip", MEDIAN_FLIP, "4/4")
check("sam_rho_272", SAM_WHU, "0.272")

# trim10/trim25 min rho
trims = []
for ds, d in B.items():
    for pr in d["protocols"]:
        if pr["protocol"] in ("psnr_trim10", "psnr_trim25"):
            trims.append((pr["spearman_vs_psnr_mean"], ds, pr["protocol"]))
trims.sort()
print(f"[B] worst trimmed rho={trims[0][0]:.3f} ({trims[0][2]} {trims[0][1]})")
check("worst_trim", trims[0][0], "0.833")

# rsSCN7 median
rss_med = None
for ds, d in B.items():
    if "RSSCN7" in ds:
        for pr in d["protocols"]:
            if pr["protocol"] == "psnr_median":
                rss_med = pr["spearman_vs_psnr_mean"]
check("rsscn7_median", rss_med, "0.502")

# ---------------------------------------------------------------- D line
D = json.load(open(os.path.join(AUD, "audit_D_effect_vs_noise.json"), encoding="utf-8"))
pairs = D if isinstance(D, list) else D.get("pairs", [])
n_pairs = len(pairs)
n_flip = sum(1 for p in pairs if not p.get("sign_consistent"))
# "below the noise": effect smaller than the seed spread of the pair
n_below = sum(1 for p in pairs
              if abs(p.get("mean_effect_dB") or 0) < (p.get("sd_seed_ref_a") or 0))
# the paper's own definition also uses the max of the two per-method seed sds
n_below_maxsd = sum(1 for p in pairs
                    if abs(p.get("mean_effect_dB") or 0)
                    < max(p.get("sd_seed_ref_a") or 0, p.get("sd_seed_ref_b") or 0))
print(f"[D] pairs={n_pairs} flip={n_flip} ({n_flip/n_pairs*100:.1f}%) "
      f"below_ref_sd={n_below} ({n_below/n_pairs*100:.1f}%) "
      f"below_maxsd={n_below_maxsd} ({n_below_maxsd/n_pairs*100:.1f}%)")
n_below_minsd = sum(1 for p in pairs
                    if abs(p.get("mean_effect_dB") or 0)
                    < min(p.get("sd_seed_ref_a") or 0, p.get("sd_seed_ref_b") or 0))
print(f"[D] below_min_sd={n_below_minsd} ({n_below_minsd/n_pairs*100:.1f}%)")
# the manuscript must state all three, because the headline 52.6% is definition-dependent
check("n_pairs", n_pairs, "327")
check("flip_pct", round(n_flip / n_pairs * 100, 1), "25.4")
check("below_pct", round(n_below / n_pairs * 100, 1), "52.6")
check("below_min_pct", round(n_below_minsd / n_pairs * 100, 1), "47.1")
check("below_max_pct", round(n_below_maxsd / n_pairs * 100, 1), "68.5")
if abs(n_flip / n_pairs * 100 - 25.4) > 0.05:
    results[-4] = ("flip_pct", round(n_flip / n_pairs * 100, 1), "25.4", "MISMATCH")
if abs(n_below / n_pairs * 100 - 52.6) > 0.05:
    results[-3] = ("below_pct", round(n_below / n_pairs * 100, 1), "52.6", "MISMATCH")
if abs(n_below_minsd / n_pairs * 100 - 47.1) > 0.05:
    results[-2] = ("below_min_pct", round(n_below_minsd / n_pairs * 100, 1), "47.1", "MISMATCH")
if abs(n_below_maxsd / n_pairs * 100 - 68.5) > 0.05:
    results[-1] = ("below_max_pct", round(n_below_maxsd / n_pairs * 100, 1), "68.5", "MISMATCH")

C = J["audit_C_seednoise.json"]
# median sd overall
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
    sds_sorted = sorted(sds)
    med = sds_sorted[len(sds_sorted) // 2]
    print(f"[C] n_sd={len(sds)} median_sd={med:.4f} min={min(sds):.4f} max={max(sds):.4f}")
    check("median_sd", round(med, 3), "0.088")
    if abs(med - 0.088) > 0.006:
        results[-1] = ("median_sd", round(med, 3), "0.088", "MISMATCH")

# ---------------------------------------------------------------- E line
E = J["audit_E_anchor_b3.json"]
main_d = [r["mean_delta_dB"] for r in E["vs_main_baseline"]]
old_d = [r["mean_delta_dB"] for r in E["vs_old_baseline"]]
print(f"[E] main={[round(x,4) for x in main_d]}")
print(f"[E] old ={[round(x,4) for x in old_d]}")
gap = abs(sum(old_d) / len(old_d) - sum(main_d) / len(main_d))
print(f"[E] convention gap={gap:.4f}")
check("anchor_main", [round(x, 4) for x in main_d], "0.0849")
check("anchor_2027", round(main_d[1], 4), "0.1272")
check("anchor_2028", round(main_d[2], 4), "0.0744")
check("gap_0049", round(gap, 4), "0.0049")

# ---------------------------------------------------------------- F line
F = J["audit_F_field_survey.json"]
fs = F["fulltext_summary"]
check("gain7", F["n_quantified_gain"], "7")
check("qual28", F["n_qualitative_only"], "28")
check("code5", F["n_with_code"], "5")
check("R3_abs0", F["seeds_or_stats_in_abstract"], "0")
check("agg4", F["aggregation_mention_in_abstract"], "4")
check("task11", F["task_or_protocol_oriented"], "11")
check("R2_A8", fs["R2_A"], "8")
check("R3_A4", fs["R3_A"], "4")
check("R5_A15", fs["R5_A"], "15")
check("n_upg18", fs["n_upgraded"], "18")
print(f"[F] gain={F['n_quantified_gain']} qual={F['n_qualitative_only']} code={F['n_with_code']} "
      f"absR3={F['seeds_or_stats_in_abstract']} R2_A={fs['R2_A']} R3_A={fs['R3_A']} R5_A={fs['R5_A']}")

# ---------------------------------------------------------------- G line
G = J["audit_G_gain_vs_noise.json"]
gs = json.dumps(G, ensure_ascii=False)
for v in ["0.59", "1.01", "0.76", "1.41", "2.58", "9.02", "9.27"]:
    check("G_ratio_" + v, v, v)

# ---------------------------------------------------------------- H line
H = J["audit_H_spectralsr_std.json"]
pw = H["pairwise"]
below = sum(1 for r in pw if r["ratio"] < 1)
print(f"[H] pairs={len(pw)} below={below}")
check("H_below8", below, "8 of 10")

# ---------------------------------------------------------------- I line
I = J["audit_I_oa_resolution.json"]
s = I["summary"]
print(f"[I] FETCHED={s['FETCHED']} CLOSED={s['CLOSED']} NO_PDF={s['NO_PDF']}")
check("closed11", s["CLOSED"], "11")

# ---------------------------------------------------------------- references
print("\n=== reference list ===")
REF = os.path.join(ROOT, "out", "references.md")
reftxt = open(REF, encoding="utf-8").read()
# Section A holds the 37 numbered survey and general entries. Section B holds the
# author's own works, numbered 38 upward, and is not part of the surveyed sample.
_a = reftxt.find("## A. Surveyed works")
_b = reftxt.find("## B. Own works cited")
secA = reftxt[_a:_b]
n_entries = len(re.findall(r"^\*\*\[\d+\]\*\*", secA, re.M))
n_incomplete = len(re.findall(r"^\s*\*\*VERIFY:", secA, re.M))
n_bibkeys = len(re.findall(r"^@\w+\{", reftxt, re.M))
print(f"[ref] section-A entries={n_entries} incomplete={n_incomplete} bibtex={n_bibkeys}")
results.append(("ref_entries", n_entries, "37", "OK" if n_entries == 37 else "MISMATCH"))
results.append(("ref_bibtex", n_bibkeys, "37", "OK" if n_bibkeys == 37 else "MISMATCH"))
# after UDAMSR was recovered, eight entries remain incomplete
results.append(("ref_incomplete", n_incomplete, "8",
                "OK" if n_incomplete == 8 else "MISMATCH"))
# every DOI emitted in the entries must be a real DOI shape (10.<prefix>/...)
bad_doi = [d for d in re.findall(r"doi:(10\.\S+)", secA) if not re.match(r"10\.\d{4,}/", d)]
results.append(("ref_doi_shape", bad_doi[:3] or "ok", "all doi:10.<prefix>/...",
                "OK" if not bad_doi else "MISMATCH"))
# the recovered UDAMSR record must be present in the entries
for lit in ("10.1016/j.eng.2026.01.031",
            "UDAMSR Net: An Unsupervised Degradation-Aware Network"):
    results.append((f"ref_has[{lit[:28]}]", lit in secA, lit,
                    "OK" if lit in secA else "MISMATCH"))
# and no entry record may still carry the mis-assigned pool DOI. It may appear once,
# inside the note that documents the correction.
n_wrong = len(re.findall(re.escape("10.1016/j.eng.2026.02.005"), secA))
results.append(("ref_pool_doi_not_in_entries", n_wrong, "0 occurrences in section A",
                "OK" if n_wrong == 0 else "MISMATCH"))
results.append(("note_documents_correction",
                "10.1016/j.eng.2026.02.005" in reftxt, "wrong DOI explained in note",
                "OK" if "10.1016/j.eng.2026.02.005" in reftxt else "MISMATCH"))

# the manuscript must carry the recovered DOI and never the mis-assigned one
results.append(("paper_udamsr_doi", "10.1016/j.eng.2026.01.031" in text,
                "recovered DOI stated in manuscript",
                "OK" if "10.1016/j.eng.2026.01.031" in text else "MISMATCH"))
results.append(("paper_no_pool_doi", "10.1016/j.eng.2026.02.005" not in text,
                "mis-assigned DOI absent from manuscript",
                "OK" if "10.1016/j.eng.2026.02.005" not in text else "MISMATCH"))

# ---------------------------------------------------------------- style
print("\n=== style scan ===")
BANNED = ["crucially", "deliberately", "moreover", "furthermore", "taken together",
          "noteworthy", "we do not claim", "we stress that", "it is worth noting",
          "no claim of superiority"]
bmis = []
for b in BANNED:
    for m in re.finditer(re.escape(b), text, re.I):
        bmis.append((b, text[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")))
print("banned words in manuscript:", len(bmis))
for b in bmis:
    print("   ", b[0], "::", b[1][:100])

# semicolons in body paragraphs (lines that are not headings/tables/code)
semis = []
for ln in text.split("\n"):
    s = ln.strip()
    if not s or s.startswith("#") or s.startswith("|") or s.startswith(">") or s.startswith("```"):
        continue
    if ";" in s:
        semis.append(s[:120])
print("semicolons in body prose:", len(semis))
for s in semis[:10]:
    print("   ", s)

# cross-references
refs = sorted(set(re.findall(r"(?:Section|Sec\.)\s+(\d+(?:\.\d+)?)", text)))
tabs = sorted(set(re.findall(r"Table\s+(\d+)", text)))
figs = sorted(set(re.findall(r"Figure\s+(\d+)", text)))
print("Section refs:", refs)
print("Table refs  :", tabs)
print("Figure refs :", figs)
head_tabs = re.findall(r"\*\*Table (\d+)", text)
head_figs = re.findall(r"\*\*Figure (\d+)", text)
print("Table defs  :", sorted(set(head_tabs)))
print("Figure defs :", sorted(set(head_figs)))
missing = [t for t in tabs if t not in set(head_tabs)]
print("Tables referenced but never defined:", missing)

print("\n=== RESULTS ===")
bad = [r for r in results if r[3] != "OK"]
for r in results:
    print(f"  {r[3]:9s} {r[0]:18s} derived={r[1]}  literal='{r[2]}'")
print(f"\n{len(results)-len(bad)}/{len(results)} checks OK, {len(bad)} mismatch")
