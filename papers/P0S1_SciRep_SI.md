# Supplementary information
<!-- Supplementary tables for the Scientific Reports submission. -->
## Supplementary tables

Tables S1 to S3 carry the supporting audit detail that would take the main text past the eight-display-item limit.

**TABLE S1. The four audit lines.**

| Line | Question | Criterion |
|---|---|---|
| **A** per-image consistency | Is the same test set literally the same images | Exact path-set comparison and Jaccard index per benchmark |
| **B** convention sensitivity | Does the ranking or the champion change when the metric or aggregation changes | Eight conventions, Spearman rank correlation against mean PSNR, and top-1 agreement |
| **C/D** effect versus noise | Which is larger, the method effect or the seed-to-seed fluctuation | Seed-to-seed standard deviation of paired ΔPSNR, and the sign-reversal rate |
| **E** anchor | Is the audit pipeline itself correct | Reproduce a known result and compare to the published numbers digit by digit |

**TABLE S2. Seed noise by benchmark.**

| Benchmark | Test images | Median sd (dB) | Max sd (dB) | Reversal rate |
|---|---|---|---|---|
| AID | 1000 | 0.0728 | 0.1187 | 30.0% |
| RSSCN7 | 281 | 0.0632 | 0.1169 | 15.4% |
| UCMerced | 210 | 0.1070 | 0.1701 | 17.6% |
| WHU-RS19 | 101 | 0.1202 | 0.2485 | 47.3% |

**TABLE S3. Anchor comparison.**

| Comparison | This audit | Published | Agreement |
|---|---|---|---|
| B3 vs base_ssm, primary convention | +0.0849 / +0.1272 / +0.0744 dB | same | digit for digit |
| B3 vs base_ssm, legacy convention | +0.1015 / +0.1193 / +0.0804 dB | same | digit for digit |
| Difference attributable to the baseline convention alone | **0.0049 dB** | — | — |

