# PQID-Bench External Model Traceability Manifest

- exported at UTC: `2026-07-14T08:35:00+00:00`
- prompt manifest: `artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl`
- prompt manifest SHA-256: `cc6ba5c8a1fbf8677bd016d3cad47c7934981a685cc51052bdc3beb03f99b6eb`
- prompt rows: `154`
- generation config: `{"max_output_tokens":2048,"n":1,"single_pass":true,"temperature":0.0,"top_p":1.0}`

## Files

| kind | path | SHA-256 | rows |
| --- | --- | --- | ---: |
| request_jsonl | `artifacts/external_model_batches_154/mistral_parent_control/requests/openrouter_mistralai_mistral-small-3_2-24b-instruct_requests.jsonl` | `dc6bd606b50f478cfc400c3ffead8dced21486dfc120f09b17b69081d1d23cbb` | 154 |
| response_template_jsonl | `artifacts/external_model_batches_154/mistral_parent_control/responses/openrouter_mistralai_mistral-small-3_2-24b-instruct_responses_template.jsonl` | `7d89ee9e6a2bb9b91c079aa2fe453c161a4c824e9b4e97e2a9b7fafc7747e97e` | 154 |
| model_matrix_json | `artifacts/external_model_batches_154/mistral_parent_control/external_model_run_matrix.json` | `0ad46224cb6cab5f1d5e4f1228cd12fe30fce557c61571551375c3cfe644aacf` | 1 |
| model_matrix_md | `artifacts/external_model_batches_154/mistral_parent_control/external_model_run_matrix.md` | `ccecef419e9947a0d7ea2ca1661c48225754323eff95ba0687154df16c2a228a` | 1 |
| traceability_manifest_json | `artifacts/external_model_batches_154/mistral_parent_control/manifests/external_model_traceability_manifest.json` | `9606894c9c056791879621f2e37e290765bf633c98f7993f087640b27d559449` | 1 |

## Evaluation Commands

- `python scripts/run_pqid_bench_external_model_generation_harness.py --prompt-path artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl --template-path artifacts/external_model_batches_154/mistral_parent_control/responses/openrouter_mistralai_mistral-small-3_2-24b-instruct_responses_template.jsonl --response-path artifacts/external_model_batches_154/mistral_parent_control/responses/openrouter_mistralai_mistral-small-3_2-24b-instruct_responses.jsonl --output-dir artifacts/external_model_batches_154/mistral_parent_control/evaluations/openrouter_mistralai_mistral-small-3_2-24b-instruct`
