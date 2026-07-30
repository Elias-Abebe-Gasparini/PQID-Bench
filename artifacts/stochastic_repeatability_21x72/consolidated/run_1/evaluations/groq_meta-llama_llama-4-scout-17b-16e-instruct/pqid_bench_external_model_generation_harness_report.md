# PQID-Bench External Model Generation Harness Report

- evaluator version: `pqid-bench-evaluator-1.1.0-safe-builtins`
- structural predicate version: `pqid-bench-reference-signature-1.0.0-count-map`
- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- split policy: frozen split manifest `artifacts/test_split_154/pqid_bench_split_154_manifest.json`
- exported prompts: `artifacts/stochastic_repeatability_21x72/consolidated/panel/pqid_bench_stochastic_repeatability_prompts_72.jsonl`
- response template: `artifacts/stochastic_repeatability_21x72/consolidated/run_1/responses/groq_meta-llama_llama-4-scout-17b-16e-instruct_responses_template.jsonl`
- expected response path: `artifacts/stochastic_repeatability_21x72/consolidated/run_1/responses/groq_meta-llama_llama-4-scout-17b-16e-instruct_responses.jsonl`

## Clean Pool

| slice | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |

## Held-Out Prompt Split

| split | rows | groups | strict_n8 | extended_n8 |
| --- | ---: | ---: | ---: | ---: |
| `train` | 514 | 386 | 301 | 213 |
| `validation` | 66 | 59 | 37 | 29 |
| `test` | 154 | 143 | 77 | 77 |

## Response Schema

Fill `generated_code` for each prompt in the response template. Optional fields `provider`, `model`, `raw_response`, and `finish_reason` are preserved in the evaluation JSON.

Use only the `prompt` or `messages` fields as model input. `target_metadata` is included for transparent scoring and should not be passed to the model.

Required matching key: `prompt_id` or `row_id`.

## Evaluation Status

- evaluator version: `pqid-bench-evaluator-1.1.0-safe-builtins`
- structural predicate: `pqid-bench-reference-signature-1.0.0-count-map`
- evaluated responses: `72`
- missing prompts: `0`

| metric | count | rate |
| --- | ---: | ---: |
| empty generation | 0 | 0.00% |
| Python execution success | 59 | 81.94% |
| executable circuit returned, E | 59 | 81.94% |
| reference-signature match | 31 | 43.06% |
| gate-type count-map match | 35 | 48.61% |
| gate count match | 45 | 62.50% |
| qubit count match | 55 | 76.39% |
| QASM3 export success | 59 | 81.94% |
| target-context recovery execution success | 59 | 81.94% |
| target-context recovery reference-signature match | 31 | 43.06% |
