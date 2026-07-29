# PQID-Bench Cluster-Aware Inferential Analysis

## Analysis Contract

- held-out prompts: `154`
- unique evaluator-facing signatures: `144`
- completed model rows: `19`
- prompt-model outcomes: `2926`
- estimand: adjusted associations and paired contrasts for the fixed observed model panel
- uncertainty unit: evaluator-facing target-signature cluster
- causal interpretation: not supported

The task-feature logistic models use each prompt's number of successes over the fixed 19-model panel. Continuous circuit descriptors are standardized over prompts, and percentile intervals come from resampling complete target-signature clusters. The primary entropy model does not include gate-type count; a parallel sensitivity model replaces entropy with gate-type count to avoid treating correlated diversity descriptors as independent causes.

## Adjusted Logistic Associations

All grouped-binomial point fits converged. Across the five analyses, `10,000` / `10,000` target-signature bootstrap refits converged.

| outcome / analysis | descriptor | adjusted OR | cluster-bootstrap 95% CI | average marginal effect | cluster-bootstrap 95% CI |
| --- | --- | ---: | ---: | ---: | ---: |
| signature match, entropy model | gate entropy (per SD) | 0.49 | [0.28, 0.71] | -14.21 pp | [-23.49, -6.83] pp |
| signature match, entropy model | log gate count (per SD) | 1.06 | [0.71, 2.29] | +1.07 pp | [-6.58, +15.80] pp |
| signature match, entropy model | qubits (per SD) | 0.93 | [0.57, 1.32] | -1.41 pp | [-10.75, +5.33] pp |
| signature match, entropy model | classical bits (per SD) | 0.77 | [0.48, 1.09] | -5.25 pp | [-13.91, +1.60] pp |
| signature match, entropy model | barrier present | 0.33 | [0.16, 0.63] | -24.48 pp | [-37.98, -9.91] pp |
| signature match, gate-type model | gate-type count (per SD) | 0.34 | [0.15, 0.56] | -21.11 pp | [-35.10, -11.29] pp |
| signature match, gate-type model | log gate count (per SD) | 1.23 | [0.81, 2.92] | +4.14 pp | [-3.98, +20.08] pp |
| signature match, gate-type model | qubits (per SD) | 0.97 | [0.61, 1.34] | -0.68 pp | [-9.32, +5.59] pp |
| signature match, gate-type model | classical bits (per SD) | 0.75 | [0.48, 1.08] | -5.51 pp | [-14.14, +1.41] pp |
| signature match, gate-type model | barrier present | 0.35 | [0.17, 0.72] | -22.99 pp | [-37.33, -6.92] pp |
| execution, entropy model | gate entropy (per SD) | 0.66 | [0.46, 0.92] | -3.18 pp | [-6.12, -0.64] pp |
| execution, entropy model | barrier present | 1.11 | [0.70, 1.84] | +0.76 pp | [-2.78, +4.45] pp |
| signature match given execution | gate entropy (per SD) | 0.49 | [0.25, 0.74] | -13.47 pp | [-23.97, -5.68] pp |
| signature match given execution | barrier present | 0.29 | [0.14, 0.59] | -26.98 pp | [-41.28, -10.88] pp |
| signature match, identifiable 150 | gate entropy (per SD) | 0.40 | [0.25, 0.61] | -17.80 pp | [-25.50, -9.78] pp |
| signature match, identifiable 150 | barrier present | 0.37 | [0.19, 0.71] | -21.49 pp | [-36.06, -7.11] pp |

## Execution Versus Conditional Fidelity

| descriptor | conditional-signature AME minus execution AME | cluster-bootstrap 95% CI |
| --- | ---: | ---: |
| gate entropy (per SD) | -10.29 pp | [-21.11, -2.13] pp |
| barrier present | -27.75 pp | [-42.79, -11.25] pp |

## Target-Signature-Grouped Cross-Validation

Out-of-fold predictions use 10 folds grouped by target signature. Negative deltas are improvements for log loss and Brier score; positive deltas are improvements for AUC.

| model | log loss | delta vs size only (95% CI) | Brier | delta vs size only (95% CI) | AUC | delta vs size only (95% CI) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| size only | 0.6562 | -- | 0.2331 | -- | 0.638 | -- |
| size + entropy + barrier | 0.5956 | -0.0606 [-0.1140, -0.0004] | 0.2019 | -0.0312 [-0.0545, -0.0057] | 0.747 | +0.1094 [+0.0381, +0.1790] |
| size + gate types + barrier | 0.5898 | -0.0665 [-0.1198, -0.0058] | 0.2006 | -0.0325 [-0.0561, -0.0070] | 0.751 | +0.1129 [+0.0422, +0.1814] |

## Selected Paired Model Comparisons

