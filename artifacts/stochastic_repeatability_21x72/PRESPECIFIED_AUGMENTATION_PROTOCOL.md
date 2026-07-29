# PQID-Bench 72-Prompt Repeatability Augmentation Protocol

## Status And Temporal Boundary

This document freezes the 36-prompt augmentation that expands the completed
21-model by 36-prompt by 3-run stochastic-repeatability audit to 21 models by
72 prompts by 3 runs. The decision to increase the prompt-cluster sample was
made after the original 36-prompt audit had been analyzed. It was motivated by
reviewer-facing precision, subgroup resolution, and replication concerns, not
by an outcome-dependent stopping threshold. The resulting study is therefore
reported as a deterministic, outcome-blind sequential augmentation, not as a
claim that the full 72-prompt design was preregistered before the original
audit.

The augmentation-selection program does not load model responses, evaluation
reports, or outcome matrices. It uses only frozen prompt records,
evaluator-facing reference signatures, the existing panel, and the previously
declared prompt-identifiability exclusions. The panel, requests, endpoints,
and analysis rules below were frozen before any augmentation prompt was sent
for a new repeat run.

Freeze time: `2026-07-15T14:39:20Z`.

## Frozen Selection

The completed original panel remains immutable:

- prompts: `36`;
- unique reference signatures: `36`;
- panel SHA-256:
  `a607d5cd17abb8728acfc857d7bcc6aa122f71945a4f4072808a4c52079dab61`.

The augmentation adds another `36` prompts and `36` signatures disjoint from
the original panel. It excludes the same four prespecified prompt-
identifiability exceptions. Its rank seed is derived rather than freely
chosen:

```text
seed = SHA256("pqid-bench-stochastic-repeatability-augmentation-v1"
              || NUL || original_panel_sha256).
```

The resulting seed is
`13523d72ec07fde91188178f214ae9c9558ae6d8f07baa097dd89a53c14e048b`.

Frozen augmentation artifacts:

- augmentation panel SHA-256:
  `9f36bdfabbfe53d0b719e95961d84cf50bb38c21a8dbbaf01d047416dfe241b0`;
- combined 72-prompt panel SHA-256:
  `3e242bf2d8db9e4deda76a1a62c06484949ff245e8aa6284c64948e51c4049ed`;
- augmentation-manifest SHA-256:
  `e31ebde8120f4c6f33d1267759a2407e8b83d33614aaf4db6af159f7ac5b4799`;
- selection-program SHA-256:
  `c94bb45e2269f382f7b02d589ce9fddd53c36aa90148dcbf3476d49c42c9179c`.

The combined panel has the following fixed margins:

- `36` pilot-cohort and `36` extension-cohort prompts;
- `24` prompts with `1-2` gate types, `24` with `3-4`, and `24` with `5+`;
- `29` barrier/staged and `43` non-barrier prompts;
- `72` distinct evaluator-facing reference signatures;
- no prompt-identifiability exception.

The augmentation itself contains `18` prompts from each benchmark cohort and
`12` from each gate-diversity band. Cross-stratum allocation is kept as close
to equal as the remaining unique-signature pool permits.

The frozen `3 x 2` crossing is:

| Gate-type bin | Pilot | Extension | Total |
| --- | ---: | ---: | ---: |
| `1-2` | 7 | 5 | 12 |
| `3-4` | 6 | 6 | 12 |
| `5+` | 5 | 7 | 12 |
| **Added panel** | **18** | **18** | **36** |

An exact `6/6` allocation in every row is infeasible: after excluding the
original panel's signatures and the four prompt-identifiability exceptions,
the eligible pool contains only five remaining pilot-cohort signatures in the
`5+` bin. The deterministic allocation therefore selects all five and places
the compensating pilot prompt in the `1-2` bin. This attains the exact cohort
and gate-diversity margins while minimizing the maximum cell deviation from
six. The combined 72-prompt panel covers `72 / 154 = 46.8%` of the complete
prompt set and `72 / 140 = 51.4%` of the eligible identifiable unique-signature
population.

## Frozen Requests And Runs

