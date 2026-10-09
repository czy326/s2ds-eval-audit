# -*- coding: utf-8 -*-
"""Portable chain runner shipped with the repo.

Order matters: s1_fulltext_coding.py must run AFTER s1_field_survey.py, because
the survey script resets R2/R3/R5 to tier C and the coding script is what
upgrades them back using full-text evidence.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

env = dict(os.environ)
env.setdefault("S2DS_AUDIT_ROOT", ROOT)
env.setdefault("S2DS_AUDIT_OUT", os.path.join(ROOT, "results"))
# s1_build_manifest.py scans <DATA_ROOT>/runs/**/test_per_image.jsonl
env.setdefault("S2DS_DATA_ROOT", os.path.join(ROOT, "data"))
env.setdefault("S2DS_RUNS_ROOT", os.path.join(ROOT, "data", "runs"))

CHAIN = [
    ("s1_build_manifest.py", False),
    ("s1_audit_core.py", False),
    ("s1_effect_vs_noise.py", False),
    ("s1_anchor_b3.py", False),
    ("s1_field_survey.py", False),
    ("s1_fulltext_coding.py", False),
    ("s1_gain_vs_noise.py", False),
    ("s1_spectralsr_std_evidence.py", True),
    ("s1_oa_resolution.py", True),
    ("s1_make_paper_figures.py", True),
]

fail = 0
for script, optional in CHAIN:
    p = os.path.join(HERE, script)
    if not os.path.exists(p):
        print(f"[skip] {script} not present")
        continue
    print(f"\n{'='*72}\n>>> {script}\n{'='*72}")
    r = subprocess.run([sys.executable, p], cwd=HERE, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    sys.stdout.write(r.stdout or "")
    if r.returncode != 0:
        sys.stderr.write(r.stderr or "")
        print(f"!! {script} exited {r.returncode}")
        if not optional:
            fail = r.returncode
            break
print("\n[chain finished]", "FAILED" if fail else "OK")
sys.exit(fail)
