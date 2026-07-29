# PQID-Bench Statistical Diminishing-Returns Analysis

- prompts: `70`
- completed external models: `15`
- prompt-model evaluations: `1050`
- unit for complexity correlations: prompt-level mean structural rate across completed models
- confidence intervals: prompt-cluster bootstrap, 5,000 resamples

## Complexity Correlations

| descriptor | Pearson r | Spearman rho | permutation p | slope per unit |
| --- | ---: | ---: | ---: | ---: |
| `num_qubits` | 0.040 | -0.075 | 0.5369 | 0.81 pp |
| `num_clbits` | -0.145 | -0.079 | 0.5143 | -3.69 pp |
| `gate_count` | -0.270 | -0.076 | 0.5349 | -2.42 pp |
| `gate_type_count` | -0.527 | -0.531 | 0.0002 | -14.19 pp |
| `gate_entropy` | -0.559 | -0.545 | 0.0002 | -61.16 pp |

## Prompt-Level Structural Contrasts

| contrast | no mean | yes mean | yes - no | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| `high_gate_diversity` | 63.28% | 2.42% | -60.85 pp | [-70.49, -50.97] pp |
| `high_gate_count` | 57.50% | 13.33% | -44.17 pp | [-62.36, -20.17] pp |
| `has_barrier` | 70.54% | 26.91% | -43.63 pp | [-59.02, -26.65] pp |
| `has_controlled_or_entangling` | 67.62% | 47.76% | -19.86 pp | [-37.41, -1.31] pp |
| `has_rotation` | 55.00% | 40.00% | -15.00 pp | [-46.36, 14.83] pp |
| `has_measure` | 57.22% | 51.88% | -5.34 pp | [-23.13, 12.03] pp |

## Model-Side Returns By Descriptive Tier

| tier | models | execution | structural | exec-structure gap | delta execution | delta structural |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| retrieval-copy lower bound | 1 | 90.00% | 24.29% | 65.71% | -- | -- |
| low / experimental hosted | 3 | 60.95% | 33.33% | 27.62% | -29.05 pp | +9.05 pp |
| strong hosted open/code | 4 | 92.14% | 53.21% | 38.93% | +31.19 pp | +19.88 pp |
| frontier APIs | 8 | 95.54% | 61.61% | 33.93% | +3.39 pp | +8.39 pp |

## Paired Upgrade Comparisons

| comparison | execution before -> after | structural before -> after | delta execution | delta structural | delta gate types | delta gate count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama 8B -> 70B | 47.14% -> 94.29% | 22.86% -> 50.00% | +47.14 pp | +27.14 pp | +41.43 pp | +41.43 pp |
| GPT-OSS 20B -> 120B | 84.29% -> 94.29% | 51.43% -> 52.86% | +10.00 pp | +1.43 pp | +0.00 pp | +0.00 pp |
| Gemini 2.5 Pro -> 3.1 Pro Preview | 92.86% -> 97.14% | 62.86% -> 62.86% | +4.29 pp | +0.00 pp | +4.29 pp | +10.00 pp |
| Claude Sonnet 4.6 -> Opus 4.8 | 92.86% -> 100.00% | 61.43% -> 61.43% | +7.14 pp | +0.00 pp | +2.86 pp | +5.71 pp |
| DeepSeek V4 Flash -> Pro | 92.86% -> 92.86% | 58.57% -> 58.57% | +0.00 pp | +0.00 pp | +1.43 pp | +2.86 pp |

## Interpretation

The statistical summaries support a cautious diminishing-returns claim. On the task side, structural success decreases most strongly with gate-type count and gate entropy, while raw qubit count has almost no relationship with prompt-level structural rate in this split. On the model side, stronger systems rapidly approach high execution and QASM3 rates, but structural match improves more slowly and then clusters near the high-50% to low-60% range for frontier APIs. The paired Gemini, Anthropic, and DeepSeek upgrades improve execution or component metrics without improving all-structure match, which suggests that additional model capability is being absorbed by executable formatting and partial structure before it solves the stricter circuit-recovery target.

Caveat: these are descriptive statistics over the current 70-prompt held-out split. They are useful manuscript evidence, but the final paper should describe them as preliminary and release-bound rather than as universal scaling laws.
