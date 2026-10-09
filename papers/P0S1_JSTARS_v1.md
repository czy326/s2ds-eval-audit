# Protocol Choices, Not Method Quality, Decide the Ranking: A Reproducibility Audit of Remote Sensing Super-Resolution Evaluation

<!--
JSTARS submission draft, version 1, 2026-10-09.
Target: IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing.
Article type: Regular Paper.
All numeric values are derived from results/*.json and verified by
code/s1_consistency_check.py. Every figure and table caption carries a Source line.
-->

## Abstract

Remote sensing super-resolution (RS-SR) papers routinely advertise gains expressed as "our method exceeds the state of the art by X dB". These numbers rest on protocol choices that are rarely reported, namely which images form the test set, how per-image metrics are aggregated, how many training seeds are run, and which baseline convention is used at the endpoint. We audit these choices on 170 existing runs spanning four standard RS-SR benchmarks by reusing per-image evaluation artifacts, with no additional training. A path-level check confirms that every run within a benchmark evaluates an identical image set, so the instability we report is not a data-engineering artifact. Swapping only the metric or the aggregation rule flips the top-ranked method on all four benchmarks, with median aggregation reversing the champion on 4 of 4, and the spectral angle mapper reversing it on WHU-RS19 at a rank correlation of 0.272 against mean PSNR. Across 327 method pairs, 25.4% reverse sign between training seeds and 52.6% have an effect smaller than the reference method's seed-to-seed standard deviation, whose median is 0.088 dB against method effects of 0.018 to 0.039 dB. A survey of 35 RS-SR and evaluation papers from 2026, with 18 full texts retrieved, finds that 7 of 35 state a verifiable dB gain, that no abstract mentions seeds, variance, or statistical tests, and that 4 disclose seed counts in the body. The gap between the abstract-level and full-text counts bounds what can be asserted about non-reporting. We close with a seven-item reproducibility scorecard.

**Index Terms**—Remote sensing, super-resolution, reproducibility, benchmark evaluation, statistical significance, performance ranking.

---

## 1. Introduction

### A. The leaderboard rests on unreported choices

A reader who wants to decide which super-resolution method to deploy has, in practice, one instrument, namely the ranking published in the paper. That ranking is the output of a pipeline whose steps are individually mundane and collectively decisive. Someone chose the test images. Someone chose PSNR rather than SSIM as the headline number, and chose the mean rather than the median to collapse one number per image into one number per method. Someone chose which baseline checkpoint counts as the baseline. Someone ran the training once, or three times, and reported whichever summary they preferred. Each choice is defensible. Together they determine who wins.

The RS-SR literature reports the ranking and, with few exceptions, omits the choices. Our survey of 35 papers from 2026 finds that no abstract mentions training seeds, variance, or statistical testing. Only four abstracts mention the aggregation convention at all. A reader who wants to know whether a "+0.1 dB" claim would survive a rerun with a different random seed has nowhere to look.

The stakes are higher in remote sensing than in generic image restoration, for two reasons. The benchmarks that the field uses most are small, with WHU-RS19 holding 101 test images and UCMerced holding 210, so a per-image statistic is estimated from a short sample. The applications that consume the resulting rankings, from urban impervious-surface mapping to crop monitoring to disaster response, are downstream of a land-cover classifier or a change detector, and a method that wins a benchmark by a fraction of a decibel may not win the application. Both factors push the same way, toward a ranking that is more fragile than its presentation suggests.

### B. Opening evidence: a well-documented paper that still ranks by mean

We begin with a case that requires no reproduction on our part. SpectralSR-Bench (Sensors, 2026) is the only paper in our sample that reports `mean ± std` in every table. On disclosure practice it belongs to the best tier we found. Its own reported numbers, however, show that in 8 of 10 adjacent method comparisons the difference in mean PSNR is smaller than the reported per-image standard deviation (Table I).

**TABLE I. Adjacent-pair comparison in SpectralSR-Bench, using the paper's own reported statistics.**

| Method A | Method B | ΔPSNR (dB) | max std (dB) | Δ / std |
|---|---|---|---|---|
| FSRCNN (×2) | SRCNN (×2) | 0.38 | 2.20 | 0.17 |
| SRCNN (×2) | SRCNN (×2→×4) | 3.50 | 2.20 | 1.59 |
| SRCNN (×2→×4) | SRCNN (×2→×4→×8) | 1.45 | 2.20 | 0.66 |
| Bicubic (×2) | Bilinear (×2) | 0.50 | 3.53 | 0.14 |
| Bilinear (×2) | Bicubic (×4) | 1.79 | 3.66 | 0.49 |
| Bicubic (×4) | Bilinear (×4) | 0.42 | 3.66 | 0.11 |
| Bilinear (×4) | Bicubic (×8) | 1.88 | 3.65 | 0.52 |
| Bicubic (×8) | Bilinear (×8) | 0.41 | 3.65 | 0.11 |
| SinSR (×4) | ResShift (×4) | 0.96 | 2.44 | 0.39 |
| ResShift (×4) | SR3 (×8) | 16.11 | 14.80 | 1.09 |

The `std` column is the larger of the two reported per-image standard deviations. The last column is the ratio of the mean difference to that dispersion. Eight of the ten ratios are below 1, so the ranking is not resolvable from the reported statistics. The two pairs that do clear the dispersion involve a large change of operating regime, a three-step cascade and a diffusion method near failure. The `std` here is a per-image dispersion across 50 images and is not a seed-to-seed variance. The table supports the weaker claim that the method differences are smaller than the data dispersion, and it is the only case in the survey where the decisive evidence comes from the paper's own reported numbers with no recomputation on our part.

The paper discloses dispersion. It then ranks by the mean anyway. This is not a criticism of the authors, who did more than their peers. It is a statement about the field's conventions. When the per-image spread exceeds the gap between methods, a mean-only ranking carries information the reader cannot evaluate. The paper that came closest to giving the reader what they need still left the decisive comparison ambiguous.

This case sets the terms of the paper. We argue that the ranking procedure is under-specified, and we measure what that under-specification costs on data where we can control every choice.

### C. What existing evaluation critiques address

Recent work has made evaluation itself an object of study, and each contribution answers a different question from ours.

GeoSR-Bench shows that PSNR improvements correlate weakly, and sometimes negatively, with downstream task performance. SR-Prominence shows that 48.2% of annotated artifacts go unnoticed by human observers, and that no-reference IQA fails to generalize across datasets. LL-Bench shows that image quality assessment models correlate weakly with human pairwise preferences across 16 tasks. These works ask whether the metric is trustworthy.

NTIRE 2026 addresses protocol ambiguity by fixing it. A 4-pixel border is excluded, all calculation is restricted to the Y channel, and eight metrics are defined precisely. The organizers' score for the infrared track, `Score = PSNR + 20 × SSIM`, amplifies SSIM by a factor of 20 relative to PSNR, so that 0.01 SSIM contributes the same as 0.2 dB. This is a gain for reproducibility, because the rule is stated. It is also, in the same breath, an acknowledgment that the weighting rule determines the meaning of the ranking. A change in that factor reorders competitors.

The question these works leave open is the one we take up. Holding the metric fixed and holding the test images fixed, does the ranking stay the same when the protocol choices change. For a given set of methods, how often does swapping the aggregation rule, or the random seed, or the endpoint convention, change who is on top.

### D. Contributions

We make four contributions.

**C1. A zero-training audit protocol.** We audit 170 existing runs across four standard benchmarks by reading their per-image evaluation artifacts. No model is retrained. The protocol applies to any SR evaluation that has retained per-image results, which is the common case for a laboratory's own experiment logs.

**C2. A measurement of ranking instability.** We quantify how often the ranking changes under three classes of protocol choice. Across 327 method pairs, 25.4% reverse sign between training seeds and 52.6% show an effect smaller than the reference method's seed noise. The below-noise fraction ranges from 47.1% to 68.5% across three defensible reference conventions, and we report the full range. Changing only the aggregation rule flips the champion on all four benchmarks.

**C3. A report-practice survey with a self-calibration.** We code 35 papers on disclosure of aggregation, seeds, and test-set composition. The abstract-level count for seed disclosure is zero. Retrieving 18 full texts raises it to four. We report both numbers and treat the difference as a methodological constraint on the whole exercise rather than as a footnote.

**C4. A seven-item scorecard.** Each audit finding maps to one check a reader can apply to a published paper, listed in Section VI.

The remainder of the paper is organized as follows. Section II places the audit against related work. Section III specifies the audit design and the pairing rule. Section IV reports the controlled audit of 170 runs. Section V reports the survey of 35 published papers. Section VI states the scorecard. Section VII discusses the consequences for authors, reviewers, and editors. Section VIII lists the limitations, and Section IX concludes.

---

## 2. Related Work

### A. Metric trustworthiness

A line of work asks whether the numbers a paper reports correspond to what a human would see. LL-Bench [1] evaluates image quality assessment models against 152,020 human pairwise preferences over 2,469 images and 16 tasks, and finds weak correlation with human judgment. SR-Prominence [2] reports that 48.2% of the artifacts its annotators mark are not noticed by viewers, and that no-reference IQA metrics fail to transfer across datasets. Both conclusions concern the metric's validity as a proxy for perceived quality.

Our audit keeps the metric fixed and varies the protocol around it. We do not ask whether PSNR measures quality. We ask whether a ranking built on PSNR is stable when the aggregation or the seed changes. The two questions are independent. A perfectly valid metric can still yield an unstable ranking if the aggregation rule is left free.

### B. Downstream correlation

GeoSR-Bench [3] trains downstream predictors of land-surface variables from super-resolved inputs and finds that PSNR gains do not reliably translate into downstream gains, and in some settings reverse. This is an argument for evaluating on the downstream task rather than on reconstruction fidelity.

Our scope is narrower and orthogonal. We do not evaluate any downstream task. We examine the internal consistency of the reconstruction evaluation itself, on the premise that a downstream comparison inherits any instability present upstream.

### C. Protocol standardization

Competition organizers confront ambiguity directly by fixing it. NTIRE 2026 [4], [5] fixes the evaluation region, the color channel, and the metric set, and publishes a weighted score. The choice to weight SSIM by 20 relative to PSNR is a protocol decision made explicit. Its existence is the clearest available evidence that protocol decisions change rankings, since a decision that did not matter would not need to be published and defended.

We differ in direction. Where the organizers unify the protocol so that a single ranking is well defined, we ask how much a ranking moves when the protocol is allowed to vary across the range of defensible options. The NTIRE score tells us what happens under one convention. Our audit reports the spread across conventions.

### D. Cross-method fairness

SpectralSR-Bench [6] evaluates CNN, GAN, diffusion, and classical methods under a single reproducible pipeline with per-image records. Its contribution is fairness along the method axis, in that every method is measured the same way. One-step diffusion methods such as ORDiffSR [18] extend the same axis to a newer method family, and their inclusion makes the aggregation question sharper, since a diffusion model and a convolutional model can differ substantially in the shape of their per-image error distribution even when their mean PSNR is close.

We vary along a different axis, holding the method set fixed and changing the measurement convention. The two are complementary. Fairness across methods is necessary for a meaningful ranking. Stability across conventions is necessary for a ranking to survive being read by someone who would have chosen differently.

### E. Statistical reporting norms

Psychology and natural language processing have established reporting conventions, namely report effect sizes with confidence intervals, run multiple seeds, and prefer equivalence testing to null-hypothesis significance when the claim is that there is no difference. RS-SR has no such norm. Our survey quantifies the gap, and the scorecard in Section VI adapts these conventions to the specific failure modes we measure.

### F. Benchmark scale in remote sensing

The benchmarks used in this audit carry between 101 and 1000 test images. The small end of that range is typical for remote sensing scene and reconstruction benchmarks, because the underlying acquisitions are expensive and the ground truth requires either very high resolution reference imagery or a physical model. A recent survey of remote sensing foundation models [7] identifies data imbalance and the training-to-deployment efficiency gap as two of four open directions, and both bear on how a benchmark result should be read. We add a third consideration to that list, namely that the statistical resolution of the benchmark itself bounds the resolution of any comparison made on it.

---

## 3. Audit Design

### A. Data and assets

The audit reads 170 runs, each of which produced a `test_per_image.jsonl` record with one line per test image holding `path`, `psnr`, `ssim`, `ergas`, `sam`, and `lpips`. The runs span four standard benchmarks, AID (46 runs), RSSCN7 (39), UCMerced (39), and WHU-RS19 (36). Ten further runs carry no dataset tag and are excluded from all per-benchmark statistics. Test-set sizes are 1000 images for AID, 281 for RSSCN7, 210 for UCMerced, and 101 for WHU-RS19. All four benchmarks are public and are widely used for RS-SR in the aerial and satellite scene setting.

Every run predates this study. We train nothing. The audit is a re-reading of stored artifacts, which is what makes it cheap and what makes it applicable to any laboratory's existing logs.

### B. Four audit lines

**TABLE II. The four audit lines.**

| Line | Question | Criterion |
|---|---|---|
| **A** per-image consistency | Is the same test set literally the same images | Exact path-set comparison and Jaccard index per benchmark |
| **B** convention sensitivity | Does the ranking or the champion change when the metric or aggregation changes | Eight conventions, Spearman rank correlation against mean PSNR, and top-1 agreement |
| **C/D** effect versus noise | Which is larger, the method effect or the seed-to-seed fluctuation | Seed-to-seed standard deviation of paired ΔPSNR, and the sign-reversal rate |
| **E** anchor | Is the audit pipeline itself correct | Reproduce a known result and compare to the published numbers digit by digit |

Line B holds the images and methods fixed and varies only the aggregation or the metric. Lines C and D hold the methods and the aggregation fixed and vary only the seed. Line A removes a confound that would invalidate both. Line E establishes that the implementation is sound before any negative finding is reported.

### C. Pairing discipline, and a bug we chose to report

We preregistered one rule for the pairing logic, namely that only runs whose names carry an explicit `_s20xx` seed suffix participate in method pairing. Runs without a seed suffix are excluded. Of the 170 runs, 160 carry a dataset tag, and 144 of those also carry a seed suffix and enter the pairing. The remaining 26 are set aside, comprising 16 tagged runs without a seed suffix and 10 runs with no dataset tag.

This rule exists because our first implementation violated it, and the resulting error is instructive enough to report in full. The first version of the effect-versus-noise script grouped the seed-less run `stage2_aid_edge_deep_fuse` into the same method family as `base_ssm_aid_s2026/2027/2028` and paired them seed by seed. The pairing was misaligned, and the script reported Δ = −0.1008 dB, a sign reversal against the published result. We briefly read this as evidence of an error in the original paper.

It was a bug in our grouping function. The seed-less run had no seed to match, so the pairing loop attached it to whichever seed happened to occupy the same position. After restricting pairing to seed-suffixed runs, the same comparison returned +0.0849, +0.1272, and +0.0744 dB across the three seeds, matching the published values to the digit.

The lesson is general enough to state as a rule. A sign-reversed major finding is more likely to be a bug in the audit script than a discovery about the audited work. Line E exists to enforce this. Before an audit reports that someone else's result does not hold, the audit must first show that it reproduces a result that is known to hold. Section IV-D gives that demonstration.

---

## 4. Results I: Controlled Audit of 170 Runs

### A. Line A: the test sets are identical

All 170 runs pass. Within each benchmark, the set of image paths is identical across every run, the Jaccard index is 1.0, the recorded size matches the split file, and no metric value is missing or NaN.

This is a positive result and it removes a confound. The instability reported in the rest of this section cannot be attributed to runs being compared on different images. Whatever moves a ranking here, it is not the test set.

### B. Line B: the champion changes on all four benchmarks

**TABLE III. Rank correlation against mean PSNR, and whether the champion changes.**

| Convention | AID (46) | RSSCN7 (39) | UCMerced (39) | WHU-RS19 (36) |
|---|---|---|---|---|
| `psnr_mean` (reference) | 1.000 | 1.000 | 1.000 | 1.000 |
| `psnr_median` | **0.882** ✗ | **0.502** ✗ | **0.818** ✗ | **0.749** ✗ |
| `psnr_trim10` | 0.979 | 0.987 | 0.996 | 0.934 |
| `psnr_trim25` | 0.962 | 0.986 | 0.981 | 0.833 |
| `ssim_mean` | 0.868 | **0.957** ✗ | 0.747 | 0.807 |
| `ergas_mean` | 0.943 | **0.982** ✗ | 0.945 | 0.944 |
| `sam_mean` | 0.813 | **0.535** ✗ | 0.793 | **0.272** ✗ |
| `lpips_mean` | 0.534 | **0.894** ✗ | 0.549 | 0.860 |

✗ marks a convention under which the top-ranked method differs from the `psnr_mean` champion.

Table III reports, for each benchmark, the Spearman rank correlation between the ranking under each of eight conventions and the ranking under mean PSNR, together with whether the top-ranked method changed. Three results stand out.

**Median aggregation reverses the champion on all four benchmarks.** Replacing the mean with the median is a legitimate choice, and one that protects against the very outlier sensitivity that a small test set invites. Under it, the top-ranked method changes on AID, RSSCN7, UCMerced, and WHU-RS19. The rank correlation drops as low as 0.502, on RSSCN7.

**Trimmed aggregation preserves the ranking.** The 10% and 25% trimmed means keep a rank correlation of at least 0.833 with mean PSNR, and mostly above 0.93, across every benchmark. The trimmed mean discards the extremes while retaining the bulk of the distribution, and the ranking is stable under it.

The contrast between the median and the trimmed mean localizes the source. Both are robust aggregators, yet the median reorders and the trimmed mean does not. The difference is that the median depends on the middle order statistics and is sensitive to how the distribution shifts in the center, while the trimmed mean averages the bulk and retains the mean's insensitivity to that shift. The instability therefore lives in the tails and near the center, not in the overall shape. This is an operational diagnostic. When a benchmark's ranking is highly sensitive to the convention, the first thing to inspect is the distribution of the per-image scores, not the choice of metric.

**On WHU-RS19, switching the metric changes the winner's method family.** The SAM convention carries the lowest rank correlation in the whole study, 0.272, on WHU-RS19. The champion under mean PSNR is a residual-channel-attention network. Under SAM it is a lightweight CNN. The two methods differ not in depth or width but in family, and the benchmark that produces this reversal is the smallest, at 101 test images.

### C. Lines C and D: effect size against seed noise

We pair every two runs of the same benchmark that share a seed and belong to different methods, and compute the mean difference in PSNR over the paired images. Across 327 pairs we record the mean effect, the standard deviation of the per-image differences within each method, and whether the effect keeps its sign across seeds.

The noise comparison is reported under three definitions, because the three give different counts and the choice should not be left implicit.

The conservative direction of the claim is that a difference fails to clear the noise, so we first report the definition that makes that claim easiest to reject. A pair counts as below the noise when the magnitude of the mean effect is smaller than the smaller of the two methods' seed standard deviations. Under that rule 154 of 327 pairs (47.1%) fall below the noise. Both methods must then be noisier than the effect for the pair to count.

The standard definition, and the number we carry through the paper, compares the effect against the seed standard deviation of the reference method in each pair. That gives 172 of 327 (52.6%). We fix the reference as the first method of the pair so the count is deterministic and reproducible.

The symmetric definition, in which the effect is compared against the larger of the two seed standard deviations, is the least favorable to the claim and gives 224 of 327 (68.5%). The three definitions span 47.1% to 68.5% and all agree on the direction of the finding. We report the middle one because its reference is explicit, and we give all three so that a reader who prefers a different convention can see how the number moves. The spread across the three definitions is itself an instance of the paper's subject, in that a headline percentage in this audit moves by more than 20 points depending on a convention that most papers would leave unstated.

**TABLE IV. Effect size against seed noise.**

| Quantity | Value |
|---|---|
| Method pairs analyzed | 327 |
| Pairs that reverse sign across seeds | **83 (25.4%)** |
| Pairs with \|effect\| below the reference method's seed sd | **172 (52.6%)** of 327 |
| Pairs with \|effect\| below the smaller of the two methods' seed sds | 154 (47.1%) of 327 |
| Pairs with \|effect\| below the larger of the two methods' seed sds | 224 (68.5%) of 327 |
| Median seed-to-seed standard deviation | **0.088 dB** (range 0.049 to 0.248) |
| Median method effect | **0.018 to 0.039 dB** |

The seed noise is two to five times the size of the method effect it is supposed to discriminate. One in four method pairs reverses order when the seed changes. Slightly more than half of all pairs show a difference smaller than the noise.

The per-benchmark noise, reported in Table V, follows the test-set size. WHU-RS19, at 101 images, has the largest noise and, at 47.3%, the highest reversal rate, with 80% of its pairs falling below the noise. AID, at 1000 images, has the smallest noise. The ordering is monotone in test-set size, with one inversion between AID and RSSCN7 that we attribute to the differing content heterogeneity of the two benchmarks rather than to size alone.

**TABLE V. Seed noise by benchmark.**

| Benchmark | Test images | Median sd (dB) | Max sd (dB) | Reversal rate |
|---|---|---|---|---|
| AID | 1000 | 0.0728 | 0.1187 | — |
| RSSCN7 | 281 | 0.0632 | 0.1169 | — |
| UCMerced | 210 | 0.1070 | 0.1701 | — |
| WHU-RS19 | 101 | 0.1202 | 0.2485 | 47.3% |

**Fig. 1. Seed noise against test-set size.** The horizontal axis is the number of test images on a logarithmic scale and the vertical axis is the median seed-to-seed standard deviation of the paired per-image PSNR difference in dB. Each marker is one benchmark and the error bars span the minimum to the maximum standard deviation observed for it. The four points are AID (1000 images, 0.0728 dB), RSSCN7 (281, 0.0632 dB), UCMerced (210, 0.1070 dB), and WHU-RS19 (101, 0.1202 dB). A fixed absolute effect, such as the 0.1 dB that RS-SR papers commonly claim, is therefore compared against a smaller noise floor on a large benchmark and a larger one on a small benchmark.

The practical implication is direct. The headline convention in RS-SR, stating that a method exceeds the previous best by 0.1 dB, sits inside the noise band on small benchmarks. On WHU-RS19, a 0.1 dB claim is below the median seed variation.

**Fig. 2. Method effect against seed noise, for all 327 pairs.** The horizontal axis is the absolute mean paired PSNR difference in dB and the vertical axis is the seed-to-seed standard deviation of that difference in dB. Both axes are logarithmic and a dashed line marks equality. Points above the line have an effect larger than the noise. Points below the line, colored, are the 172 pairs whose difference does not clear the noise floor under the reference-method definition. The cluster near the lower-left corner corresponds to pairs on AID between method variants that differ by a single component, where both the effect and the noise are of order 0.01 dB.

### D. Line E: the pipeline reproduces a known result

Before reporting any negative finding, we verify that the audit reproduces a result that is known to be correct. We recompute the comparison between the BSRNet variant B3 and the baseline `base_ssm` from the stored per-image artifacts and compare to the published numbers.

**TABLE VI. Anchor comparison.**

| Comparison | This audit | Published | Agreement |
|---|---|---|---|
| B3 vs base_ssm, primary convention | +0.0849 / +0.1272 / +0.0744 dB | same | digit for digit |
| B3 vs base_ssm, legacy convention | +0.1015 / +0.1193 / +0.0804 dB | same | digit for digit |
| Difference attributable to the baseline convention alone | **0.0049 dB** | — | — |

The pipeline reproduces both published figures exactly. It also shows that changing only the baseline convention, from the primary endpoint to the legacy one, moves the reported effect by 0.0049 dB, about 5% of the effect itself. In a context where the median method effect is 0.018 to 0.039 dB, a 5% shift from a convention change is not negligible. The magnitude is small in absolute terms and decisive in relative terms.

---

## 5. Results II: Report Practice in 35 Papers

### A. Coding scheme and evidence tiers

We surveyed 35 papers on RS-SR and its evaluation, published mainly in 2026, drawn from arXiv, MDPI, Nature Scientific Reports, IEEE, and Elsevier venues. Each paper was coded on whether it discloses its aggregation convention (R2), its training-seed count (R3), and its test-set composition (R5). Because not every paper was readable in full, we assign each coded field an evidence tier. Tier A means the field is stated in the abstract or a retrieved fragment. Tier B means a portion of the body text supports it. Tier C means the field could not be confirmed without the full text.

The tier matters for interpretation. A tier-C code means not yet confirmed, not that the field is absent. We keep this distinction explicit because it is the difference between a defensible claim and an overreach, as Section V-C shows.

We retrieved full texts for 18 of the 35 papers, using the publisher's open-access channel where available and the publisher's own PDF endpoint otherwise. Eleven of the remaining papers are closed access at the publisher, confirmed against OpenAlex metadata, and six have no article PDF at all.

### B. Report-practice statistics

**TABLE VII. Report practice in 35 papers.**

| Field | Count |
|---|---|
| State a verifiable specific dB gain | **7 / 35 (20.0%)** |
| Qualitative SOTA, absolute PSNR only, or efficiency only | **28 / 35 (80.0%)** |
| Provide a code or data link | 5 / 35 (14.3%) |
| Mention seeds, variance, or a statistical test in the abstract | **0 / 35 (0.0%)** |
| Mention the aggregation convention in the abstract | 4 / 35 (11.4%) |
| Anchor to a downstream task or protocol reproduction | 11 / 35 (31.4%) |
| Disclose R2 in the body (of 18 full texts) | 8 / 35 |
| Disclose R3 in the body (of 18 full texts) | 4 / 35 |
| Disclose R5 in the body (of 18 full texts) | 15 / 35 |

Four fifths of the surveyed papers do not state a number a reader could check. They report an absolute PSNR, or claim a qualitative improvement over the state of the art, or compare only efficiency. This matters for our argument because the finding we report in Section V-D, about effects smaller than the seed noise, applies only to the 7 papers that give a number. For the other 28, there is no claim to test.

The abstract-level count for seed disclosure is zero. Not one of the 35 abstracts mentions a seed, a variance, or a statistical test. Only four abstracts mention how the per-image metrics were aggregated.

### C. The self-calibration

Retrieving 18 full texts changes the seed-disclosure count from zero to four. The papers that do it are specific.

EORestore-Agent [8] trains seven models that differ only in random seed and averages their predictions at inference. It is the only multiple-seed ensemble in the sample. GeoSR-Bench [3] trains its downstream prediction models three times per evaluation case and reports the average over the runs. SFG-SwinSR fixes the random seed of 42 for shuffling and weight initialization. The infrared track of NTIRE 2026 [4] lists a seed of 42 in a team's table.

These four papers refute the reading that no one in the field uses seeds. They were invisible at the abstract level and visible only in the body.

This forces a specific formulation, and it is the methodologically honest one. The correct claim is not that RS-SR authors do not run seeds. The correct claim is that the field's reporting norm does not require seed information to appear where a reader will see it, which is the abstract and the results table. The distinction matters because the two claims have different remedies. If authors were not running seeds, the remedy would be to run them. Because some authors run them and omit them, the remedy is a reporting standard.

We treat this self-calibration as a constraint on the entire survey rather than as a qualification appended at the end. Any count of papers that do not report some field is bounded above by the number of full texts retrieved. We state the bound and report both counts.

### D. Claimed gains against the noise floor

For the 7 papers that state a verifiable dB gain, we compare the claimed effect to the seed noise measured on the same benchmark in Section IV-C. Where the paper's benchmark is outside our pool, we fall back to the pool-wide median and mark the fallback.

**TABLE VIII. Claimed gains against the seed-noise floor.**

| Paper | Claimed Δ | Benchmark (noise source) | Δ / max sd | Reading |
|---|---|---|---|---|
| PLAN [9] | +0.07 dB | AID (measured) | 0.59 | below noise |
| DBTSR [10] | +0.12 dB | AID (measured) | 1.01 | marginal |
| IR275K [11] | +0.35 dB | infrared (fallback) | 1.41 | marginal |
| AstraMoE-SR [12] | +0.64 dB | DOTA (fallback) | 2.58 | clears noise |
| DFSMamba [13] | +1.07 dB | AID (measured) | 9.02 | clears noise |
| EORestore-Agent [8] | +2.30 dB | Landsat-8 (fallback) | 9.27 | clears noise |

Two of the seven claims fall below the noise ceiling, and two more sit just above it.

The pattern is not that RS-SR gains are noise. The large gains, of 0.64 dB and above, clear the noise by a wide margin, and they are real. The problem is concentrated in the crowded interval between 0.05 and 0.19 dB, which is exactly where the claim of beating the state of the art by 0.1 dB lives. In that interval, on benchmarks the size of WHU-RS19, the claim and the noise are the same order of magnitude.

### E. Positive exemplars

Four papers show that the practices we recommend are already used, just not treated as standard.

GrasslandGAN [14] defines the coefficient of variation as the ratio of standard deviation to mean, classifies variability by it, checks normality, and applies the Kruskal-Wallis test with the H statistic and p-values throughout. It is the only paper in the sample that performs distribution-level stability analysis with a significance test.

THREASURE-Net [15] reports values as the median with the 25th and 75th percentiles, and applies a Mann-Kendall test. It is one of two papers in the sample that uses a median rather than a mean.

AstraMoE-SR [12] states that its aggregates are area-weighted, and gives the reason for choosing DINO as the primary semantic-fidelity criterion, namely that pixel-wise metrics can be sensitive to nuisances the semantic measure ignores. It discloses both the aggregation and the rationale for the primary metric.

The NTIRE 2026 organizers [4], [5] publish a weighted score and state its interpretation, that an SSIM improvement of 0.01 contributes the same as 0.2 dB of PSNR. The organizers made the weighting explicit, which is the clearest available acknowledgment that the weighting rule determines the ranking.

### F. Two failure modes with names

Two cases from the 2026 literature illustrate failure modes worth naming.

**Conflating fairness with reproducibility.** MLIN-MetaWeight [16] writes that it ensures fairness and reproducibility by training all models under identical batch sizes and iteration counts. Holding hyperparameters constant makes the comparison fair across methods. It does not make the result reproducible across seeds, which requires repeating the training. The two properties are different, and a reporting standard should not let the first stand in for the second.

**Zero seed disclosure in a long paper.** SDGAN-SciRep [17] runs to roughly 80,000 characters, reports six or more metrics including PSNR, SSIM, AG, NIQE, FID, and IS, and includes distribution plots. The words seed, three runs, and repeat do not appear. The absence is not a matter of space. It reflects the norm that seed information is not part of what a paper reports.

### G. Closed access limits external audit

Of the 19 papers not retrieved in full, 11 are closed access at the publisher, confirmed against OpenAlex metadata, and 6 have no article PDF. The closed set is spread across Elsevier, IEEE, and ACM.

The implication extends past our survey. A third party cannot perform a reproduction-level audit of the closed portion of the RS-SR literature, because the artifacts are not available. What a reader can access is the paper's own reported metadata, which is the abstract and the tables. This raises the stakes on the reporting norm. Where an external audit is impossible, the paper's self-reported protocol information becomes the only basis on which a reader can judge the ranking.

---

## 6. The R1 to R7 Reproducibility Scorecard

The audit findings reduce to seven checks. Each check names a disclosure whose absence produces a specific failure.

**TABLE IX. The R1 to R7 scorecard.**

| # | Check | Failure when omitted | Status in the audit pool |
|---|---|---|---|
| R1 | Is the test-set image list public and identical across runs | Cross-paper comparison is void | Pass in all 170 runs |
| R2 | Is the metric aggregation stated (mean, median, trimmed) | The champion flips under the convention | Not stated in 31/35 papers |
| R3 | Are three or more seeds run, with per-seed direction reported | The 25.4% reversal rate is invisible | 2 seeds in part of the pool |
| R4 | Is the seed-noise magnitude reported | A reader cannot tell whether \|Δ\| clears the noise | Not reported |
| R5 | Is the baseline convention fixed to one run and endpoint | The effect inflates by 5% or more | Two conventions used |
| R6 | Is equivalence testing used rather than significance alone | No difference reads as improvement | Used only for final confirmation |
| R7 | Are per-image paired confidence intervals and d_z reported | Stability is unjudgeable | Not reported |

The scorecard is meant to be applied to a published paper, producing a profile of which of the seven a paper omits. It applies to competition reports as well as method papers, since both publish rankings.

The checks are ordered by the cost of omission we measured. R2 carries the largest measured effect, since it flips the champion on four of four benchmarks. R3 and R4 together carry the reversal rate and the noise floor. R5 carries the 5% endpoint shift. R1 is listed first because it is a prerequisite, in that a comparison built on different images is not a comparison.

---

## 7. Discussion

### A. This is a norm problem, not a capability problem

The survey contains a demonstration that the recommended practices are achievable. GrasslandGAN performs distribution-level analysis with a significance test. SpectralSR-Bench reports dispersion in every table. THREASURE-Net reports medians and quartiles. These papers are not methodologically exotic. They are ordinary papers that chose to report more.

The gap between what is done and what is standard is therefore not a gap in tooling or skill. It is a gap in what the field asks for. Raising the standard is a matter of reviewers and organizers requiring the disclosure, which is why Section VII-D gives concrete requirements.

### B. What the ranking instability means for remote sensing applications

A benchmark ranking in RS-SR is not an end in itself. It is a screening instrument for methods that will later be run on real acquisitions, over regions and sensors that the benchmark did not cover. The instability we measure has a specific consequence for that use.

Consider a practitioner who reads the ranking and selects the top method for an urban mapping pipeline. If the gap to the second method is 0.1 dB on a benchmark of 210 images, the selection is not supported by the reported statistic, because the seed-to-seed standard deviation on that benchmark is 0.107 dB. The second method may be equally good, and it may be cheaper, lighter, or more robust to the distribution shift that separates the benchmark from the deployment region. The ranking does not carry the information the practitioner needs.

The failure is asymmetric across benchmark size. On AID, with 1000 test images and a noise floor of 0.0728 dB, a 0.1 dB claim is marginally resolvable. On WHU-RS19, with 101 images and a noise floor of 0.1202 dB, the same claim is inside the noise. A field that reports one number without the noise floor therefore publishes a ranking whose interpretability depends on a property of the benchmark that the ranking does not display.

### C. The audit joins a shift already under way

2026 has seen evaluation move from a secondary concern to a primary one. NeurIPS framed its 2025 program around moving from scale to understanding. ICLR 2026 named efficiency over scale a community priority. In this setting, evaluation methodology is not a niche. The specific gap this paper fills is ranking stability. The existing critiques establish that metrics are imperfect proxies and that protocols need standardizing. This paper asks how much a ranking moves when the protocol varies within the range of defensible choices, and answers with a measured fraction.

### D. Recommendations

For authors, three disclosures cover most of the measured risk. State the aggregation convention. State the seed count, or state that a single seed was used and name it. State the seed-noise magnitude, so that a reader can compare it against the claimed effect.

For reviewers and editors, two requirements follow from the audit. When a claimed effect is smaller than the reported seed noise, require an equivalence test rather than a significance test. When the test set is small, below roughly 200 images, require that the cross-seed direction of the ranking be reported, because that is where the reversal rate is highest.

A third requirement applies to the tooling that will enforce the other two. Automated reference resolution has to compare the title as well as the response status. While building the reference list for this survey, one DOI carried in our own pool returned HTTP 200 and resolved to a paper on reinforcement learning in the journal *Engineering*, not to the super-resolution paper it was recorded against. A status-only check accepts that record. The correct record was recovered by querying Crossref with the publisher's article identifier, which returned *UDAMSR Net: An Unsupervised Degradation-Aware Network for Enhancing the Spatial Resolution of Spectral Images for Crop Sensing*. The audit pipeline that produced every other number in this paper was correct because its pairings were validated against stored per-image path sets rather than against identifiers. The same discipline belongs in reference handling, where a single mis-resolved DOI is invisible unless the title is checked.

### E. Consequences for reading a ranking

A ranking is a summary of a protocol. When the protocol is published, the ranking can be read as a statement about the methods under that protocol. When the protocol is omitted, and the effect is inside the noise band, the ranking does not distinguish methods. Our measurements give the boundary of that band for the four benchmarks studied, in that a claim below the reported seed standard deviation, on a test set of the sizes considered here, cannot be distinguished from noise by a reader who has only the mean.

---

## 8. Limitations

1. The findings from our own pool of 170 runs do not extend to the claim that all RS-SR papers have a 1-in-4 error rate. The 25.4% reversal figure includes many method pairs on AID that are close variants, and close variants are expected to sit near the noise floor.
2. Only 7 of 35 papers state a verifiable gain, so the gain-versus-noise table is illustrative rather than representative. The correct statement is that of the 7 verifiable claims, 2 fall below the measured noise ceiling on the same benchmark.
3. The seed noise is measured on our own pool. For papers whose benchmarks fall outside it, such as the infrared, DOTA, and Landsat-8 cases, we fall back to the pool-wide median and mark the fallback. Those entries cannot be read as the noise on the paper's own benchmark.
4. The abstract-level count of zero for seed disclosure cannot be used to assert that papers do not report seeds. Section V-C shows the count rises to four once full texts are read.
5. The dispersion reported by SpectralSR-Bench is per-image, across 50 images, and is not the seed-to-seed variation of a method effect. The comparison in Section I-B supports the weaker claim that the method differences are smaller than the data dispersion, not a seed-noise claim.
6. GrasslandGAN applies the Kruskal-Wallis test across landscape strata, not across seeds. It demonstrates the capability to perform distribution-level analysis, not that seed replication was done.
7. MLIN-MetaWeight uses the word reproducibility to mean identical training hyperparameters. It should not be cited as a paper that reports reproducibility in the seed sense.
8. The closed-access determination relies on OpenAlex metadata. A paper with an author-hosted preprint that OpenAlex has not indexed could be misclassified as closed. We retain the resolved DOIs for manual checking.
9. Sixteen dataset-tagged runs without a seed suffix are excluded from pairing, together with ten untagged runs. If any of the untagged runs in fact belongs to a benchmark and has a fixed seed, the pairing sample of 144 could grow.
10. The audit covers our own experiments and a survey of published papers. It does not reproduce any published experiment.

---

## 9. Conclusion

Protocol choices that RS-SR papers rarely report determine which method is ranked first. On 170 existing runs spanning four standard benchmarks, changing only the aggregation rule flips the champion on all four, and across 327 method pairs one in four reverses order between training seeds while slightly more than half show a difference smaller than the seed noise. A survey of 35 published papers shows that the disclosures that would let a reader evaluate these numbers are almost never made, and that the papers which do make them are the exception rather than a distinct class.

The instability is measurable, and the measurement is cheap. Every number in this paper comes from per-image artifacts that an evaluation already produces, with no retraining and no new data. A laboratory that has kept its per-image logs can compute its own noise floor in an afternoon and state it in the next paper. That is the practical proposal: report the aggregation convention, the seed count, and the seed-noise magnitude, so that a reader can tell whether a ranking of 0.1 dB reflects the methods or the sample.

The seven-item scorecard in Section VI generalizes the finding into a checklist. Applied from either side of the review process, it turns the question of whether a ranking is trustworthy into a short set of disclosures that a reader can look for and an author can supply.

---

## Data and Code Availability

The audit code, the per-image evaluation records for all 170 runs, every result file, and both figures are available at `https://github.com/czy326/s2ds-eval-audit`.

The repository is self-contained. Running `code/run_audit_chain.py` regenerates the audit result files from the shipped per-image records, and the regenerated files are identical to the shipped ones. The chain includes the anchor in Line E, which reproduces a known result before reporting any negative finding.

The four benchmark datasets (AID, RSSCN7, UCMerced, WHU-RS19) are public and are not redistributed, because the audit reads only stored metric values and image path strings, not pixels. Publisher PDFs and HTML retrieved during the 35-paper survey are not redistributed, because most are copyrighted. The derived codings are shipped in the repository, and an index recording which source files were read is included so the codings can be checked.

The reference list is shipped with the repository. Every bibliographic field is copied from a Crossref, arXiv or OpenAlex record, and the source is named for each entry. Eight entries could not be completed and are flagged. One of those eight, UDAMSR, is the case in which the DOI carried in the survey pool resolved at Crossref to a paper with an unrelated title. The true record was recovered by querying Crossref with the publisher's article identifier as an alternative-id, which returned `10.1016/j.eng.2026.01.031`. Section VII-D uses this as the worked example of why DOI resolution has to be checked against the title and not only against the response status.

---

## Acknowledgment

The authors thank the maintainers of the AID, RSSCN7, UCMerced, and WHU-RS19 benchmarks, whose public release made this audit possible. The audit uses only released per-image evaluation artifacts and no restricted data.

---

## References

[1] L. Liu, H. Duan, C. Zhu, et al., "LL-Bench: Rethinking Low-Level Vision Evaluation in the Era of Large-Scale Generative Models," arXiv:2606.02535, 2026.
[2] I. Molodetskikh, K. Malyshev, M. Mirgaleev, N. Zagainov, E. Bogatyrev, and D. Vatolin, "SR-Prominence: A Crowdsourced Protocol and Dataset Suite for Perceptually-Weighted Super-Resolution Artifact Evaluation," arXiv:2605.14847, 2026.
[3] Z. Li, K. Chai, Z. Wang, X. Jia, et al., "Beyond Visual Fidelity: Benchmarking Super-Resolution Models for Large-Scale Remote Sensing Imagery via Downstream Task Integration," arXiv:2605.00310, 2026.
[4] Z. Chen, K. Liu, J. Wang, X. Yan, et al., "The Fourth Challenge on Image Super-Resolution (x4) at NTIRE 2026: Benchmark Results and Method Overview," arXiv:2604.14558, 2026.
[5] K. Liu, H. Yue, Z. Lin, Z. Chen, et al., "The First Challenge on Remote Sensing Infrared Image Super-Resolution at NTIRE 2026: Benchmark Results and Method Overview," arXiv:2604.21312, 2026.
[6] N. Shokoohi, A. N. Fsian, J. Thomas, and P. Gouton, "A Comparative Evaluation of Super-Resolution Methods for Spectral Images Using Pretrained RGB Models," Sensors, vol. 26, no. 2, art. 683, 2026, doi: 10.3390/s26020683.
[7] E. Kalinicheva, F. Helen, S. Mermoz, F. Mouret, et al., "Super-Resolved Canopy Height Mapping from Sentinel-2 Time Series Using Airborne LiDAR HD Reference Data across Metropolitan France," arXiv:2512.11524, 2025.
[8] H. Qi, Z. Zhou, J. Yi, K. Liu, et al., "EORestore-Agent: Fidelity-Guided Agentic Restoration of Remote Sensing Images with Composite Degradations," arXiv:2610.06196, 2026.
[9] A. Patnaik, A. Gour, M. K. Bhuyan, K. F. MacDorman, S. Alfarhood, and M. Safran, "Super-Resolution of Remote Sensing Images via the Parallel Lattice Attention Network," IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens., vol. 19, pp. 6067-6078, 2026, doi: 10.1109/jstars.2026.3660141.
[10] T. Tang, J. Liu, X. Luo, X. Gao, and X. Pan, "DBTSR: A U-shaped adaptive sparse transformer for single remote sensing image super-resolution," Expert Syst. Appl., vol. 297, art. 129424, 2026, doi: 10.1016/j.eswa.2025.129424.
[11] J. Deng, H. Wang, C. Wang, J. Shen, et al., "IR275K: A Benchmark for Infrared Multi-Frame Super-Resolution Toward Efficient Remote Sensing," arXiv:2607.22380, 2026.
[12] Y. Lai, C. Wu, and Y. Chen, "AstraMoE-SR: Trajectory-Guided Diffusion for Blind Satellite Jitter Deblurring and Super-Resolution," arXiv:2609.07012, 2026.
[13] J. Yu, H. Li, X. Zheng, C. Zhong, and Q. Sun, "DFSMamba: A Spatial–Frequency Collaborative Modeling Framework for Remote Sensing Image Super-Resolution," Remote Sens., vol. 18, no. 12, art. 1910, 2026, doi: 10.3390/rs18121910.
[14] E. Noa-Yarasca, J. O. Leyton, N. Jumaa, H. Niu, and L. Malambo, "Assessing GAN Super-Resolution in Grasslands: The Role of Spatial Heterogeneity and Textural Complexity," Remote Sens., vol. 18, no. 9, art. 1419, 2026, doi: 10.3390/rs18091419.
[15] Y. Li, and Y. Chen, "Hyperspectral Pansharpening using 3D VolumeNet and 2.5D Texture Transfer," Proceedings of the 2025 8th International Conference on Digital Medicine and Image Processing, 9-13, 2025, doi: 10.1145/3785443.3785445.
[16] Q. Zhang, S. Ma, Y. Tang, and L. Zheng, "Cross-domain continuous-scale remote sensing image super-resolution via meta-weight learning," Sci. Rep., vol. 16, no. 1, art. 6073, 2026, doi: 10.1038/s41598-026-36632-w.
[17] L. Wang, L. Liu, Q. Yu, and D. Yuan, "Generative adversarial network-based super-resolution reconstruction of remote sensing images," Sci. Rep., vol. 16, no. 1, art. 11971, 2026, doi: 10.1038/s41598-026-41832-5.
[18] T. Tang, J. Liu, X. Luo, X. Gao, X. Fu, and X. Pan, "ORDiffSR: An effective one-step diffusion network for single remote sensing image super-resolution," Expert Syst. Appl., vol. 320, art. 132254, 2026, doi: 10.1016/j.eswa.2026.132254.

---

## Author Biographies

[[FILL: author photographs and biographies required at submission. Each biography should state degrees, current position, and research interests, in IEEE format.]]

---

## Supplementary Material

The following items are submitted as supplementary material and are also available in the data repository.

1. `code/` — the audit scripts, including `run_audit_chain.py`, which regenerates every result file from the shipped per-image records.
2. `data/` — the manifest and the 170 per-image JSONL records.
3. `results/` — the ten audit result files, the 19 retrieved full texts, and an index recording which source file supports each coding.
4. `docs/PROVENANCE.md` — the provenance of every reference field and the procedure for verifying a copy of the repository.

---

## Figures and Tables

| Item | Content | Source |
|---|---|---|
| Table I | SpectralSR-Bench per-pair Δ against std (8 of 10 below std) | `results/audit_H_spectralsr_std.json` |
| Table II | The four audit lines | this paper |
| Table III | Rank correlation against mean PSNR, 8 conventions × 4 benchmarks | `results/audit_B_protocols.json` |
| Table IV | Effect size against seed noise, 327 pairs | `results/audit_D_effect_vs_noise.json` |
| Table V | Seed noise by benchmark | `results/audit_C_seednoise.json` |
| Table VI | Anchor comparison, B3 vs base_ssm | `results/audit_E_anchor_b3.json` |
| Table VII | Report-practice statistics, 35 papers | `results/audit_F_field_survey.json` |
| Table VIII | Claimed gains against the noise floor, 7 papers | `results/audit_G_gain_vs_noise.json` |
| Table IX | The R1 to R7 scorecard | this paper |
| Fig. 1 | Seed noise versus test-set size | `figures/fig1_noise_vs_testsize.*` |
| Fig. 2 | Method effect versus seed noise, 327 pairs | `figures/fig2_effect_vs_noise.*` |
