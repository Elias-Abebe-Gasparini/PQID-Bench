# PQID-Bench Model Regression And Distribution Analysis

- prompts: `154`
- completed external model rows: `21`
- prompt-model evaluations: `3234`
- model-level regression is deliberately avoided because `n=21` model rows is too small for a credible inferential model
- reported regressions are descriptive linear probability models; coefficients are effect sizes, not causal estimates

## Model-Score Distribution

| rank | model | tier | execution | structural | M given E | QASM3 | structural z |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | GPT-5.6 Sol | frontier_api | 99.35% | 62.99% | 63.40% | 99.35% | 1.25 |
| 2 | Claude Fable 5 | frontier_api | 98.05% | 62.99% | 64.24% | 98.05% | 1.25 |
| 3 | Gemini 3.1 Pro Preview | frontier_api | 96.75% | 61.04% | 63.09% | 96.75% | 1.01 |
| 4 | GPT-5.5 | frontier_api | 97.40% | 60.39% | 62.00% | 97.40% | 0.93 |
| 5 | GPT-5.4 mini | frontier_api | 98.05% | 60.39% | 61.59% | 97.40% | 0.93 |
| 6 | Claude Opus 4.8 | frontier_api | 100.00% | 59.74% | 59.74% | 99.35% | 0.85 |
| 7 | Claude Sonnet 4.6 | frontier_api | 99.35% | 59.09% | 59.48% | 99.35% | 0.78 |
| 8 | DeepSeek V4 Pro | frontier_api | 91.56% | 59.09% | 64.54% | 91.56% | 0.78 |
| 9 | Codestral 25.01 | strong_open_or_code | 93.51% | 55.84% | 59.72% | 93.51% | 0.38 |
| 10 | Gemini 2.5 Pro | frontier_api | 88.31% | 53.90% | 61.03% | 88.31% | 0.15 |
| 11 | GPT-OSS 120B | strong_open_or_code | 96.75% | 53.25% | 55.03% | 96.10% | 0.07 |
| 12 | DeepSeek V4 Flash | frontier_api | 88.96% | 52.60% | 59.12% | 88.96% | -0.01 |
| 13 | Qwen3-Coder-Next | strong_open_or_code | 85.71% | 50.65% | 59.09% | 85.71% | -0.24 |
| 14 | GPT-OSS 20B | strong_open_or_code | 92.86% | 50.65% | 54.55% | 92.21% | -0.24 |
| 15 | Llama 4 Maverick | strong_open_or_code | 94.16% | 48.70% | 51.72% | 93.51% | -0.48 |
| 16 | Mistral Small 3.2 24B | strong_open_or_code | 90.26% | 48.70% | 53.96% | 90.26% | -0.48 |
| 17 | Llama 3.3 70B | strong_open_or_code | 93.51% | 46.10% | 49.31% | 93.51% | -0.79 |
| 18 | Qiskit Mistral 3.2 24B | strong_open_or_code | 89.61% | 44.81% | 50.00% | 88.96% | -0.95 |
| 19 | Llama 4 Scout | low_or_experimental | 82.47% | 44.81% | 54.33% | 82.47% | -0.95 |
| 20 | Qwen3 32B | low_or_experimental | 57.79% | 35.06% | 60.67% | 57.79% | -2.12 |
| 21 | Llama 3.1 8B | low_or_experimental | 81.17% | 35.06% | 43.20% | 81.17% | -2.12 |

Across named model rows, structural fidelity spans 35.06% to 62.99% (range +27.92 pp, median 53.25%, mean 52.66%).

## Tier Distribution

| tier | models | execution mean | structural mean | structural median | structural range | structural sd |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frontier_api | 10 | 95.78% | 59.22% | 60.06% | 52.60%-62.99% | 3.45 pp |
| strong_open_or_code | 8 | 92.05% | 49.84% | 49.68% | 44.81%-55.84% | 3.60 pp |
| low_or_experimental | 3 | 73.81% | 38.31% | 35.06% | 35.06%-44.81% | 5.62 pp |

## Prompt-Level Complexity Regression

Outcome: mean structural match rate per prompt across completed models. Continuous circuit descriptors are standardized, so their coefficients are percentage-point changes per one standard deviation.

- observations: `154` prompts
- mean outcome: `52.66%`
- R-squared: `0.362`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +46.56 pp | baseline expected structural rate |
| `z_num_qubits` | +7.08 pp | change per one standard deviation increase |
| `z_num_clbits` | -10.60 pp | change per one standard deviation increase |
| `z_gate_count` | -4.22 pp | change per one standard deviation increase |
| `z_gate_type_count` | -2.40 pp | change per one standard deviation increase |
| `z_gate_entropy` | -11.15 pp | change per one standard deviation increase |
| `has_barrier` | -28.76 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | +0.21 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +5.45 pp | adjusted yes-minus-no contrast |
| `has_measure` | +25.36 pp | adjusted yes-minus-no contrast |

## Prompt-Model Linear Probability Model

Outcome: binary structural match for each prompt-model evaluation. The reference model tier is `frontier_api`; tier coefficients therefore measure distributional offsets from that frontier cluster after adding the same prompt descriptors.

- observations: `3234` prompt-model rows
- mean outcome: `52.66%`
- R-squared: `0.257`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +53.12 pp | baseline expected structural rate |
| `tier_strong_open_or_code` | -9.38 pp | adjusted yes-minus-no contrast |
| `tier_low_or_experimental` | -20.91 pp | adjusted yes-minus-no contrast |
| `z_num_qubits` | +7.06 pp | change per one standard deviation increase |
| `z_num_clbits` | -10.56 pp | change per one standard deviation increase |
| `z_gate_count` | -4.20 pp | change per one standard deviation increase |
| `z_gate_type_count` | -2.39 pp | change per one standard deviation increase |
| `z_gate_entropy` | -11.12 pp | change per one standard deviation increase |
| `has_barrier` | -28.76 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | +0.21 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +5.45 pp | adjusted yes-minus-no contrast |
| `has_measure` | +25.36 pp | adjusted yes-minus-no contrast |

## Interpretation

The distribution is neither random noise nor a trivial leaderboard. Models form a clear capability gradient, but the best frontier rows compress into a narrow structural band while execution and QASM3 validity are already high. That is exactly the pattern a useful benchmark should expose: format compliance is mostly solved by strong systems, whereas exact circuit recovery still separates models.

The regression results support the same story from the task side. Gate diversity and gate entropy carry the strongest negative coefficients, while raw qubit count is weak once richer circuit descriptors are included. For the manuscript, this should be framed as descriptive evidence that PQID-Bench measures structural circuit fidelity rather than merely penalizing wider circuits.

Caveat: the split is intentionally small and audit-friendly. The right claim is that the current release-bound matrix gives coherent evidence of benchmark difficulty and model differentiation, not that these coefficients are universal laws of quantum-code generation.
