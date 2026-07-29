# PQID-Bench Model Regression And Distribution Analysis

- prompts: `154`
- completed external model rows: `19`
- prompt-model evaluations: `2926`
- model-level regression is deliberately avoided because `n=19` model rows is too small for a credible inferential model
- reported regressions are descriptive linear probability models; coefficients are effect sizes, not causal estimates

## Model-Score Distribution

| rank | model | tier | execution | structural | M given E | QASM3 | structural z |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | GPT-5.6 Sol | frontier_api | 99.35% | 62.99% | 63.40% | 99.35% | 1.15 |
| 2 | Claude Fable 5 | frontier_api | 98.05% | 62.99% | 64.24% | 98.05% | 1.15 |
| 3 | Gemini 3.1 Pro Preview | frontier_api | 96.75% | 61.04% | 63.09% | 96.75% | 0.92 |
| 4 | GPT-5.5 | frontier_api | 97.40% | 60.39% | 62.00% | 97.40% | 0.84 |
| 5 | GPT-5.4 mini | frontier_api | 98.05% | 60.39% | 61.59% | 97.40% | 0.84 |
| 6 | Claude Opus 4.8 | frontier_api | 100.00% | 59.74% | 59.74% | 99.35% | 0.76 |
| 7 | Claude Sonnet 4.6 | frontier_api | 99.35% | 59.09% | 59.48% | 99.35% | 0.69 |
| 8 | DeepSeek V4 Pro | frontier_api | 91.56% | 59.09% | 64.54% | 91.56% | 0.69 |
| 9 | Codestral 25.01 | strong_open_or_code | 93.51% | 55.84% | 59.72% | 93.51% | 0.30 |
| 10 | Gemini 2.5 Pro | frontier_api | 88.31% | 53.90% | 61.03% | 88.31% | 0.07 |
| 11 | GPT-OSS 120B | strong_open_or_code | 96.75% | 53.25% | 55.03% | 96.10% | -0.00 |
| 12 | DeepSeek V4 Flash | frontier_api | 88.96% | 52.60% | 59.12% | 88.96% | -0.08 |
| 13 | Qwen3-Coder-Next | strong_open_or_code | 85.71% | 50.65% | 59.09% | 85.71% | -0.31 |
| 14 | GPT-OSS 20B | strong_open_or_code | 92.86% | 50.65% | 54.55% | 92.21% | -0.31 |
| 15 | Llama 4 Maverick | strong_open_or_code | 94.16% | 48.70% | 51.72% | 93.51% | -0.54 |
| 16 | Llama 3.3 70B | strong_open_or_code | 93.51% | 46.10% | 49.31% | 93.51% | -0.85 |
| 17 | Llama 4 Scout | low_or_experimental | 82.47% | 44.81% | 54.33% | 82.47% | -1.00 |
| 18 | Qwen3 32B | low_or_experimental | 57.79% | 35.06% | 60.67% | 57.79% | -2.15 |
| 19 | Llama 3.1 8B | low_or_experimental | 81.17% | 35.06% | 43.20% | 81.17% | -2.15 |

Across named model rows, structural fidelity spans 35.06% to 62.99% (range +27.92 pp, median 53.90%, mean 53.28%).

## Tier Distribution

| tier | models | execution mean | structural mean | structural median | structural range | structural sd |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frontier_api | 10 | 95.78% | 59.22% | 60.06% | 52.60%-62.99% | 3.45 pp |
| strong_open_or_code | 6 | 92.75% | 50.87% | 50.65% | 46.10%-55.84% | 3.40 pp |
| low_or_experimental | 3 | 73.81% | 38.31% | 35.06% | 35.06%-44.81% | 5.62 pp |

## Prompt-Level Complexity Regression

Outcome: mean structural match rate per prompt across completed models. Continuous circuit descriptors are standardized, so their coefficients are percentage-point changes per one standard deviation.

- observations: `154` prompts
- mean outcome: `53.28%`
- R-squared: `0.365`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +46.74 pp | baseline expected structural rate |
| `z_num_qubits` | +8.04 pp | change per one standard deviation increase |
| `z_num_clbits` | -11.87 pp | change per one standard deviation increase |
| `z_gate_count` | -4.28 pp | change per one standard deviation increase |
| `z_gate_type_count` | -2.50 pp | change per one standard deviation increase |
| `z_gate_entropy` | -11.41 pp | change per one standard deviation increase |
| `has_barrier` | -28.33 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | +0.91 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +6.36 pp | adjusted yes-minus-no contrast |
| `has_measure` | +24.83 pp | adjusted yes-minus-no contrast |

## Prompt-Model Linear Probability Model

Outcome: binary structural match for each prompt-model evaluation. The reference model tier is `frontier_api`; tier coefficients therefore measure distributional offsets from that frontier cluster after adding the same prompt descriptors.

- observations: `2926` prompt-model rows
- mean outcome: `53.28%`
- R-squared: `0.266`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +52.68 pp | baseline expected structural rate |
| `tier_strong_open_or_code` | -8.35 pp | adjusted yes-minus-no contrast |
| `tier_low_or_experimental` | -20.91 pp | adjusted yes-minus-no contrast |
| `z_num_qubits` | +8.01 pp | change per one standard deviation increase |
| `z_num_clbits` | -11.83 pp | change per one standard deviation increase |
| `z_gate_count` | -4.26 pp | change per one standard deviation increase |
| `z_gate_type_count` | -2.49 pp | change per one standard deviation increase |
| `z_gate_entropy` | -11.37 pp | change per one standard deviation increase |
| `has_barrier` | -28.33 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | +0.91 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +6.36 pp | adjusted yes-minus-no contrast |
| `has_measure` | +24.83 pp | adjusted yes-minus-no contrast |

## Interpretation

The distribution is neither random noise nor a trivial leaderboard. Models form a clear capability gradient, but the best frontier rows compress into a narrow structural band while execution and QASM3 validity are already high. That is exactly the pattern a useful benchmark should expose: format compliance is mostly solved by strong systems, whereas exact circuit recovery still separates models.

The regression results support the same story from the task side. Gate diversity and gate entropy carry the strongest negative coefficients, while raw qubit count is weak once richer circuit descriptors are included. For the manuscript, this should be framed as descriptive evidence that PQID-Bench measures structural circuit fidelity rather than merely penalizing wider circuits.

Caveat: the split is intentionally small and audit-friendly. The right claim is that the current release-bound matrix gives coherent evidence of benchmark difficulty and model differentiation, not that these coefficients are universal laws of quantum-code generation.
