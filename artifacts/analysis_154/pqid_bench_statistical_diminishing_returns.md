# PQID-Bench Statistical Diminishing-Returns Analysis

- prompts: `154`
- completed external models: `21`
- prompt-model evaluations: `3234`
- unit for complexity correlations: prompt-level mean structural rate across completed models
- confidence intervals: prompt-cluster bootstrap, 5,000 resamples

## Complexity Correlations

| descriptor | Pearson r | Spearman rho | permutation p | slope per unit |
| --- | ---: | ---: | ---: | ---: |
| `num_qubits` | -0.052 | -0.089 | 0.2747 | -0.94 pp |
| `num_clbits` | -0.199 | -0.094 | 0.2438 | -3.70 pp |
| `gate_count` | -0.231 | -0.183 | 0.0210 | -0.72 pp |
| `gate_type_count` | -0.414 | -0.445 | 0.0002 | -9.16 pp |
| `gate_entropy` | -0.433 | -0.428 | 0.0002 | -42.26 pp |

## Prompt-Level Structural Contrasts

| contrast | no mean | yes mean | yes - no | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| `high_gate_diversity` | 59.81% | 19.05% | -40.76 pp | [-53.53, -26.88] pp |
| `high_gate_count` | 56.70% | 15.24% | -41.46 pp | [-55.78, -24.94] pp |
| `has_barrier` | 65.16% | 28.84% | -36.32 pp | [-48.60, -24.18] pp |
| `has_controlled_or_entangling` | 58.93% | 49.82% | -9.11 pp | [-22.89, 4.63] pp |
| `has_rotation` | 54.98% | 37.14% | -17.83 pp | [-34.29, -1.85] pp |
| `has_measure` | 50.61% | 54.04% | +3.42 pp | [-9.01, 15.70] pp |

## Model-Side Returns By Descriptive Tier

| tier | models | execution | structural | exec-structure gap | delta execution | delta structural |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| retrieval-copy lower bound | 1 | 91.56% | 15.58% | 75.97% | -- | -- |
| low / experimental hosted | 3 | 73.81% | 38.31% | 35.50% | -17.75 pp | +22.73 pp |
| strong hosted open/code | 8 | 92.05% | 49.84% | 42.21% | +18.24 pp | +11.53 pp |
| frontier APIs | 10 | 95.78% | 59.22% | 36.56% | +3.73 pp | +9.38 pp |

## Paired Upgrade Comparisons

| comparison | execution before -> after | structural before -> after | delta execution | delta structural | delta gate types | delta gate count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama 8B -> 70B | 81.17% -> 93.51% | 35.06% -> 46.10% | +12.34 pp | +11.04 pp | +18.18 pp | +14.94 pp |
| Llama 4 Scout -> Maverick | 82.47% -> 94.16% | 44.81% -> 48.70% | +11.69 pp | +3.90 pp | +12.99 pp | +16.88 pp |
| GPT-OSS 20B -> 120B | 92.86% -> 96.75% | 50.65% -> 53.25% | +3.90 pp | +2.60 pp | +0.00 pp | +1.30 pp |
| Gemini 2.5 Pro -> 3.1 Pro Preview | 88.31% -> 96.75% | 53.90% -> 61.04% | +8.44 pp | +7.14 pp | +7.14 pp | +7.79 pp |
| Claude Sonnet 4.6 -> Opus 4.8 | 99.35% -> 100.00% | 59.09% -> 59.74% | +0.65 pp | +0.65 pp | +1.30 pp | +1.95 pp |
| DeepSeek V4 Flash -> Pro | 88.96% -> 91.56% | 52.60% -> 59.09% | +2.60 pp | +6.49 pp | +5.84 pp | +5.19 pp |
| Mistral parent -> Qiskit specialist | 90.26% -> 89.61% | 48.70% -> 44.81% | -0.65 pp | -3.90 pp | -6.49 pp | -10.39 pp |

## Interpretation

The statistical summaries support a cautious diminishing-returns claim. On the task side, reference-signature success decreases most strongly with gate-type count and gate entropy, while raw qubit count has almost no relationship with prompt-level signature-match rate in this split. On the model side, stronger systems rapidly approach high execution and QASM3 rates, while reference-signature match improves more slowly and clusters in a narrower high-50% to low-60% range for frontier APIs. Most paired upgrades improve signature match in the final 21-model matrix, but the gains are uneven and are generally smaller than the largest execution improvements; the matched Mistral parent-specialist comparison is reported separately and does not improve on this split. This pattern suggests that additional capability improves executable formatting and partial circuit recovery without closing the stricter source-signature gap.

Caveat: these are descriptive statistics over the final 154-prompt held-out split. They are useful release-bound evidence, not universal scaling laws.
