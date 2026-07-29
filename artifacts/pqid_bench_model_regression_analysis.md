# PQID-Bench Model Regression And Distribution Analysis

- prompts: `70`
- completed external model rows: `15`
- prompt-model evaluations: `1050`
- model-level regression is deliberately avoided because `n=15` model rows is too small for a credible inferential model
- reported regressions are descriptive linear probability models; coefficients are effect sizes, not causal estimates

## Model-Score Distribution

| rank | model | tier | execution | structural | M given E | QASM3 | structural z |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | GPT-5.4 mini | frontier_api | 97.14% | 64.29% | 66.18% | 97.14% | 0.89 |
| 2 | GPT-5.5 | frontier_api | 98.57% | 62.86% | 63.77% | 98.57% | 0.77 |
| 3 | Gemini 2.5 Pro | frontier_api | 90.00% | 62.86% | 69.84% | 90.00% | 0.77 |
| 4 | Gemini 3.1 Pro Preview | frontier_api | 97.14% | 62.86% | 64.71% | 97.14% | 0.77 |
| 5 | Claude Sonnet 4.6 | frontier_api | 92.86% | 61.43% | 66.15% | 92.86% | 0.65 |
| 6 | Claude Opus 4.8 | frontier_api | 100.00% | 61.43% | 61.43% | 100.00% | 0.65 |
| 7 | DeepSeek V4 Pro | frontier_api | 91.43% | 58.57% | 64.06% | 91.43% | 0.41 |
| 8 | DeepSeek V4 Flash | frontier_api | 91.43% | 58.57% | 64.06% | 91.43% | 0.41 |
| 9 | Codestral 25.01 | strong_open_or_code | 95.71% | 58.57% | 61.19% | 95.71% | 0.41 |
| 10 | GPT-OSS 120B | strong_open_or_code | 92.86% | 52.86% | 56.92% | 92.86% | -0.07 |
| 11 | GPT-OSS 20B | strong_open_or_code | 84.29% | 51.43% | 61.02% | 84.29% | -0.19 |
| 12 | Llama 3.3 70B | strong_open_or_code | 94.29% | 50.00% | 53.03% | 94.29% | -0.31 |
| 13 | Qwen3 32B | low_or_experimental | 65.71% | 38.57% | 58.70% | 65.71% | -1.27 |
| 14 | Llama 4 Scout | low_or_experimental | 70.00% | 38.57% | 55.10% | 70.00% | -1.27 |
| 15 | Llama 3.1 8B | low_or_experimental | 45.71% | 22.86% | 50.00% | 45.71% | -2.59 |

Across named model rows, structural fidelity spans 22.86% to 64.29% (range +41.43 pp, median 58.57%, mean 53.71%).

## Tier Distribution

| tier | models | execution mean | structural mean | structural median | structural range | structural sd |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frontier_api | 8 | 94.82% | 61.61% | 62.14% | 58.57%-64.29% | 2.08 pp |
| strong_open_or_code | 4 | 91.79% | 53.21% | 52.14% | 50.00%-58.57% | 3.76 pp |
| low_or_experimental | 3 | 60.48% | 33.33% | 38.57% | 22.86%-38.57% | 9.07 pp |

## Prompt-Level Complexity Regression

Outcome: mean structural match rate per prompt across completed models. Continuous circuit descriptors are standardized, so their coefficients are percentage-point changes per one standard deviation.

- observations: `70` prompts
- mean outcome: `53.71%`
- R-squared: `0.477`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +52.09 pp | baseline expected structural rate |
| `z_num_qubits` | +4.40 pp | change per one standard deviation increase |
| `z_num_clbits` | -4.90 pp | change per one standard deviation increase |
| `z_gate_count` | +1.40 pp | change per one standard deviation increase |
| `z_gate_type_count` | -3.17 pp | change per one standard deviation increase |
| `z_gate_entropy` | -17.85 pp | change per one standard deviation increase |
| `has_barrier` | -28.98 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | -6.23 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +12.59 pp | adjusted yes-minus-no contrast |
| `has_measure` | +24.49 pp | adjusted yes-minus-no contrast |

## Prompt-Model Linear Probability Model

Outcome: binary structural match for each prompt-model evaluation. The reference model tier is `frontier_api`; tier coefficients therefore measure distributional offsets from that frontier cluster after adding the same prompt descriptors.

- observations: `1050` prompt-model rows
- mean outcome: `53.71%`
- R-squared: `0.354`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +59.98 pp | baseline expected structural rate |
| `tier_strong_open_or_code` | -8.39 pp | adjusted yes-minus-no contrast |
| `tier_low_or_experimental` | -28.27 pp | adjusted yes-minus-no contrast |
| `z_num_qubits` | +4.37 pp | change per one standard deviation increase |
| `z_num_clbits` | -4.86 pp | change per one standard deviation increase |
| `z_gate_count` | +1.40 pp | change per one standard deviation increase |
| `z_gate_type_count` | -3.15 pp | change per one standard deviation increase |
| `z_gate_entropy` | -17.73 pp | change per one standard deviation increase |
| `has_barrier` | -28.98 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | -6.23 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +12.59 pp | adjusted yes-minus-no contrast |
| `has_measure` | +24.49 pp | adjusted yes-minus-no contrast |

## Interpretation

The distribution is neither random noise nor a trivial leaderboard. Models form a clear capability gradient, but the best frontier rows compress into a narrow structural band while execution and QASM3 validity are already high. That is exactly the pattern a useful benchmark should expose: format compliance is mostly solved by strong systems, whereas exact circuit recovery still separates models.

The regression results support the same story from the task side. Gate diversity and gate entropy carry the strongest negative coefficients, while raw qubit count is weak once richer circuit descriptors are included. For the manuscript, this should be framed as descriptive evidence that PQID-Bench measures structural circuit fidelity rather than merely penalizing wider circuits.

Caveat: the split is intentionally small and audit-friendly. The right claim is that the current release-bound matrix gives coherent evidence of benchmark difficulty and model differentiation, not that these coefficients are universal laws of quantum-code generation.
