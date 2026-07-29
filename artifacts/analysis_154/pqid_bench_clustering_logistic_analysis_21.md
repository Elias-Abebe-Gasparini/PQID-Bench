# PQID-Bench Hierarchical Clustering And Logistic Regression

- prompts: `154`
- models: `21`
- prompt-model rows for logistic regression: `3234`
- logistic positive rate: `52.66%`
- primary logistic AUC: `0.802`
- primary McFadden pseudo-R2: `0.220`
- entropy-only sensitivity AUC: `0.801`
- entropy-only sensitivity McFadden pseudo-R2: `0.215`

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
| strong open/code tier | -0.512 | 0.599 | -9.31 pp |
| low/experimental tier | -1.136 | 0.321 | -20.71 pp |
| barrier / staged structure | -1.047 | 0.351 | -21.10 pp |
| gate-type count | -1.179 | 0.308 | -21.43 pp |
| controlled / entangling | 0.092 | 1.097 | +1.68 pp |
| classical bits | -0.692 | 0.501 | -12.57 pp |
| qubits | 0.577 | 1.781 | +10.49 pp |
| gate count | -0.417 | 0.659 | -7.59 pp |
| rotation gate | 0.327 | 1.387 | +5.86 pp |
| measurement | 1.534 | 4.639 | +26.16 pp |

## Entropy Sensitivity Specification

This specification replaces gate-type count with gate entropy. It checks whether the entropy result survives when the collinear gate-vocabulary count is not included in the same logistic model.

| predictor | log-odds | odds ratio | average marginal effect |
| --- | ---: | ---: | ---: |
| strong open/code tier | -0.507 | 0.602 | -9.29 pp |
| low/experimental tier | -1.129 | 0.323 | -20.67 pp |
| gate entropy | -0.764 | 0.466 | -13.99 pp |
| barrier / staged structure | -1.157 | 0.314 | -23.48 pp |
| controlled / entangling | 0.055 | 1.056 | +1.00 pp |
| classical bits | -0.708 | 0.493 | -12.97 pp |
| qubits | 0.496 | 1.643 | +9.10 pp |
| gate count | -0.651 | 0.522 | -11.93 pp |
| rotation gate | 0.285 | 1.330 | +5.16 pp |
| measurement | 1.505 | 4.503 | +25.92 pp |

## Collinearity Note

When gate entropy and gate-type count are included together, the model assigns the main heterogeneity penalty to gate-type count (-23.25 pp) and the gate-entropy term becomes small (+1.33 pp). This is a descriptor-collinearity warning, not evidence that entropy is unimportant.

## Interpretation

Hierarchical clustering is useful here because it compares models by which prompts they solve, not just by aggregate score. The nearest-pair table shows that some models with different providers can share nearly identical structural-success profiles on this held-out split.

The logistic regression is the binary-outcome counterpart to the linear probability model. It preserves the same directional story for model tier, gate-vocabulary complexity, and staged/barrier structure. The entropy-only sensitivity confirms that gate entropy is negative when it is not competing with gate-type count inside the same logistic model. The estimates remain descriptive because prompt-model rows share prompts and models.
