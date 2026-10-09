#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 Audit / Step 6 (v2): 把"论文声称的 dB 增益"换算成"它自己数据集上的噪声倍数"。

核心表（能直接进论文）:
  对每条声称增益 Δ，与**本审计实测的同数据集种子噪声 sd** 相除:
      ratio = Δ / sd_seed(dataset)
  ratio < 1  ⇒ 该"超越 SOTA"落在换一个种子就会消失的范围内
  1 ≤ ratio < 2 ⇒ 勉强可见
  ratio ≥ 2  ⇒ 较稳健

数据来源:
  - 声称增益 CLAIMS：**从 audit_F_field_survey.json 自动抽取**（单一真源，避免两处不同步）
  - 各数据集噪声 sd：**从 audit_C_seednoise.json 读实测值**（若缺失则回落到全库中位）
"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = OUT_DIR


def load_json(name):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def dataset_noise_from_auditC():
    """从 audit_C 抽出逐数据集配对 ΔPSNR 的 sd 中位/max。返回 {ds: {...}}。

    audit_C 实际结构 = 扁平 list[{dataset, method, seed_a, seed_b, n_paired,
                                 mean_delta_psnr, sd_delta_psnr, max_abs_delta, ...}]
    """
    c = load_json("audit_C_seednoise.json")
    if not c:
        return {}
    if isinstance(c, dict) and "pairs" in c:
        c = c["pairs"]
    if not isinstance(c, list):
        return {}
    by_ds = {}
    for row in c:
        if not isinstance(row, dict):
            continue
        ds = row.get("dataset")
        sd = row.get("sd_delta_psnr")
        if ds is None or not isinstance(sd, (int, float)):
            continue
        by_ds.setdefault(ds, []).append(float(sd))
    out = {}
    for ds, sds in by_ds.items():
        sds = sorted(sds)
        out[ds] = {
            "sd_median": sds[len(sds) // 2],
            "sd_max": sds[-1],
            "sd_min": sds[0],
            "n_pairs": len(sds),
        }
    return out


def main():
    cnoise = dataset_noise_from_auditC()
    # 全库回落值（本审计 C/D 线实测）
    FALLBACK = {"sd_median": 0.088, "sd_max": 0.248}

    survey = load_json("audit_F_field_survey.json")
    if not survey:
        print("!! 缺少 audit_F_field_survey.json，请先运行 s1_field_survey.py")
        return

    # 从编码表抽取所有 non-None 增益
    claims = []
    for p in survey["papers"]:
        g = p.get("claimed_gain_dB")
        if g is None:
            continue
        claims.append({
            "id": p["id"],
            "gain": float(g),
            "datasets": p.get("datasets") or [],
            "vs": p.get("claimed_vs") or "",
            "quote": p.get("gain_quote") or "",
        })

    print("=" * 100)
    print("论文声称增益 ÷ 本审计实测种子噪声（P0-S1 核心表 · 从编码表自动抽取）")
    print("=" * 100)
    print(f"编码表论文总数: {survey['n_papers']}；其中给出可核查 dB 增益: {len(claims)}")
    print(f"审计实测各数据集噪声: {json.dumps(cnoise, ensure_ascii=False) if cnoise else '(未解析到，用全库中位)'}")
    print("-" * 100)
    print(f"{'论文':16s} {'增益(dB)':>8s} {'噪声sd中位':>10s} {'Δ/sd':>6s}  {'判读':12s} 数据集")
    print("-" * 100)

    SAME_DS_MATCH = {   # 声称增益所对应数据集 → audit_C 中的键名候选
        "AID": ["AID", "aid"],
        "WHU-RS19": ["WHU-RS19", "whu"],
        "UCMerced": ["UCMerced", "UCMerced_LandUse", "ucm"],
        "RSSCN7": ["RSSCN7", "rsscn7"],
    }

    def noise_for(datasets):
        for d in datasets:
            for k, cands in SAME_DS_MATCH.items():
                if any(c in d for c in cands):
                    for nk, nv in cnoise.items():
                        if any(c in nk for c in cands):
                            return nv, k
        return FALLBACK, "全库中位(回落)"

    rows = []
    for c in sorted(claims, key=lambda x: x["gain"]):
        nv, ds_label = noise_for(c["datasets"])
        sd = nv["sd_median"]
        ratio = c["gain"] / sd if sd else float("inf")
        if ratio < 1:
            verdict = "⚠️ 噪声内"
        elif ratio < 2:
            verdict = "△ 勉强可见"
        else:
            verdict = "✅ 超噪声"
        print(f"{c['id']:16s} {c['gain']:>8.2f} {sd:>10.3f} {ratio:>6.2f}  {verdict:12s} {ds_label}")
        rows.append({**c, "sd_median": sd, "sd_max": nv["sd_max"],
                     "ratio": ratio, "verdict": verdict, "noise_src": ds_label})

    # 严格口径：用该数据集噪声上限
    print("\n[严格口径] 用噪声 sd 上限重判（若连上限都超不过 ⇒ 必然落在噪声内）：")
    n_strict = 0
    for r in rows:
        rr = r["gain"] / r["sd_max"] if r["sd_max"] else float("inf")
        if rr < 1:
            n_strict += 1
        flag = "⚠️ 噪声内" if rr < 1 else ("△ 勉强" if rr < 2 else "✅ 稳健")
        print(f"  {r['id']:16s} +{r['gain']:.2f} dB  Δ/sd_max = {rr:.2f}  {flag}")

    n_within = sum(1 for r in rows if r["verdict"] == "⚠️ 噪声内")
    print("-" * 100)
    print(f"\n⇒ 按噪声中位判读: {n_within}/{len(rows)} 条声称增益落在换种子即消失的范围内。")
    print(f"⇒ 按噪声上限判读: {n_strict}/{len(rows)} 条。")
    print(f"\n⚠️ 证据边界（必须写进论文方法节）：")
    print(f"   - 上述噪声 sd 来自**本审计的 RS-SR 库**（AID/RSSCN7/UCMerced/WHU-RS19），")
    print(f"     不是被引论文自己数据集上的实测值。跨数据集比较时须注明。")
    print(f"   - 只对**给出了具体 dB** 的 {len(rows)}/{survey['n_papers']} 篇可判读；")
    print(f"     其余 {survey['n_papers']-len(rows)} 篇因未给 dB 而无法纳入此表（本身即一项发现）。")

    json.dump({
        "n_papers_total": survey["n_papers"],
        "n_claims_quantified": len(rows),
        "n_within_noise_median": n_within,
        "n_within_noise_max": n_strict,
        "seed_noise_by_dataset": cnoise,
        "fallback": FALLBACK,
        "rows": rows,
        "boundary_note": "噪声 sd 来自本审计 RS-SR 库，非被引论文自身数据集。"
                         "仅对给出具体 dB 的论文可判读。",
    }, open(os.path.join(OUT, "audit_G_gain_vs_noise.json"), "w", encoding="utf-8"),
        ensure_ascii=False, indent=1)
    print("\nwrote audit_G_gain_vs_noise.json")


if __name__ == "__main__":
    main()
