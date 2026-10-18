# -*- coding: utf-8 -*-
"""
Produce the anonymised main document that IJRS requires alongside the title
page, from the full manuscript.

Removed or replaced, because each one identifies the authors:
  * the author block (names, ORCID, e-mail, affiliations)
  * Acknowledgements, Funding and Author contributions: they name people and a
    grant, and the submission system collects both separately
  * the repository URL in the data availability statement, which carries the
    account name

Every substitution is asserted, so a change to the full manuscript cannot leave
an identifying string behind silently.
"""
import os
import re
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get("S2DS_AUDIT_ROOT") or os.path.dirname(_HERE)
_CANDS = [os.environ.get("S2DS_OUT"), os.path.join(_ROOT, "papers"),
          os.path.join(os.path.dirname(_ROOT), "out")]
OUT = next((c for c in _CANDS
            if c and os.path.exists(os.path.join(c, "P0S1_IJRS_v1.tex"))),
           _CANDS[-1])

SRC = os.path.join(OUT, "P0S1_IJRS_v1.tex")
DST = os.path.join(OUT, "P0S1_IJRS_v1_PN.tex")

ANON_AUTHOR = r"""\author{}"""
ANON_AVAIL = ("The data that support the findings of this study are available "
              "from the corresponding author upon reasonable request.")

DROP_SECTIONS = ["Acknowledgements", "Funding", "Author contributions"]
IDENTIFYING = ["Zhengyang", "Dawei", "Zhiheng", "Engineering University",
               "Earth Environment", "Chinese Academy", "wjmicheal",
               "18392366572", "1250368357", "liuzhiheng", "0009-0003", "42502302",
               "czy326", "github.com"]


def main():
    tex = open(SRC, encoding="utf-8").read()
    n0 = len(tex)

    # 1. author block, delimited by sentinels so nested braces cannot fool the
    # match
    m = re.search(r"%% AUTHOR-BEGIN.*?%% AUTHOR-END", tex, re.S)
    if not m:
        raise SystemExit("author block sentinels not found")
    tex = tex[:m.start()] + "%% AUTHOR-BEGIN\n" + ANON_AUTHOR + "\n%% AUTHOR-END" + tex[m.end():]

    # 2. sections that name people or a grant
    for name in DROP_SECTIONS:
        pat = re.compile(r"\\section\*\{\s*" + re.escape(name)
                         + r"\s*\}\s*\n.*?(?=\\section\*\{|\\begin\{thebibliography\})",
                         re.S)
        tex, n = pat.subn("", tex, count=1)
        if n != 1:
            raise SystemExit("could not remove the %s section" % name)

    # 3. the data availability statement: keep it, drop the URL
    pat = re.compile(r"(\\section\*\{Data availability statement\}\s*\n).*?(?=\\section\*\{|\\begin\{thebibliography\})",
                     re.S)
    tex, n = pat.subn(lambda mm: mm.group(1) + "\n" + ANON_AVAIL + "\n\n", tex, count=1)
    if n != 1:
        raise SystemExit("could not rewrite the data availability statement")

    # 4. no identifying string may survive
    hits = [k for k in IDENTIFYING if k in tex]
    if hits:
        raise SystemExit("identifying strings left in the anonymous tex: %s" % hits)

    with open(DST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(tex)

    print("wrote %s (%d bytes, from %d)" % (DST, len(tex.encode("utf-8")), n0))
    print("author block  :", re.search(r"\\author\{[^\n]*", tex).group(0))
    print("sections kept :", re.findall(r"\\section\*\{([^}]+)\}", tex))
    print("identifying   : none")
    print("citations     :", len(re.findall(r"\\citep\{", tex)),
          "| bibitems:", len(re.findall(r"\\bibitem", tex)))


if __name__ == "__main__":
    main()
