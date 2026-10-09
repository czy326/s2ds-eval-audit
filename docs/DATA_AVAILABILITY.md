# Data availability

This document states what is and is not redistributed, and why.

## What is redistributed

### `data/perimage/` — 170 files

One file per audit run, named `<run_name>__test_per_image.jsonl.json`. Each file
is a JSON object with two keys:

- `meta` — the run identifier, dataset tag, and the metric configuration used.
- `images` — a list with one entry per test image, each holding `path`, `psnr`,
  `ssim`, `ergas`, `sam`, and `lpips`.

These files are the audit's only inputs. They are sufficient to recompute every
number in Tables 2, 3, and 4 and in Figures 1 and 2.

They contain **image path strings and metric values only**. No image pixels, no
model weights, and no training data are included.

### `data/manifest.json`, `data/manifest_summary.csv`

The index of the 170 runs: which run belongs to which method family, dataset,
and seed, and whether it carries a seed suffix. This is what the pairing rule is
applied to.

### `data/fulltext_index/index.json`

For each file retrieved during the 35-paper survey, the filename, byte size, and
SHA-256. It lets a reader confirm which source files were read without those
files being redistributed.

### `results/` — all `audit_*.json`

Every intermediate and final result: the path-set check (A), the protocol grid
(B), the seed-noise table (C), the effect-versus-noise table (D), the anchor (E),
the survey codings (F), the gain-versus-noise analysis (G), the SpectralSR-Bench
dispersion evidence (H), and the open-access resolution table (I).

Two further files record how bibliographic metadata was obtained:
`_doi_meta.json` (Crossref and OpenAlex records, keyed by resolved DOI) and
`_arxiv_meta.json`, `_arxiv_meta_extra.json` (arXiv API records).

## What is not redistributed

### Source images

The four benchmarks (AID, RSSCN7, UCMerced, WHU-RS19) are public. The audit
reads only stored metric values, so no image needs to be shipped.

### Publisher PDFs and HTML

Full texts retrieved during the survey are not redistributed, because most are
copyrighted. The derived codings are shipped instead, in
`results/audit_F_field_survey.json`. Each coded field carries an evidence tier:

- **Tier A** — the field is stated in the abstract or a retrieved fragment.
- **Tier B** — a portion of the body text supports it.
- **Tier C** — the field could not be confirmed without the full text.

A tier-C code means "not yet confirmed", never "not reported".

## The reproducibility receipt

The audit reproduces one result that is known to be correct, before reporting
any negative finding. `code/s1_anchor_b3.py` recomputes the BSRNet variant B3
against the baseline `base_ssm` and compares to the published numbers.

| Comparison | This audit | Published |
|---|---|---|
| B3 vs base_ssm, primary convention | +0.0849 / +0.1272 / +0.0744 dB | same |
| B3 vs base_ssm, legacy convention | +0.1015 / +0.1193 / +0.0804 dB | same |

Both agree digit for digit. The pipeline is therefore known to be correct on a
case with a known answer before it is used on a case without one.

## Limits

- The seed noise is measured on our own pool of 170 runs. For surveyed papers
  whose datasets fall outside that pool, the gain-versus-noise table falls back
  to the pool-wide median, and those rows are marked as fallbacks.
- The dispersion reported by SpectralSR-Bench is per-image across 50 images. It
  is not a seed-to-seed variance and is not presented as one.
- The closed-access determination relies on OpenAlex metadata. A paper with an
  author-hosted preprint that OpenAlex has not indexed could be misclassified.
  `results/audit_I_oa_resolution.json` retains the resolved DOIs for manual
  checking.
