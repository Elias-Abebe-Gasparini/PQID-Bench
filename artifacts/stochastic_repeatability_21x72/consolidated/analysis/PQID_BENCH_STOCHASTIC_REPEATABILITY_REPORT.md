# PQID-Bench Stochastic Repeatability Audit

Run 1 is the frozen canonical benchmark output. Runs 2 and 3 are two new
single-generation invocations on an outcome-blind, signature-unique 72-prompt
panel. The provider route, model identifier, provider request body, evaluator,
and target are held fixed. Runs 2--3 estimate short-window API repeatability;
Run 1 comparisons additionally include temporal deployment drift.
Stored request hashes are identical across all three runs for all `1512` model-prompt pairs.
The frozen panel hash and report target metadata are verified for all `4536` scored cells.
Canonical completeness: expected `4536` cells; observed `4536`; missing `0`; duplicate keys `0`; unexpected keys `0`; request-hash mismatches `0`; target-metadata mismatches `0`.

The scored endpoint is the nonredundant predicate
`M = Q AND K AND T`, where each component is execution-gated and `T` is complete operation-type count-map equality.
Scalar gate-count agreement `G` remains a diagnostic; the analyzer asserts the
frozen count-map invariant `T => G` for every evaluated output.
Historical artifact fields `gate_types`, `gate_type_bin`, and `gate_entropy` encode
the evaluator-visible operation vocabulary, including barriers and measurements.

## Sequential Replication Comparison

The original and confirmatory halves are signature-disjoint; the confirmatory panel was frozen before transmission.
Full-panel entries give Runs 1/2/3. Common-cell ranges and agreement use one denominator with no recorded transport disturbance in any run within each evidence layer.
Agreement is the mean of the three pairwise equality rates (Runs 1--2, 1--3, and 2--3) on that same common set; it is distinct from unanimous three-run agreement.

| evidence layer | full execution R1/R2/R3 | full signature R1/R2/R3 | full ES-Gap R1/R2/R3 (pp) | common cells/run | common execution range | common signature range | common ES-Gap range (pp) | execution agreement | signature agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original 36 | 91.27%/79.37%/80.29% | 51.85%/43.65%/45.63% | 39.42 pp/35.71 pp/34.66 pp | 578 | 92.56%--93.25% | 52.08%--53.29% | 39.62--41.00 pp | 94.93% | 95.85% |
| confirmatory 36 | 91.93%/81.48%/79.37% | 50.53%/46.03%/44.71% | 41.40 pp/35.45 pp/34.66 pp | 544 | 95.04%--95.96% | 54.41%--55.15% | 40.44--40.81 pp | 96.69% | 96.20% |
| pooled 72 | 91.60%/80.42%/79.83% | 51.19%/44.84%/45.17% | 40.41 pp/35.58 pp/34.66 pp | 1122 | 93.76%--94.56% | 53.57%--54.19% | 40.11--40.73 pp | 95.78% | 96.02% |

| evidence layer | 1--2 types, R1/R2/R3 | 3--4 types, R1/R2/R3 | 5+ types, R1/R2/R3 |
| --- | ---: | ---: | ---: |
| original 36 | 76.59%/63.89%/66.27% | 58.33%/47.62%/50.79% | 20.63%/19.44%/19.84% |
| confirmatory 36 | 68.65%/61.51%/59.13% | 62.30%/57.54%/55.16% | 20.63%/19.05%/19.84% |
| pooled 72 | 72.62%/62.70%/62.70% | 60.32%/52.58%/52.98% | 20.63%/19.25%/19.84% |

## Panel-Unweighted Outcomes

Crossed intervals independently resample the 21 model rows and 72 prompt signatures.

| run | cells | execution (95% CI) | signature match (95% CI) | ES-Gap (95% CI; pp) | wrong signature given execution | provider errors |
| ---: | ---: | --- | --- | --- | ---: | ---: |
| 1 | 1512 | 91.60% [86.24%, 95.83%] | 51.19% [41.00%, 61.24%] | 40.41 pp [31.68, 49.47] pp | 44.12% | 0 |
| 2 | 1512 | 80.42% [67.26%, 91.20%] | 44.84% [34.19%, 55.89%] | 35.58 pp [26.65, 44.91] pp | 44.24% | 211 |
| 3 | 1512 | 79.83% [66.27%, 91.01%] | 45.17% [34.13%, 56.68%] | 34.66 pp [25.60, 43.98] pp | 43.41% | 221 |

