# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
Fill title/authors for every DOI we already hold, via Crossref
(api.crossref.org/works/<doi>) and OpenAlex as fallback.
Writes audit/out/_doi_meta.json . No fabrication: only what the APIs return.
"""
import json, io, os, sys, time, urllib.request, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = OUT_DIR
UA = "s2ds-eval-audit/1.0 (mailto:czy@example.edu)"

DOIS = {
    "DBTSR": "10.1016/j.eswa.2025.129424",
    "ORDiffSR": "10.1016/j.eswa.2026.132254",
    "DFSMamba": "10.3390/rs18121910",
    "MT-Hybrid": "10.1109/tgrs.2026.3651693",
    "LocalStateSpace": None,
    "JNUN-CA": None,
    "MLIN-MetaWeight": "10.1038/s41598-026-36632-w",
    "Sen4x": "10.1109/jstars.2026.11435384",
    "S3-ESRGAN": "10.1109/icmlc66258.2025.11280263",
    "GrasslandGAN": "10.3390/rs18091419",
    "HAC-MoE": "10.1016/j.neucom.2026.133615",
    "BKX-HMM": "10.1109/tpami.2026.3681688",
    "VolumeNet+TT": "10.1145/3785443.3785445",
    "SpectralSR-Bench": "10.3390/s26020683",
    "SDGAN-SciRep": "10.1038/s41598-026-41832-5",
    "UDAMSR": "10.1016/j.eng.2026.02.005",
    "PLAN": "10.1109/tgrs.2026.3612345",
}


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


out = {}
for pid, doi in DOIS.items():
    if not doi:
        out[pid] = {"status": "NO_DOI", "doi": None}
        print(f"{pid:22s} NO_DOI")
        continue
    # ---- Crossref
    rec = {"status": "MISS", "doi": doi, "source": None}
    try:
        d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
        m = d["message"]
        auth = []
        for a in (m.get("author") or [])[:6]:
            nm = " ".join(x for x in [a.get("given"), a.get("family")] if x)
            if nm:
                auth.append(nm)
        year = None
        for k in ("published-print", "published-online", "issued", "created"):
            if m.get(k) and m[k].get("date-parts"):
                year = str(m[k]["date-parts"][0][0])
                break
        rec = {
            "status": "OK", "source": "crossref", "doi": doi,
            "title": (m.get("title") or [""])[0],
            "authors": auth, "n_auth": m.get("author-count", {}).get("value") if isinstance(m.get("author-count"), dict) else len(m.get("author") or []),
            "container": (m.get("container-title") or [""])[0],
            "short_container": (m.get("short-container-title") or [""])[0] if m.get("short-container-title") else "",
            "volume": m.get("volume"), "issue": m.get("issue"), "page": m.get("page"),
            "article_number": m.get("article-number"),
            "year": year, "type": m.get("type"),
        }
    except Exception as e:
        rec["crossref_error"] = repr(e)[:160]
    # ---- OpenAlex fallback / cross-check
    if rec["status"] != "OK":
        try:
            d = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) + "?mailto=czy@example.edu")
            auth = [a["author"]["display_name"] for a in (d.get("authorships") or [])[:6]]
            rec = {
                "status": "OK", "source": "openalex", "doi": doi,
                "title": d.get("title") or (d.get("primary_location") or {}).get("source", {}).get("display_name"),
                "authors": auth, "n_auth": len(d.get("authorships") or []),
                "container": ((d.get("primary_location") or {}).get("source") or {}).get("display_name"),
                "volume": (d.get("biblio") or {}).get("volume"),
                "issue": (d.get("biblio") or {}).get("issue"),
                "page": "-".join(str(x) for x in [(d.get("biblio") or {}).get("first_page"), (d.get("biblio") or {}).get("last_page")] if x),
                "year": str(d.get("publication_year")), "type": d.get("type"),
            }
        except Exception as e:
            rec["openalex_error"] = repr(e)[:160]
    out[pid] = rec
    if rec["status"] == "OK":
        a = (rec.get("authors") or ["?"])[0]
        print(f"{pid:22s} OK/{rec['source']:8s} {rec.get('year')} | {rec.get('container','')[:38]:38s} | {rec.get('title','')[:58]} | {a}")
    else:
        print(f"{pid:22s} FAIL {rec.get('crossref_error') or rec.get('openalex_error') or rec.get('status')}")
    time.sleep(0.6)

json.dump(out, open(os.path.join(AUD, "_doi_meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nwrote", os.path.join(AUD, "_doi_meta.json"))
