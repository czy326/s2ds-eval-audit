# -*- coding: utf-8 -*-
"""Resolve candidate references against Crossref and print the verified metadata."""
import io, json, sys, time, urllib.parse, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CANDIDATES = [
    ("AID dataset", "AID: A Benchmark Data Set for Performance Evaluation of Aerial Scene Classification"),
    ("RSSCN7", "Deep Learning Based Feature Selection for Remote Sensing Scene Classification"),
    ("UCMerced", "Geographic Image Retrieval Using Local Invariant Features"),
    ("WHU-RS19", "Structural High-resolution Satellite Image Indexing"),
    ("EDSR", "Enhanced Deep Residual Networks for Single Image Super-Resolution"),
    ("RCAN", "Image Super-Resolution Using Very Deep Residual Channel Attention Networks"),
    ("SwinIR", "SwinIR: Image Restoration Using Swin Transformer"),
    ("SRCNN", "Image Super-Resolution Using Deep Convolutional Networks"),
    ("Bouthillier variance", "Accounting for Variance in Machine Learning Benchmarks"),
    ("Reimers score distributions", "Reporting Score Distributions Makes a Difference: Performance Study of LSTM-networks for Sequence Tagging"),
    ("Blau perception-distortion", "The Perception-Distortion Tradeoff"),
    ("SSIM", "Image quality assessment: from error visibility to structural similarity"),
]

UA = {"User-Agent": "s2ds-audit/1.0 (mailto:18392366572@163.com)"}


def query(q):
    url = ("https://api.crossref.org/works?rows=3&select=DOI,title,container-title,"
           "issued,volume,issue,page,author,type&query.bibliographic="
           + urllib.parse.quote(q))
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=45))["message"]["items"]
        except Exception as e:
            if attempt == 2:
                return [{"error": str(e)}]
            time.sleep(2)


def fmt(it):
    if "error" in it:
        return "ERROR " + it["error"][:70]
    au = it.get("author", [])
    names = []
    for a in au[:3]:
        fam = a.get("family", "")
        giv = a.get("given", "")
        ini = " ".join(p[0] + "." for p in giv.replace("-", " ").split() if p)
        names.append("%s %s" % (fam, ini))
    if len(au) > 3:
        names.append("et al.")
    yr = it.get("issued", {}).get("date-parts", [[None]])[0][0]
    return "%s | %s | %s %s %s | %s" % (
        (it.get("title") or [""])[0][:95], it.get("DOI"),
        (it.get("container-title") or [""])[0][:38],
        it.get("volume", ""), (it.get("page") or ""),
        ", ".join(names)[:80]) + " | %s" % yr


for label, q in CANDIDATES:
    print("=== %s" % label)
    items = query(q)
    for k, it in enumerate(items[:2]):
        print("   [%d] %s" % (k, fmt(it)))
    print()