## Secondary Operation-Type-Bin-Standardized Panel Outcomes

These sensitivities weight only the panel's three operation-diversity bands to the
full 154-prompt frequencies (`42/154`, `85/154`, and `27/154`). They neither
correct the panel's signature uniqueness, identifiability exclusions, cohort
balance, or barrier balance nor estimate an unbiased full-population rate.
They do not replace the prespecified balanced-panel analysis.

| run | execution (95% CI) | signature match (95% CI) | ES-Gap (95% CI; pp) |
| ---: | --- | --- | --- |
| 1 | 92.32% [87.22%, 96.35%] | 56.72% [46.45%, 66.29%] | 35.60 pp [26.73, 45.00] pp |
| 2 | 81.11% [68.72%, 91.56%] | 49.49% [37.97%, 60.63%] | 31.62 pp [22.93, 41.31] pp |
| 3 | 80.33% [67.57%, 91.10%] | 49.82% [38.40%, 61.23%] | 30.51 pp [21.72, 40.47] pp |

## Difficulty-Gradient Reproducibility

Rates below retain the balanced panel denominator and show whether the
prespecified cohort, operation-diversity, and barrier contrasts point in the same
direction across all three draws.

| stratum | level | execution runs 1 / 2 / 3 | signature runs 1 / 2 / 3 | ES-Gap runs 1 / 2 / 3 (pp) |
| --- | --- | --- | --- | --- |
| cohort | pilot | 94.31% / 82.80% / 82.41% | 53.44% / 45.24% / 46.16% | 40.87 pp / 37.57 pp / 36.24 pp |
| cohort | extension | 88.89% / 78.04% / 77.25% | 48.94% / 44.44% / 44.18% | 39.95 pp / 33.60 pp / 33.07 pp |
| gate_type_bin | 1-2 | 96.43% / 83.93% / 82.94% | 72.62% / 62.70% / 62.70% | 23.81 pp / 21.23 pp / 20.24 pp |
| gate_type_bin | 3-4 | 92.26% / 81.35% / 80.36% | 60.32% / 52.58% / 52.98% | 31.94 pp / 28.77 pp / 27.38 pp |
| gate_type_bin | 5+ | 86.11% / 75.99% / 76.19% | 20.63% / 19.25% / 19.84% | 65.48 pp / 56.75 pp / 56.35 pp |
| has_barrier | false | 92.80% / 80.40% / 80.29% | 62.90% / 54.60% / 54.15% | 29.90 pp / 25.80 pp / 26.14 pp |
| has_barrier | true | 89.82% / 80.46% / 79.15% | 33.83% / 30.38% / 31.86% | 55.99 pp / 50.08 pp / 47.29 pp |

## Primary Run-Effect Inference

Each endpoint uses a linear-probability run-effect model with model and prompt
fixed effects. Crossed model-prompt bootstrap intervals are primary;
Cameron--Gelbach--Miller two-way clustered covariance is retained as a
sensitivity. This parameterization directly estimates the prespecified
percentage-point run-rate differences and avoids separation at high execution
prevalence. The empirical joint crossed-bootstrap test assesses whether both
later-run effects are zero and remains defined under singular covariance.

| endpoint | contrast | delta pp (crossed 95% CI) | crossed p | joint run-effect p |
| --- | --- | --- | ---: | ---: |
| Execution | run 2 vs run 1 | -11.18 [-22.42, -2.51] | 0.02819 | 0.02739 |
| Execution | run 3 vs run 1 | -11.77 [-23.41, -2.58] | 0.02759 |  |
| Execution | run 3 vs run 2 | -0.60 [-3.64, +2.05] | 0.6623 |  |
| Reference-signature match | run 2 vs run 1 | -6.35 [-12.50, -1.52] | 0.02759 | 0.03079 |
| Reference-signature match | run 3 vs run 1 | -6.02 [-12.37, -0.99] | 0.04059 |  |
| Reference-signature match | run 3 vs run 2 | +0.33 [-2.12, +2.65] | 0.771 |  |
| Executable reference-signature disagreement | run 2 vs run 1 | -4.83 [-11.11, +0.07] | 0.08458 | 0.05659 |
| Executable reference-signature disagreement | run 3 vs run 1 | -5.75 [-11.84, -0.73] | 0.04239 |  |
| Executable reference-signature disagreement | run 3 vs run 2 | -0.93 [-3.57, +1.52] | 0.4639 |  |

