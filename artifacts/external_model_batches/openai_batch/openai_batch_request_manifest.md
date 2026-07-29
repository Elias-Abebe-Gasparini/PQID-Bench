# PQID-Bench OpenAI Batch Request Manifest

- exported at UTC: `2026-06-17T15:48:57+00:00`
- OpenAI request files: `2`
- API endpoint: `/v1/responses`
- this file records batch inputs only; it is not a model result

## Files

| model | batch request file | rows | SHA-256 |
| --- | --- | ---: | --- |
| `gpt-5.4-mini` | `artifacts/external_model_batches/openai_batch/requests/openai_gpt-5_4-mini_batch_requests.jsonl` | 70 | `cc6ed6d905831cd1fe5a264a75d349a7593889ed47596bdb15671ad2b4401a00` |
| `gpt-5.5` | `artifacts/external_model_batches/openai_batch/requests/openai_gpt-5_5_batch_requests.jsonl` | 70 | `2226c5204efaa9b44717e42e3a971f4cc29f214016b6378d17496345a01098af` |

## Commands

### gpt-5.4-mini

- create_or_inspect_batch: `python scripts/run_pqid_bench_openai_batch_job.py --request-file artifacts/external_model_batches/openai_batch/requests/openai_gpt-5_4-mini_batch_requests.jsonl --state-file artifacts/external_model_batches/openai_batch/state/openai_gpt-5_4-mini_batch_state.json --endpoint /v1/responses --completion-window 24h`
- wait_and_download: `python scripts/run_pqid_bench_openai_batch_job.py --batch-id <BATCH_ID_FROM_STATE> --state-file artifacts/external_model_batches/openai_batch/state/openai_gpt-5_4-mini_batch_state.json --wait --download-output-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_4-mini_batch_output.jsonl --download-error-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_4-mini_batch_errors.jsonl`
- materialize_response_log: `python scripts/materialize_pqid_bench_openai_batch_responses.py --request-file artifacts/external_model_batches/requests/openai_gpt-5_4-mini_requests.jsonl --batch-output-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_4-mini_batch_output.jsonl --batch-error-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_4-mini_batch_errors.jsonl --output-file artifacts/external_model_batches/responses/openai_gpt-5_4-mini_responses.jsonl`
- score_response_log: `python scripts/run_pqid_bench_external_model_generation_harness.py --prompt-path artifacts/pqid_bench_external_generation_prompts.jsonl --template-path artifacts/pqid_bench_external_generation_response_template.jsonl --response-path artifacts/external_model_batches/responses/openai_gpt-5_4-mini_responses.jsonl --output-dir artifacts/external_model_batches/evaluations/openai_gpt-5_4-mini`

### gpt-5.5

- create_or_inspect_batch: `python scripts/run_pqid_bench_openai_batch_job.py --request-file artifacts/external_model_batches/openai_batch/requests/openai_gpt-5_5_batch_requests.jsonl --state-file artifacts/external_model_batches/openai_batch/state/openai_gpt-5_5_batch_state.json --endpoint /v1/responses --completion-window 24h`
- wait_and_download: `python scripts/run_pqid_bench_openai_batch_job.py --batch-id <BATCH_ID_FROM_STATE> --state-file artifacts/external_model_batches/openai_batch/state/openai_gpt-5_5_batch_state.json --wait --download-output-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_5_batch_output.jsonl --download-error-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_5_batch_errors.jsonl`
- materialize_response_log: `python scripts/materialize_pqid_bench_openai_batch_responses.py --request-file artifacts/external_model_batches/requests/openai_gpt-5_5_requests.jsonl --batch-output-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_5_batch_output.jsonl --batch-error-file artifacts/external_model_batches/openai_batch/raw_outputs/openai_gpt-5_5_batch_errors.jsonl --output-file artifacts/external_model_batches/responses/openai_gpt-5_5_responses.jsonl`
- score_response_log: `python scripts/run_pqid_bench_external_model_generation_harness.py --prompt-path artifacts/pqid_bench_external_generation_prompts.jsonl --template-path artifacts/pqid_bench_external_generation_response_template.jsonl --response-path artifacts/external_model_batches/responses/openai_gpt-5_5_responses.jsonl --output-dir artifacts/external_model_batches/evaluations/openai_gpt-5_5`
