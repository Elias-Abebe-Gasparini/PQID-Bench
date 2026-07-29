# PQID-Bench Learned Readiness Baseline Report

- input file: `PQID/data/processed/pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl`
- source rows: `91,719`
- split policy: deterministic stratified group split by `split_group_id`
- group overlap: train/validation `0`, train/test `0`, validation/test `0`

## Direct Fields Excluded

`benchmark_view_membership`, `benchmark_suitability_tier`, `benchmark_suitability_tier_v2`, `expected_model_stance`, `evidence_regime`, `release_view_membership`, `public_release_bucket`, `review_trace_id`

## Feature Sets

| feature set | categorical fields | numeric fields |
| --- | --- | --- |
| `source_proxy_metadata` | `source`, `language`, `retrieval_mode`, `qiskit_version`, `circuit_stats_available`, `validation_error_type`, `openqasm3_export_successful`, `api_deprecated_usage` | `prompt_length_chars`, `prompt_word_count`, `prompt_token_count_cl100k`, `output_token_count_cl100k` |
| `primitive_metadata` | `validation_status`, `extraction_confidence`, `contains_demo_scaffolding`, `cleanup_candidate`, `retrieval_strategy`, `retrieval_mode`, `mutation_suite_candidate` | `code_lines`, `gate_count` |
| `broad_metadata` | `validation_status`, `extraction_confidence`, `contains_demo_scaffolding`, `cleanup_candidate`, `retrieval_strategy`, `retrieval_mode`, `mutation_suite_candidate`, `circuit_stats_available`, `context_sufficiency_class`, `repairability_band`, `domain_slice`, `shift_axis`, `source`, `language`, `validation_error_type`, `openqasm3_export_successful`, `api_deprecated_usage` | `code_lines`, `gate_count`, `repairability_score`, `prompt_length_chars`, `prompt_word_count`, `prompt_token_count_cl100k`, `output_token_count_cl100k` |

## Split Summary

| split | rows | groups | strict_n8 | extended_n8 | validated_broad_n8 | validated_master_only | mutation_stress_n8 | tier2_unvalidated |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 73,387 | 37,182 | 338 | 260 | 1,253 | 590 | 9,012 | 61,934 |
| validation | 9,183 | 4,648 | 39 | 32 | 131 | 65 | 1,126 | 7,790 |
| test | 9,149 | 4,650 | 38 | 27 | 147 | 82 | 1,127 | 7,728 |

## Test Results

| baseline | accuracy | balanced accuracy | macro-F1 | false-clean rate | mismatches |
| --- | ---: | ---: | ---: | ---: | ---: |
| majority class (`tier2_unvalidated`) | 84.47% | 16.67% | 15.26% | 0.00% | 1,421 |
| categorical Naive Bayes (source_proxy_metadata, empirical priors) | 98.27% | 64.17% | 62.97% | 0.15% | 158 |
| categorical Naive Bayes (source_proxy_metadata, uniform priors) | 93.07% | 71.88% | 52.96% | 5.48% | 634 |
| categorical Naive Bayes (primitive_metadata, empirical priors) | 100.00% | 100.00% | 100.00% | 0.00% | 0 |
| categorical Naive Bayes (primitive_metadata, uniform priors) | 99.93% | 99.42% | 98.13% | 0.01% | 6 |
| categorical Naive Bayes (broad_metadata, empirical priors) | 99.87% | 98.64% | 99.20% | 0.00% | 12 |
| categorical Naive Bayes (broad_metadata, uniform priors) | 99.98% | 99.77% | 99.87% | 0.00% | 2 |

## Source-Proxy Empirical Priors Per-Class Metrics

| label | precision | recall | F1 | support |
| --- | ---: | ---: | ---: | ---: |
| `strict_n8` | 53.85% | 73.68% | 62.22% | 38 |
| `extended_n8` | 0.00% | 0.00% | 0.00% | 27 |
| `validated_broad_n8` | 67.01% | 44.22% | 53.28% | 147 |
| `validated_master_only` | 63.64% | 68.29% | 65.88% | 82 |
| `mutation_stress_n8` | 94.09% | 98.85% | 96.41% | 1,127 |
| `tier2_unvalidated` | 100.00% | 100.00% | 100.00% | 7,728 |

Best learned model by macro-F1: **categorical Naive Bayes (primitive_metadata, empirical priors)**.

## Best Learned Model Per-Class Metrics

| label | precision | recall | F1 | support |
| --- | ---: | ---: | ---: | ---: |
| `strict_n8` | 100.00% | 100.00% | 100.00% | 38 |
| `extended_n8` | 100.00% | 100.00% | 100.00% | 27 |
| `validated_broad_n8` | 100.00% | 100.00% | 100.00% | 147 |
| `validated_master_only` | 100.00% | 100.00% | 100.00% | 82 |
| `mutation_stress_n8` | 100.00% | 100.00% | 100.00% | 1,127 |
| `tier2_unvalidated` | 100.00% | 100.00% | 100.00% | 7,728 |

## Best Learned Model Confusion Matrix

| true label | strict_n8 | extended_n8 | validated_broad_n8 | validated_master_only | mutation_stress_n8 | tier2_unvalidated |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 38 | 0 | 0 | 0 | 0 | 0 |
| `extended_n8` | 0 | 27 | 0 | 0 | 0 | 0 |
| `validated_broad_n8` | 0 | 0 | 147 | 0 | 0 | 0 |
| `validated_master_only` | 0 | 0 | 0 | 82 | 0 | 0 |
| `mutation_stress_n8` | 0 | 0 | 0 | 0 | 1,127 | 0 |
| `tier2_unvalidated` | 0 | 0 | 0 | 0 | 0 | 7,728 |
