# PQID-Bench Final 21-Model Status Report

Generated: `2026-07-14`

## Executive Assessment

The primary external-generation experiment is complete and auditable. All
`21` named model rows contain one canonical outcome for each of the `154`
held-out prompts, giving a final `21 x 154 = 3,234` model-prompt matrix. The
matched Mistral parent and Qiskit-specialist checkpoints are ordinary members
of this roster and also support a within-roster paired comparison. The earlier
`19 x 154` matrix is retained only as a roster-sensitivity snapshot.

The central execution-structure gap remains the flagship result. Signature
failure establishes disagreement with at least one measured structural
component, whereas signature success does not establish ordered-circuit or
semantic equivalence. No further provider calls are required for the current
manuscript analysis.

## Final Experimental Design

- clean pool: `734` rows (`415` strict and `319` extended)
- split: `514` train, `66` validation, and `154` test rows
- test composition: `77` strict and `77` extended rows
- held-out structure: `143` source groups and `144` reference signatures
- source-group overlap between every split pair: `0`
- test-set construction: the `70`-prompt pilot plus `84` metadata-selected
  prompts, with no model outcomes used for selection
- primary model roster: `21` completed named rows
- primary model-prompt denominator: `3,234`

## Canonical External-Model Results

- executable circuit returned: `2,950 / 3,234` (`91.22%`)
- QASM3 export: `2,944 / 3,234` (`91.03%`)
- reference-signature match: `1,703 / 3,234` (`52.66%`)
- execution-structure gap: `38.56` percentage points
- runnable but signature-wrong: `1,247 / 3,234` (`38.56%`)
- signature-wrong among executable outputs: `1,247 / 2,950` (`42.27%`)
- reference-signature match conditional on execution: `57.73%`
- gate-type match: `60.42%`
- gate-count match: `77.86%`
- qubit-count match: `87.97%`
- classical-bit-count match: `77.55%`

The complete model table is stored in `tables_copy_ready/table_04.tsv` and in
`artifacts/analysis_154/PQID_BENCH_21_MODEL_PERFORMANCE_AND_INSIGHTS.md`.

## Roster Sensitivity

The initial `19`-model snapshot contains `2,926` cells, `91.35%` execution,
`53.28%` reference-signature match, and a `38.07`-point ES-gap. Moving to the
final 21-model roster changes pooled execution by `-0.13` points, signature
match by `-0.62` points, and the ES-gap by `+0.49` points. The main
interpretation is therefore not an artifact of adding the matched Mistral
pair. Files ending in `_initial19` preserve this check.

## Difficulty And Failure Structure

- prompts missed by all `21` models: `36`
- prompts matched by all `21` models: `16`
- prompts with mixed model disagreement: `102`
- dominant primary failure: gate-type mismatch (`996` cells)
- all nonmatches failing gate types: `1,280`
- executable nonmatches failing gate types: `996`

Reference-signature match is `71.20%` for targets with `1--2` gate types,
`54.17%` for `3--4`, and `19.05%` for `5+`. Prompt-level correlation with
signature match is weak for qubit count (`r=-0.052`) and stronger for
gate-type count (`r=-0.414`) and gate entropy (`r=-0.433`).

Cluster-aware grouped-binomial analysis associates standardized gate entropy
with lower signature recovery (odds ratio `0.49`) and barrier or staged
structure with a larger reduction (odds ratio `0.32`) after size adjustment.
The corresponding execution associations are smaller or uncertain. Under
target-signature-grouped cross-validation, AUC increases from `0.638` for the
size-only specification to `0.739` with entropy plus barriers and `0.743` with
gate types plus barriers. These are release-bound associations and predictive
comparisons, not causal effects.

## Sensitivity Analyses

Four prompts (`0040`, `0117`, `0141`, and `0142`) do not uniquely determine
their frozen reference signature from the model-visible text. Excluding them
produces a `150`-prompt sensitivity matrix with `3,150` cells, `91.75%`
execution, and `54.06%` reference-signature match. Model ordering is
unchanged.

The `154` prompts collapse to `144` unique reference signatures. Giving each
signature equal weight changes match from `52.66%` to `51.96%` (`-0.70`
points), so repeated signatures do not drive the headline result.

## Matched Parent-Specialist Comparison

The Mistral Small 3.2 24B parent reaches `48.70%` reference-signature match;
the Qiskit-specialized checkpoint reaches `44.81%`. The paired specialist
minus parent estimate is `-3.90` points with a target-signature-cluster
interval spanning zero. This supplies no evidence that specialization
improves the signature endpoint. Because the checkpoints were served through
different provider routes, the comparison does not isolate fine-tuning from
every serving-stack difference.

## Retrieval-Copy Context

TF-IDF instruction copy is the strongest non-oracle sparse-copy baseline at
`15.58%` reference-signature match. Six prompts representing four signatures
are matched by at least one sparse-copy baseline and by none of the `21`
models. This narrow complementarity motivates retrieval-conditioned generation
or signature-based reranking; it does not show that sparse copying is a strong
standalone generator or that copied programs are semantically equivalent.

## Completion And Recovery Diagnostics

- all `21` canonical rows are complete at `154 / 154`
- provider errors, refusals, and recovery attempts remain in append-only trace
  logs; only one canonical outcome per prompt enters scoring
- Fable prompt `0141` remains a provider-side refusal and is scored as a valid
  failure outcome rather than treated as missing data
- Codestral, Qwen3-Coder-Next, and Maverick recovery records are preserved but
  superseded records do not enter the matrix
- the evaluator correction audit changed only executor behavior for ordinary
  safe `print` and `reversed` built-ins; prompts, outputs, targets, and the
  scoring predicate were unchanged

## Interpretation Boundaries

1. Reference-signature match checks qubit count, classical-bit count, counted
   operation total, and gate-type multiset. It does not test gate order,
   operands, unitary equivalence, or output-distribution equivalence.
2. The ES-gap is an observed benchmark gap, not a causal effect or a complete
   semantic-error rate.
3. The four under-specified prompts require the labelled 150-prompt
   sensitivity analysis; they are retained in the stress-inclusive primary
   denominator for transparency.
4. Regression, bootstrap, permutation, rank, and cross-validation results are
   inferentially disciplined but remain specific to this fixed release.
5. Source-code execution reaches `100%` only after documented conservative
   context recovery; strict standalone source execution is `90.60%`.

## Publication Status

The analytical artifacts and all downstream publication derivatives use the
same final 21-model roster. Copy-ready tables, rendered figures, manuscript
sources, and the undeployed gateway are reproducible downstream outputs but are
not part of the public benchmark release. Package synchronization and automated
consistency validation are complete. The evidence supports the bounded core
claim:
strong systems usually emit executable quantum code, but recovering the
reference structure is substantially harder, especially for heterogeneous or
staged circuits.
