# PQID-Bench Readiness And Packaging Report

- input file: `PQID/data/processed/pqid_2026_enriched_github_circuits_plus_metadata_design_v3.jsonl`
- source rows: `91,719`
- clean n/8 repository-clearance view: `True`

## Effective Slice By Release Bucket

This PQID-Bench release view treats `strict_n8` and `extended_n8` as repository-cleared based on the updated repository-level license evidence. The raw source-metadata audit is preserved in the next table.

| benchmark view | total | public_open | public_open_with_obligations | public_review_required | restricted_internal_only |
| --- | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 415 | 415 | 0 | 0 | 0 |
| `extended_n8` | 319 | 319 | 0 | 0 | 0 |
| `validated_broad_n8` | 1,531 | 847 | 5 | 2 | 677 |
| `validated_master_only` | 737 | 374 | 5 | 1 | 357 |
| `mutation_stress_n8` | 11,265 | 11,265 | 0 | 0 | 0 |
| `tier2_unvalidated` | 77,452 | 27,092 | 1,207 | 114 | 49,039 |

## Raw Source-Metadata Release Bucket Audit

These counts preserve the older row-level metadata before the repository-level clearance decision for the clean n/8 benchmark package.

| benchmark view | total | public_open | public_open_with_obligations | public_review_required | restricted_internal_only |
| --- | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 415 | 188 | 9 | 0 | 218 |
| `extended_n8` | 319 | 40 | 0 | 0 | 279 |
| `validated_broad_n8` | 1,531 | 847 | 5 | 2 | 677 |
| `validated_master_only` | 737 | 374 | 5 | 1 | 357 |
| `mutation_stress_n8` | 11,265 | 11,265 | 0 | 0 | 0 |
| `tier2_unvalidated` | 77,452 | 27,092 | 1,207 | 114 | 49,039 |

## Readiness Label Distribution

| label | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |
| `validated_broad_n8` | 1,531 |
| `validated_master_only` | 737 |
| `mutation_stress_n8` | 11,265 |
| `tier2_unvalidated` | 77,452 |

## Dependency-Free Baselines

The deterministic gate reconstruction is a sanity check for the documented readiness rules, not a learned ML baseline.

| baseline | accuracy | balanced accuracy | macro-F1 | false-clean rate | mismatches |
| --- | ---: | ---: | ---: | ---: | ---: |
| majority class (`tier2_unvalidated`) | 84.44% | 16.67% | 15.26% | 0.00% | 14,267 |
| deterministic n/8 gate reconstruction | 100.00% | 100.00% | 100.00% | 0.00% | 0 |

## Gate Reconstruction Per-Class Metrics

| label | precision | recall | F1 | support |
| --- | ---: | ---: | ---: | ---: |
| `strict_n8` | 100.00% | 100.00% | 100.00% | 415 |
| `extended_n8` | 100.00% | 100.00% | 100.00% | 319 |
| `validated_broad_n8` | 100.00% | 100.00% | 100.00% | 1,531 |
| `validated_master_only` | 100.00% | 100.00% | 100.00% | 737 |
| `mutation_stress_n8` | 100.00% | 100.00% | 100.00% | 11,265 |
| `tier2_unvalidated` | 100.00% | 100.00% | 100.00% | 77,452 |
