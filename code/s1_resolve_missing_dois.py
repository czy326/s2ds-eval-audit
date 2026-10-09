# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
Resolve the two unresolved survey DOIs by title search, not by guessing.
 - PLAN : our pool recorded a bogus DOI. Search Crossref/OpenAlex by the exact
          title string to obtain the real DOI.
 - Sen4x: Crossref 404 on 10.1109/jstars.2026.11435384. Search by title.
Also search the two CNKI papers (作者/期刊, 无 DOI) - expected to stay unresolved,
which is itself a documented finding.
Writes audit/out/_doi_meta_extra.json
"""
import json, io, os, sys, time, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = OUT_DIR
UA = "s2ds-eval-audit/1.0 (mailto:czy@example.edu)"


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


QUERIES = {
    "PLAN": "Parallel Lattice Attention Network remote sensing super-resolution",
    "Sen4x": "Sen4x remote sensing super-resolution JSTARS",
    "NGram-MoSE": "NGram-MoSE N-Gram context mixture of experts remote sensing super-resolution",
}

out = {}
for pid, q in QUERIES.items():
    recs = []
    try:
        d = get("https://api.crossref.org/works?rows=5&query.bibliographic=" + urllib.parse.quote(q))
        for it in d["message"]["items"]:
            auth = []
            for a in (it.get("author") or [])[:4]:
                nm = " ".join(x for x in [a.get("given"), a.get("family")] if x)
                if nm:
                    auth.append(nm)
            yr = ""
            for k in ("published-print", "published-online", "issued", "created"):
                if it.get(k) and it[k].get("date-parts"):
                    yr = str(it[k]["date-parts"][0][0])
                    break
            recs.append({"doi": it.get("DOI"), "title": (it.get("title") or [""])[0],
                         "container": (it.get("container-title") or [""])[0],
                         "authors": auth, "year": yr})
    except Exception as e:
        recs.append({"error": repr(e)[:120]})
    out[pid] = {"query": q, "crossref_top5": recs}
    print("==", pid)
    for r in recs:
        print("   ", r.get("doi"), "|", r.get("year"), "|", str(r.get("container"))[:34], "|", str(r.get("title"))[:64])
    time.sleep(0.6)

json.dump(out, open(os.path.join(AUD, "_doi_meta_extra.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nwrote", os.path.join(AUD, "_doi_meta_extra.json"))
