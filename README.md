# Protocol Choices, Not Method Quality, Decide the Ranking

**A zero-training reproducibility audit of remote sensing super-resolution evaluation.**

This repository contains the code, data, and results for an audit of how much a
remote-sensing super-resolution (RS-SR) ranking moves when the protocol around a
fixed metric is allowed to vary. No model is trained or fine-tuned at any point.
The audit re-reads per-image evaluation artifacts that already exist.

## Headline results

| Finding | Value |
|---|---|
| Runs re-read | 170, across AID / RSSCN7 / UCMerced / WHU-RS19 |
| Test-set identity check (Line A) | 170/170 pass, Jaccard index 1.0 |
| Datasets where median aggregation flips the champion | 4 of 4 |
| Lowest rank correlation found | 0.272 (SAM on WHU-RS19, the only cross-family flip) |
| Method pairs analyzed | 327 |
| Pairs that reverse sign across training seeds | 83 (25.4%) |
| Pairs with effect smaller than the seed standard deviation | 172 (52.6%) |
| Median seed-to-seed standard deviation | 0.088 dB (range 0.049 to 0.248) |
| Median method effect | 0.018 to 0.039 dB |
| Surveyed papers that state a verifiable dB gain | 7 of 35 (20.0%) |
| Surveyed abstracts that mention seeds, variance, or a test | 0 of 35 |

The seed noise is two to five times the method effect it is meant to
discriminate. On the smallest benchmark, a 0.1 dB claim sits below the median
seed variation.

## The seven-point scorecard (R1 to R7)

| # | Check | Failure when omitted |
|---|---|---|
| R1 | Is the test-set image list public and identical across runs? | Cross-paper comparison is void |
| R2 | Is the metric aggregation stated (mean, median, trimmed)? | The champion flips under the convention |
| R3 | Are three or more seeds run, with per-seed direction reported? | The 25.4% reversal rate is invisible |
| R4 | Is the seed-noise magnitude reported? | A reader cannot tell whether the effect clears the noise |
| R5 | Is the baseline convention fixed to one run and endpoint? | The effect inflates by 5% or more |
| R6 | Is equivalence testing used rather than significance alone? | "No difference" reads as "improvement" |
| R7 | Are per-image paired confidence intervals and d_z reported? | Stability is unjudgeable |

## Repository layout

```
code/          recomputation scripts (standard library + optional numpy)
data/          per-image evaluation artifacts (170 files) and the run manifest
results/       every audit_*.json produced by the scripts
figures/       Figure 1 and Figure 2, in png / pdf / svg at 300 dpi
papers/        the manuscript draft, the R2 protocol grid, and the reference list
docs/          data availability, provenance, and reproduction notes
```

## Reproducing the audit

The scripts require Python 3.11 or newer. `numpy` is optional and only speeds up
the aggregation. Everything else uses the standard library.

```bash
export S2DS_AUDIT_ROOT="$(pwd)"
export S2DS_AUDIT_OUT="$(pwd)/results"
export S2DS_DATA_ROOT="$(pwd)/data"
export S2DS_RUNS_ROOT="$(pwd)/data/perimage"

# Lines A to E: the controlled audit of the 170 runs
python code/s1_build_manifest.py
python code/s1_audit_core.py
python code/s1_effect_vs_noise.py
python code/s1_anchor_b3.py

# Lines F to I: the 35-paper report-practice survey
python code/run_audit_chain.py        # field survey -> full-text coding -> gain vs noise
python code/s1_oa_resolution.py
python code/s1_make_paper_figures.py
```

Outputs land in `results/`. The provenance of every number in the manuscript is
listed in `docs/PROVENANCE.md`, which maps each table and figure to the JSON file
that produced it and to the script that writes that file.

## The one rule that matters

**Only runs whose names carry an explicit seed suffix participate in method
pairing.** Runs without a seed suffix are excluded.

This rule is enforced because our first implementation violated it. A seed-less
run was grouped into the same method family as three seed-suffixed runs and
paired positionally, producing a sign-reversed difference of −0.1008 dB. After
restricting pairing to seed-suffixed runs, the same comparison returned
+0.0849, +0.1272, and +0.0744 dB, matching the published values to the digit.

A sign-reversed "major finding" is more likely to be a bug in the audit script
than a discovery about the audited work. `code/s1_anchor_b3.py` exists to
enforce this before any negative result is reported.

## Data availability

`data/perimage/` holds the per-image evaluation records the audit reads, one
file per run. Each record carries the image path and the per-image
PSNR, SSIM, ERGAS, SAM, and LPIPS values. The image pixels themselves are not
redistributed. See `docs/DATA_AVAILABILITY.md`.

Publisher PDFs and HTML retrieved during the survey are not redistributed. Only
the derived codings are shipped, in `results/audit_F_field_survey.json`, and
`data/fulltext_index/index.json` records which files were read so the codings
can be checked.

## Citation

See `CITATION.cff`. The manuscript is in preparation.

## License

Code is released under the MIT License (`LICENSE`). The derived result files
and the codings are released under CC BY 4.0.
