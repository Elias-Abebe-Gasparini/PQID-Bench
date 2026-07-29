# Ordered And Operand-Aware Validation Of The PQID-Bench Signature Predicate

## Audit design

- evaluator version: `pqid-bench-evaluator-1.1.0-safe-builtins`
- structural predicate: `pqid-bench-reference-signature-1.0.0-count-map`

The audit replays `3,234` frozen prompt-model outputs and the `154` clean reference programs through the same restricted Qiskit namespace and circuit-selection functions used by the published harness. Clean references receive the conservative metadata-derived context aliases already documented by the source-validity ablation; generated outputs retain the strict standalone namespace. The audit compares the selected circuits without changing the headline scores.

The current reference-signature predicate is

$$M_i(f)=Q_i(f)K_i(f)T_i(f),$$

where the scored indicators compare qubit count, classical-bit count, and the complete gate-type count map. Scalar non-barrier gate-count agreement is recorded separately as G_i(f). Because exact count-map equality implies scalar gate-count equality for every frozen target and evaluated candidate, G_i(f) is retained as a diagnostic rather than an independent restriction. The stricter ordered-wire diagnostic is

$$W_i(f)=\mathbf{1}[(q_i,c_i,(o_t,\mathbf{q}_t,\mathbf{c}_t)_{t=1}^{L_i})=(q_i^*,c_i^*,(o_t^*,\mathbf{q}_t^*,\mathbf{c}_t^*)_{t=1}^{L_i^*})],$$

with circuit widths $(q_i,c_i)$, operation name $o_t$, ordered quantum operands $\mathbf{q}_t$, and ordered classical operands $\mathbf{c}_t$ at tape position $t$. Parameter tokens and global phase are reported as still stricter diagnostics.

## Replay integrity

All `154` reference circuits materialized and matched their frozen signatures; reference failures: `0`. Of `2,950` outputs marked executable by the stored reports, `2,950` replayed successfully. Signature replay disagreements: `0`; selected-circuit-name disagreements: `0`.

## Conditional agreement among current signature passes

| diagnostic | matches / signature passes | rate | crossed model-by-signature 95% interval |
|---|---:|---:|---:|
| operation-name order | 1,633 / 1,703 | 95.89% | [92.77%, 98.50%] |
| ordered quantum operands | 1,578 / 1,703 | 92.66% | [88.39%, 96.36%] |
| ordered classical operands | 1,686 / 1,703 | 99.00% | [97.48%, 99.89%] |
| ordered operation-and-wire tape | 1,576 / 1,703 | 92.54% | [87.94%, 96.20%] |
| ordered wire tape plus exact parameter values | 1,545 / 1,703 | 90.72% | [85.54%, 94.77%] |
| parameter-aware tape plus global phase | 1,545 / 1,703 | 90.72% | [85.86%, 94.83%] |

For signature-matched targets containing measurements, the exact qubit-to-classical-bit map agrees in `1,029 / 1,044` cases (`98.56%`). There are `0` replayed ordered-wire matches outside the current signature-pass set; an exact ordered-wire match should imply the four coarser signature components, so any nonzero value would indicate an evaluator inconsistency.

A signature pass that fails the ordered-wire test is called a *signature-only pass* here, not a semantic false positive. Exact source order is stricter than physical or algorithmic equivalence and can reject valid commuting or rewritten circuits.

## Cohort sensitivity

| cohort | cells | signature passes | ordered-wire / signature | parameter-aware / signature |
|---|---:|---:|---:|---:|
| pilot | 1,470 | 836 | 795/836 (95.10%) | 784/836 (93.78%) |
| extension | 1,764 | 867 | 781/867 (90.08%) | 761/867 (87.77%) |

Excluding the four prespecified prompt-identifiability exceptions leaves `3,150` cells and `1,703` signature passes. Its ordered-wire conditional agreement is `92.54%`.

## Per-model audit

| model | executable | signature | ordered-wire | ordered-wire / signature | parameter-aware / signature |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 Sol | 153 | 97 | 90 | 92.78% | 90.72% |
| GPT-5.5 | 150 | 93 | 86 | 92.47% | 91.40% |
| GPT-5.4 mini | 151 | 93 | 87 | 93.55% | 91.40% |
| Claude Fable 5 | 151 | 97 | 90 | 92.78% | 91.75% |
| Claude Sonnet 4.6 | 153 | 91 | 84 | 92.31% | 91.21% |
| Claude Opus 4.8 | 154 | 92 | 87 | 94.57% | 92.39% |
| Gemini 2.5 Pro | 136 | 83 | 77 | 92.77% | 92.77% |
| Gemini 3.1 Pro Preview | 149 | 94 | 86 | 91.49% | 90.43% |
| DeepSeek V4 Pro | 141 | 91 | 87 | 95.60% | 92.31% |
| DeepSeek V4 Flash | 137 | 81 | 77 | 95.06% | 93.83% |
| Codestral 25.01 | 144 | 86 | 78 | 90.70% | 86.05% |
| Qwen3-Coder-Next | 132 | 78 | 69 | 88.46% | 88.46% |
| Llama 4 Maverick | 145 | 75 | 71 | 94.67% | 94.67% |
| Llama 3.3 70B | 144 | 71 | 63 | 88.73% | 87.32% |
| GPT-OSS 120B | 149 | 82 | 77 | 93.90% | 91.46% |
| GPT-OSS 20B | 143 | 78 | 73 | 93.59% | 89.74% |
| Mistral Small 3.2 24B | 139 | 75 | 67 | 89.33% | 86.67% |
| Qiskit Mistral 3.2 24B | 138 | 69 | 65 | 94.20% | 92.75% |
| Qwen3 32B | 89 | 54 | 49 | 90.74% | 85.19% |
| Llama 4 Scout | 127 | 69 | 61 | 88.41% | 86.96% |
| Llama 3.1 8B | 125 | 54 | 52 | 96.30% | 96.30% |

## Interpretation

The ordered-wire rate quantifies how often the current signature predicate also recovers the evaluator-selected reference operation-and-operand tape. It should be used as a validation layer and a design target for PQID-Bench 2, not retroactively substituted for the published headline denominator. Parameter-token and global-phase agreement are separate stricter representation-level checks; neither proves nor disproves semantic circuit equivalence.

## Reproduction

```powershell
python PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_ordered_operand_validation.py
```

- machine-readable summary: `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_ordered_operand_validation.json`
- cell-level audit: `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_ordered_operand_cell_audit.jsonl`
- per-model table: `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_ordered_operand_by_model.csv`
- Supplemental Table S30 TSV: `PQID/submissions/acm_tqc_benchmark/tables_copy_ready/table_s30_ordered_operand_validation.tsv`
