# -*- coding: utf-8 -*-
"""
Rebuild the raw runs/ tree so the repo is self-contained and the manifest script
can regenerate data/perimage/ from scratch.

Input : data/perimage/*.json  (derived form, {meta:{rel,...}, images:[{path,metrics}]})
Output: data/runs/<rel dir>/test_per_image.jsonl   (raw jsonl form)

The reverse mapping is exact: `rel` in the meta names the original jsonl path.
This is what makes the repo re-runnable without shipping the training pipeline.
"""
import json, os, io, sys, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.environ.get("S2DS_REPO",
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PI = os.path.join(REPO, "data", "perimage")
RUNS = os.path.join(REPO, "data", "runs")

n = 0
for f in sorted(glob.glob(os.path.join(PI, "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    meta = d.get("meta", {})
    imgs = d.get("images", [])
    rel = meta.get("rel")
    if not rel:
        # fall back to filename convention: <group>__<run>__test_per_image.jsonl.json
        base = os.path.basename(f).replace("__test_per_image.jsonl.json", "")
        group, _, run = base.partition("__")
        rel = f"{group}/{run}/test_per_image.jsonl"
    rel = rel.replace("\\", "/")
    dest = os.path.join(RUNS, *rel.split("/"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        for r in imgs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    n += 1

print(f"rebuilt {n} raw jsonl files under {RUNS}")
# sanity: how many dirs
import collections
c = collections.Counter()
for root, _, files in os.walk(RUNS):
    for x in files:
        c[x] += 1
print(dict(c))