## Three-Run Endpoint Repeatability

Crossed intervals are primary. Prompt-cluster intervals with the model roster
held fixed are retained in the JSON artifact. Cochran's Q is descriptive only
because its ordinary independence assumption does not match the crossed matrix.

| endpoint | items | unanimous | any flip (crossed 95% CI) | Gwet AC1 (crossed 95% CI) | descriptive Cochran Q p |
| --- | ---: | ---: | ---: | ---: | ---: |
| Execution | 1512 | 78.64% | 21.36% [10.98%, 33.86%] | 0.805 [0.639, 0.914] | 2.779e-41 |
| Reference-signature match | 1512 | 86.11% | 13.89% [8.07%, 20.83%] | 0.815 [0.727, 0.895] | 7.615e-19 |
| Executable reference-signature disagreement | 1512 | 84.33% | 15.67% [9.85%, 22.35%] | 0.804 [0.720, 0.880] | 1.007e-12 |
| QASM3 export | 1512 | 78.31% | 21.69% [11.90%, 33.40%] | 0.800 [0.641, 0.904] | 1.075e-39 |

## Pairwise Agreement And Directional Churn

The 2--3 comparison is the short-window contrast. Comparisons involving Run 1
also contain temporal deployment variation.

| endpoint | runs | agreement (crossed 95% CI) | Gwet AC1 (crossed 95% CI) | loss | gain | total flip | delta (pp; crossed 95% CI) | exact McNemar Holm p* |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| Execution | 1-2 | 84.59% [73.54%, 93.19%] | 0.797 [0.604, 0.920] | 13.29% | 2.12% | 15.41% | -11.18 [-22.42, -2.51] | 7.988e-31 |
| Execution | 1-3 | 83.20% [71.89%, 92.26%] | 0.778 [0.576, 0.908] | 14.29% | 2.51% | 16.80% | -11.77 [-23.41, -2.58] | 6.292e-31 |
| Execution | 2-3 | 89.48% [83.47%, 94.78%] | 0.846 [0.726, 0.932] | 5.56% | 4.96% | 10.52% | -0.60 [-3.64, +2.05] | 0.5259 |
| Reference-signature match | 1-2 | 89.68% [83.73%, 94.58%] | 0.794 [0.678, 0.893] | 8.33% | 1.98% | 10.32% | -6.35 [-12.50, -1.52] | 1.017e-14 |
| Reference-signature match | 1-3 | 90.15% [84.13%, 95.11%] | 0.803 [0.686, 0.903] | 7.94% | 1.92% | 9.85% | -6.02 [-12.37, -0.99] | 4.728e-14 |
| Reference-signature match | 2-3 | 92.39% [88.43%, 95.70%] | 0.849 [0.773, 0.916] | 3.64% | 3.97% | 7.61% | +0.33 [-2.12, +2.65] | 0.7093 |
| Executable reference-signature disagreement | 1-2 | 88.56% [82.67%, 93.52%] | 0.784 [0.675, 0.878] | 8.13% | 3.31% | 11.44% | -4.83 [-11.11, +0.07] | 5.53e-08 |
| Executable reference-signature disagreement | 1-3 | 88.69% [82.74%, 93.65%] | 0.787 [0.673, 0.881] | 8.53% | 2.78% | 11.31% | -5.75 [-11.84, -0.73] | 5.223e-11 |
| Executable reference-signature disagreement | 2-3 | 91.40% [87.57%, 94.78%] | 0.842 [0.766, 0.909] | 4.76% | 3.84% | 8.60% | -0.93 [-3.57, +1.52] | 0.2541 |
| QASM3 export | 1-2 | 84.19% [73.15%, 92.39%] | 0.789 [0.593, 0.911] | 13.49% | 2.31% | 15.81% | -11.18 [-22.75, -2.45] | 1.012e-29 |
| QASM3 export | 1-3 | 82.80% [71.89%, 91.27%] | 0.770 [0.572, 0.897] | 14.35% | 2.84% | 17.20% | -11.51 [-23.02, -2.38] | 7.829e-29 |
| QASM3 export | 2-3 | 89.62% [83.53%, 94.64%] | 0.846 [0.732, 0.930] | 5.36% | 5.03% | 10.38% | -0.33 [-3.24, +2.25] | 0.7497 |

