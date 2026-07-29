# PQID-Bench External Model Generation Harness Report

- evaluator version: `pqid-bench-evaluator-1.1.0-safe-builtins`
- structural predicate: `pqid-bench-reference-signature-1.0.0-count-map`

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- split policy: frozen split manifest `PQID/submissions/acm_tqc_benchmark/artifacts/test_split_154/pqid_bench_split_154_manifest.json`
- exported prompts: `PQID/submissions/acm_tqc_benchmark/artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl`
- response template: `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches_154/qiskit_mistral/responses/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_responses_template.jsonl`
- expected response path: `PQID/submissions/acm_tqc_benchmark/artifacts/external_model_batches_154/qiskit_mistral/responses/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_responses.jsonl`

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

- evaluated responses: `154`
- missing prompts: `0`

| metric | count | rate |
| --- | ---: | ---: |
| empty generation | 1 | 0.65% |
| Python execution success | 139 | 90.26% |
| executable circuit returned, E | 138 | 89.61% |
| reference-signature match | 69 | 44.81% |
| gate-type count-map match | 79 | 51.30% |
| gate count match | 99 | 64.29% |
| qubit count match | 132 | 85.71% |
| QASM3 export success | 137 | 88.96% |
| target-context recovery execution success | 138 | 89.61% |
| target-context recovery reference-signature match | 70 | 45.45% |
