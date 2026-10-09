# -*- coding: utf-8 -*-
# --- portable roots ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
DATA_RUNS = _os.environ.get("S2DS_RUNS_ROOT", _os.path.join(DATA_ROOT, "runs"))
# --- end portable roots ---
"""
P0-S1 Audit / Step 4: 锚点案例 —— BSRNet B3 vs base_ssm 在主口径下的效应量与可复现性。

Pairing discipline:
  - per-image pairing on identical paths, seeds are never merged
  - 报告 点估计 + 逐图配对 95% CI + Cohen's d_z + 方向一致性
  - 同一端点（都是 30k last.pt 口径，产物即 test_per_image.jsonl）

对照组选择（两条基线口径，都要报，因为"口径不一致"本身就是审计对象）:
  B0 = runs/main/base_ssm_aid_s*         (主网格基线, 之前记录 +0.0849)
  B1 = runs/bsr_stage1/stage1_aid_A1_emssm  (旧口径, 之前记录 +0.1015)

处理组：
  T0 = runs/bsr_stage2/stage2_aid_edge_deep_fuse_s2027 / _s2028 / (无后缀, 视作 s2026)
"""
import json, os, sys, io, math, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

R = DATA_RUNS
OUT = OUT_DIR


def load(rel):
    p = os.path.join(R, rel, "test_per_image.jsonl")
    if not os.path.exists(p):
        return None
    return {json.loads(l)["path"]: json.loads(l)["psnr"]
            for l in open(p, encoding="utf-8") if l.strip()}


def paired_report(a, b, name_a, name_b):
    common = sorted(set(a) & set(b))
    if len(common) < 10:
        return None
    d = [a[k] - b[k] for k in common]
    n = len(d)
    mu = statistics.mean(d)
    sd = statistics.stdev(d) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 1 else 0.0
    # 正态近似 95% CI
    ci = (mu - 1.96 * se, mu + 1.96 * se)
    dz = mu / sd if sd > 0 else float("inf")
    wins = sum(1 for x in d if x > 0) / n
    return {
        "name_a": name_a, "name_b": name_b, "n": n,
        "mean_delta_dB": mu, "sd": sd, "se": se,
        "ci95_lo": ci[0], "ci95_hi": ci[1],
        "dz": dz, "win_rate": wins,
        "significant_95": (ci[0] > 0 or ci[1] < 0),
        "mean_a": statistics.mean(a[k] for k in common),
        "mean_b": statistics.mean(b[k] for k in common),
    }


def main():
    base_main = {s: load(f"main/base_ssm_aid_s{s}") for s in [2026, 2027, 2028]}
    base_old = load("bsr_stage1/stage1_aid_A1_emssm")
    b3 = {
        2026: load("bsr_stage2/stage2_aid_edge_deep_fuse"),
        2027: load("bsr_stage2/stage2_aid_edge_deep_fuse_s2027"),
        2028: load("bsr_stage2/stage2_aid_edge_deep_fuse_s2028"),
    }

    print("=" * 78)
    print("锚点：BSRNet B3 (stage2_aid_edge_deep_fuse) vs 两条基线口径")
    print("=" * 78)

    results = {"vs_main_baseline": [], "vs_old_baseline": []}

    print("\n[A] 对主网格基线 runs/main/base_ssm_aid_s*  （同 seed 配对）")
    for s in [2026, 2027, 2028]:
        if b3[s] is None or base_main[s] is None:
            continue
        r = paired_report(b3[s], base_main[s], f"B3_s{s}", f"base_ssm_s{s}")
        if r:
            results["vs_main_baseline"].append(r)
            print(f"  seed {s}: Δ={r['mean_delta_dB']:+.4f} dB  "
                  f"95%CI=[{r['ci95_lo']:+.4f},{r['ci95_hi']:+.4f}]  "
                  f"d_z={r['dz']:.2f}  胜率={r['win_rate']*100:.1f}%  n={r['n']}")

    print("\n[B] 对旧口径基线 runs/bsr_stage1/stage1_aid_A1_emssm （跨 seed 配同一基线）")
    for s in [2026, 2027, 2028]:
        if b3[s] is None or base_old is None:
            continue
        r = paired_report(b3[s], base_old, f"B3_s{s}", "stage1_aid_A1_emssm")
        if r:
            results["vs_old_baseline"].append(r)
            print(f"  seed {s}: Δ={r['mean_delta_dB']:+.4f} dB  "
                  f"95%CI=[{r['ci95_lo']:+.4f},{r['ci95_hi']:+.4f}]  "
                  f"d_z={r['dz']:.2f}  胜率={r['win_rate']*100:.1f}%  n={r['n']}")

    # 汇总：两条口径给出的"效应量"是否一致
    if results["vs_main_baseline"]:
        m1 = statistics.mean(r["mean_delta_dB"] for r in results["vs_main_baseline"])
        print(f"\n  主口径均值 Δ = {m1:+.4f} dB  （历史记录 +0.0849）")
    if results["vs_old_baseline"]:
        m2 = statistics.mean(r["mean_delta_dB"] for r in results["vs_old_baseline"])
        print(f"  旧口径均值 Δ = {m2:+.4f} dB  （历史记录 +0.1015）")
    if results["vs_main_baseline"] and results["vs_old_baseline"]:
        gap = abs(m2 - m1)
        print(f"  ⇒ 仅换基线口径造成的效应量差异 = {gap:.4f} dB"
              f"  （占主口径效应的 {gap/abs(m1)*100:.0f}%）")

    with open(os.path.join(OUT, "audit_E_anchor_b3.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    print("\nwrote audit_E_anchor_b3.json")


if __name__ == "__main__":
    main()
