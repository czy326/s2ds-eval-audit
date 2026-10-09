# -*- coding: utf-8 -*-
DATA_RUNS = _os.environ.get("S2DS_RUNS_ROOT", _os.path.join(DATA_ROOT, "runs"))
import os as _os

import json, glob, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def m(xs):
    return sum(xs) / len(xs)

print("=== base_ssm_aid (主线基线) ===")
for s in [2026, 2027, 2028]:
    p = os.path.join(r"data/runs\main", f"base_ssm_aid_s{s}", "test_per_image.jsonl")
    if os.path.exists(p):
        ps = [json.loads(l)["psnr"] for l in open(p, encoding="utf-8") if l.strip()]
        print(f"  base_ssm_aid_s{s}: n={len(ps)} meanPSNR={m(ps):.4f}")

print("\n=== 所有含 edge_deep_fuse 的 run ===")
for p in glob.glob(os.path.join(DATA_RUNS, "**", "test_per_image.jsonl"), recursive=True):
    rel = os.path.relpath(p, DATA_RUNS)
    if "edge_deep_fuse" in rel or "stage2" in rel:
        ps = [json.loads(l)["psnr"] for l in open(p, encoding="utf-8") if l.strip()]
        print(f"  {rel}: n={len(ps)} meanPSNR={m(ps):.4f}")

print("\n=== AID 上所有 run 的 meanPSNR 排序 ===")
rows = []
for p in glob.glob(os.path.join(DATA_RUNS, "**", "test_per_image.jsonl"), recursive=True):
    rel = os.path.relpath(p, DATA_RUNS)
    if "aid" in rel.lower():
        ps = [json.loads(l)["psnr"] for l in open(p, encoding="utf-8") if l.strip()]
        rows.append((m(ps), rel, len(ps)))
for v, rel, n in sorted(rows, reverse=True):
    print(f"  {v:.4f}  n={n:4d}  {rel}")
