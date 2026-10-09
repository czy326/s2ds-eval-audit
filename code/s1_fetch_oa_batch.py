#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1 / Step 7c: 逐篇试非 arXiv 论文的 OA 变体（剩余 19 篇）。

对本机通道的现实判断：
  - www.mdpi.com 主站 403；mdpi-res.com CDN 可达（已通）。
  - doi.org 403；Unpaywall 422。
  - Semantic Scholar Graph API 可达（DOI/标题 -> openAccessPdf.url, isOpenAccess）。
  - Nature (nature.com) 常可达。
  - IEEE/Elsevier/ACM 主站基本 403，但可能通过 S2 拿到 OA 变体（作者仓库/PMC/preprint）。

策略（每篇按序尝试）:
  1) Semantic Scholar（按 DOI 或标题）-> openAccessPdf.url（若非主站域名则尝试下载）
  2) 直接尝试已知 OA 域名候选（nature.com / mdpi-res.com / PMC / research.utwente.nl 等）
  3) 记录失败原因，供报告 §6.5 表格使用

用法:
  python s1_fetch_oa_batch.py            # 全部
  python s1_fetch_oa_batch.py sen4x      # 单篇（按 key）
"""
import os, sys, io, json, time, re, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = os.path.join(OUT_DIR, "fulltext")
os.makedirs(OUT, exist_ok=True)

HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/pdf,text/html,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# key -> {label, doi, title, direct[]}
TARGETS = {
    # ---- IEEE / Elsevier / ACM 系（需权限，先试 S2 OA 变体）----
    "sen4x":       {"label": "sen4x_jstars",        "doi": "10.1109/JSTARS.2026.1143538",
                    "title": "Sen4x Sentinel-2 super-resolution downstream classification", "direct": []},
    "hacmoe":      {"label": "hacmoe_neucom",       "doi": "10.1016/j.neucom.2026.133615",
                    "title": "HAC-MoE unsupervised blind super-resolution", "direct": []},
    "udamsr":      {"label": "udamsr_eng",          "doi": "10.1016/j.eng.2026.03.012",
                    "title": "UDAMSR unsupervised domain adaptation multi-scale super-resolution", "direct": []},
    "volumenet":   {"label": "volumenet_tt_acm",    "doi": "10.1145/3785443.3785445",
                    "title": "VolumeNet+TT pansharpening", "direct": []},
    "bkxhmm":      {"label": "bkx_hmm_tpami",       "doi": "",
                    "title": "BKX-HMM hyperspectral super-resolution", "direct": []},
    "mt_hybrid":   {"label": "mt_hybrid_tgrs",      "doi": "",
                    "title": "MT-Hybrid multi-temporal super-resolution TGRS", "direct": []},

    # ---- Nature / Sci Rep 系（常可达）----
    "sdgan":       {"label": "sdgan_scirep",        "doi": "10.1038/s41598-026-11971-2",
                    "title": "SDGAN super-resolution Scientific Reports", "direct": []},
    "mlin":        {"label": "mlin_metaw_scirep",   "doi": "",
                    "title": "MLIN MetaWeight continuous-scale super-resolution Scientific Reports", "direct": []},

    # ---- 机构仓库 / DOAJ 系 ----
    "s3esrgan":    {"label": "s3esrgan_utwente",    "doi": "",
                    "title": "S3-ESRGAN Sentinel-2 UAV super-resolution University of Twente",
                    "direct": ["https://research.utwente.nl/en/publications/ce847b6d-4fbc-4e27-9a90-11cd7658afa8"]},
    "diffbsr":     {"label": "diffbsr_doaj",        "doi": "",
                    "title": "DiffBSR diffusion blind super-resolution",
                    "direct": ["https://doaj.org/article/b98e0f0f1167469299cbc9cac67c9755"]},
    "plan":        {"label": "plan_doaj",           "doi": "",
                    "title": "PLAN Parallel Lattice Attention Network super-resolution", "direct": []},

    # ---- 中文期刊（知网，基本取不到）----
    "localspace":  {"label": "localstatespace_jig", "doi": "",
                    "title": "中国图象图形学报 LocalStateSpace", "direct": []},
    "jnun":        {"label": "jnun_ca_nwu",         "doi": "",
                    "title": "西北大学学报 JNUN-CA", "direct": []},

    # ---- 其他期刊 ----
    "dbtsr":       {"label": "dbtsr_eswa",          "doi": "",
                    "title": "DBTSR dual-branch transformer super-resolution Expert Systems with Applications", "direct": []},
    "ordiff":      {"label": "ordiffsr_eswa",       "doi": "",
                    "title": "ORDiffSR ocean remote sensing diffusion super-resolution", "direct": []},
    "udamsr_mean": {"label": "udamsr_mean_crop",    "doi": "",
                    "title": "UDAMSR mean crop sensing", "direct": []},
    "plgmamba":    {"label": "plgmamba_hsi",        "doi": "",
                    "title": "PLGMamba hyperspectral super-resolution", "direct": []},
    "hsisrkan":    {"label": "hsisr_kan",           "doi": "",
                    "title": "HSISR-KAN hyperspectral super-resolution KAN", "direct": []},
    "ntire_esr":   {"label": "ntire2026_esr",       "doi": "",
                    "title": "NTIRE 2026 ESR efficient super-resolution challenge",
                    "direct": ["https://www.codabench.org/competitions/13553/"]},
    "text_rsir":   {"label": "text_rsir",           "doi": "", "title": "Text-RSIR", "direct": []},
}


def get(url, timeout=60, maxbytes=60_000_000):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(maxbytes), r.headers.get("Content-Type", "")


def get_retry(url, timeout=60, maxbytes=60_000_000, tries=4, base=6):
    """带 429 退避的重试（Semantic Scholar 无 key 时限流很紧）。"""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(maxbytes), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                time.sleep(base * (i + 1))
                continue
            raise
        except Exception as e:
            last = e
            time.sleep(base)
    raise last


def s2_lookup(doi=None, title=None):
    """返回 (openAccessPdfUrl, isOA, resolvedTitle, externalIds, status)"""
    try:
        if doi:
            q = f"DOI:{urllib.parse.quote(doi)}"
        else:
            q = f"title:{urllib.parse.quote(title)}"
        u = (f"https://api.semanticscholar.org/graph/v1/paper/{q}"
             f"?fields=title,openAccessPdf,isOpenAccess,externalIds,venue,year")
        raw, _ = get_retry(u, timeout=30)
        j = json.loads(raw)
        oa = j.get("openAccessPdf") or {}
        return oa.get("url"), j.get("isOpenAccess"), j.get("title", ""), j.get("externalIds", {}), "ok"
    except urllib.error.HTTPError as e:
        return None, None, f"<s2 HTTP {e.code}>", {}, f"http{e.code}"
    except Exception as e:
        return None, None, f"<s2 fail: {type(e).__name__}>", {}, type(e).__name__


def s2_search(title):
    """标题搜索，取第一条。"""
    try:
        u = ("https://api.semanticscholar.org/graph/v1/paper/search"
             f"?query={urllib.parse.quote(title)}&limit=1"
             "&fields=title,openAccessPdf,isOpenAccess,externalIds,venue,year")
        raw, _ = get_retry(u, timeout=30)
        j = json.loads(raw)
        data = j.get("data") or []
        if not data:
            return None, None, "", {}, "empty"
        d = data[0]
        oa = d.get("openAccessPdf") or {}
        return oa.get("url"), d.get("isOpenAccess"), d.get("title", ""), d.get("externalIds", {}), "ok"
    except urllib.error.HTTPError as e:
        return None, None, "", {}, f"http{e.code}"
    except Exception as e:
        return None, None, "", {}, type(e).__name__


def try_pdf(url, dest):
    try:
        raw, ct = get(url)
        if raw[:5] == b"%PDF-":
            open(dest, "wb").write(raw)
            return True, len(raw), "pdf"
        # HTML 也可能有全文（如 MDPI html / Nature html）
        if b"<html" in raw[:3000].lower() or b"<!doctype" in raw[:3000].lower():
            open(dest.replace(".pdf", ".html"), "wb").write(raw)
            return True, len(raw), "html"
        return False, len(raw), ct
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {str(e)[:70]}"


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    status = {}
    for key, meta in TARGETS.items():
        if only and key != only:
            continue
        label = meta["label"]
        print("=" * 90)
        print(f"[{key}] {label}")
        rec = {"label": label, "venue": "", "doi": meta.get("doi", ""),
               "ok": False, "kind": None, "path": None, "note": ""}

        s2url = isOA = None
        rtitle = extids = None
        s2st = ""
        # 1) S2 by DOI
        if meta.get("doi"):
            s2url, isOA, rtitle, extids, s2st = s2_lookup(doi=meta["doi"])
            time.sleep(3.0)          # S2 无 key 限流紧，逐次间隔
        # 2) S2 by title search
        if not s2url:
            s2url, isOA, rtitle, extids, s2st = s2_search(meta["title"])
            time.sleep(3.0)
        print(f"  [S2] status={s2st}  title={(rtitle or '')[:70]}")
        print(f"  [S2] isOA={isOA}  pdf={s2url}")
        rec["s2_status"] = s2st
        if extids:
            rec["doi"] = rec["doi"] or extids.get("DOI", "")
            rec["arxiv"] = extids.get("ArXiv", "")
        rec["s2_pdf"] = s2url

        got = False
        # 3) 试 S2 PDF（排除已知 403 主站前缀，仍试以留证）
        if s2url:
            dest = os.path.join(OUT, label + (".pdf" if s2url.lower().endswith(".pdf") else ".pdf"))
            ok, n, kind = try_pdf(s2url, dest)
            print(f"       -> {'OK' if ok else 'FAIL'} {n} {kind}")
            if ok:
                got = True
                rec.update(ok=True, kind=kind, path=dest)
        # 4) 试 direct 候选
        if not got:
            for u in meta.get("direct", []):
                kind_guess = ".pdf" if u.lower().endswith(".pdf") else ".html"
                dest = os.path.join(OUT, label + kind_guess)
                ok, n, kind = try_pdf(u, dest)
                print(f"  [DIR] {u[:70]} -> {'OK' if ok else 'FAIL'} {n} {kind}")
                if ok:
                    got = True
                    rec.update(ok=True, kind=kind, path=dest)
                    break
        rec["note"] = "" if got else f"S2={rec.get('s2_status','')} no OA channel"
        status[key] = rec
        time.sleep(2.0)

    json.dump(status, open(os.path.join(OUT, "_fetch_oa_batch.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n_ok = sum(1 for v in status.values() if v["ok"])
    print(f"\n==== 成功 {n_ok}/{len(status)} ====")
    for k, v in status.items():
        print(f"  {'OK  ' if v['ok'] else 'FAIL'} {k:14s} {v['label']:24s} "
              f"{'doi=' + v['doi'] if v['doi'] else ''}")


if __name__ == "__main__":
    main()