*The pooled exact McNemar result is a familiar paired-cell sensitivity, not
the primary crossed-dependence test. Per-model exact McNemar results are
provided as a separate CSV artifact.

## Three-Run Stability Classes

| endpoint | always 0 | always 1 | one positive run | one negative run | unanimous |
| --- | ---: | ---: | ---: | ---: | ---: |
| Execution | 80 | 1109 | 165 | 158 | 78.64% |
| Reference-signature match | 694 | 608 | 109 | 101 | 86.11% |
| Executable reference-signature disagreement | 833 | 442 | 127 | 110 | 84.33% |

## Model-Level Signature Stability

| model | run 1 | run 2 | run 3 | range (pp) | any flip | Gwet AC1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.6 Sol | 59.72% | 59.72% | 59.72% | 0.00 | 0.00% | 1.000 |
| GPT-5.5 | 58.33% | 59.72% | 59.72% | 1.39 | 1.39% | 0.982 |
| GPT-5.4 mini | 58.33% | 55.56% | 56.94% | 2.78 | 4.17% | 0.945 |
| Claude Fable 5 | 61.11% | 59.72% | 62.50% | 2.78 | 4.17% | 0.947 |
| Claude Sonnet 4.6 | 58.33% | 55.56% | 59.72% | 4.17 | 4.17% | 0.946 |
| Claude Opus 4.8 | 59.72% | 59.72% | 59.72% | 0.00 | 0.00% | 1.000 |
| Gemini 2.5 Pro | 51.39% | 47.22% | 50.00% | 4.17 | 12.50% | 0.833 |
| Gemini 3.1 Pro Preview | 58.33% | 58.33% | 58.33% | 0.00 | 0.00% | 1.000 |
| DeepSeek V4 Pro | 55.56% | 52.78% | 55.56% | 2.78 | 13.89% | 0.816 |
| DeepSeek V4 Flash | 48.61% | 54.17% | 54.17% | 5.56 | 13.89% | 0.815 |
| Codestral 25.01 | 51.39% | 47.22% | 51.39% | 4.17 | 4.17% | 0.944 |
| Qwen3-Coder-Next | 47.22% | 51.39% | 51.39% | 4.17 | 6.94% | 0.907 |
| Llama 4 Maverick | 50.00% | 31.94% | 34.72% | 18.06 | 29.17% | 0.629 |
| Llama 3.3 70B | 48.61% | 43.06% | 47.22% | 5.56 | 11.11% | 0.853 |
| GPT-OSS 120B | 54.17% | 41.67% | 34.72% | 19.44 | 27.78% | 0.636 |
| GPT-OSS 20B | 45.83% | 31.94% | 30.56% | 15.28 | 36.11% | 0.553 |
| Mistral Small 3.2 24B | 50.00% | 48.61% | 48.61% | 1.39 | 8.33% | 0.889 |
| Qiskit Mistral 3.2 24B | 47.22% | 0.00% | 0.00% | 47.22 | 47.22% | 0.572 |
| Qwen3 32B | 33.33% | 9.72% | 9.72% | 23.61 | 36.11% | 0.661 |
| Llama 4 Scout | 43.06% | 47.22% | 44.44% | 4.17 | 12.50% | 0.835 |
| Llama 3.1 8B | 34.72% | 26.39% | 19.44% | 15.28 | 18.06% | 0.802 |

## Deployment-Level Model-Ordering Stability

Exact ranks move in 1.39-point increments on 72 prompts, so the audit reports
rank correlations and tie-inclusive top-five overlap rather than treating every
one-position change as substantive.
These raw ranks retain provider failures and therefore describe deployment-level ordering, not a capability ranking on the common no-recorded-disturbance subset.

