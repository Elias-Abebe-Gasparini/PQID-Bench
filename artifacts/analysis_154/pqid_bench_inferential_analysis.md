# PQID-Bench Cluster-Aware Inferential Analysis

## Analysis Contract

- held-out prompts: `154`
- unique evaluator-facing signatures: `144`
- completed model rows: `21`
- prompt-model outcomes: `3234`
- estimand: adjusted associations and paired contrasts for the fixed observed model panel
- uncertainty unit: evaluator-facing target-signature cluster
- causal interpretation: not supported

The task-feature logistic models use each prompt's number of successes over the fixed 21-model panel. Continuous circuit descriptors are standardized over prompts, and percentile intervals come from resampling complete target-signature clusters. The primary entropy model does not include gate-type count; a parallel sensitivity model replaces entropy with gate-type count to avoid treating correlated diversity descriptors as independent causes.

## Adjusted Logistic Associations

All grouped-binomial point fits converged. Across the five analyses, `10,000` / `10,000` target-signature bootstrap refits converged.

| outcome / analysis | descriptor | adjusted OR | cluster-bootstrap 95% CI | average marginal effect | cluster-bootstrap 95% CI |
| --- | --- | ---: | ---: | ---: | ---: |
| signature match, entropy model | gate entropy (per SD) | 0.49 | [0.28, 0.71] | -14.40 pp | [-23.58, -7.04] pp |
| signature match, entropy model | log gate count (per SD) | 1.09 | [0.74, 2.31] | +1.69 pp | [-6.02, +16.10] pp |
| signature match, entropy model | qubits (per SD) | 0.86 | [0.52, 1.21] | -3.06 pp | [-12.56, +3.63] pp |
| signature match, entropy model | classical bits (per SD) | 0.84 | [0.55, 1.18] | -3.50 pp | [-11.85, +3.18] pp |
| signature match, entropy model | barrier present | 0.32 | [0.16, 0.62] | -24.95 pp | [-38.66, -10.38] pp |
| signature match, gate-type model | gate-type count (per SD) | 0.34 | [0.15, 0.55] | -21.56 pp | [-35.51, -11.80] pp |
| signature match, gate-type model | log gate count (per SD) | 1.28 | [0.85, 2.97] | +4.87 pp | [-3.17, +20.55] pp |
| signature match, gate-type model | qubits (per SD) | 0.89 | [0.56, 1.22] | -2.32 pp | [-10.90, +3.93] pp |
| signature match, gate-type model | classical bits (per SD) | 0.82 | [0.53, 1.17] | -3.87 pp | [-12.16, +3.02] pp |
| signature match, gate-type model | barrier present | 0.35 | [0.17, 0.70] | -23.39 pp | [-37.85, -7.53] pp |
| execution, entropy model | gate entropy (per SD) | 0.63 | [0.44, 0.88] | -3.51 pp | [-6.57, -0.89] pp |
| execution, entropy model | barrier present | 1.11 | [0.70, 1.80] | +0.82 pp | [-2.74, +4.40] pp |
| signature match given execution | gate entropy (per SD) | 0.49 | [0.26, 0.74] | -13.61 pp | [-23.94, -5.89] pp |
| signature match given execution | barrier present | 0.29 | [0.14, 0.58] | -27.53 pp | [-41.71, -11.43] pp |
| signature match, identifiable 150 | gate entropy (per SD) | 0.41 | [0.25, 0.62] | -17.79 pp | [-25.42, -9.86] pp |
| signature match, identifiable 150 | barrier present | 0.36 | [0.18, 0.68] | -22.24 pp | [-36.99, -7.95] pp |

## Execution Versus Conditional Fidelity

| descriptor | conditional-signature AME minus execution AME | cluster-bootstrap 95% CI |
| --- | ---: | ---: |
| gate entropy (per SD) | -10.10 pp | [-20.92, -2.19] pp |
| barrier present | -28.35 pp | [-43.28, -11.84] pp |

## Target-Signature-Grouped Cross-Validation

Out-of-fold predictions use 10 folds grouped by target signature. Negative deltas are improvements for log loss and Brier score; positive deltas are improvements for AUC.

| model | log loss | delta vs size only (95% CI) | Brier | delta vs size only (95% CI) | AUC | delta vs size only (95% CI) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| size only | 0.6561 | -- | 0.2329 | -- | 0.638 | -- |
| size + entropy + barrier | 0.6042 | -0.0519 [-0.1052, +0.0074] | 0.2060 | -0.0269 [-0.0504, -0.0015] | 0.739 | +0.1016 [+0.0295, +0.1703] |
| size + gate types + barrier | 0.5981 | -0.0580 [-0.1129, +0.0033] | 0.2047 | -0.0281 [-0.0522, -0.0023] | 0.743 | +0.1052 [+0.0334, +0.1737] |

## Selected Paired Model Comparisons

