# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""Fetch full Crossref metadata for the two DOIs resolved by title search,
and for the remaining 'no stable identifier' cases attempt an OpenAlex title
search so we can at least record what the record is. Appends into
audit/out/_doi_meta.json (merging) so downstream reads one file.
"""
import json, io, os, sys, time, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = OUT_DIR
UA = "s2ds-eval-audit/1.0 (mailto:czy@example.edu)"


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def crossref(doi):
    d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
    auth = []
    for a in (d.get("author") or [])[:6]:
        nm = " ".join(x for x in [a.get("given"), a.get("family")] if x)
        if nm:
            auth.append(nm)
    year = ""
    for k in ("published-print", "published-online", "issued", "created"):
        if d.get(k) and d[k].get("date-parts"):
            year = str(d[k]["date-parts"][0][0])
            break
    return {
        "status": "OK", "source": "crossref", "doi": doi,
        "title": (d.get("title") or [""])[0],
        "authors": auth, "n_auth": len(d.get("author") or []),
        "container": (d.get("container-title") or [""])[0],
        "volume": d.get("volume"), "issue": d.get("issue"),
        "page": d.get("page"), "article_number": d.get("article-number"),
        "year": year, "type": d.get("type"),
    }


ADD = {
    "PLAN": "10.1109/jstars.2026.3660141",
    "NGram-MoSE": "10.1109/metroaerospace69299.2026.11646695",
}
# Sen4x: try the alternate IEEE DOI pattern from the xplorestaging id
ADD_TRY = {"Sen4x": ["10.1109/jstars.2026.11435384", "10.1109/lgrss.2026.11435384"]}

meta = json.load(open(os.path.join(AUD, "_doi_meta.json"), encoding="utf-8"))

for pid, doi in ADD.items():
    old = meta.get(pid, {})
    try:
        r = crossref(doi)
        r["prev"] = {k: old.get(k) for k in ("status", "doi", "title")}
        meta[pid] = r
        print(f"{pid:16s} OK  {r['year']} | {r['container'][:40]:40s} | {r['title'][:56]} | {r['authors'][0] if r['authors'] else '?'}")
    except Exception as e:
        print(f"{pid:16s} FAIL {e!r}")
    time.sleep(0.6)

for pid, dois in ADD_TRY.items():
    for doi in dois:
        try:
            r = crossref(doi)
            meta[pid] = r
            print(f"{pid:16s} OK  {r['year']} | {r['container'][:40]:40s} | {r['title'][:56]}")
            break
        except Exception as e:
            print(f"{pid:16s} try {doi} -> {e!r}")
        time.sleep(0.4)

json.dump(meta, open(os.path.join(AUD, "_doi_meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
ok = sum(1 for v in meta.values() if v.get("status") == "OK")
print(f"\nwrote _doi_meta.json : {ok}/{len(meta)} resolvable")
for pid, v in meta.items():
    if v.get("status") != "OK":
        print("  UNRESOLVED", pid, v.get("status"), v.get("doi"))
