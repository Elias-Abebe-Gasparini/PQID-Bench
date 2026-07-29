# PQID-Bench Hierarchical Clustering And Logistic Regression

- prompts: `154`
- models: `19`
- prompt-model rows for logistic regression: `2926`
- logistic positive rate: `53.28%`
- primary logistic AUC: `0.807`
- primary McFadden pseudo-R2: `0.230`
- entropy-only sensitivity AUC: `0.807`
- entropy-only sensitivity McFadden pseudo-R2: `0.226`

## Nearest Model-Profile Pairs

| model A | model B | Hamming distance | prompt disagreements |
| --- | --- | ---: | ---: |
| GPT-5.6 Sol | Gemini 3.1 Pro Preview | 0.019 | 3 |
| Gemini 3.1 Pro Preview | GPT-5.5 | 0.019 | 3 |
| GPT-5.6 Sol | Claude Fable 5 | 0.026 | 4 |
| GPT-5.6 Sol | GPT-5.5 | 0.026 | 4 |
| Claude Fable 5 | Gemini 3.1 Pro Preview | 0.032 | 5 |
| Claude Opus 4.8 | Claude Sonnet 4.6 | 0.032 | 5 |
| GPT-5.4 mini | Claude Opus 4.8 | 0.032 | 5 |
| GPT-5.6 Sol | Claude Opus 4.8 | 0.032 | 5 |
| Gemini 3.1 Pro Preview | Claude Sonnet 4.6 | 0.032 | 5 |
| Gemini 3.1 Pro Preview | GPT-5.4 mini | 0.032 | 5 |
| Claude Fable 5 | GPT-5.5 | 0.039 | 6 |
| GPT-5.4 mini | Claude Sonnet 4.6 | 0.039 | 6 |

## Logistic Regression Average Marginal Effects

Primary specification: model-tier indicators plus gate-type count and other circuit descriptors. Gate entropy is omitted from this primary model because it is strongly related to gate-type count.

| predictor | log-odds | odds ratio | average marginal effect |
| --- | ---: | ---: | ---: |
| strong open/code tier | -0.462 | 0.630 | -8.28 pp |
| low/experimental tier | -1.152 | 0.316 | -20.77 pp |
| barrier / staged structure | -1.016 | 0.362 | -20.13 pp |
| gate-type count | -1.226 | 0.293 | -21.94 pp |
| controlled / entangling | 0.138 | 1.148 | +2.47 pp |
| classical bits | -0.828 | 0.437 | -14.82 pp |
| qubits | 0.697 | 2.007 | +12.46 pp |
| gate count | -0.463 | 0.629 | -8.29 pp |
| rotation gate | 0.348 | 1.416 | +6.13 pp |
| measurement | 1.556 | 4.741 | +26.01 pp |

## Entropy Sensitivity Specification

This specification replaces gate-type count with gate entropy. It checks whether the entropy result survives when the collinear gate-vocabulary count is not included in the same logistic model.

| predictor | log-odds | odds ratio | average marginal effect |
| --- | ---: | ---: | ---: |
| strong open/code tier | -0.458 | 0.632 | -8.27 pp |
| low/experimental tier | -1.146 | 0.318 | -20.74 pp |
| gate entropy | -0.807 | 0.446 | -14.54 pp |
| barrier / staged structure | -1.124 | 0.325 | -22.44 pp |
| controlled / entangling | 0.104 | 1.110 | +1.88 pp |
| classical bits | -0.849 | 0.428 | -15.30 pp |
| qubits | 0.612 | 1.845 | +11.04 pp |
| gate count | -0.706 | 0.494 | -12.73 pp |
| rotation gate | 0.310 | 1.363 | +5.51 pp |
| measurement | 1.531 | 4.622 | +25.81 pp |

## Collinearity Note

When gate entropy and gate-type count are included together, the model assigns the main heterogeneity penalty to gate-type count (-21.85 pp) and the gate-entropy term becomes small (-0.06 pp). This is a descriptor-collinearity warning, not evidence that entropy is unimportant.

## Interpretation

Hierarchical clustering is useful here because it compares models by which prompts they solve, not just by aggregate score. The nearest-pair table shows that some models with different providers can share nearly identical structural-success profiles on this held-out split.

The logistic regression is the binary-outcome counterpart to the linear probability model. It preserves the same directional story for model tier, gate-vocabulary complexity, and staged/barrier structure. The entropy-only sensitivity confirms that gate entropy is negative when it is not competing with gate-type count inside the same logistic model. The estimates remain descriptive because prompt-model rows share prompts and models.
