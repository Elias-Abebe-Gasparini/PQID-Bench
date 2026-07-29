# PQID-Bench Stochastic Repeatability Protocol

## Status And Freeze Boundary

This document freezes the analysis and reporting rules for the 21-model by
36-prompt by 3-run stochastic repeatability audit. The 36-prompt panel was
selected outcome-blind on 2026-07-15 before either repeat run was observed.
The statistical safeguards in this document were finalized at
`2026-07-15T18:01:15+09:00`, after Run 2 API collection had completed but
before any Run 3 response existed and before a repeatability analysis artifact
had been generated. During this finalization, generated code and Run 2 endpoint
outcomes were not inspected. This is therefore an outcome-blind panel with a
prospectively frozen Run 3 analysis plan, not a claim of registry-based
preregistration before all Run 2 transmission.

An implementation audit initiated while Run 3 collection was underway
identified protocol ambiguities. The user-launched process generated
preliminary analysis artifacts before all corrections were finalized, but
those outcome files were not inspected and are explicitly invalidated. The
non-outcome-driven corrections are recorded in `PROTOCOL_AMENDMENTS.md`; the
corrected analyzer enforces the final protocol and amendment hashes.

At the freeze boundary:

- Run 2 had `21` response files with `36` rows each;
- the concurrently running evaluator had not yet completed all Run 2 model rows;
- Run 3 had `0` response files and `0` evaluation directories;
- the final analysis directory contained no result artifact.

No repeat response may replace another valid response because of its execution,
signature, or code-quality result.

Before estimation, the analyzer must verify one unchanged evaluator version,
one unchanged stored predicate version, and identical stored request hashes
across Runs 1, 2, and 3 for every model-prompt pair. It must also verify the
hard-coded frozen panel-file hash and exact equality between every report's
hidden target metadata and the corresponding reference signature.

## Scientific Question

The audit asks whether the Execution-Structure Gap (ES-Gap), the
complexity-conditioned difficulty gradient, and the broad model ordering remain
stable across repeated live-API draws under nominally unchanged requests.

It separates:

1. cell-level repeatability for each model-prompt pair;
2. aggregate endpoint and ES-Gap repeatability;
3. reproducibility of the paper's scientific conclusions.

Runs 2 and 3 form the short-window stochastic-repeatability comparison. Run 1
versus Runs 2 or 3 is temporal deployment reproducibility and may include
decoding variation, provider routing, serving changes, or model updates.

## Frozen Panel

The panel contains `36` identifiable prompts and `36` distinct evaluator-facing
reference signatures. It is balanced by construction:

- `18` pilot prompts and `18` extension prompts;
- `12` prompts with `1-2` gate types, `12` with `3-4`, and `12` with `5+`;
- `14` barrier/staged prompts and `22` without barriers;
- none of the four prespecified prompt-identifiability exceptions.

Selection seed:
`pqid-bench-stochastic-repeatability-v1-20260715`.

Panel SHA-256:
`a607d5cd17abb8728acfc857d7bcc6aa122f71945a4f4072808a4c52079dab61`.

Because the gate-diversity strata receive equal allocation, the panel is a
prespecified stress-balanced repeatability panel. It is not described as a
representative sample of the full 154-prompt distribution.

## Frozen Endpoints

For model `f`, prompt `i`, and run `r`, define execution success as

```text
E_ifr = 1[the extracted program executes and returns a QuantumCircuit].
```

The nonredundant reference-signature endpoint is

```text
M_ifr = E_ifr * Q_ifr * K_ifr * T_ifr,
```

where `Q` is qubit-count equality, `K` is classical-bit-count equality, and
`T` is equality of the complete gate-type count map. Scalar non-barrier gate
count agreement `G` remains a reported diagnostic but is not an independent
conjunct, because the frozen count-map convention implies `T => G`. The
analyzer must assert that explicit `QKT` and the legacy stored `QKGT`
`all_match` field select exactly the same cells.

The runnable-but-signature-wrong endpoint is

```text
R_ifr = E_ifr - M_ifr.
```

The analyzer must verify this identity at cell and aggregate levels. QASM3
export remains a secondary diagnostic.

## Primary Estimands

For `Z` in `{E, M, R}`, the balanced-panel run rate is

```text
Z_bar_r = (1 / (21 * 36)) * sum_f sum_i Z_ifr.
```

The run-specific ES-Gap is

```text
Delta_ES,r = E_bar_r - M_bar_r = R_bar_r.
```

For runs `r` and `s`, total and directional flips are

```text
F_Z(r,s)   = mean(1[Z_ifr != Z_ifs]),
F_Z+(r,s)  = mean(1[Z_ifr = 0 and Z_ifs = 1]),
F_Z-(r,s)  = mean(1[Z_ifr = 1 and Z_ifs = 0]).
```

Three-run unanimity is

```text
U_Z = mean(1[Z_if1 = Z_if2 = Z_if3]).
```

All eight binary three-run patterns are retained so symmetric churn cannot be
hidden by a stable aggregate rate.

## Weighting And Strata

Panel-unweighted estimates are primary. As a secondary sensitivity, the panel's
gate-bin rates are standardized to the full 154-prompt gate-bin frequencies:

- `1-2`: `42/154`;
- `3-4`: `85/154`;
- `5+`: `27/154`.

