#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 Audit / Step 2: 可复现性评分卡 —— 核心审计。

三条审计线，每条都直接对应"论文是否报告了影响结论的协议选择":

  A. 逐图一致性 (path-set identity)
     同一 (dataset) 下，不同 run 的逐图 path 集合是否**逐位相同**?
     若不同 → 所谓"同一测试集"其实是不同子集，跨论文比较即失效。
     ★ 用集合 Jaccard + 排序后逐位比较两种口径。

  B. 端点敏感性 (endpoint sensitivity)  ← 最核心
     同一批方法，在不同"指标口径"下的**排名**是否稳定?
     口径 = { PSNR, SSIM, ERGAS↓, SAM↓, LPIPS↓ }
     以及 PSNR 的 **聚合方式**: 逐图均值 / 中位 / 剔除 top-k% 离群。
     若排名随口径翻转 → "谁更好"没有单一答案。

  C. 种子噪声 vs 方法效应 (seed noise vs effect)
     对同一方法的不同 seed，逐图配对算 ΔPSNR 的 sd。
     若 |方法间 Δ| 小于种子间 sd → 该排名不可复现。

零外部依赖（只用标准库 + 可选 numpy）。无 numpy 时走纯 Python 回退。
"""
import json, os, glob, csv, sys, io, random, statistics
from collections import defaultdict, Counter
from itertools import combinations

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = DATA_ROOT
OUT = OUT_DIR
PI_DIR = os.path.join(OUT, "perimage")

try:
    import numpy as np
    HAVE_NP = True
except Exception:
    HAVE_NP = False

METRIC_DIR = {"psnr": +1, "ssim": +1, "ergas": -1, "sam": -1, "lpips": -1}  # +1 越大越好


def load_all():
    files = sorted(glob.glob(os.path.join(PI_DIR, "*.json")))
    runs = []
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        meta = d["meta"]
        meta["images"] = d["images"]
        runs.append(meta)
    return runs


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


# ---------------- A. 逐图一致性 ----------------
def audit_A(runs):
    by_ds = defaultdict(list)
    for r in runs:
        if r["dataset"]:
            by_ds[r["dataset"]].append(r)
    out = {}
    for ds, rs in sorted(by_ds.items()):
        # 以第一个为参考，比较全部
        ref = rs[0]
        ref_set = {im["path"] for im in ref["images"]}
        ref_sorted = sorted(ref_set)
        rows = []
        for r in rs:
            s = {im["path"] for im in r["images"]}
            inter = len(s & ref_set)
            union = len(s | ref_set)
            jac = inter / union if union else None
            same_sorted = (sorted(s) == ref_sorted)
            rows.append({
                "run": r["rel"], "n": r["n_images"],
                "jaccard_vs_ref": jac,
                "identical_pathset": same_sorted,
                "only_in_ref": len(ref_set - s),
                "only_in_run": len(s - ref_set),
            })
        out[ds] = {
            "n_runs": len(rs),
            "ref_run": ref["rel"],
            "n_unique_pathsets": len({frozenset(im["path"] for im in r["images"]) for r in rs}),
            "n_runs_size_match": sum(1 for r in rs if r.get("size_match")),
            "n_runs_identical_to_ref": sum(1 for x in rows if x["identical_pathset"]),
            "min_jaccard": min((x["jaccard_vs_ref"] for x in rows if x["jaccard_vs_ref"] is not None),
                              default=None),
            "rows": rows,
        }
    return out


# ---------------- B. 端点/口径敏感性 ----------------
def _agg(images, metric, how="mean", trim=0.0):
    vals = sorted(im[metric] for im in images if im.get(metric) is not None)
    if not vals:
        return None
    if how == "mean":
        return sum(vals) / len(vals)
    if how == "median":
        return median(vals)
    if how == "trimmed":
        k = int(len(vals) * trim)
        core = vals[k:len(vals) - k] if k else vals
        return sum(core) / len(core) if core else None
    raise ValueError(how)


def audit_B(runs, ds_filter=None):
    """按 (dataset) 分组，对每个 dataset 内的 method 排名，比较各口径下排名差异。"""
    by_ds = defaultdict(list)
    for r in runs:
        if r["dataset"] and (ds_filter is None or r["dataset"] == ds_filter):
            by_ds[r["dataset"]].append(r)

    protocols = []
    for m, sign in METRIC_DIR.items():
        protocols.append((f"{m}_mean", m, "mean", 0.0, sign))
    protocols += [
        ("psnr_median", "psnr", "median", 0.0, +1),
        ("psnr_trim10", "psnr", "trimmed", 0.10, +1),
        ("psnr_trim25", "psnr", "trimmed", 0.25, +1),
    ]

    report = {}
    for ds, rs in sorted(by_ds.items()):
        # 只对"同族多方法"比较：用 run_name 里的方法前缀聚合（取各 seed 的均值）
        # 这里做的是"每个 run 作为一个条目"的口径敏感性（seed 也参与排名，暴露 seed 噪声）
        table = {}
        for r in rs:
            table[r["run_name"]] = {
                pname: _agg(r["images"], m, how, trim)
                for (pname, m, how, trim, sign) in protocols
            }
        # 每个口径下排名
        ranks = {}
        for (pname, m, how, trim, sign) in protocols:
            items = [(k, v[pname]) for k, v in table.items() if v[pname] is not None]
            items.sort(key=lambda kv: sign * kv[1], reverse=True)
            ranks[pname] = [k for k, _ in items]

        # 与 psnr_mean 的 Spearman + top-1 是否一致
        ref = ranks["psnr_mean"]
        ref_top1 = ref[0] if ref else None
        summary = []
        for pname, rk in ranks.items():
            # Spearman：只在两个排名的**公共条目**上算
            common = [k for k in rk if k in set(ref)]
            n = len(common)
            if n > 3:
                rpos = {k: i for i, k in enumerate(rk)}
                mpos = {k: i for i, k in enumerate(ref)}
                d2 = sum((rpos[k] - mpos[k]) ** 2 for k in common)
                rho = 1 - 6 * d2 / (n * (n * n - 1))
                coverage = n / len(ref)
            else:
                rho, coverage = None, (n / len(ref) if ref else None)
            summary.append({
                "protocol": pname,
                "n_ranked": n,
                "coverage_vs_ref": coverage,
                "top1": rk[0] if rk else None,
                "top1_same_as_psnr_mean": (rk[0] == ref_top1) if rk else None,
                "spearman_vs_psnr_mean": rho,
            })
        report[ds] = {"n_runs": len(rs), "protocols": summary, "values": table}
    return report


# ---------------- C. 种子噪声 ----------------
def audit_C(runs):
    """同 (dataset, method-prefix) 不同 seed 的逐图配对 Δ 分布。"""
    def method_of(name):
        # 去掉尾部 _s20xx / _sNNNN
        import re
        return re.sub(r"_s20\d\d$", "", name)

    by = defaultdict(list)
    for r in runs:
        if r["dataset"] and r["seed"] is not None:
            by[(r["dataset"], method_of(r["run_name"]))].append(r)

    rows = []
    for (ds, meth), rs in sorted(by.items()):
        if len(rs) < 2:
            continue
        # 逐图配对：以 path 为键
        keyed = []
        for r in rs:
            keyed.append({im["path"]: im["psnr"] for im in r["images"] if im.get("psnr") is not None})
        seeds = [r["seed"] for r in rs]
        for i, j in combinations(range(len(rs)), 2):
            a, b = keyed[i], keyed[j]
            common = sorted(set(a) & set(b))
            if len(common) < 10:
                continue
            diffs = [a[p] - b[p] for p in common]
            sd = statistics.pstdev(diffs) if len(diffs) > 1 else 0.0
            rows.append({
                "dataset": ds, "method": meth,
                "seed_a": seeds[i], "seed_b": seeds[j],
                "n_paired": len(common),
                "mean_delta_psnr": mean(diffs),
                "sd_delta_psnr": sd,
                "max_abs_delta": max(abs(x) for x in diffs),
                "mean_a": mean(list(a.values())), "mean_b": mean(list(b.values())),
            })
    return rows


def main():
    runs = load_all()
    print("loaded runs:", len(runs))

    A = audit_A(runs)
    print("\n=== A. 逐图 path 集合一致性 ===")
    for ds, v in A.items():
        print(f"  {ds}: runs={v['n_runs']} unique_pathsets={v['n_unique_pathsets']} "
              f"size_match={v['n_runs_size_match']}/{v['n_runs']} "
              f"identical_to_ref={v['n_runs_identical_to_ref']} minJaccard={v['min_jaccard']}")

    B = audit_B(runs)
    print("\n=== B. 口径敏感性（vs psnr_mean）===")
    for ds, v in B.items():
        print(f"  --- {ds} (n_runs={v['n_runs']}) ---")
        for s in v["protocols"]:
            print(f"     {s['protocol']:14s} top1_same={str(s['top1_same_as_psnr_mean']):5s} "
                  f"rho={s['spearman_vs_psnr_mean'] and round(s['spearman_vs_psnr_mean'],3)}")

    C = audit_C(runs)
    print("\n=== C. 种子噪声（逐图配对 ΔPSNR 的 sd）===")
    sds = [r["sd_delta_psnr"] for r in C]
    if sds:
        print(f"  n_pairs={len(C)}  sd: min={min(sds):.3f} median={median(sds):.3f} max={max(sds):.3f}")
        big = sorted(C, key=lambda r: -r["sd_delta_psnr"])[:8]
        for r in big:
            print(f"     {r['dataset']:18s} {r['method']:24s} s{r['seed_a']}vs{r['seed_b']} "
                  f"sd={r['sd_delta_psnr']:.3f} meanΔ={r['mean_delta_psnr']:+.3f} n={r['n_paired']}")

    with open(os.path.join(OUT, "audit_A_pathset.json"), "w", encoding="utf-8") as fh:
        json.dump(A, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "audit_B_protocols.json"), "w", encoding="utf-8") as fh:
        json.dump(B, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "audit_C_seednoise.json"), "w", encoding="utf-8") as fh:
        json.dump(C, fh, ensure_ascii=False, indent=1)
    print("\nwrote audit_A/B/C json to", OUT)


if __name__ == "__main__":
    main()
