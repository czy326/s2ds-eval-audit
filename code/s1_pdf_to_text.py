#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0-S1 / Step 7c: 把已抓取的 PDF 转成 txt，并抽取 R2/R3/R5 证据行。

用于 MDPI 等非 arXiv 来源（Step 7b 产物）。
"""
import os, sys, io, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FT = os.path.join(OUT_DIR, "fulltext")

try:
    import pypdf
except ImportError:
    print("需要 pypdf：请用 envs/default 里的 python 运行")
    sys.exit(1)

PAT = re.compile(
    r"(random seeds?|fixed seed|seed of|three (independent )?runs|five runs|"
    r"averaged? over|per-image|per image|standard deviation|std\.?|"
    r"confidence interval|significan|Wilcoxon|p-value|p ?< ?0\.|bootstrap|"
    r"median|interquartile|trimmed|"
    r"train(ing)?[- ]?(/|and|&)?\s*(validation|val)?[- ]?(/|and|&)?\s*test|"
    r"test set (of|contains|comprises)|split (of|into|contains)|"
    r"we (train|use|adopt|follow|report|evaluate)|"
    r"reproduc|retrain|pretrained (weights|models)|zero-shot)",
    re.I)


def pdf_to_text(pdf):
    out = pdf[:-4] + ".txt"
    try:
        r = pypdf.PdfReader(pdf)
        n = len(r.pages)
        parts = []
        for pg in r.pages:
            try:
                parts.append(pg.extract_text() or "")
            except Exception:
                parts.append("")
        txt = "\n".join(parts)
        txt = re.sub(r"[ \t]+", " ", txt)
        txt = re.sub(r"\n\s*\n\s*\n+", "\n\n", txt)
        open(out, "w", encoding="utf-8").write(txt)
        return n, len(txt)
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def main():
    pdfs = sorted(p for p in glob.glob(os.path.join(FT, "*.pdf")))
    if not pdfs:
        print("没有 PDF"); return
    for pdf in pdfs:
        n, L = pdf_to_text(pdf)
        name = os.path.basename(pdf)
        print("=" * 90)
        print(f"{name}  pages={n}  chars={L}")

    # 证据行
    print("\n" + "#" * 90)
    print("# R2/R3/R5 证据行（每篇最多 12 条）")
    print("#" * 90)
    for pdf in pdfs:
        txt_p = pdf[:-4] + ".txt"
        if not os.path.exists(txt_p):
            continue
        txt = open(txt_p, encoding="utf-8").read()
        print("\n" + "=" * 90)
        print(os.path.basename(txt_p))
        seen = set()
        cnt = 0
        for m in PAT.finditer(txt):
            s = max(0, m.start() - 130)
            e = min(len(txt), m.end() + 200)
            seg = re.sub(r"\s+", " ", txt[s:e]).strip()
            key = seg[:70]
            if key in seen:
                continue
            seen.add(key)
            # 跳过低信息片段
            if len(seg) < 80:
                continue
            print("  •", seg[:300])
            cnt += 1
            if cnt >= 12:
                break


if __name__ == "__main__":
    main()