This is a gate-bin-standardized panel sensitivity, not an unbiased estimate of
the 154-prompt population. It does not correct signature-unique selection, the
four zero-inclusion identifiability exceptions, pilot/extension balance, or
barrier balance.

Run-specific rates are also reported by pilot/extension cohort, gate-diversity
band, and barrier presence. These tables assess directional persistence of the
complexity and staged-structure gradients; they are not causal estimates.

## Crossed Dependence And Inference

The outcome matrix is crossed by model and prompt. Primary uncertainty for
pooled rates, agreements, AC1 statistics, and run-rate differences therefore
uses an independent model-by-prompt bootstrap: resample the 21 model rows and
36 prompt signatures independently with replacement. The seed is `20260715`
and the final analysis uses `5,000` replicates. A prompt-only bootstrap with the
21-model roster fixed is retained as a sensitivity.

For each endpoint in `{E, M, R}`, the primary run-effect specification is a
linear-probability model with Run 2 and Run 3 indicators plus model and prompt
fixed effects. This parameterization directly estimates percentage-point run
differences and avoids binary-model separation at high execution prevalence.
Crossed-bootstrap intervals and tests are primary. Cameron-Gelbach-Miller
two-way clustered covariance is reported as a sensitivity. A joint empirical
test uses the Euclidean magnitude of the Run 2 and Run 3 coefficient vector
against its centered crossed-bootstrap null distribution; this remains defined
when bootstrap covariance is singular. Pairwise and joint bootstrap p-values
use the finite-replicate plus-one correction.

These intervals condition on the three observed run occasions. They generalize
over the audited model and prompt dimensions, not over a hypothetical
population of future API dates or unobserved common deployment shocks.

Gwet's AC1 is the primary chance-adjusted agreement statistic. Pairwise values
are reported for Runs 1-2, 1-3, and 2-3. Ordinary pooled Cochran's Q is labeled
descriptive because its independence assumption does not match the crossed
matrix. Exact McNemar tests are reported per model, and pooled exact McNemar
with Holm adjustment is retained only as a familiar paired-cell sensitivity.

## Provider And Retry Policy

The canonical trial is the first valid provider response obtained within the
route-specific attempt envelope. A valid refusal, empty completion, truncation,
Python execution failure, QASM3 failure, or signature failure is an observed
model outcome and never a retry trigger. No best-of-n response selection is
permitted.

For direct API routes:

- at most three local transport attempts (`--max-retries 2`);
- local backoff of `1` second and then `2` seconds;
- retry only after a timeout, connection, HTTP, or provider service exception
  before a valid response exists;
- hidden retries are disabled in the OpenAI-compatible SDK for newly started
  direct-route processes.

OpenAI Batch submits one item per model-prompt-run cell. It uses the provider's
batch validation, processing, and item-error lifecycle and receives no local
response-level resubmission under this protocol.

Attempt count, attempt timestamps, error class, recovery status, request hash,
and response hash are recorded where the route runner exposes them. Run 1,
already-completed Run 2 processes, and provider-managed batch rows may lack a
local attempt trace; their attempt count, initial-attempt status, and recovery
status must remain null rather than receive an invented history. Trace coverage
requires a nonempty attempt-trace array whose length equals the recorded attempt
count. The secondary transport sensitivity excludes cells with a known
recorded transport disturbance. It does not imply that untraced rows are proven
disturbance-free.

## Generated-Code Equality

Code reproducibility is evaluated at two explicitly separate levels.

Normalized-text equality:

- convert CRLF and CR to LF;
- remove one outer Markdown Python code fence;
- remove leading and trailing blank lines;
- strip trailing whitespace;
- collapse consecutive blank lines;
- preserve comments, identifiers, literals, statement order, indentation, and
  interior token spacing.

Canonical-AST equality:

- parse the normalized text with Python `ast.parse`;
- serialize with `ast.dump(annotate_fields=True, include_attributes=False)`;
- preserve identifiers, literals, operands, and statement order;
- do not rename variables or reorder statements.

All-three and pairwise equality are reported with their applicable denominators.
AST equality is stricter than functional equivalence and is not labeled a
semantic-equivalence test.

## Model Ordering And Majority Vote

Per-model rates move in increments of `1/36 = 2.78` percentage points. The
ordering audit therefore emphasizes Spearman correlation, Kendall tau-b,
tie-inclusive top-five overlap, frontier-cluster means, and each model's
three-run minimum-to-maximum range. Exact rank positions are not treated as
stable quantities.

The three-run majority-vote endpoints are secondary deployment sensitivities:

```text
M_if^maj = 1[M_if1 + M_if2 + M_if3 >= 2].
E_if^maj = 1[E_if1 + E_if2 + E_if3 >= 2].
R_if^maj = E_if^maj - M_if^maj.
```

The ES-Gap uses the derived `R_if^maj`, preserving `R=E-M`. A separate direct
majority vote over the three runwise `R_ifr` values is reported only as a
diagnostic because it need not equal the derived endpoint. Majority voting does
not replace the canonical single-draw benchmark and is not used to select or
discard a run.

## Interpretation Boundary

The audit can support repeatability of system-level benchmark conclusions, not
causal attribution of individual flips. The central claim is considered
reproducible when the three ES-Gaps remain large and similar, the diversity and
barrier gradients remain directionally consistent, and the broad model
ordering remains correlated even if some individual cells change state.

Crossed-bootstrap uncertainty is conditional on these three observed run
occasions and must not be described as an estimate of the distribution over all
future provider deployments.
