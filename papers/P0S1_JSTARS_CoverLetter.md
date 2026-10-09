# Cover Letter — IEEE JSTARS Submission

> Draft for submission through ScholarOne (mc.manuscriptcentral.com/jstars).
> Fill the bracketed placeholders before sending. Do not invent author details.

---

[Date]

Prof. Peifeng Ma
Editor-in-Chief
*IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing*

Dear Prof. Ma,

We submit for consideration as a Regular Paper the manuscript entitled
**"Protocol Choices, Not Method Quality, Decide the Ranking: A Reproducibility Audit
of Remote Sensing Super-Resolution Evaluation"** by [author list].

**What the paper does.** Remote sensing super-resolution (RS-SR) papers routinely
report that a method exceeds the previous best by a small margin expressed in dB. We
audit the protocol choices behind those numbers, namely the test-set composition, the
metric aggregation convention, the training-seed count, and the baseline convention
used at the endpoint. The audit reads 170 existing runs across four standard
benchmarks, AID, RSSCN7, UCMerced, and WHU-RS19, by reusing their per-image
evaluation artifacts. No model is retrained.

**Why it belongs in JSTARS.** The journal's readership consumes RS-SR rankings as an
input to downstream Earth-observation applications. The finding that bears most
directly on that use is that the seed-to-seed variability of a benchmark grows as the
benchmark shrinks, so the smallest and most widely used benchmarks are the ones whose
rankings are least resolvable. On WHU-RS19, with 101 test images, the median seed
standard deviation is 0.1202 dB, and 47.3% of method pairs reverse order between
training seeds. A 0.1 dB claim, which is the working currency of the field, lies
inside that noise band. The paper quantifies this on benchmarks the JSTARS community
uses daily, and it supplies a checklist that authors, reviewers, and editors can
apply without new experiments.

**Why the result is credible.** Three design choices matter. First, the audit is
zero-training: it reads stored per-image metrics, so there is no new training run
whose configuration could bias the comparison. Second, the audit includes an anchor
that reproduces a published result digit for digit before reporting any negative
finding, which rules out a scripting artifact as the source of the instability.
Third, the companion survey of 35 published 2026 papers reports both the
abstract-level and the full-text counts of each disclosure, so the claim about
non-reporting is bounded by how many papers were actually read rather than asserted
from metadata.

**Reproducibility.** The complete audit, including the per-image records for all 170
runs, the result files, the figure scripts, and the survey codings, is available at
`https://github.com/czy326/s2ds-eval-audit`. Running `code/run_audit_chain.py`
regenerates every result file from the shipped records, and the regenerated files are
identical to the shipped ones. The four benchmarks are public and are not
redistributed.

**Novelty relative to existing evaluation critiques.** Prior work asks whether the
metric is trustworthy, for example whether PSNR correlates with human judgment or
with downstream utility, and whether the protocol should be standardized. This paper
asks a question those works leave open, namely whether the ranking of a fixed set of
methods is stable when the protocol is allowed to vary within the range of defensible
choices. It answers with measured fractions rather than a position.

**Article type and length.** We submit this as a Regular Paper. The manuscript is
written in IEEE two-column format, and [the body is within the six-page length that
avoids the excessive-length charge OR the estimated length is N pages].

**Suggested reviewers.** [Optional. Up to three names with affiliations and emails,
none of whom are collaborators or from our institution.]

**Declarations.** The manuscript is original, has not been published, and is not under
consideration elsewhere. All authors have approved the submission and declare no
competing interests. [Confirm preprint status if the work has been posted.]

Thank you for considering the manuscript.

Sincerely,

[Corresponding author name]
[Affiliation, address]
[Email, ORCID]
on behalf of all authors
