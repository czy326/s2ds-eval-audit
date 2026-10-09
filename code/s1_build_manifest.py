#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 Audit / Step 1: 建立 run manifest —— 把 170 个 test_per_image.jsonl 收拢成一张可审计的表。

只读，不改任何原文件。输出:
  out/manifest.json      每个 run 的元信息 + 逐图记录
  out/manifest_summary.csv  便于人工浏览的摘要

审计维度（每一条后面都要有"可复现性"含义）:
  - dataset / model_family / seed / variant
  - n_images（逐图产物行数）与官方 split 的 test 大小是否一致
  - path 集合是否与同类 run 完全一致（同一测试集是否真的用了同一批图）
  - 指标字段完整性（psnr/ssim/ergas/sam/lpips 是否有 NaN / 缺失）
"""
import json, os, glob, csv, re, sys, io
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = DATA_ROOT
OUT = OUT_DIR
os.makedirs(OUT, exist_ok=True)

_raw_splits = json.load(open(os.path.join(ROOT, "splits.json"), encoding="utf-8"))


def _split_size(entry):
    """splits.json 的 value 可能是 list（真实路径列表）或 int（计数）。统一取计数。"""
    if entry is None:
        return None
    if isinstance(entry, int):
        return entry
    if isinstance(entry, (list, tuple)):
        return len(entry)
    if isinstance(entry, dict):  # 兜底：嵌套 {split: [...]}
        tot = 0
        for v in entry.values():
            tot += _split_size(v) or 0
        return tot or None
    return None


SPLITS = {k: {kk: _split_size(vv) for kk, vv in v.items()} for k, v in _raw_splits.items()}
# 数据集名归一化：从 run 路径里出现的 token 判断
DS_TOKENS = {
    "aid": "AID",
    "rsscn7": "RSSCN7",
    "ucmerced": "UCMerced_LandUse",
    "whurs19": "WHU-RS19",
    "s2ds": "S2DS",
}
METRICS = ["psnr", "ssim", "ergas", "sam", "lpips"]


def parse_run_name(rel):
    """从相对路径推断 dataset / seed / variant。"""
    parts = rel.replace("\\", "/").split("/")
    run_name = parts[-2] if len(parts) >= 2 else parts[0]
    group = parts[0]
    low = run_name.lower()

    ds = None
    for tok, canon in DS_TOKENS.items():
        if tok in low:
            ds = canon
            break

    m = re.search(r"s(20\d\d)", low)
    seed = int(m.group(1)) if m else None
    return group, run_name, ds, seed


def main():
    paths = sorted(glob.glob(os.path.join(ROOT, "runs", "**", "test_per_image.jsonl"),
                             recursive=True))
    records = []
    for p in paths:
        rel = os.path.relpath(p, os.path.join(ROOT, "runs"))
        group, run_name, ds, seed = parse_run_name(rel)
        per_img = []
        n_bad = 0
        with open(p, encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    n_bad += 1
                    continue
                per_img.append({
                    "path": d.get("path"),
                    **{k: d.get(k) for k in METRICS},
                })
        n = len(per_img)
        n_nan = sum(1 for r in per_img if r.get("psnr") is None)
        ds_test_size = SPLITS.get(ds, {}).get("test") if ds in SPLITS else None
        records.append({
            "rel": rel.replace("\\", "/"),
            "group": group,
            "run_name": run_name,
            "dataset": ds,
            "seed": seed,
            "n_images": n,
            "n_bad_lines": n_bad,
            "n_nan_psnr": n_nan,
            "split_test_size": ds_test_size,
            "size_match": (n == ds_test_size) if ds_test_size else None,
            "first_3_paths": [r["path"] for r in per_img[:3]],
            "mean_psnr": (sum(r["psnr"] for r in per_img if r["psnr"] is not None) / n) if n else None,
        })
        # 落盘逐图记录供后续配对统计
        with open(os.path.join(OUT, "perimage", rel.replace("\\", "__") + ".json"),
                  "w", encoding="utf-8") as fh:
            json.dump({"meta": records[-1], "images": per_img}, fh, ensure_ascii=False)

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=1)

    with open(os.path.join(OUT, "manifest_summary.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["rel", "group", "run_name", "dataset", "seed",
                                           "n_images", "split_test_size", "size_match",
                                           "n_nan_psnr", "n_bad_lines", "mean_psnr"])
        w.writeheader()
        for r in records:
            w.writerow({k: r[k] for k in w.fieldnames})

    print("total runs:", len(records))
    print("by dataset:", dict(Counter(r["dataset"] for r in records)))
    print("size_match True/False/None:",
          dict(Counter(str(r["size_match"]) for r in records)))
    print("n_nan_psnr > 0:", sum(1 for r in records if r["n_nan_psnr"]))
    print("n_bad_lines > 0:", sum(1 for r in records if r["n_bad_lines"]))


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "perimage"), exist_ok=True)
    main()
