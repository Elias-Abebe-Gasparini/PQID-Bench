# PQID-Bench Mutation-Stress Detection Baseline Report

- input file: `PQID/data/processed/pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl`
- selected rows: `11,999`
- clean controls: `734`
- mutation-stress rows: `11,265`
- split: deterministic stratified group split by `split_group_id`

## Detection Pool

| benchmark label | rows | target |
| --- | ---: | --- |
| `strict_n8` | 415 | `clean_control` |
| `extended_n8` | 319 | `clean_control` |
| `mutation_stress_n8` | 11,265 | `mutation_stress` |

## Split Counts

| split | clean_control | mutation_stress | total |
| --- | ---: | ---: | ---: |
| train | 580 | 9,012 | 9,592 |
| validation | 77 | 1,126 | 1,203 |
| test | 77 | 1,127 | 1,204 |

## Baselines

The direct mutation flag baseline is an audit sanity check, not a fair learned baseline. Learned baselines exclude direct target aliases.

| baseline | feature view | priors | accuracy | balanced accuracy | macro-F1 | AUROC | false-clean rate | false-stress rate | mismatches |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| majority class (mutation_stress) | none | n/a | 93.60% | 50.00% | 48.35% | 0.5000 | 0.00% | 100.00% | 77 |
| direct mutation flag | mutation_suite_candidate | n/a | 100.00% | 100.00% | 100.00% | 1.0000 | 0.00% | 0.00% | 0 |
| categorical Naive Bayes (source_proxy_metadata, empirical priors) | source and retrieval metadata, excluding direct mutation and release aliases | empirical | 94.60% | 80.18% | 78.61% | 0.8056 | 3.28% | 36.36% | 65 |
| categorical Naive Bayes (source_proxy_metadata, uniform priors) | source and retrieval metadata, excluding direct mutation and release aliases | uniform | 94.60% | 80.18% | 78.61% | 0.8056 | 3.28% | 36.36% | 65 |
| categorical Naive Bayes (structural_metadata, empirical priors) | validated circuit-structure metadata, excluding direct mutation aliases | empirical | 94.52% | 95.86% | 83.22% | 0.9907 | 5.68% | 2.60% | 66 |
| categorical Naive Bayes (structural_metadata, uniform priors) | validated circuit-structure metadata, excluding direct mutation aliases | uniform | 93.27% | 95.20% | 80.61% | 0.9907 | 7.01% | 2.60% | 81 |
| categorical Naive Bayes (code_tokens, empirical priors) | code lexical tokens only | empirical | 99.75% | 98.05% | 98.94% | 0.9905 | 0.00% | 3.90% | 3 |
| categorical Naive Bayes (code_tokens, uniform priors) | code lexical tokens only | uniform | 99.75% | 98.05% | 98.94% | 0.9905 | 0.00% | 3.90% | 3 |
| categorical Naive Bayes (structure_plus_code, empirical priors) | structural metadata plus code lexical tokens | empirical | 97.34% | 97.37% | 90.49% | 0.9910 | 2.66% | 2.60% | 32 |
| categorical Naive Bayes (structure_plus_code, uniform priors) | structural metadata plus code lexical tokens | uniform | 96.26% | 96.79% | 87.44% | 0.9910 | 3.82% | 2.60% | 45 |

## Best Fair Learned Baseline Per-Class Metrics

Best fair baseline: `categorical Naive Bayes (code_tokens, empirical priors)`.

| class | precision | recall | F1 | support |
| --- | ---: | ---: | ---: | ---: |
| `clean_control` | 100.00% | 96.10% | 98.01% | 77 |
| `mutation_stress` | 99.73% | 100.00% | 99.87% | 1,127 |

## Clean-Slice False-Stress Rates

| clean slice | support | false-stress rows | false-stress rate |
| --- | ---: | ---: | ---: |
| `strict_n8` | 47 | 1 | 2.13% |
| `extended_n8` | 30 | 2 | 6.67% |

## Direct Alias Fields Excluded From Fair Baselines

- `benchmark_view_membership`
- `benchmark_suitability_tier`
- `benchmark_suitability_tier_v2`
- `expected_model_stance`
- `evidence_regime`
- `mutation_suite_candidate`
- `release_view_membership`
- `public_release_bucket`
- `review_trace_id`
