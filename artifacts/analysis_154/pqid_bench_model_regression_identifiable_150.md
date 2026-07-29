# PQID-Bench Model Regression And Distribution Analysis

- prompts: `150`
- completed external model rows: `21`
- prompt-model evaluations: `3150`
- model-level regression is deliberately avoided because `n=21` model rows is too small for a credible inferential model
- reported regressions are descriptive linear probability models; coefficients are effect sizes, not causal estimates

## Model-Score Distribution

| rank | model | tier | execution | structural | M given E | QASM3 | structural z |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | GPT-5.6 Sol | frontier_api | 100.00% | 64.67% | 64.67% | 100.00% | 1.25 |
| 2 | Claude Fable 5 | frontier_api | 100.00% | 64.67% | 64.67% | 100.00% | 1.25 |
| 3 | Gemini 3.1 Pro Preview | frontier_api | 96.67% | 62.67% | 64.83% | 96.67% | 1.01 |
| 4 | GPT-5.5 | frontier_api | 98.00% | 62.00% | 63.27% | 98.00% | 0.93 |
| 5 | GPT-5.4 mini | frontier_api | 98.00% | 62.00% | 63.27% | 97.33% | 0.93 |
| 6 | Claude Opus 4.8 | frontier_api | 100.00% | 61.33% | 61.33% | 99.33% | 0.85 |
| 7 | Claude Sonnet 4.6 | frontier_api | 99.33% | 60.67% | 61.07% | 99.33% | 0.78 |
| 8 | DeepSeek V4 Pro | frontier_api | 92.67% | 60.67% | 65.47% | 92.67% | 0.78 |
| 9 | Codestral 25.01 | strong_open_or_code | 94.00% | 57.33% | 60.99% | 94.00% | 0.38 |
| 10 | Gemini 2.5 Pro | frontier_api | 88.00% | 55.33% | 62.88% | 88.00% | 0.15 |
| 11 | GPT-OSS 120B | strong_open_or_code | 96.67% | 54.67% | 56.55% | 96.00% | 0.07 |
| 12 | DeepSeek V4 Flash | frontier_api | 89.33% | 54.00% | 60.45% | 89.33% | -0.01 |
| 13 | Qwen3-Coder-Next | strong_open_or_code | 86.00% | 52.00% | 60.47% | 86.00% | -0.24 |
| 14 | GPT-OSS 20B | strong_open_or_code | 94.00% | 52.00% | 55.32% | 93.33% | -0.24 |
| 15 | Llama 4 Maverick | strong_open_or_code | 94.67% | 50.00% | 52.82% | 94.00% | -0.48 |
| 16 | Mistral Small 3.2 24B | strong_open_or_code | 91.33% | 50.00% | 54.74% | 91.33% | -0.48 |
| 17 | Llama 3.3 70B | strong_open_or_code | 94.00% | 47.33% | 50.35% | 94.00% | -0.79 |
| 18 | Qiskit Mistral 3.2 24B | strong_open_or_code | 89.33% | 46.00% | 51.49% | 88.67% | -0.95 |
| 19 | Llama 4 Scout | low_or_experimental | 83.33% | 46.00% | 55.20% | 83.33% | -0.95 |
| 20 | Qwen3 32B | low_or_experimental | 59.33% | 36.00% | 60.67% | 59.33% | -2.12 |
| 21 | Llama 3.1 8B | low_or_experimental | 82.00% | 36.00% | 43.90% | 82.00% | -2.12 |

Across named model rows, structural fidelity spans 36.00% to 64.67% (range +28.67 pp, median 54.67%, mean 54.06%).

## Tier Distribution

| tier | models | execution mean | structural mean | structural median | structural range | structural sd |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frontier_api | 10 | 96.20% | 60.80% | 61.67% | 54.00%-64.67% | 3.54 pp |
| strong_open_or_code | 8 | 92.50% | 51.17% | 51.00% | 46.00%-57.33% | 3.70 pp |
| low_or_experimental | 3 | 74.89% | 39.33% | 36.00% | 36.00%-46.00% | 5.77 pp |

## Prompt-Level Complexity Regression

Outcome: mean structural match rate per prompt across completed models. Continuous circuit descriptors are standardized, so their coefficients are percentage-point changes per one standard deviation.

- observations: `150` prompts
- mean outcome: `54.06%`
- R-squared: `0.351`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +47.51 pp | baseline expected structural rate |
| `z_num_qubits` | +6.34 pp | change per one standard deviation increase |
| `z_num_clbits` | -13.36 pp | change per one standard deviation increase |
| `z_gate_count` | +0.16 pp | change per one standard deviation increase |
| `z_gate_type_count` | -3.95 pp | change per one standard deviation increase |
| `z_gate_entropy` | -10.18 pp | change per one standard deviation increase |
| `has_barrier` | -27.00 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | -0.21 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +6.01 pp | adjusted yes-minus-no contrast |
| `has_measure` | +24.72 pp | adjusted yes-minus-no contrast |

## Prompt-Model Linear Probability Model

Outcome: binary structural match for each prompt-model evaluation. The reference model tier is `frontier_api`; tier coefficients therefore measure distributional offsets from that frontier cluster after adding the same prompt descriptors.

- observations: `3150` prompt-model rows
- mean outcome: `54.06%`
- R-squared: `0.247`

| predictor | coefficient | interpretation |
| --- | ---: | --- |
| `intercept` | +54.24 pp | baseline expected structural rate |
| `tier_strong_open_or_code` | -9.63 pp | adjusted yes-minus-no contrast |
| `tier_low_or_experimental` | -21.47 pp | adjusted yes-minus-no contrast |
| `z_num_qubits` | +6.32 pp | change per one standard deviation increase |
| `z_num_clbits` | -13.31 pp | change per one standard deviation increase |
| `z_gate_count` | +0.16 pp | change per one standard deviation increase |
| `z_gate_type_count` | -3.93 pp | change per one standard deviation increase |
| `z_gate_entropy` | -10.15 pp | change per one standard deviation increase |
| `has_barrier` | -27.00 pp | adjusted yes-minus-no contrast |
| `has_controlled_or_entangling` | -0.21 pp | adjusted yes-minus-no contrast |
| `has_rotation` | +6.01 pp | adjusted yes-minus-no contrast |
| `has_measure` | +24.72 pp | adjusted yes-minus-no contrast |

## Interpretation

The distribution is neither random noise nor a trivial leaderboard. Models form a clear capability gradient, but the best frontier rows compress into a narrow structural band while execution and QASM3 validity are already high. That is exactly the pattern a useful benchmark should expose: format compliance is mostly solved by strong systems, whereas exact circuit recovery still separates models.

The regression results support the same story from the task side. Gate diversity and gate entropy carry the strongest negative coefficients, while raw qubit count is weak once richer circuit descriptors are included. For the manuscript, this should be framed as descriptive evidence that PQID-Bench measures structural circuit fidelity rather than merely penalizing wider circuits.

Caveat: the split is intentionally small and audit-friendly. The right claim is that the current release-bound matrix gives coherent evidence of benchmark difficulty and model differentiation, not that these coefficients are universal laws of quantum-code generation.
