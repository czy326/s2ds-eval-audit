#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 Audit / Step 3: 效应量 vs 噪声量 —— 决定性的一步。

把"论文声称的方法效应"与"同一方法换种子造成的波动"放在同一把尺子上：
  - 方法效应 |Δ_method|：同 seed、跨方法的逐图配对 ΔPSNR
  - 种子噪声 sd_seed：同方法、跨种子的逐图配对 ΔPSNR 的 sd
若 |Δ_method| < sd_seed 且跨种子方向不一致 → 该排名不可复现。

这是把论文4 的"测试集构成主导排名"推广到"协议/种子主导排名"的直接证据。
"""
import json, os, re, sys, io, statistics
from collections import defaultdict
from itertools import combinations

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OUT = OUT_DIR


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def method_of(name):
    return re.sub(r"_s20\d\d$", "", name)


def has_seed(name):
    return re.search(r"_s20\d\d$", name) is not None


def load():
    import glob
    runs = []
    for f in sorted(glob.glob(os.path.join(OUT, "perimage", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        m = d["meta"]
        m["images"] = d["images"]
        runs.append(m)
    return runs


def paired(a, b, metric="psnr"):
    ka = {im["path"]: im[metric] for im in a["images"] if im.get(metric) is not None}
    kb = {im["path"]: im[metric] for im in b["images"] if im.get(metric) is not None}
    common = sorted(set(ka) & set(kb))
    if not common:
        return None
    diffs = [ka[p] - kb[p] for p in common]
    return {
        "n": len(common),
        "mean": mean(diffs),
        "sd": statistics.pstdev(diffs) if len(diffs) > 1 else 0.0,
        "stderr": (statistics.pstdev(diffs) / (len(diffs) ** 0.5)) if len(diffs) > 1 else None,
        "win_rate": sum(1 for x in diffs if x > 0) / len(diffs),
    }


def main():
    runs = load()
    # 索引: (ds, method, seed) -> run
    # ★ 纪律：只有带显式 _s20xx 后缀的 run 才参与配对（否则 seed 归属不明，会错配）
    idx = {}
    n_noseed = 0
    for r in runs:
        if not (r["dataset"] and r["seed"] is not None and has_seed(r["run_name"])):
            if r["dataset"]:
                n_noseed += 1
            continue
        idx[(r["dataset"], method_of(r["run_name"]), r["seed"])] = r
    print(f"[纪律] 排除无 seed 后缀 run: {n_noseed} 个（避免错配）")
    print(f"[纪律] 参与配对的 run: {len(idx)} 个")

    by_ds = defaultdict(lambda: defaultdict(dict))
    for (ds, meth, seed), r in idx.items():
        by_ds[ds][meth][seed] = r

    rows = []
    for ds, meths in sorted(by_ds.items()):
        # 选一个有 ≥3 seed 的"参考方法"来量化种子噪声
        seed_sd = {}
        for meth, seeds in meths.items():
            if len(seeds) < 2:
                continue
            sds = []
            for i, j in combinations(sorted(seeds), 2):
                p = paired(seeds[i], seeds[j])
                if p:
                    sds.append(p["sd"])
            if sds:
                seed_sd[meth] = statistics.mean(sds)

        # 方法间效应：同 seed 下，两两方法配对
        methods = sorted(meths)
        for a, b in combinations(methods, 2):
            common_seeds = sorted(set(meths[a]) & set(meths[b]))
            if not common_seeds:
                continue
            ds_effects = []
            ds_sds = []
            same_sign = []
            for s in common_seeds:
                p = paired(meths[a][s], meths[b][s])
                if p:
                    ds_effects.append(p["mean"])
                    ds_sds.append(p["sd"])
                    same_sign.append(p["mean"] > 0)
            rows.append({
                "dataset": ds,
                "method_a": a, "method_b": b,
                "n_seeds": len(common_seeds),
                "mean_effect_dB": statistics.mean(ds_effects),
                "seed_spread_dB": (max(ds_effects) - min(ds_effects)) if len(ds_effects) > 1 else 0.0,
                "sd_seed_ref_a": seed_sd.get(a),
                "sd_seed_ref_b": seed_sd.get(b),
                "sign_consistent": (len(set(same_sign)) == 1) if same_sign else None,
                "effects": ds_effects,
            })

    # 汇总：效应 < 种子 spread 的比例
    n = len(rows)
    flip = [r for r in rows if r["sign_consistent"] is False]
    tiny = [r for r in rows if r["sd_seed_ref_a"] and abs(r["mean_effect_dB"]) < r["sd_seed_ref_a"]]
    print(f"方法间配对总数: {n}")
    print(f"跨种子方向翻转(不可复现): {len(flip)}/{n} = {len(flip)/n*100:.1f}%")
    print(f"|效应| < 种子sd (落在噪声内): {len(tiny)}/{n} = {len(tiny)/n*100:.1f}%")
    print("\n--- 锚点：BSRNet B3 vs base_ssm 类配对 ---")
    for r in rows:
        if ("b3" in r["method_a"] or "b3" in r["method_b"] or
                "edge" in r["method_a"] or "edge" in r["method_b"]):
            if "base_ssm" in (r["method_a"], r["method_b"]):
                print(f"  {r['dataset']:18s} {r['method_a'][:26]:26s} vs {r['method_b'][:26]:26s} "
                      f"Δ={r['mean_effect_dB']:+.4f} seed_spread={r['seed_spread_dB']:.4f} "
                      f"sign_consistent={r['sign_consistent']} effects={[round(x,3) for x in r['effects']]}")

    print("\n--- 方向翻转的配对 (前 12) ---")
    for r in flip[:12]:
        print(f"  {r['dataset']:18s} {r['method_a'][:24]:24s} vs {r['method_b'][:24]:24s} "
              f"Δ={r['mean_effect_dB']:+.4f} effects={[round(x,3) for x in r['effects']]}")

    with open(os.path.join(OUT, "audit_D_effect_vs_noise.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    print("\nwrote audit_D_effect_vs_noise.json")


if __name__ == "__main__":
    main()