| comparison | before -> after | paired difference | signature-cluster 95% CI | wins-losses-ties | cluster permutation p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama 8B -> 70B | 35.06% -> 46.10% | +11.04 pp | [+3.77, +18.29] pp | 26-9-119 | 0.0062 | 0.0560 |
| Llama 4 Scout -> Maverick | 44.81% -> 48.70% | +3.90 pp | [-3.90, +11.77] pp | 20-14-120 | 0.4057 | 1.0000 |
| GPT-OSS 20B -> 120B | 50.65% -> 53.25% | +2.60 pp | [-2.60, +7.74] pp | 10-6-138 | 0.4526 | 1.0000 |
| Gemini 2.5 -> 3.1 | 53.90% -> 61.04% | +7.14 pp | [+1.87, +13.07] pp | 16-5-133 | 0.0260 | 0.2078 |
| Claude Sonnet -> Opus | 59.09% -> 59.74% | +0.65 pp | [-2.00, +3.70] pp | 3-2-149 | 1.0000 | 1.0000 |
| Claude Opus -> Fable | 59.74% -> 62.99% | +3.25 pp | [+0.00, +6.85] pp | 6-1-147 | 0.1255 | 0.7423 |
| DeepSeek Flash -> Pro | 52.60% -> 59.09% | +6.49 pp | [+0.64, +12.74] pp | 17-7-130 | 0.0626 | 0.4382 |
| Qwen3 general -> Coder | 35.06% -> 50.65% | +15.58 pp | [+7.24, +23.75] pp | 35-11-108 | 0.0010 | 0.0098 |
| GPT-5.4 mini -> GPT-5.5 | 60.39% -> 60.39% | +0.00 pp | [-3.25, +3.23] pp | 3-3-148 | 1.0000 | 1.0000 |
| GPT-5.5 -> GPT-5.6 Sol | 60.39% -> 62.99% | +2.60 pp | [+0.63, +5.36] pp | 4-0-150 | 0.1237 | 0.7423 |

## Bootstrap Rank Stability

Mean Spearman correlation between each bootstrap ranking and the original ranking is `0.961` with a 95% interval of `[0.914, 0.989]`.

| model | score | score 95% CI | original rank | rank 95% interval | top-3 probability |
| --- | ---: | ---: | ---: | ---: | ---: |
| Claude Fable 5 | 62.99% | [54.61%, 70.91%] | 1.5 | [1.0, 4.5] | 92.40% |
| GPT-5.6 Sol | 62.99% | [54.66%, 70.99%] | 1.5 | [1.0, 3.0] | 98.48% |
| Gemini 3.1 Pro Preview | 61.04% | [52.83%, 69.08%] | 3.0 | [2.0, 6.5] | 31.24% |
| GPT-5.4 mini | 60.39% | [51.97%, 68.42%] | 4.5 | [1.5, 8.0] | 17.38% |
| GPT-5.5 | 60.39% | [51.95%, 68.46%] | 4.5 | [2.5, 8.0] | 11.64% |
| Claude Opus 4.8 | 59.74% | [51.28%, 67.95%] | 6.0 | [3.0, 9.0] | 7.16% |
| Claude Sonnet 4.6 | 59.09% | [50.65%, 67.30%] | 7.5 | [3.5, 9.0] | 1.16% |
| DeepSeek V4 Pro | 59.09% | [50.67%, 67.26%] | 7.5 | [1.5, 10.0] | 10.84% |
| Codestral 25.01 | 55.84% | [47.44%, 64.05%] | 9.0 | [6.0, 12.5] | 0.16% |
| Gemini 2.5 Pro | 53.90% | [45.34%, 62.16%] | 10.0 | [7.0, 15.0] | 0.26% |
| GPT-OSS 120B | 53.25% | [44.37%, 61.82%] | 11.0 | [8.5, 14.5] | 0.00% |
| DeepSeek V4 Flash | 52.60% | [43.87%, 60.76%] | 12.0 | [9.0, 15.0] | 0.00% |
| GPT-OSS 20B | 50.65% | [41.94%, 59.18%] | 13.5 | [10.0, 16.0] | 0.00% |
| Qwen3-Coder-Next | 50.65% | [42.21%, 58.93%] | 13.5 | [10.0, 16.0] | 0.00% |
| Llama 4 Maverick | 48.70% | [40.13%, 57.14%] | 15.0 | [11.0, 17.0] | 0.00% |
| Llama 3.3 70B | 46.10% | [37.16%, 54.84%] | 16.0 | [12.0, 17.0] | 0.00% |
| Llama 4 Scout | 44.81% | [36.55%, 53.09%] | 17.0 | [14.0, 17.0] | 0.00% |
| Llama 3.1 8B | 35.06% | [27.10%, 43.31%] | 18.5 | [18.0, 19.0] | 0.00% |
| Qwen3 32B | 35.06% | [27.56%, 42.67%] | 18.5 | [17.0, 19.0] | 0.00% |

## Main Inferential Findings

After adjustment for log gate count, qubit width, classical width, and barrier presence, one standard deviation of gate entropy is associated with OR `0.49` for reference-signature match (95% cluster-bootstrap CI `[0.28, 0.71]`) and an average marginal change of `-14.21 pp`. Barrier presence is associated with OR `0.33` and `-24.48 pp`.

The entropy association is weak for execution (OR `0.66`, 95% CI `[0.46, 0.92]`) but remains strong among outputs that execute (OR `0.49`, 95% CI `[0.25, 0.74]`). This supports the bounded interpretation that heterogeneity is primarily associated with recovering the wrong reference signature, not with failure to produce runnable code.

Adding entropy and barrier information to size controls improves grouped out-of-fold AUC by `+0.109` (95% CI `[+0.038, +0.179]`) and Brier score by `-0.0312` (95% CI `[-0.0545, -0.0057]`). The log-loss interval includes zero, so predictive improvement should be described as metric-dependent rather than universal.

After Holm correction, the selected paired improvements that remain distinguishable under target-signature permutation are: Qwen3 general -> Coder (+15.58 pp, adjusted p=0.0098). Other within-family differences are estimates with uncertainty, not confirmed ordering claims.

## Interpretation Boundary

These analyses quantify uncertainty under changes in the held-out target-signature composition and compare models on paired prompts. They do not identify causal effects of circuit descriptors or model tier. The model panel is fixed rather than randomly sampled, circuit descriptors are correlated, and decoding is represented by one frozen response per model-prompt cell.
