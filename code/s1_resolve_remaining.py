#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1 / Step 8: 逐篇试取剩余 19 篇的 OA 全文。

本机现实（务必记住）:
  - www.mdpi.com 硬 403；mdpi-res.com CDN 可用
  - doi.org 403；Unpaywall 422；api.crossref.org 可用（元数据 → 找 OA 链接字段）
  - api.semanticscholar.org 可用（DOI -> openAccessPdf）
  - api.openalex.org 可用（DOI -> best_oa_location.pdf_url）★ 本机未试过，优先试
  - www.nature.com 通常可直连（Scientific Reports 全 OA）
  - sciencedirect / ieeexplore / dl.acm.org 几乎必被墙

策略（逐篇按优先级短路）:
  1) OpenAlex  DOI -> best_oa_location.pdf_url / locations[].pdf_url
  2) OpenAlex  DOI -> primary_location.landing_page_url（有的落地页就是 PDF）
  3) Semantic Scholar openAccessPdf
  4) 逐篇手工登记的直链兜底（nature / 机构仓库 / 预印本）
"""
import os, sys, io, json, time, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = os.path.join(OUT_DIR, "fulltext")
os.makedirs(OUT, exist_ok=True)

HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/pdf,text/html,application/json,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── 逐篇登记表 ───────────────────────────────────────────────────────────
# doi      : 若已知
# label    : 落盘名
# direct   : 已知/猜测的直链（逐步试）
# note     : 出版社/线索
TARGETS = [
    # ---- Elsevier / Expert Systems with Applications ----
    dict(id="DBTSR", label="dbtsr_eswa", doi=None,
         note="Expert Systems with Applications", direct=[]),
    dict(id="ORDiffSR", label="ordiffsr_eswa", doi=None,
         note="Expert Systems with Applications; GitHub 可能给预印本", direct=[]),

    # ---- DOAJ 收录（PLAN / DiffBSR）→ DOAJ API 可查元数据 ----
    dict(id="PLAN", label="plan_doaj", doi=None,
         note="DOAJ (Parallel Lattice Attention Network)", doaj=True, direct=[]),
    dict(id="DiffBSR", label="diffbsr_doaj", doi=None,
         note="DOAJ 收录",
         direct=["https://doaj.org/article/b98e0f0f1167469299cbc9cac67c9755"]),

    # ---- IEEE ----
    dict(id="MT-Hybrid", label="mt_hybrid_tgrs", doi=None,
         note="IEEE TGRS Vol 64", direct=[]),
    dict(id="Sen4x", label="sen4x_jstars", doi=None,
         note="IEEE JSTARS 19, 11042-11051",
         direct=["https://xplorestaging.ieee.org/document/11435384/"]),
    dict(id="BKX-HMM", label="bkx_hmm_tpami", doi=None,
         note="IEEE TPAMI 2026", direct=[]),

    # ---- Elsevier Engineering (CAE) ----
    dict(id="UDAMSR", label="udamsr_engineering", doi=None,
         note="Engineering (Elsevier/CAE)",
         direct=["https://www.sciencedirect.com/science/article/pii/S2095809926001682"]),
    dict(id="UDAMSR-mean", label="udamsr_mean", doi=None,
         note="同 UDAMSR 同源，单列记录 mean 口径", skip=True, direct=[]),

    # ---- Elsevier Neurocomputing ----
    dict(id="HAC-MoE", label="hac_moe_neucom", doi="10.1016/j.neucom.2026.133615",
         note="Neurocomputing Vol 685",
         direct=["https://www.sciencedirect.com/science/article/pii/S092523122600615"]),

    # ---- ACM ----
    dict(id="VolumeNet+TT", label="volumenet_tt_acm", doi="10.1145/3785443.3785445",
         note="ACM ICMIP",
         direct=["https://dl.acm.org/doi/abs/10.1145/3785443.3785445",
                 "https://dl.acm.org/doi/pdf/10.1145/3785443.3785445"]),

    # ---- Nature / Scientific Reports ----
    dict(id="MLIN-MetaWeight", label="mlin_metaw_srep", doi=None,
         note="Scientific Reports", nature=True, direct=[]),
    dict(id="SDGAN-SciRep", label="sdgan_srep", doi="10.1038/s41598-026-11971-3",
         note="Scientific Reports 16, 11971", nature=True,
         direct=["https://www.nature.com/articles/s41598-026-11971-3",
                 "https://www.nature.com/articles/s41598-026-11971-3.pdf"]),

    # ---- 机构仓库（Univ. Twente）----
    dict(id="S3-ESRGAN", label="s3_esrgan_utwente", doi=None,
         note="Univ. Twente research portal",
         direct=["https://research.utwente.nl/en/publications/ce847b6d-4fbc-4e27-9a90-11"]),

    # ---- 中文期刊（知网，基本无 OA）----
    dict(id="LocalStateSpace", label="local_state_space_cjig", doi=None,
         note="中国图象图形学报", cn=True, direct=[]),
    dict(id="JNUN-CA", label="jnun_ca_xbdx", doi=None,
         note="西北大学学报(自然科学版) 56(1):108-117", cn=True, direct=[]),

    # ---- 会议/榜单（无 PDF，只有榜单页）----
    dict(id="NTIRE2026-ESR", label="ntire2026_esr_codabench", doi=None,
         note="Codabench (CVPRW); 无论文 PDF，仅榜单",
         direct=["https://www.codabench.org/competitions/13553/"]),

    # ---- 其余 ----
    dict(id="PLGMamba", label="plgmamba_hsi", doi=None,
         note="HSI-SR 期刊（radaislice 新闻页）",
         direct=["https://radaislice.com/news/ai-state-space-model-enhances-hyperspectra"]),
    dict(id="HSISR-KAN", label="hsisr_kan", doi=None,
         note="HSI-SR 方法/综述（emergentmind 汇总）",
         direct=["https://www.emergentmind.com/topics/hyperspectral-single-image-super-resolutio"]),
]


def get(url, timeout=45, raw=False):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        return (b, r.headers.get("Content-Type", "")) if not raw else b


def jget(url, timeout=30):
    b, ct = get(url, timeout=timeout)
    # OpenAlex 需要 mailto 参数才稳定；这里统一加在调用处
    txt = b.decode("utf-8", "replace")
    return json.loads(txt)


def openalex_by_doi(doi):
    """OpenAlex: DOI -> 可能的 OA PDF 链接候选（含 landing page）。"""
    try:
        u = ("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) +
             "?mailto=czy@example.org")
        j = jget(u)
    except Exception as e:
        return [], f"<openalex fail {type(e).__name__}>"
    cands = []
    for key in ("best_oa_location", "primary_location"):
        loc = j.get(key) or {}
        for f in ("pdf_url", "landing_page_url"):
            if loc.get(f):
                cands.append(loc[f])
    for loc in (j.get("locations") or []):
        for f in ("pdf_url", "landing_page_url"):
            if loc.get(f):
                cands.append(loc[f])
    # 去重保序
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c); out.append(c)
    return out, j.get("title", "")


def s2_open_pdf(doi):
    try:
        u = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(doi)}"
             f"?fields=title,openAccessPdf,externalIds")
        j = jget(u)
        return j.get("openAccessPdf", {}).get("url"), j.get("title", "")
    except Exception as e:
        return None, f"<s2 fail: {type(e).__name__}>"


def doaj_by_title(q):
    """DOAJ 搜索 -> 可能的 fulltext 链接。"""
    try:
        u = ("https://doaj.org/api/search/articles/" + urllib.parse.quote(q) +
             "?pageSize=3")
        j = jget(u)
    except Exception as e:
        return [], f"<doaj fail {type(e).__name__}>"
    out = []
    for r in j.get("results", []):
        for l in (r.get("bibjson", {}).get("link") or []):
            if l.get("url"):
                out.append(l["url"])
        ja = (r.get("bibjson", {}).get("journal") or {})
        if ja.get("publisher"):
            out.append("PUBLISHER::" + ja["publisher"])
    return out, ""


def try_pdf(url, dest):
    try:
        raw, ct = get(url, timeout=60)
        ispdf = raw[:5] == b"%PDF-"
        if ispdf:
            open(dest, "wb").write(raw)
            return True, len(raw), "application/pdf"
        # 非 PDF 也存一份 html 供人工看（只存小的）
        if len(raw) < 3_000_000 and b"<html" in raw[:4000].lower():
            open(dest.replace(".pdf", ".landing.html"), "wb").write(raw)
        return False, len(raw), ct
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {str(e)[:50]}"


def main():
    status = {}
    for t in TARGETS:
        tid, label = t["id"], t["label"]
        print("=" * 88)
        print(f"{tid}  ({label})   {t.get('note','')}")
        if t.get("skip"):
            print("  SKIP（与已处理条目同源）")
            status[tid] = {"ok": False, "reason": "skip-duplicate"}
            continue
        if t.get("cn"):
            print("  SKIP（中文期刊/知网，无 OA 直链）")
            status[tid] = {"ok": False, "reason": "cn-journal-no-oa"}
            continue

        dest = os.path.join(OUT, f"{label}.pdf")
        cands = []
        title = ""

        # (a) OpenAlex / S2 by DOI
        if t.get("doi"):
            oa, title = openalex_by_doi(t["doi"])
            print(f"  [OpenAlex] {len(oa)} 候选  title={title[:50]}")
            for c in oa[:6]:
                print(f"      - {c[:110]}")
            cands += oa
            s2u, _ = s2_open_pdf(t["doi"])
            if s2u:
                print(f"  [S2] {s2u[:110]}")
                cands.append(s2u)

        # (b) DOAJ
        if t.get("doaj"):
            dj, _ = doaj_by_title(tid)
            print(f"  [DOAJ] {len(dj)} 链接")
            for c in dj[:6]:
                print(f"      - {c[:110]}")
            cands += [c for c in dj if not c.startswith("PUBLISHER::")]

        # (c) 直链兜底
        cands += t.get("direct", [])

        # 去重
        seen, uniq = set(), []
        for c in cands:
            if c not in seen:
                seen.add(c); uniq.append(c)

        got = False
        for c in uniq:
            ok, n, ct = try_pdf(c, dest)
            tag = "OK  " if ok else "FAIL"
            print(f"  {tag} {n:>9} {ct[:28]:<28} {c[:88]}")
            if ok:
                got = True
                break

        status[tid] = {"ok": got, "pdf": dest if got else None,
                       "label": label, "n_cand": len(uniq), "title": title}
        time.sleep(1.2)

    json.dump(status, open(os.path.join(OUT, "_fetch_remaining.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = [k for k, v in status.items() if v.get("ok")]
    print("\n" + "=" * 88)
    print(f"成功取到 PDF: {len(ok)}/{len(status)} -> {ok}")
    for k, v in status.items():
        if not v.get("ok"):
            print(f"  MISS {k:<18} {v.get('reason','')}")


if __name__ == "__main__":
    main()
