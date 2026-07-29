# PQID-Bench External Model Traceability Manifest

- exported at UTC: `2026-07-14T07:46:27+00:00`
- prompt manifest: `artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl`
- prompt manifest SHA-256: `cc6ba5c8a1fbf8677bd016d3cad47c7934981a685cc51052bdc3beb03f99b6eb`
- prompt rows: `154`
- generation config: `{"max_output_tokens":2048,"n":1,"single_pass":true,"temperature":0.0,"top_p":1.0}`

## Files

| kind | path | SHA-256 | rows |
| --- | --- | --- | ---: |
| request_jsonl | `artifacts/external_model_batches_154/qiskit_mistral/requests/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_requests.jsonl` | `25420fd211c4e692ffc7ed14721b030f3b0d39c7726c2043f4d60e963ec5a325` | 154 |
| response_template_jsonl | `artifacts/external_model_batches_154/qiskit_mistral/responses/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_responses_template.jsonl` | `53c5adde7b6d823354a648548579b5448053ed4d15588f88be09842187a984db` | 154 |
| model_matrix_json | `artifacts/external_model_batches_154/qiskit_mistral/external_model_run_matrix.json` | `f8098543c2011712c08e624acdbe5032522b130988debd72df516d8c2a864302` | 1 |
| model_matrix_md | `artifacts/external_model_batches_154/qiskit_mistral/external_model_run_matrix.md` | `e5c3d8e1787348a28875b6bfdfcebd48f059f33515a56e8e2746d52a9264a0d7` | 1 |
| traceability_manifest_json | `artifacts/external_model_batches_154/qiskit_mistral/manifests/external_model_traceability_manifest.json` | `3033ddbad7e5af0126397f8ef1ca28d8942a02c8a448c4f17d112f38ba31b7ed` | 1 |

## Evaluation Commands

- `python scripts/run_pqid_bench_external_model_generation_harness.py --prompt-path artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl --template-path artifacts/external_model_batches_154/qiskit_mistral/responses/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_responses_template.jsonl --response-path artifacts/external_model_batches_154/qiskit_mistral/responses/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_responses.jsonl --output-dir artifacts/external_model_batches_154/qiskit_mistral/evaluations/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai`
