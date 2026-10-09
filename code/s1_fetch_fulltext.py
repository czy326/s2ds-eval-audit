#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1 / Step 7: 批量抓取 arXiv 全文 HTML，供逐篇核 R2/R3/R5。

为什么不直接用 WebFetch:
  本机 arXiv html 通道断续（常返回空）。改用托管 Python urllib，
  它自动吃 http_proxy/https_proxy 环境变量，落盘后再本地解析，稳定可复核。

用法:
  python s1_fetch_fulltext.py            # 抓全部
  python s1_fetch_fulltext.py 2606.08535 # 抓单篇
"""
import os, re, sys, io, json, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = os.path.join(OUT_DIR, "fulltext")
os.makedirs(OUT, exist_ok=True)

# arXiv ID -> 期望的版本后缀（有的必须带 vN 才出 HTML）
TARGETS = {
    "2606.08535": "v1",   # NGram-MoSE  ✅已成功取过一次
    "2607.22380": "v2",   # IR275K
    "2609.07012": "v1",   # AstraMoE-SR
    "2605.09687": "v1",   # SFG-SwinSR
    "2605.00310": "v1",   # GeoSR-Bench
    "2604.14558": "v1",   # NTIRE2026-SR
    "2604.21801": "v1",   # SyMTRS
    "2604.21312": "v1",   # NTIRE2026-IR
    "2605.02198": "v1",   # SlimDiffSR
    "2605.15558": "v1",   # Text-RSIR
    "2605.17980": "v1",   # DS-DiT
    "2610.06196": "v1",   # EORestore-Agent
    "2512.11524": "v3",   # THREASURE-Net
}


def fetch(arxiv_id, ver, retries=3):
    urls = [
        f"https://arxiv.org/html/{arxiv_id}{ver}",
        f"https://arxiv.org/html/{arxiv_id}",
    ]
    dest = os.path.join(OUT, f"{arxiv_id}.html")
    for attempt in range(retries):
        for u in urls:
            try:
                req = urllib.request.Request(u, headers={
                    "User-Agent": "Mozilla/5.0 (research; fulltext audit)"})
                with urllib.request.urlopen(req, timeout=45) as r:
                    data = r.read()
                if len(data) > 20000:      # 太短的通常是没有正文的占位页
                    with open(dest, "wb") as fh:
                        fh.write(data)
                    return True, len(data), u
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
        time.sleep(2)
    return False, 0, locals().get("last", "n/a")


def to_text(arxiv_id):
    """把落盘 HTML 粗剥成纯文本（去掉标签/脚本），便于后续 Grep。"""
    src = os.path.join(OUT, f"{arxiv_id}.html")
    dst = os.path.join(OUT, f"{arxiv_id}.txt")
    if not os.path.exists(src):
        return 0
    raw = open(src, "rb").read().decode("utf-8", "ignore")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    txt = re.sub(r"(?s)<[^>]+>", " ", raw)
    txt = re.sub(r"&nbsp;?", " ", txt)
    txt = re.sub(r"&amp;", "&", txt)
    txt = re.sub(r"&lt;", "<", txt)
    txt = re.sub(r"&gt;", ">", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n\s*\n+", "\n\n", txt)
    open(dst, "w", encoding="utf-8").write(txt)
    return len(txt)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ok_list, fail_list = [], []
    for aid, ver in TARGETS.items():
        if only and aid != only:
            continue
        good, n, used = fetch(aid, ver)
        if good:
            t = to_text(aid)
            ok_list.append((aid, n, t, used))
            print(f"[OK]   {aid:12s} html={n:>8d}  txt={t:>8d}  {used}")
        else:
            fail_list.append((aid, used))
            print(f"[FAIL] {aid:12s} {used}")
    print(f"\n成功 {len(ok_list)} / 失败 {len(fail_list)}")
    if fail_list:
        print("失败清单:", [a for a, _ in fail_list])
    json.dump({"ok": [a for a, _, _, _ in ok_list],
               "fail": [a for a, _ in fail_list]},
              open(os.path.join(OUT, "_fetch_status.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