Run 1 for every added model-prompt cell is the already frozen canonical
154-prompt benchmark response. Runs 2 and 3 are new live-API draws. The
augmentation therefore requires

```text
21 * 36 * 2 = 1,512
```

new logical API calls. Together with the original panel, the final audit
contains

```text
21 * 72 * 3 = 4,536
```

model-prompt-run observations before any explicitly labeled transport
sensitivity.

Each of the 21 rows retains its canonical provider, provider route, model
identifier, request family, generation configuration, and provider request
body. The prepared augmentation request-manifest SHA-256 is
`911ae8e60ff994795a8220407bac90b0d35c0d8126cfed3da1d8c142fbdef9ea`.
Stored request-body hashes must be identical across all three runs for every
model-prompt pair. A valid response is never replaced because of its execution
or structural result.

## Inherited Endpoints And Provider Rules

Except for the expanded prompt panel and the separately reported augmentation
half, all endpoint, retry, evaluator, code-normalization, uncertainty, and
interpretation rules are inherited unchanged from:

- `stochastic_repeatability_21x36/PRESPECIFIED_PROTOCOL.md`, SHA-256
  `29b5026427df975eda8de75fb2c32de958270bb64f3aa1d3c64f1b0efdc4d577`;
- `stochastic_repeatability_21x36/PROTOCOL_AMENDMENTS.md`, SHA-256
  `8ca6d47ab24b590609d34e4e1a82abe066ec86452fc2f1722c5d174528b3066d`.

In particular,

```text
E_ifr = 1[the extracted program executes and returns a QuantumCircuit],
M_ifr = E_ifr * Q_ifr * K_ifr * T_ifr,
R_ifr = E_ifr - M_ifr,
Delta_ES,r = E_bar_r - M_bar_r = R_bar_r.
```

`T` is equality of the frozen complete gate-type count map. Scalar gate-count
agreement remains diagnostic because it is redundant under this convention.
The evaluator version and stored predicate must remain unchanged.

Direct routes retain at most three local transport attempts, retrying only
transport or provider-service failures before a valid response exists. OpenAI
Batch retains its provider-managed item lifecycle. Refusal, truncation, empty
output, execution failure, QASM3 failure, and signature failure are observed
outcomes and never retry triggers.

## Frozen Analysis

The following views are all reported:

1. the original 36-prompt panel;
2. the disjoint 36-prompt augmentation;
3. the pooled 72-prompt panel.

The pooled panel is the primary precision-enhanced repeatability estimate. The
two 36-prompt halves provide an explicit internal replication check; they are
not selected or relabeled according to their results.

For endpoint `Z` in `{E, M, R}`, the pooled run rate is

```text
Z_bar_r = (1 / (21 * 72)) * sum_f sum_i Z_ifr.
```

Primary uncertainty resamples the 21 model rows and 72 prompt-signature
columns independently with replacement using `5,000` crossed-bootstrap
replicates and seed `20260715`. The fixed-effects run model contains Run 2 and
Run 3 indicators plus model and prompt fixed effects. Pairwise agreement,
Gwet's AC1, directional flips, unanimity, all eight three-run patterns,
rank stability, majority-vote sensitivity, exact code equality, and the
prespecified descriptive paired tests are recomputed on the pooled panel.

Panel-half estimates and their original-versus-augmentation differences use
the same crossed dependence logic. Gate-diversity, pilot/extension, and
barrier strata are reported descriptively. Gate-bin-standardized results use
the unchanged full-benchmark weights `42/154`, `85/154`, and `27/154`.

The primary analysis retains every frozen model-prompt cell, including
provider errors. A secondary common-cell sensitivity excludes a model-prompt
pair only when at least one run has a known recorded transport disturbance.
The same surviving pair set must be used in all three runs; its denominator is
computed from the observed union of recorded disturbances and is not assumed
in advance. Missing attempt traces remain unknown rather than being labeled
clean.

No interim result may alter the panel, target sample size, model roster,
provider route, endpoint, retry envelope, or reporting set. Collection ends
only after every planned logical cell has either a valid response or a frozen
terminal provider-error record.
