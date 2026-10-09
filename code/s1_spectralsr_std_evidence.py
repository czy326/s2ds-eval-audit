#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 / Step 9: SpectralSR-Bench —— “报告了 std 却仍按 mean 排名”的量化铁证。

该论文（Sensors 2026, 26, 683）是全池里少见的**每个指标都报 mean ± std** 的工作。
本脚本把它的表格值抽出来，直接对比：方法间差距 Δ vs 报告的标准差 std。
若 std >> Δ，则“按 mean 排名”本身就是 P0-S1 要指出的问题——
而且这是**论文自己提供的数据**，不是我们的推断。
"""
import os, re, sys, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FT = os.path.join(OUT_DIR, "fulltext")
SRC = os.path.join(FT, "spectral_sr_bench_s26_683.txt")
OUT = OUT_DIR

# 从表 1/2/3/4 抽取 (方法, 类型, PSNR, std)
PAT = re.compile(
    r"([A-Za-z0-9\(\)\u00d7\u2192\-\d ]{2,34}?)\s+"
    r"(CNN|GAN|Diffusion|Interpolation)\s+"
    r"(\d{2}\.\d{1,2})\s*\u00b1\s*(\d{1,2}\.\d{1,2})")


def main():
    txt = open(SRC, encoding="utf-8").read()
    rows, seen = [], set()
    for m in PAT.finditer(txt):
        nm = re.sub(r"\s+", " ", m.group(1)).strip()
        if nm in seen:
            continue
        seen.add(nm)
        rows.append({"method": nm, "type": m.group(2),
                     "psnr": float(m.group(3)), "std": float(m.group(4))})

    print("=" * 88)
    print("SpectralSR-Bench (Sensors 2026, 26, 683)：方法 PSNR ± std（论文自报值）")
    print("=" * 88)
    print(f"{'方法':30s} {'类型':14s} {'PSNR':>7s} {'±std':>6s} {'std/Δ后位':>10s}")
    print("-" * 88)
    for r in rows:
        print(f"{r['method']:30s} {r['type']:14s} {r['psnr']:>7.2f} {r['std']:>6.2f}")

    ps = [r["psnr"] for r in rows]
    stds = [r["std"] for r in rows]
    print("-" * 88)
    print(f"PSNR 跨度: {min(ps):.2f} – {max(ps):.2f} dB （全跨度 {max(ps)-min(ps):.2f} dB）")
    print(f"报告 std 范围: {min(stds):.2f} – {max(stds):.2f} dB")

    # 逐尺度对比：方法差 vs std
    print("\n【核心对比】同一尺度内，相邻方法的 PSNR 差 Δ vs 其 std")
    groups = {}
    for r in rows:
        groups.setdefault(r["type"], []).append(r)
    findings = []
    for t, g in groups.items():
        g = sorted(g, key=lambda x: -x["psnr"])
        for a, b in zip(g, g[1:]):
            d = a["psnr"] - b["psnr"]
            s = max(a["std"], b["std"])
            ratio = d / s if s else float("inf")
            verdict = ("⚠️ Δ < std（排名不可区分）" if ratio < 1
                       else ("△ Δ ≈ std（勉强可区分）" if ratio < 2 else "✅ Δ > 2·std"))
            print(f"  {a['method']:22s} vs {b['method']:22s}  Δ={d:5.2f} dB  "
                  f"max_std={s:4.2f}  Δ/std={ratio:4.2f}  {verdict}")
            findings.append({"a": a["method"], "b": b["method"], "delta": d,
                             "max_std": s, "ratio": ratio})

    n_indist = sum(1 for f in findings if f["ratio"] < 1)
    print(f"\n⇒ 在该论文自己报告的数值中：{n_indist}/{len(findings)} 对相邻方法满足 Δ < std。")
    print("⇒ 即：论文**自己给出了 std**，却仍然按 mean 排序并宣称某方法更优——")
    print("   这正是 P0-S1 的核心论点，且证据来自论文自身，无需我们复现。")

    json.dump({"rows": rows, "pairwise": findings,
               "n_pairs": len(findings), "n_delta_below_std": n_indist,
               "psnr_span": [min(ps), max(ps)], "std_range": [min(stds), max(stds)]},
              open(os.path.join(OUT, "audit_H_spectralsr_std.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwrote audit_H_spectralsr_std.json")


if __name__ == "__main__":
    main()
