# PQID-Bench External Model Generation Harness Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- split policy: same deterministic source-file-group split used by the retrieval-copy generation baseline
- exported prompts: `artifacts/pqid_bench_external_generation_prompts.jsonl`
- response template: `artifacts/pqid_bench_external_generation_response_template.jsonl`
- expected response path: `artifacts/external_model_batches/responses/apifreellm_apifreellm_responses.jsonl`

## Clean Pool

| slice | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |

## Held-Out Prompt Split

| split | rows | groups | strict_n8 | extended_n8 |
| --- | ---: | ---: | ---: | ---: |
| `train` | 598 | 470 | 342 | 256 |
| `validation` | 66 | 59 | 37 | 29 |
| `test` | 70 | 59 | 36 | 34 |

## Response Schema

Fill `generated_code` for each prompt in the response template. Optional fields `provider`, `model`, `raw_response`, and `finish_reason` are preserved in the evaluation JSON.

Use only the `prompt` or `messages` fields as model input. `target_metadata` is included for transparent scoring and should not be passed to the model.

Required matching key: `prompt_id` or `row_id`.

## Evaluation Status

- evaluated responses: `70`
- missing prompts: `0`

| metric | count | rate |
| --- | ---: | ---: |
| empty generation | 0 | 0.00% |
| execution success | 39 | 55.71% |
| circuit found | 38 | 54.29% |
| structural match | 24 | 34.29% |
| gate types match | 25 | 35.71% |
| gate count match | 30 | 42.86% |
| qubit count match | 37 | 52.86% |
| QASM3 export success | 38 | 54.29% |
| target-context recovery execution success | 39 | 55.71% |
| target-context recovery structural match | 24 | 34.29% |
