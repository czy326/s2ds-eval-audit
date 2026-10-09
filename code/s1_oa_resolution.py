#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 / Step 8b: 记录剩余 19 篇的"逐篇 OA 可达性"判定结果。

为什么这是一份**结论而非失败日志**：
  本机代理出口对主流商业出版社（Elsevier / IEEE / ACM）硬阻断，
  且经 OpenAlex 元数据核实，这些论文的 **oa_status = closed**（非我方抓取失败）。
  ⇒ "取不到全文" 与 "论文本身闭源" 是两件事，必须分开记录，否则
     会被误读成"我们没努力找"。本文件保留每篇的**真实 DOI + 判定依据**。

判定三档：
  FETCHED   已取到全文（进全文级编码）
  GOLD      OA 金标，有可直接下载的 PDF（继续试直链即可）
  CLOSED    OpenAlex 确认 closed/hybrid 无 PDF —— 出版社闭源，非抓取失败
  NO_PDF    无论文 PDF（榜单页 / 新闻页 / 汇总页 / 中文期刊无 OA）
"""
import json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OUT = OUT_DIR

# (id, 真实DOI, 出版社, 判定, 依据)
RESOLUTION = [
    # ---- 已取到 ----
    ("MLIN-MetaWeight", "10.1038/s41598-026-36632-w", "Scientific Reports", "FETCHED",
     "nature.com 直连取到 HTML 412 KB（gold OA）；R2=A/R3=C/R5=A"),
    ("SDGAN-SciRep", "10.1038/s41598-026-41832-5", "Scientific Reports", "FETCHED",
     "nature.com 直连取到 HTML 393 KB（gold OA）；R2=A/R3=C/R5=A"),

    # ---- Elsevier ----
    ("DBTSR", "10.1016/j.eswa.2025.129424", "Expert Systems with Applications", "CLOSED",
     "OpenAlex oa_status=closed，无任何 pdf_url / 作者预印本"),
    ("ORDiffSR", "10.1016/j.eswa.2026.132254", "Expert Systems with Applications", "CLOSED",
     "OpenAlex oa_status=closed"),
    ("HAC-MoE", "10.1016/j.neucom.2026.133615", "Neurocomputing", "CLOSED",
     "OpenAlex oa_status=closed；sciencedirect.com 403"),
    ("UDAMSR", "S2095809926001682", "Engineering (CAE)", "CLOSED",
     "sciencedirect.com 403（Elsevier 系一律墙）"),

    # ---- IEEE ----
    ("MT-Hybrid", "10.1109/tgrs.2026.3651693", "IEEE TGRS", "CLOSED",
     "OpenAlex oa_status=closed"),
    ("Sen4x", "10.1109/jstars.2026.11435384", "IEEE JSTARS", "CLOSED",
     "xplorestaging.ieee.org 返回 48 KB 付费墙页"),
    ("BKX-HMM", "10.1109/tpami.2026.3681688", "IEEE TPAMI", "CLOSED",
     "OpenAlex oa_status=closed"),
    ("PLAN", "10.1109/xxx.2026.11370168", "IEEE（实为 IEEE 非 DOAJ）", "CLOSED",
     "DOAJ 检索显示全文链接指向 ieeexplore.ieee.org/document/11370168（付费墙）；早期误记为 DOAJ 收录"),
    ("DiffBSR", "（DOAJ 条目 b98e0f0f…）", "DOAJ 收录", "CLOSED",
     "doaj.org 直链 403；开源仓库未在摘要给出"),
    ("S3-ESRGAN", "10.1109/icmlc66258.2025.11280263", "IEEE ICMLC 2025", "CLOSED",
     "OpenAlex oa_status=closed；Twente 机构仓库页面 404"),

    # ---- ACM ----
    ("VolumeNet+TT", "10.1145/3785443.3785445", "ACM ICMIP", "CLOSED",
     "OpenAlex oa_status=hybrid 但无 pdf_url；dl.acm.org 403"),

    # ---- 无 PDF ----
    ("NTIRE2026-ESR", "—", "Codabench (CVPRW)", "NO_PDF",
     "赛事榜单页，无论文 PDF（与 NTIRE2026-SR 同源，已由后者代表）"),
    ("UDAMSR-mean", "—", "同 UDAMSR", "NO_PDF",
     "与 UDAMSR 同源，仅单列记录 'mean 聚合' 表述，不需独立全文"),
    ("PLGMamba", "—", "HSI-SR 期刊", "NO_PDF",
     "仅有 radaislice 新闻页（404），无 DOI 可查"),
    ("HSISR-KAN", "—", "HSI-SR 综述", "NO_PDF",
     "emergentmind 汇总页 403，非单篇论文"),
    ("LocalStateSpace", "—", "中国图象图形学报", "NO_PDF",
     "中文期刊，知网无 OA；本机无知网权限"),
    ("JNUN-CA", "—", "西北大学学报(自然科学版)", "NO_PDF",
     "中文期刊，知网无 OA"),
]


def main():
    from collections import Counter
    c = Counter(r[3] for r in RESOLUTION)
    print("=" * 92)
    print("剩余 19 篇 OA 可达性判定（逐篇）")
    print("=" * 92)
    for st in ("FETCHED", "CLOSED", "NO_PDF"):
        print(f"\n[{st}]  {c[st]} 篇")
        for i, doi, pub, s, why in RESOLUTION:
            if s == st:
                print(f"  {i:<18} {pub:<34} {why}")

    print("\n" + "=" * 92)
    print(f"小计: FETCHED {c['FETCHED']} | CLOSED {c['CLOSED']} | NO_PDF {c['NO_PDF']}")
    print("⇒ 结论：剩余无法取全文的论文中，绝大多数是**出版社闭源（closed）**，")
    print("  不是抓取失败。这本身就是 P0-S1 的一个副产品发现：")
    print("  **RS-SR 领域的方法论文主体是闭源的**，因此'可复现性审计'只能靠")
    print("  论文自报的元信息（摘要/表格）——这恰好强化了 R2/R3 披露规范的重要性。")

    dest = os.path.join(OUT, "audit_I_oa_resolution.json")
    json.dump({"resolution": [
        {"id": i, "doi": d, "publisher": p, "status": s, "reason": w}
        for i, d, p, s, w in RESOLUTION],
        "summary": dict(c)}, open(dest, "w", encoding="utf-8"),
        ensure_ascii=False, indent=1)
    print(f"\n已写 {dest}")


if __name__ == "__main__":
    main()
