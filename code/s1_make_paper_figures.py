#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 / Figures: 论文两张核心图（Q2+ 期刊质量，300 dpi PNG + PDF + SVG）。

Fig 1: 种子噪声 sd vs 测试集规模（4 点 + 单调趋势）
Fig 2: 方法效应 vs 种子噪声（327 配对散点 + y=x 参考线）
"""
import os, sys, io, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = OUT_DIR
FIG = os.path.join(PROJ_ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

# ---- 统一风格（细线 + 紧凑 + 四边全封）----
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.linewidth": 0.55,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "xtick.major.width": 0.55, "ytick.major.width": 0.55,
    "xtick.major.size": 3.0, "ytick.major.size": 3.0,
    "axes.grid": True, "grid.linewidth": 0.35, "grid.alpha": 0.35,
    "legend.frameon": True, "legend.framealpha": 0.9,
    "legend.edgecolor": "0.7", "legend.fontsize": 8,
    "figure.dpi": 300, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})

C_RED = "#C0392B"     # 涨/危险
C_GREEN = "#1E8449"   # 跌/安全
C_BLUE = "#2471A3"
C_GREY = "#7F8C8D"


def save(fig, name):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"))
    print(f"  saved {name}.png/.pdf/.svg")


# ============================================================
# Fig 1: 种子噪声 vs 测试集规模
# ============================================================
def fig1():
    b = json.load(open(os.path.join(OUT, "audit_B_protocols.json"), encoding="utf-8"))
    n_imgs = {"AID": 1000, "RSSCN7": 281, "UCMerced_LandUse": 210, "WHU-RS19": 101}
    med = {"AID": 0.0728, "RSSCN7": 0.0632, "UCMerced_LandUse": 0.1070, "WHU-RS19": 0.1202}
    mx = {"AID": 0.1187, "RSSCN7": 0.1169, "UCMerced_LandUse": 0.1701, "WHU-RS19": 0.2485}
    labels = {"AID": "AID", "RSSCN7": "RSSCN7", "UCMerced_LandUse": "UCMerced", "WHU-RS19": "WHU-RS19"}

    fig, ax = plt.subplots(figsize=(3.6, 2.7))
    xs = [n_imgs[k] for k in n_imgs]
    ys = [med[k] for k in n_imgs]
    yl = [mx[k] for k in n_imgs]

    ax.errorbar(xs, ys, yerr=[[ys[i] - 0 for i in range(4)],
                              [yl[i] - ys[i] for i in range(4)]],
                fmt="o", color=C_BLUE, ecolor=C_GREY, elinewidth=0.55,
                capsize=2.2, capthick=0.55, ms=4.5, lw=0.55,
                label="median $\\pm$ (min, max)")

    for k in n_imgs:
        ax.annotate(labels[k], (n_imgs[k], med[k]),
                    textcoords="offset points", xytext=(4, 5),
                    fontsize=7.5, color="#2C3E50")

    ax.set_xscale("log")
    ax.set_xticks([101, 210, 281, 1000])
    ax.set_xticklabels(["101", "210", "281", "1000"])
    ax.set_xlabel("Test-set size (images, log scale)")
    ax.set_ylabel("Seed-noise sd of $\\Delta$PSNR (dB)")
    ax.set_ylim(0.0, 0.28)
    ax.legend(loc="upper right")
    for s in ax.spines.values():
        s.set_linewidth(0.55)

    save(fig, "fig1_noise_vs_testsize")
    plt.close(fig)


# ============================================================
# Fig 2: 效应 vs 噪声（327 配对）
# ============================================================
def fig2():
    d = json.load(open(os.path.join(OUT, "audit_D_effect_vs_noise.json"), encoding="utf-8"))
    eff, noise, flip = [], [], []
    for r in d:
        e = abs(r["mean_effect_dB"])
        n = r.get("sd_seed_ref_a", 0) or 0
        eff.append(e); noise.append(n)
        flip.append(not r.get("sign_consistent", True))

    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    lim = max(max(eff), max(noise)) * 1.08
    ax.plot([0, lim], [0, lim], ls="--", lw=0.7, color=C_GREY, zorder=1,
            label="$|\\Delta|$ = seed sd")

    ef = [e for e, f in zip(eff, flip) if f]
    nf = [n for n, f in zip(noise, flip) if f]
    es = [e for e, f in zip(eff, flip) if not f]
    ns = [n for n, f in zip(noise, flip) if not f]

    ax.scatter(ns, es, s=5, color=C_GREEN, alpha=0.55, lw=0, zorder=2,
               label=f"stable ({(len(es))})")
    ax.scatter(nf, ef, s=5, color=C_RED, alpha=0.55, lw=0, zorder=2,
               label=f"sign-flipped ({len(ef)})")

    below = sum(1 for e, n in zip(eff, noise) if e < n)
    ax.text(0.04, 0.96, f"{below}/{len(d)} = {below/len(d)*100:.1f}%\nbelow noise",
            transform=ax.transAxes, va="top", fontsize=7.8, color="#2C3E50")

    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Seed-noise sd (dB)")
    ax.set_ylabel("$|$Method effect$|$ (dB)")
    ax.legend(loc="lower right")
    for s in ax.spines.values():
        s.set_linewidth(0.55)

    save(fig, "fig2_effect_vs_noise")
    plt.close(fig)


if __name__ == "__main__":
    print("生成论文图（300 dpi PNG + PDF + SVG）...")
    fig1()
    fig2()
    print("完成 ->", FIG)