| runs | Spearman rho | Kendall tau-b | top-five Jaccard | frontier mean first -> second |
| --- | ---: | ---: | ---: | --- |
| 1-2 | 0.838 | 0.688 | 0.714 | 56.94% -> 56.25% |
| 1-3 | 0.874 | 0.743 | 0.714 | 56.94% -> 57.64% |
| 2-3 | 0.977 | 0.918 | 0.667 | 56.25% -> 57.64% |

## Ranking And Majority-Vote Sensitivities

- Majority-vote signature rate: `46.89%`; change from run 1: `-4.30` percentage points.
- Majority-vote ES-Gap, derived as `E^maj - M^maj`: `36.90 pp`.
- Direct majority vote over the three runwise `R` indicators (diagnostic): `36.51%`.
- Majority-vote versus run-1 model-rank Spearman correlation: `0.890`.
- Majority vote is a three-query deployment sensitivity, not a replacement for the canonical single-draw score.

## Generated-Code Reproducibility

- Formatting-normalized text equality across all three runs: `32.56%` among `1210` complete cells.
- Normalized-text pairwise equality (1--2 / 1--3 / 2--3): `40.61%` (`n=1283`) / `42.41%` (`n=1271`) / `44.12%` (`n=1215`).
- Canonical Python-AST equality across all three runs: `40.82%` among `1166` parseable complete cells.
- Canonical-AST pairwise equality (1--2 / 1--3 / 2--3): `50.16%` (`n=1224`) / `52.19%` (`n=1209`) / `52.56%` (`n=1174`).
- AST parse successes: `3803 / 4536` outputs.
- Neither normalization renames identifiers or reorders statements; AST equality remains stricter than functional equivalence.

## Provider-Attempt Audit

| run | trials | trace covered | recorded attempts | first-attempt success | recovered | terminal errors | known transport affected |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1512 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1512 | 648 | 968 | 471 | 75 | 211 | 286 |
| 3 | 1512 | 1296 | 1926 | 954 | 121 | 221 | 342 |

### Common No-Recorded-Disturbance Complete-Cell Sensitivity

This secondary analysis retains only model--prompt pairs with no recorded
transport disturbance in any of the three runs, giving one common denominator
of `1122` cells per run. It separates known endpoint
availability failures from outcome variation, but untraced legacy and batch
rows cannot be certified as first-attempt clean.

| run | cells | execution | signature match | ES-Gap (pp) | wrong signature given execution |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1122 | 93.76% | 53.65% | 40.11 pp | 42.78% |
| 2 | 1122 | 94.30% | 53.57% | 40.73 pp | 43.19% |
| 3 | 1122 | 94.56% | 54.19% | 40.37 pp | 42.70% |

Complete-cell three-run repeatability: execution agreement `95.78%` (Gwet AC1 `0.953`); signature agreement `96.02%` (Gwet AC1 `0.921`).

Direct-route trials permit at most three transport attempts with 1 s and 2 s
local backoff. Retry is allowed only before a valid provider response exists.
Refusal, truncation, empty generation, execution failure, and signature failure
are never retry triggers. The first valid response is canonical; no best-of-n
selection occurs. OpenAI Batch items are submitted once and retain the provider-
managed batch lifecycle rather than receiving local response-level retries.
The common no-recorded-disturbance sensitivity excludes any trial with a known
transport disturbance and does not replace the full analysis. Legacy or batch
rows without local attempt traces remain explicitly identifiable as untraced.

## Interpretation Boundary

This is a repeatability audit under fixed deployed endpoints, not a claim that
hosted model snapshots are permanently reproducible. High endpoint agreement
supports the stability of the benchmark conclusions under repeated decoding;
observed flips quantify deployment and decoding variability that must remain in
the uncertainty budget. Crossed intervals condition on the three observed run
occasions: they generalize over the audited model and prompt dimensions, not over
an unobserved population of future API dates or common deployment shocks. The
audit does not identify a causal source of a flip.

## Artifacts

- Cell outcomes: `artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_cell_outcomes.csv`
- Model summary: `artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_model_summary.csv`
- Per-model McNemar sensitivity: `artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_per_model_mcnemar.csv`
- File manifest: `artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_file_manifest.json`
- Figure: `artifacts/stochastic_repeatability_21x72/consolidated/analysis/pqid_bench_stochastic_repeatability_panel.svg`
