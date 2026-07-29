# PQID-Bench Hierarchical Clustering And Logistic Regression

- prompts: `70`
- models: `15`
- prompt-model rows for logistic regression: `1050`
- logistic positive rate: `53.71%`
- primary logistic AUC: `0.861`
- primary McFadden pseudo-R2: `0.324`
- entropy-only sensitivity AUC: `0.856`
- entropy-only sensitivity McFadden pseudo-R2: `0.312`

## Nearest Model-Profile Pairs

| model A | model B | Hamming distance | prompt disagreements |
| --- | --- | ---: | ---: |
| GPT-5.5 | Gemini 3.1 Pro Preview | 0.000 | 0 |
| GPT-5.4 mini | GPT-5.5 | 0.014 | 1 |
| GPT-5.4 mini | Gemini 3.1 Pro Preview | 0.014 | 1 |
| GPT-5.5 | Claude Opus 4.8 | 0.014 | 1 |
| GPT-5.5 | Claude Sonnet 4.6 | 0.014 | 1 |
| Gemini 3.1 Pro Preview | Claude Opus 4.8 | 0.014 | 1 |
| Gemini 3.1 Pro Preview | Claude Sonnet 4.6 | 0.014 | 1 |
| Claude Sonnet 4.6 | Claude Opus 4.8 | 0.029 | 2 |
| GPT-5.4 mini | Claude Opus 4.8 | 0.029 | 2 |
| GPT-5.4 mini | Claude Sonnet 4.6 | 0.029 | 2 |
| GPT-5.5 | Codestral 2501 | 0.071 | 5 |
| Gemini 3.1 Pro Preview | Codestral 2501 | 0.071 | 5 |

## Logistic Regression Average Marginal Effects

Primary specification: model-tier indicators plus gate-type count and other circuit descriptors. Gate entropy is omitted from this primary model because it is strongly related to gate-type count.

| predictor | log-odds | odds ratio | average marginal effect |
| --- | ---: | ---: | ---: |
| strong open/code tier | -0.538 | 0.584 | -8.21 pp |
| low/experimental tier | -1.814 | 0.163 | -28.02 pp |
| barrier / staged structure | -1.098 | 0.334 | -18.93 pp |
| gate-type count | -2.054 | 0.128 | -31.39 pp |
| controlled / entangling | -0.565 | 0.568 | -8.67 pp |
| classical bits | -0.469 | 0.626 | -7.17 pp |
| qubits | 0.643 | 1.902 | +9.83 pp |
| gate count | 0.227 | 1.255 | +3.47 pp |
| rotation gate | 0.917 | 2.501 | +13.42 pp |
| measurement | 2.057 | 7.820 | +28.16 pp |

## Entropy Sensitivity Specification

This specification replaces gate-type count with gate entropy. It checks whether the entropy result survives when the collinear gate-vocabulary count is not included in the same logistic model.

| predictor | log-odds | odds ratio | average marginal effect |
| --- | ---: | ---: | ---: |
| strong open/code tier | -0.522 | 0.593 | -8.13 pp |
| low/experimental tier | -1.792 | 0.167 | -27.93 pp |
| gate entropy | -1.437 | 0.238 | -22.47 pp |
| barrier / staged structure | -1.314 | 0.269 | -23.36 pp |
| controlled / entangling | -0.470 | 0.625 | -7.38 pp |
| classical bits | -0.441 | 0.644 | -6.89 pp |
| qubits | 0.508 | 1.661 | +7.94 pp |
| gate count | -0.084 | 0.920 | -1.31 pp |
| rotation gate | 0.985 | 2.679 | +14.72 pp |
| measurement | 1.952 | 7.041 | +27.40 pp |

## Collinearity Note

When gate entropy and gate-type count are included together, the model assigns the main heterogeneity penalty to gate-type count (-34.04 pp) and the gate-entropy term becomes small (+2.10 pp). This is a descriptor-collinearity warning, not evidence that entropy is unimportant.

## Interpretation

Hierarchical clustering is useful here because it compares models by which prompts they solve, not just by aggregate score. The nearest-pair table shows that some models with different providers can share nearly identical structural-success profiles on this held-out split.

The logistic regression is the binary-outcome counterpart to the linear probability model. It preserves the same directional story for model tier, gate-vocabulary complexity, and staged/barrier structure. The entropy-only sensitivity confirms that gate entropy is negative when it is not competing with gate-type count inside the same logistic model. The estimates remain descriptive because prompt-model rows share prompts and models.
