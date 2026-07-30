# PQID-Bench External Model Generation Harness Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- split policy: same deterministic source-file-group split used by the retrieval-copy generation baseline
- exported prompts: `artifacts/pqid_bench_external_generation_prompts.jsonl`
- response template: `artifacts/pqid_bench_external_generation_response_template.jsonl`
- expected response path: `artifacts/external_model_batches/responses/groq_meta-llama_llama-4-scout-17b-16e-instruct_responses.jsonl`

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
| execution success | 49 | 70.00% |
| circuit found | 49 | 70.00% |
| structural match | 27 | 38.57% |
| gate types match | 28 | 40.00% |
| gate count match | 39 | 55.71% |
| qubit count match | 47 | 67.14% |
| QASM3 export success | 49 | 70.00% |
| target-context recovery execution success | 49 | 70.00% |
| target-context recovery structural match | 27 | 38.57% |
