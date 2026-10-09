#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1 / Step 7b: 抓取非 arXiv 论文全文（MDPI / 开放获取）。

为什么需要单独一条：
  本机代理出口被 www.mdpi.com 硬 403（所有路径皆然）。但 **MDPI 的静态资源 CDN
  `mdpi-res.com` 未被拦**，可直接拉到 article_deploy PDF。
  另用 **Semantic Scholar Graph API**（未被拦）解析 DOI → openAccessPdf 链接，
  可覆盖部分 Elsevier/Springer/IEEE 的 OA 版本（若能拿到）。

策略（按优先级）:
  1) Semantic Scholar 查 DOI → openAccessPdf.url（最通用）
  2) MDPI CDN 直链（对 MDPI 系最稳）
  3) 落盘后交给 PDF 解析

用法:
  python s1_fetch_nonarxiv.py                 # 抓 TARGETS 全部
  python s1_fetch_nonarxiv.py 10.3390/rs18091419
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

# DOI -> (标签, MDPI CDN 相对路径候选)
TARGETS = {
    "10.3390/rs18091419": {           # GrasslandGAN
        "label": "grassland_gan_rs18_1419",
        "mdpi_pdf": ["https://mdpi-res.com/d_attachment/remotesensing/remotesensing-18-01419/"
                     "article_deploy/remotesensing-18-01419.pdf"],
    },
    "10.3390/rs18121910": {           # DFSMamba
        "label": "dfsmamba_rs18_1910",
        "mdpi_pdf": ["https://mdpi-res.com/d_attachment/remotesensing/remotesensing-18-01910/"
                     "article_deploy/remotesensing-18-01910.pdf"],
    },
    "10.3390/s26020683": {            # SpectralSR-Bench
        "label": "spectral_sr_bench_s26_683",
        "mdpi_pdf": ["https://mdpi-res.com/d_attachment/sensors/sensors-26-00683/"
                     "article_deploy/sensors-26-00683.pdf"],
    },
}


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def s2_open_pdf(doi):
    """用 Semantic Scholar 解析 OA PDF 链接。"""
    try:
        u = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(doi)}"
             f"?fields=title,openAccessPdf,externalIds")
        raw, _ = get(u, timeout=30)
        j = json.loads(raw)
        return j.get("openAccessPdf", {}).get("url"), j.get("title", "")
    except Exception as e:
        return None, f"<s2 fail: {type(e).__name__}>"


def try_pdf(url, dest):
    try:
        raw, ct = get(url)
        if raw[:5] == b"%PDF-" or len(raw) > 200_000:
            open(dest, "wb").write(raw)
            return True, len(raw), "application/pdf" if raw[:5] == b"%PDF-" else ct
        return False, len(raw), ct
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {str(e)[:60]}"


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    status = {}
    for doi, meta in TARGETS.items():
        if only and doi != only:
            continue
        label = meta["label"]
        dest = os.path.join(OUT, f"{label}.pdf")
        print("=" * 84)
        print(f"DOI {doi}  ->  {label}")

        got = False
        # 1) Semantic Scholar OA
        s2url, title = s2_open_pdf(doi)
        print(f"  [S2] title={title[:60] if title else 'n/a'}")
        print(f"  [S2] openAccessPdf={s2url}")
        if s2url:
            ok, n, ct = try_pdf(s2url, dest)
            print(f"       -> {'OK' if ok else 'FAIL'} {n} bytes {ct}")
            got = ok

        # 2) MDPI CDN
        if not got:
            for u in meta.get("mdpi_pdf", []):
                ok, n, ct = try_pdf(u, dest)
                print(f"  [CDN] {u.split('/')[-1]:40s} -> {'OK' if ok else 'FAIL'} {n} {ct}")
                if ok:
                    got = True
                    break

        status[doi] = {"label": label, "ok": got,
                       "pdf": dest if got else None, "s2_url": s2url}
        time.sleep(1)

    json.dump(status, open(os.path.join(OUT, "_fetch_nonarxiv.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n_ok = sum(1 for v in status.values() if v["ok"])
    print(f"\n成功 {n_ok}/{len(status)}")
    for v in status.values():
        print(f"  {'OK ' if v['ok'] else 'FAIL'} {v['label']}")


if __name__ == "__main__":
    main()
