# -*- coding: utf-8 -*-
"""
Measure vertical white space on each page, counting both text baselines and
image placements. A text-only scan reports a figure's plot area as blank, which
is wrong.
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pypdf import PdfReader

path = sys.argv[1]
LIMIT = 90  # pt; ~1.25 in of uninterrupted white space is what a reader notices
r = PdfReader(path)
print("%-6s %-12s %-12s %s" % ("page", "content span", "largest gap", "note"))
worst = []
for pno, page in enumerate(r.pages, 1):
    ys = []

    def visit(text, cm, tm, font, size):
        if text and text.strip():
            ys.append(tm[5])

    try:
        page.extract_text(visitor_text=visit)
    except Exception:
        ys = []

    # image placements: origin y from the translation matrix, height from the
    # scale matrix and the image's own pixel height
    try:
        stream = page.get_contents().get_data().decode("latin-1")
        xobj = page["/Resources"].get("/XObject", {})
        for m in re.finditer(r"1 0 0 1 ([-\d.]+) ([-\d.]+) cm\s*q\s*"
                             r"([-\d.]+) 0 0 ([-\d.]+) 0 0 cm[^D]*?/([A-Za-z0-9]+) Do",
                             stream):
            ty, s = float(m.group(2)), float(m.group(4))
            name = m.group(5)
            h = 0.0
            if name in xobj:
                o = xobj[name].get_object()
                if o.get("/Subtype") == "/Image":
                    h = float(o.get("/Height", 0)) * s
            ys += [ty, ty + h]
    except Exception:
        pass

    if len(ys) < 4:
        continue
    u = sorted(set(round(y, 1) for y in ys))
    gaps = [(u[i + 1] - u[i], u[i]) for i in range(len(u) - 1)]
    g, at = max(gaps)
    last = pno == len(r.pages)
    note = "last page" if last else ("LARGE" if g > LIMIT else "")
    print("%-6d %-12s %-12s %s" % (pno, "%.0f-%.0f" % (u[0], u[-1]), "%.0f pt" % g, note))
    if g > LIMIT and not last:
        worst.append((pno, int(g)))
print()
print("non-final pages with a gap over %d pt:" % LIMIT, worst or "none")
