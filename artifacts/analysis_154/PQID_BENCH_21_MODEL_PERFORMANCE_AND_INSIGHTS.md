# PQID-Bench 21-Model Performance And Insight Report

## Reporting Design

PQID-Bench evaluates each of `21` completed models on the same `154` held-out
prompts, producing the final primary matrix of `3,234` prompt-model cells. The
roster includes `Qiskit/mistral-small-3.2-24b-qiskit` and its exact parent,
`mistralai/mistral-small-3.2-24b-instruct`, as ordinary model rows. Their
matched-checkpoint contrast is analyzed within this matrix. The earlier
`19 x 154` state is retained only as a roster-sensitivity snapshot.

Execution means that the generated program returns an executable Qiskit
`QuantumCircuit`. Reference-signature match requires simultaneous agreement in
qubit count, classical-bit count, counted-operation total, and the complete
gate-type count map, equivalently the operation multiset. Gate vocabulary is
only the support of that map and is not the scored equality object. Because
all `154` targets satisfy the frozen scalar/count-map identity, exact count-map
agreement implies scalar non-barrier gate-count agreement; the scalar component
is retained as a diagnostic rather than an independent conjunct. The predicate
does not test ordered gate tape, operands, unitary equivalence, or
measurement-distribution equivalence. The execution-structure gap (ES-gap) is
execution rate minus reference-signature-match rate.

The canonical evaluator is `pqid-bench-evaluator-1.1.0-safe-builtins`, and the
unchanged structural predicate is
`pqid-bench-reference-signature-1.0.0-count-map`.

## Performance Table

Rows are ordered by reference-signature match. Tied rates share a rank.

| rank | model | execution | reference signature | ES-gap | gate-type count map | gate count | QASM3 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | GPT-5.6 Sol | 99.35% | 62.99% | 36.36 pp | 70.78% | 88.96% | 99.35% |
| 1 | Claude Fable 5 | 98.05% | 62.99% | 35.06 pp | 70.13% | 89.61% | 98.05% |
| 3 | Gemini 3.1 Pro Preview | 96.75% | 61.04% | 35.71 pp | 67.53% | 86.36% | 96.75% |
| 4 | GPT-5.5 | 97.40% | 60.39% | 37.01 pp | 68.18% | 86.36% | 97.40% |
| 4 | GPT-5.4 Mini | 98.05% | 60.39% | 37.66 pp | 68.18% | 86.36% | 97.40% |
| 6 | Claude Opus 4.8 | 100.00% | 59.74% | 40.26 pp | 67.53% | 86.36% | 99.35% |
| 7 | DeepSeek V4 Pro | 91.56% | 59.09% | 32.47 pp | 64.94% | 81.82% | 91.56% |
| 7 | Claude Sonnet 4.6 | 99.35% | 59.09% | 40.26 pp | 66.23% | 84.42% | 99.35% |
| 9 | Codestral 25.01 | 93.51% | 55.84% | 37.66 pp | 63.64% | 82.47% | 93.51% |
| 10 | Gemini 2.5 Pro | 88.31% | 53.90% | 34.42 pp | 60.39% | 78.57% | 88.31% |
| 11 | GPT-OSS 120B | 96.75% | 53.25% | 43.51 pp | 59.74% | 79.87% | 96.10% |
| 12 | DeepSeek V4 Flash | 88.96% | 52.60% | 36.36 pp | 59.09% | 76.62% | 88.96% |
| 13 | Qwen3-Coder-Next | 85.71% | 50.65% | 35.06 pp | 58.44% | 74.03% | 85.71% |
| 13 | GPT-OSS 20B | 92.86% | 50.65% | 42.21 pp | 59.74% | 78.57% | 92.21% |
| 15 | Llama 4 Maverick | 94.16% | 48.70% | 45.45 pp | 62.34% | 81.82% | 93.51% |
| 15 | Mistral Small 3.2 24B Instruct | 90.26% | 48.70% | 41.56 pp | 57.79% | 74.68% | 90.26% |
| 17 | Llama 3.3 70B | 93.51% | 46.10% | 47.40 pp | 61.04% | 75.32% | 93.51% |
| 18 | Llama 4 Scout | 82.47% | 44.81% | 37.66 pp | 49.35% | 64.94% | 82.47% |
| 18 | Qiskit Mistral Small 3.2 24B | 89.61% | 44.81% | 44.81 pp | 51.30% | 64.29% | 88.96% |
| 20 | Qwen3 32B | 57.79% | 35.06% | 22.73 pp | 39.61% | 53.25% | 57.79% |
| 20 | Llama 3.1 8B | 81.17% | 35.06% | 46.10 pp | 42.86% | 60.39% | 81.17% |

## Aggregate Results

