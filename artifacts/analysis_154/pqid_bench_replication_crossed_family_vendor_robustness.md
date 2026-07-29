# PQID-Bench Replication And Crossed Robustness Audit

## Scope

This audit uses the frozen 21-model by 154-prompt matrix. It does not add model calls, change the evaluator, or make causal claims. The 84-prompt extension was selected without model outcomes, uses source-file-group-safe assignments, contains unique target signatures, and excludes every target signature present in the 70-prompt pilot.

## 1. Pilot-versus-extension replication

| final-21 cohort | prompts | signatures | execution | reference-signature match | ES gap | entropy OR per SD |
|---|---:|---:|---:|---:|---:|---:|
| pilot | 70 | 60 | 92.45% [88.89%, 95.30%] | 56.87% [44.77%, 68.59%] | +35.58 pp | 0.22 [0.07, 0.44] |
| prospective extension | 84 | 84 | 90.19% [87.70%, 92.46%] | 49.15% [40.87%, 57.09%] | +41.04 pp | 0.66 [0.33, 1.04] |

Across the original 15-model panel, pilot-versus-extension model ranks have Spearman rho `0.761` (two-sided p `0.0009932`). Across all 21 final rows, rho is `0.769` (p `4.659e-05`). Raw cohort rates are not expected to be equal because the extension deliberately adds new, quota-balanced signatures and a larger difficult-item share.

Replication criteria are claim-level: the ES gap must remain positive in both cohorts, and greater gate entropy must retain a point estimate below one within each cohort. The extension-only entropy interval slightly includes one, so the extension reproduces the direction but is not independently conclusive at the 95% level; the combined crossed analysis supplies the better-powered inferential result.

## 2. Crossed model-by-signature robustness

A `3,000`-replicate two-way bootstrap independently resamples all `21` model rows and all `144` target-signature clusters. This treats neither prompt-model cells nor model rows as independent fixed replicates.

| quantity | point estimate | crossed 95% interval |
|---|---:|---:|
| execution | 91.22% | [86.54%, 95.02%] |
| reference-signature match | 52.66% | [44.53%, 60.60%] |
| execution-structure gap | +38.56 pp | [+31.72 pp, +45.86 pp] |
| gate entropy, OR per SD | 0.49 | [0.27, 0.72] |
| barrier/staged marker, OR | 0.32 | [0.16, 0.65] |

## 3. Circuit-family balance

The unweighted signature rate is `52.66%`. Giving each primary circuit-family label equal weight yields `45.57%`. Pooling primary families represented by fewer than three prompts before macro-averaging yields `43.87%`, while the overlapping multi-label macro estimate is `44.12%`. The rare-pooled primary-family and micro model rankings have Spearman rho `0.926`.

Primary families are assigned by the prespecified ordered keyword taxonomy used in the existing complexity audit; this is a weighting sensitivity, not a claim that the keyword taxonomy is ontologically complete.

## 4. Leave-one-developer-out sensitivity

Developer denotes the checkpoint developer, not the API host. The Qiskit specialist is assigned to IBM/Qiskit and kept separate from its Mistral parent.

| omitted developer | models retained | execution | signature | ES gap | entropy OR |
|---|---:|---:|---:|---:|---:|
| none | 21 | 91.22% | 52.66% (+0.00 pp) | +38.56 pp | 0.49 |
| Alibaba/Qwen | 19 | 93.27% | 53.69% (+1.03 pp) | +39.58 pp | 0.47 |
| Anthropic | 18 | 89.90% | 51.33% (-1.32 pp) | +38.56 pp | 0.49 |
| DeepSeek | 19 | 91.32% | 52.32% (-0.34 pp) | +39.00 pp | 0.49 |
| Google | 19 | 91.08% | 52.15% (-0.51 pp) | +38.93 pp | 0.49 |
| IBM/Qiskit | 20 | 91.30% | 53.05% (+0.39 pp) | +38.25 pp | 0.48 |
| Meta | 17 | 92.02% | 54.77% (+2.12 pp) | +37.24 pp | 0.48 |
| Mistral AI | 19 | 91.15% | 52.70% (+0.04 pp) | +38.45 pp | 0.50 |
| OpenAI | 16 | 89.45% | 51.14% (-1.52 pp) | +38.31 pp | 0.51 |

Across the eight omissions, signature match ranges from `51.14%` to `54.77%`, the ES gap from `+37.24 pp` to `+39.58 pp`, and the adjusted entropy odds ratio from `0.47` to `0.51`. The qualitative conclusions therefore do not depend on any single developer group.

## Interpretation boundary

These analyses strengthen transportability and uncertainty accounting for the frozen benchmark release. They do not identify causal effects of circuit features, because prompt properties were not randomized and several descriptors co-vary. The ordered/operand-aware evaluator audit is reported separately.

## Reproduction

```powershell
python PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_robustness_suite.py
```

- machine-readable report: `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_replication_crossed_family_vendor_robustness.json`
- per-model cohort table: `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_pilot_extension_per_model.csv`
- family/developer sensitivity table: `PQID/submissions/acm_tqc_benchmark/artifacts/analysis_154/pqid_bench_family_vendor_sensitivity.csv`
- Supplemental Table S27 TSV: `PQID/submissions/acm_tqc_benchmark/tables_copy_ready/table_s27_pilot_extension_replication.tsv`
- Supplemental Table S28 TSV: `PQID/submissions/acm_tqc_benchmark/tables_copy_ready/table_s28_crossed_robustness.tsv`
- Supplemental Table S29 TSV: `PQID/submissions/acm_tqc_benchmark/tables_copy_ready/table_s29_family_vendor_sensitivity.tsv`