| comparison | before -> after | paired difference | signature-cluster 95% CI | wins-losses-ties | cluster permutation p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama 8B -> 70B | 35.06% -> 46.10% | +11.04 pp | [+3.77, +18.29] pp | 26-9-119 | 0.0062 | 0.0622 |
| Llama 4 Scout -> Maverick | 44.81% -> 48.70% | +3.90 pp | [-3.90, +11.77] pp | 20-14-120 | 0.4057 | 1.0000 |
| GPT-OSS 20B -> 120B | 50.65% -> 53.25% | +2.60 pp | [-2.60, +7.74] pp | 10-6-138 | 0.4526 | 1.0000 |
| Gemini 2.5 -> 3.1 | 53.90% -> 61.04% | +7.14 pp | [+1.87, +13.07] pp | 16-5-133 | 0.0260 | 0.2338 |
| Claude Sonnet -> Opus | 59.09% -> 59.74% | +0.65 pp | [-2.00, +3.70] pp | 3-2-149 | 1.0000 | 1.0000 |
| Claude Opus -> Fable | 59.74% -> 62.99% | +3.25 pp | [+0.00, +6.85] pp | 6-1-147 | 0.1255 | 0.8660 |
| DeepSeek Flash -> Pro | 52.60% -> 59.09% | +6.49 pp | [+0.64, +12.74] pp | 17-7-130 | 0.0626 | 0.5008 |
| Qwen3 general -> Coder | 35.06% -> 50.65% | +15.58 pp | [+7.24, +23.75] pp | 35-11-108 | 0.0010 | 0.0108 |
| GPT-5.4 mini -> GPT-5.5 | 60.39% -> 60.39% | +0.00 pp | [-3.25, +3.23] pp | 3-3-148 | 1.0000 | 1.0000 |
| GPT-5.5 -> GPT-5.6 Sol | 60.39% -> 62.99% | +2.60 pp | [+0.63, +5.36] pp | 4-0-150 | 0.1237 | 0.8660 |
| Mistral parent -> Qiskit specialist | 48.70% -> 44.81% | -3.90 pp | [-10.26, +2.55] pp | 9-15-130 | 0.3071 | 1.0000 |

## Bootstrap Rank Stability

Mean Spearman correlation between each bootstrap ranking and the original ranking is `0.961` with a 95% interval of `[0.916, 0.988]`.

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
| Gemini 2.5 Pro | 53.90% | [45.34%, 62.16%] | 10.0 | [7.0, 16.0] | 0.26% |
| GPT-OSS 120B | 53.25% | [44.37%, 61.82%] | 11.0 | [8.5, 15.0] | 0.00% |
| DeepSeek V4 Flash | 52.60% | [43.87%, 60.76%] | 12.0 | [9.0, 15.5] | 0.00% |
| GPT-OSS 20B | 50.65% | [41.94%, 59.18%] | 13.5 | [10.0, 17.0] | 0.00% |
| Qwen3-Coder-Next | 50.65% | [42.21%, 58.93%] | 13.5 | [10.0, 17.5] | 0.00% |
| Llama 4 Maverick | 48.70% | [40.13%, 57.14%] | 15.5 | [11.0, 19.0] | 0.00% |
| Mistral Small 3.2 24B | 48.70% | [40.26%, 57.05%] | 15.5 | [10.5, 18.5] | 0.00% |
| Llama 3.3 70B | 46.10% | [37.16%, 54.84%] | 17.0 | [12.0, 19.0] | 0.00% |
| Llama 4 Scout | 44.81% | [36.55%, 53.09%] | 18.5 | [14.5, 19.0] | 0.00% |
| Qiskit Mistral 3.2 24B | 44.81% | [36.54%, 53.33%] | 18.5 | [14.5, 19.5] | 0.00% |
| Llama 3.1 8B | 35.06% | [27.10%, 43.31%] | 20.5 | [20.0, 21.0] | 0.00% |
| Qwen3 32B | 35.06% | [27.56%, 42.67%] | 20.5 | [19.0, 21.0] | 0.00% |

## Main Inferential Findings

After adjustment for log gate count, qubit width, classical width, and barrier presence, one standard deviation of gate entropy is associated with OR `0.49` for reference-signature match (95% cluster-bootstrap CI `[0.28, 0.71]`) and an average marginal change of `-14.40 pp`. Barrier presence is associated with OR `0.32` and `-24.95 pp`.

The entropy association is weak for execution (OR `0.63`, 95% CI `[0.44, 0.88]`) but remains strong among outputs that execute (OR `0.49`, 95% CI `[0.26, 0.74]`). This supports the bounded interpretation that heterogeneity is primarily associated with recovering the wrong reference signature, not with failure to produce runnable code.

Adding entropy and barrier information to size controls improves grouped out-of-fold AUC by `+0.102` (95% CI `[+0.030, +0.170]`) and Brier score by `-0.0269` (95% CI `[-0.0504, -0.0015]`). The log-loss interval includes zero, so predictive improvement should be described as metric-dependent rather than universal.

After Holm correction, the selected paired improvements that remain distinguishable under target-signature permutation are: Qwen3 general -> Coder (+15.58 pp, adjusted p=0.0108). Other within-family differences are estimates with uncertainty, not confirmed ordering claims.

## Interpretation Boundary

These analyses quantify uncertainty under changes in the held-out target-signature composition and compare models on paired prompts. They do not identify causal effects of circuit descriptors or model tier. The model panel is fixed rather than randomly sampled, circuit descriptors are correlated, and decoding is represented by one frozen response per model-prompt cell.