Across the final `21` rows, the primary aggregate is `2,950 / 3,234` execution
(`91.22%`) and `1,703 / 3,234` reference-signature match (`52.66%`). The
ES-gap is `38.56` points, and `1,247 / 2,950` executable outputs
(`42.27%`) are runnable but signature-wrong. Gate-type count-map match is
`60.42%`, scalar gate count `77.86%`, qubit count `87.97%`, classical-bit
count `77.55%`, and QASM3 export `91.03%`.

The prespecified prompt-identifiability sensitivity excludes four prompts
whose wording does not uniquely determine the frozen signature. On its common
`3,150`-cell denominator, execution is `2,890 / 3,150` (`91.75%`) and signature
match is `1,703 / 3,150` (`54.06%`). The identifiable-subset ES-gap is therefore
`1,187 / 3,150` (`37.68` points), and `1,187 / 2,890` executable outputs
(`41.07%`) remain signature-wrong. No full-154 execution rate is used in this
calculation.

As a roster-sensitivity check, the earlier `19`-model matrix records `91.35%`
execution, `53.28%` reference-signature match, and a `38.07`-point ES-gap.
Adding the matched Mistral rows therefore changes pooled execution by `-0.13`
points and signature match by `-0.62` points without changing the substantive
conclusions.

## Evaluator-Correction Audit

The superseded restricted-built-in evaluator reports `2,726 / 3,234`
executable circuits and `1,603 / 3,234` signature matches. Replaying the same
frozen outputs with ordinary safe support for `print` and `reversed` yields the
canonical `2,950` execution and `1,703` signature counts. Execution status
changes in `224` cells and signature status in `100`; every change is a gained
pass, with no losses. The ES-gap increases from `34.72` to `38.56` points
because admissibility repair recovers more executable circuits than signature
matches.

No prompt, response, target, split assignment, request/response hash, or
structural predicate changes. The canonical replay disagrees with the released
matrix in `0` cells, and all `21` per-model JSON and Markdown reports carry the
evaluator and predicate version identifiers.

## Robustness And Stricter Validation

- The original `70`-prompt cohort retains a `35.58`-point ES-gap, while the
  prospectively selected, signature-disjoint `84`-prompt extension retains a
  `41.04`-point gap. Final-model rankings across cohorts have Spearman
  \(\rho=0.769\).
- A `3,000`-replicate crossed model-by-signature bootstrap gives a `95%`
  interval of `31.72--45.86` points for the ES-gap, `0.27--0.72` for the
  entropy odds ratio, and `0.16--0.65` for the barrier/staged-marker odds ratio.
- Leave-one-developer-out estimates keep signature match within
  `51.14--54.77%` and the ES-gap within `37.24--39.58` points. Family-balanced
  weighting lowers the absolute signature rate but preserves the main model
  gradient.
- Exact ordered operation-and-wire tape agrees in `1,576 / 1,703` signature
  passes (`92.54%`, crossed interval `87.94--96.20%`). The remaining `127`
  cases are signature-only passes, not automatically semantic errors; exact
  source tape is stricter than physical equivalence.

## Main Insights

1. **Execution-structure gap.** High execution is not evidence that the
   intended circuit structure was recovered. Even the strongest rows retain
   ES-gaps of roughly `35-40` points, and the all-model descriptive gap remains
   `38.56` points.

2. **Structural hallucination.** The dominant practical failure is plausible,
   executable quantum code that loses at least one frozen target descriptor.
   In the final matrix, `42.27%` of executable outputs have this form. The
   term should be interpreted at the reference-signature level, not as proof
   of semantic or physical incorrectness.

3. **Frontier plateau.** The top eight rows occupy a narrow
   `59.09-62.99%` signature band despite execution rates as high as `100%`.
   Signature-cluster rank resampling is globally stable (mean Spearman
   `0.961`, `95%` interval `[0.916, 0.988]`), but exact frontier positions are
   uncertain.

4. **Complexity-depth divergence.** Width alone is weakly related to
   per-prompt success (`r=-0.052`). Gate entropy (`r=-0.433`) and gate-type
   count (`r=-0.414`) are much stronger difficulty descriptors. Signature
   match falls from `71.20%` for `1-2` gate types to `54.17%` for `3-4` and
   `19.05%` for `5+`.

5. **Heterogeneity acts mainly after execution.** Adjusted grouped-binomial
   models associate gate entropy with signature loss (OR `0.49`, cluster
   interval `[0.28, 0.71]`) and barrier/staged structure with an even larger
   loss (OR `0.32`, `[0.16, 0.62]`). Conditional on execution, the respective
   ORs remain `0.49` and `0.29`. Their execution associations are much smaller
   or uncertain, indicating that heterogeneity primarily produces runnable
   but structurally drifting outputs.

6. **Diversity improves prediction beyond size.** Target-signature-grouped
   cross-validation raises AUC from `0.638` for the size-only model to `0.739`
   with entropy plus barriers and `0.743` with gate types plus barriers. Brier
   score improves from `0.2329` to `0.2060` and `0.2047`; the corresponding
   improvement intervals exclude zero. Log loss also improves in point
   estimate, although its bootstrap intervals include zero.

