# PQID-Bench Frozen 154-Prompt Split

- split ID: `pqid-bench-clean-generation-154-v1`
- frozen at UTC: `2026-07-12T09:34:21+00:00`
- pilot prompts retained unchanged: `70`
- prospectively selected extension prompts: `84`
- final held-out prompts: `154`
- unique final target signatures: `144`
- model outcomes were not used to select extension rows

## Allocation

| split | rows | groups | strict clean | extended clean | 1-2 gate types | 3-4 gate types | 5+ gate types | unique signatures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 514 | 386 | 301 | 213 | 146 | 285 | 83 | 334 |
| validation | 66 | 59 | 37 | 29 | 13 | 36 | 17 | 60 |
| test | 154 | 143 | 77 | 77 | 42 | 85 | 27 | 144 |

## Selection Contract

The original 70-prompt order and identifiers are preserved. The extension moves entire singleton source-file groups from the original training split, excludes target signatures already present in the pilot, and admits at most one row per evaluator-facing signature. The final test set is balanced 77/77 across strict and extended clean views. Its 42/85/27 gate-diversity allocation is the largest-remainder projection of the complete 734-row clean pool. The joint view-by-diversity allocation is the integer solution with the smallest squared deviation from each clean view's source-pool composition under those fixed margins.

The split leaves 514 training rows (70.03% of the clean pool), keeps the existing 66-row validation partition unchanged, and contains no source-file group overlap between train, validation, and test.

## Frozen Artifacts

- split manifest: `artifacts/test_split_154/pqid_bench_split_154_manifest.json`
- complete prompt manifest: `artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl`
- extension-only prompt manifest: `artifacts/test_split_154/pqid_bench_external_generation_prompts_extension_84.jsonl`
- extension selection audit: `artifacts/test_split_154/pqid_bench_extension_84_selection.tsv`
