# -*- coding: utf-8 -*-
"""
Package the LaTeX source for the IJRS submission and verify it from the archive.

The archive is unpacked into a temporary directory and both manuscripts are
compiled there, so a broken relative path or a missing class file is caught here
rather than by the typesetter. Nothing that carries a local path, a build
artifact or an access token is admitted.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get("S2DS_AUDIT_ROOT") or os.path.dirname(_HERE)
OUT = os.environ.get("S2DS_OUT") or os.path.join(os.path.dirname(_ROOT), "out")
if not os.path.exists(os.path.join(OUT, "P0S1_IJRS_v1.tex")):
    OUT = os.path.join(_ROOT, "papers")

ZIP = os.path.join(OUT, "P0S1_IJRS_LaTeX.zip")
TOP = "P0S1_IJRS_LaTeX"
PDFLATEX = r"B:/tax/miktex/bin/x64/pdflatex.exe"

FILES = [
    ("P0S1_IJRS_v1.tex", None),
    ("P0S1_IJRS_v1_PN.tex", None),
    ("ijrs/interact.cls", "interact.cls"),
    ("figures/fig1_noise_vs_testsize.pdf", "figures/fig1_noise_vs_testsize.pdf"),
    ("figures/fig2_effect_vs_noise.pdf", "figures/fig2_effect_vs_noise.pdf"),
]

README = """LaTeX source for the submission to the International Journal of Remote Sensing

P0S1_IJRS_v1.tex      manuscript with the title page (authors, affiliations, contact)
P0S1_IJRS_v1_PN.tex   anonymised main document for single-anonymous review
interact.cls          Taylor & Francis Interact document class, v1.05, unmodified
figures/              vector figures included by both manuscripts

Both files are self-contained and compile with pdflatex, twice, from this
directory. They share interact.cls and the figures folder, so keep the layout
as unpacked.

Compile:  pdflatex P0S1_IJRS_v1.tex   (run twice for cross-references)
          pdflatex P0S1_IJRS_v1_PN.tex
"""

FORBIDDEN = [r"E:[\\/]", r"C:[\\/]Users", r"ghp_[A-Za-z0-9]{20,}",
             r"陈正洋", r"AppData"]


def build():
    if os.path.exists(ZIP):
        os.remove(ZIP)
    missing = []
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in FILES:
            p = os.path.join(OUT, src)
            if not os.path.exists(p):
                missing.append(src)
                continue
            z.write(p, "%s/%s" % (TOP, arc or src))
        z.writestr("%s/README.txt" % TOP, README)
    if missing:
        raise SystemExit("missing sources: %s" % missing)
    return ZIP


def verify():
    tmp = tempfile.mkdtemp(prefix="ijrs_pack_")
    try:
        with zipfile.ZipFile(ZIP) as z:
            names = z.namelist()
            z.extractall(tmp)
        base = os.path.join(tmp, TOP)

        print("archive entries: %d" % len(names))
        for n in sorted(names):
            print("   ", n)

        # nothing that leaks a local path or a credential
        leaks = []
        for n in names:
            if not n.endswith((".tex", ".cls", ".txt")):
                continue
            t = open(os.path.join(tmp, n), encoding="utf-8", errors="ignore").read()
            for pat in FORBIDDEN:
                for m in re.finditer(pat, t):
                    leaks.append((n, m.group(0)[:24]))
        print("\nlocal paths or tokens:", leaks or "none")

        # both manuscripts must build from the unpacked archive
        for tex in ("P0S1_IJRS_v1.tex", "P0S1_IJRS_v1_PN.tex"):
            for _ in range(2):
                r = subprocess.run([PDFLATEX, "-interaction=nonstopmode", tex],
                                   cwd=base, capture_output=True, text=True,
                                   errors="ignore")
            log = open(os.path.join(base, tex.replace(".tex", ".log")),
                       encoding="utf-8", errors="ignore").read()
            pages = re.search(r"Output written on .*?\((\d+) pages?", log)
            undef = log.count("undefined")
            errs = len(re.findall(r"(?m)^!", log))
            print("%-22s pages=%s errors=%d undefined=%d"
                  % (tex, pages.group(1) if pages else "?",
                     errs, undef))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    build()
    print("wrote %s (%.1f KB)" % (ZIP, os.path.getsize(ZIP) / 1024.0))
    print()
    verify()


if __name__ == "__main__":
    main()
