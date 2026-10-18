# -*- coding: utf-8 -*-
"""
Corrected proportions and cluster-robust intervals for the pair-level statistics.

Two defects are corrected here, both of the same kind: a quantity that cannot be
assessed was being counted as the null result.

  1. A pair whose two methods share only one seed was recorded with
     sign_consistent=True, because a single observed sign trivially forms a set
     of size one. Such a pair cannot reverse, so counting it in the denominator
     dilutes the reversal rate. Pairs with fewer than two shared seeds are now
     excluded from that denominator rather than counted as consistent.

  2. A missing seed standard deviation was read as zero, so "no reference
     dispersion is available" became "the effect is not below the noise". Those
     pairs are now excluded from the denominator of the below-noise fraction.

The 327 pairs are also not independent: each method enters many pairs. Intervals
therefore come from a cluster bootstrap over methods within benchmark, with each
pair weighted by the product of its endpoints' resampling multiplicities.

Writes audit_J_cluster_ci.json.
"""
import json
import os
import random
import io
import sys
import collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("S2DS_AUDIT_OUT") or os.path.join(
    os.path.dirname(_HERE), "out")
SRC = os.path.join(OUT, "audit_D_effect_vs_noise.json")
DST = os.path.join(OUT, "audit_J_cluster_ci.json")

N_BOOT = 4000
SEED = 20261018


def assessable(p, which):
    """Can this pair be judged under the given definition?"""
    a, b = p.get("sd_seed_ref_a"), p.get("sd_seed_ref_b")
    if which == "sign_reversal":
        return p.get("n_seeds", 0) >= 2
    if which == "below_noise_ref_a":
        return a is not None
    return a is not None and b is not None       # min and max need both


def hit(p, which):
    if which == "sign_reversal":
        return p.get("sign_consistent") is False
    a = abs(p.get("mean_effect_dB") or 0.0)
    sa, sb = p.get("sd_seed_ref_a"), p.get("sd_seed_ref_b")
    if which == "below_noise_min":
        return a < min(sa, sb)
    if which == "below_noise_ref_a":
        return a < sa
    return a < max(sa, sb)


TARGETS = ["sign_reversal", "below_noise_min", "below_noise_ref_a",
           "below_noise_max"]


def hit_old(p, which):
    """The convention in the shipped file: a missing sd is read as zero."""
    if which == "sign_reversal":
        return p.get("sign_consistent") is False
    a = abs(p.get("mean_effect_dB") or 0.0)
    sa = p.get("sd_seed_ref_a") or 0.0
    sb = p.get("sd_seed_ref_b") or 0.0
    if which == "below_noise_min":
        return a < min(sa, sb)
    if which == "below_noise_ref_a":
        return a < sa
    return a < max(sa, sb)


def main():
    pairs = json.load(open(SRC, encoding="utf-8"))
    clusters = collections.defaultdict(set)
    for p in pairs:
        clusters[p["dataset"]].add(p["method_a"])
        clusters[p["dataset"]].add(p["method_b"])
    n_clusters = sum(len(v) for v in clusters.values())

    print("pairs %d, method clusters %d, per benchmark %s"
          % (len(pairs), n_clusters, {k: len(v) for k, v in sorted(clusters.items())}))
    print("shared-seed counts:", dict(collections.Counter(p["n_seeds"] for p in pairs)))
    print()

    # ---------------------------------------------------------------- point + CI
    rng = random.Random(SEED)
    out_blocks = {}
    print("%-19s %-14s %-16s %-16s" % ("statistic", "old (all 327)", "corrected", "95% cluster CI"))
    for name in TARGETS:
        sub = [p for p in pairs if assessable(p, name)]
        k = sum(1 for p in sub if hit(p, name))
        pct = 100.0 * k / len(sub)

        reps = []
        for _ in range(N_BOOT):
            weights = {}
            for ds, methods in clusters.items():
                ms = sorted(methods)
                cnt = collections.Counter(rng.choice(ms) for _ in range(len(ms)))
                for m in ms:
                    weights[(ds, m)] = cnt.get(m, 0)
            num = den = 0.0
            for p in sub:
                w = weights.get((p["dataset"], p["method_a"]), 0) * \
                    weights.get((p["dataset"], p["method_b"]), 0)
                if w:
                    num += w * (1.0 if hit(p, name) else 0.0)
                    den += w
            if den:
                reps.append(100.0 * num / den)
        reps.sort()
        lo = reps[int(0.025 * len(reps))]
        hi = reps[int(0.975 * len(reps))]

        old_k = sum(1 for p in pairs if hit_old(p, name))
        old_all = 100.0 * old_k / len(pairs)
        print("%-19s %-14s %-16s %-16s"
              % (name, "%d/%d = %.1f%%" % (old_k, len(pairs), old_all),
                 "%d/%d = %.1f%%" % (k, len(sub), pct),
                 "[%.1f, %.1f]" % (lo, hi)))
        out_blocks[name] = {
            "k": k, "n_assessable": len(sub), "pct": round(pct, 1),
            "ci95_cluster": [round(lo, 1), round(hi, 1)],
            "old_denominator": len(pairs),
            "old_pct": round(old_all, 1),
            "n_boot": N_BOOT, "seed": SEED,
        }

    lo_range = out_blocks["below_noise_min"]["pct"]
    hi_range = out_blocks["below_noise_max"]["pct"]
    print("\nspread across the three below-noise definitions: %.1f to %.1f = %.1f points"
          % (lo_range, hi_range, hi_range - lo_range))
    print("old spread as printed in the manuscript: 47.1 to 68.5 = 21.4 points")

    # ------------------------------------------------- per-benchmark reversal rate
    print("\nper-benchmark reversal, assessable pairs only:")
    per_ds = {}
    for ds in sorted({p["dataset"] for p in pairs}):
        sub = [p for p in pairs if p["dataset"] == ds and assessable(p, "sign_reversal")]
        k = sum(1 for p in sub if hit(p, "sign_reversal"))
        per_ds[ds] = {"k": k, "n": len(sub), "pct": round(100.0 * k / len(sub), 1)}
        print("  %-18s %3d/%-3d = %5.1f%%" % (ds, k, len(sub), per_ds[ds]["pct"]))

    payload = {
        "convention": ("Denominators count only pairs whose statistic is "
                       "assessable: at least two shared seeds for sign "
                       "reversal, a defined reference seed sd for below-noise. "
                       "Intervals are percentile 95%% bounds from a cluster "
                       "bootstrap over methods within benchmark, %d replicates, "
                       "seed %d, each pair weighted by the product of its "
                       "endpoints' multiplicities." % (N_BOOT, SEED)),
        "n_pairs": len(pairs),
        "n_clusters": n_clusters,
        "proportions": out_blocks,
        "per_benchmark_reversal": per_ds,
    }
    with open(DST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    print("\nwrote %s" % DST)


if __name__ == "__main__":
    main()