7. **Specialization is objective-dependent.** Qwen3-Coder-Next improves over
   Qwen3 32B by `15.58` signature points (`95%` cluster interval
   `[7.24, 23.75]`; Holm `p=0.0108`). In contrast, the Qiskit specialist is
   `3.90` points below its exact Mistral parent. In the dedicated
   seven-endpoint paired analysis, the interval is `[-10.26, +2.47]` and the
   cluster value is `p=0.3077`; the broader eleven-comparison run gives the
   nearly identical interval `[-10.26, +2.55]` and `p=0.3071`. Its gate-count
   agreement is `10.39` points lower and is the
   only paired endpoint surviving seven-endpoint Holm correction
   (`p=0.0346`). Domain vocabulary or fine-tuning alone therefore does not
   guarantee structural fidelity.

8. **Scaling is not uniform.** Llama 3.3 70B exceeds Llama 3.1 8B by `11.04`
   signature points, but narrowly misses the family-wise threshold (Holm
   `p=0.0622`).
   Scout-to-Maverick is `+3.90` points with an interval spanning zero;
   GPT-5.4 Mini to GPT-5.5 is `0.00` points. Larger or newer models do not
   automatically reduce the ES-gap.

9. **Retrieval-copy complementarity.** TF-IDF instruction copy is weak overall
   (`15.58%` signature match), but six prompts representing four signatures
   are matched by at least one sparse-copy baseline and by none of the `21`
   model rows. Retrieval and direct generation therefore discard
   different information. This motivates retrieval-conditioned generation and
   constraint-based reranking, not a claim that sparse copy solves the task.

10. **Semantic void and prompt identifiability.** Four prompts do not uniquely
    determine their frozen reference signatures. On the common `3,150`-cell
    sensitivity denominator, execution is `91.75%`, signature match is
    `54.06%`, the ES-gap is `37.68` points, and `41.07%` of executable outputs
    remain signature-wrong. Model order is unchanged. These cases reveal a
    specification gap rather than pure model failure and motivate
    pre-inference prompt-identifiability review.

11. **Repeated templates do not drive the result.** The `154` prompts represent
    `144` reference signatures. Giving each signature equal weight changes the
    primary rate only from `52.66%` to `51.96%` (`-0.70` points).

12. **Failure anatomy.** The gate-type count map differs in `1,280` of all
    `1,531` signature nonmatches and in `996` of the `1,247` executable
    nonmatches. These overlapping component counts make count-map disagreement
    the dominant observed failure component. Qubit and classical-width checks
    add distinct information. Scalar gate count remains useful for diagnosing
    total-size errors, but it does not add an independent restriction when the
    complete count map already matches.

13. **Benchmark discrimination.** Among the `154` prompts, `36` are missed by
    all `21` models, `16` are matched by all, and `102` produce mixed
    disagreement. The split therefore contains universal stress cases, sanity
    checks, and a large model-discriminating middle region.

## Interpretation Boundaries

- The complete `21`-model matrix is the primary experiment. The initial
  `19`-model state is retained only to show that roster expansion does not
  materially change the pooled conclusions.
- The Qiskit specialist and parent use identical prompt and generation-config
  hashes for all `154` rows, but different serving providers. Their comparison
  does not isolate fine-tuning from every serving-stack effect.
- Associations between circuit descriptors and success are inferential and
  release-bound, not causal.
- Reference-signature match is an intermediate structural screen. Ordered
  gate tape, operand placement, unitary equivalence, and measurement-aware
  simulation remain future evaluation layers.
- The count-map predicate is stronger than gate-vocabulary equality but weaker
  than ordered or semantic equivalence. The separately reported scalar gate
  count is diagnostic and algebraically redundant in the joint pass set for
  this release.
- A documented evaluator audit added ordinary safe `print` and `reversed`
  built-ins and rescored every frozen output. No prompt, response, denominator,
  target, or scoring predicate changed.

## Source Artifacts

- `artifacts/analysis_154/pqid_bench_item_failure_matrix_analysis.md`
- `tables_copy_ready/table_04.tsv`
- `tables_copy_ready/table_s26_qiskit_specialist_parent.tsv`
- `artifacts/analysis_154/qiskit_specialist_parent_comparison.md`
- `artifacts/analysis_154/pqid_bench_inferential_analysis.md`
- `artifacts/analysis_154/pqid_bench_prompt_identifiability_sensitivity.md`
- `artifacts/analysis_154/pqid_bench_replication_crossed_family_vendor_robustness.md`
- `artifacts/analysis_154/pqid_bench_ordered_operand_validation.md`
- `artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv`
- `artifacts/analysis_154/evaluator_builtin_correction/evaluator_builtin_correction_report.md`
