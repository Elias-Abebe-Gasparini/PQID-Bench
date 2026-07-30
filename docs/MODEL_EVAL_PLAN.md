# PQID-Bench External Model Evaluation Plan

Status: traceability scaffold prepared; OpenAI, Anthropic, Gemini, official
DeepSeek V4 Pro and Flash, Groq bridge rows, and GitHub Models Codestral are
collected and evaluated. HF route was tried and discarded for the final matrix;
NVIDIA NIM smoke probes are logged. GitHub Models DeepSeek-V3 remains partial
because of rate limiting and is separate from the official DeepSeek V4 rows.
DeepInfra alternatives are scaffolded but awaiting credentials; ApiFreeLLM is
complete as an exploratory free-router baseline.

Access-date note: the model IDs below were checked against official provider
or Hugging Face model-card pages on 2026-06-17. Before running the final paper
table, recheck provider docs because hosted model aliases can change.

## Purpose

The external model stage is the central evidence-generation phase of the
benchmark study. It turns the local benchmark evidence into a traceable
model-quality study by
recording:

- the exact frozen prompt manifest;
- the exact model/API ID requested;
- request parameters;
- raw provider outputs;
- provider request IDs or run metadata where available;
- evaluator scripts and artifact hashes;
- per-model execution, structural, QASM 3 export, and failure-mode scores.

Closed frontier models require official API access or an equivalent official
provider surface. Open models do not require closed APIs, but they still need a
traceable run surface such as local inference, NVIDIA NIM, DeepInfra, GitHub
Models, vLLM, SGLang, or another logged OpenAI-compatible server.

Current access posture:

- OpenAI: available and first two Batch API rows are complete. `gpt-5.5`
  resolved to `gpt-5.5-2026-04-23`; `gpt-5.4-mini` resolved to
  `gpt-5.4-mini-2026-03-17`.
- Google: Gemini API access works through `GEMINI_API_KEY` or an equivalent
  local key file configured outside the repository, and the native Gemini
  `generateContent` runner has been added. After billing was linked to the
  Google Cloud project, Gemini 2.5 Pro completed `70 / 70` rows with
  `67` `STOP` finishes and `3` `MAX_TOKENS` finishes; it scores `92.86%`
  execution and `62.86%` structural match. Gemini 3.1 Pro Preview also
  completed `70 / 70` rows with `68` `STOP` finishes and `2` `MAX_TOKENS`
  finishes; it scores `97.14%` execution and `62.86%` structural match.
- Anthropic: API access works through `ANTHROPIC_API_KEY` or an equivalent
  local key file configured outside the repository, and the native Messages
  runner has been added. Claude Sonnet 4.6 completed `70 / 70`
  rows with `70` `end_turn` finishes and `0` API errors; it scores `92.86%`
  execution and `61.43%` structural match. Claude Opus 4.8 completed
  `70 / 70` rows with `70` `end_turn` finishes and `0` API errors; it scores
  `100.00%` execution and `61.43%` structural match.
- DeepSeek: official OpenAI-compatible API access works through
  `DEEPSEEK_API_KEY` or an equivalent local key file configured outside the
  repository. DeepSeek V4 Pro
  completed `70 / 70` rows with `68` `stop` finishes, `2` `length` finishes,
  and `0` API errors; it scores `92.86%` execution, `58.57%` structural match,
  and `91.43%` QASM3 export. DeepSeek V4 Flash also completed `70 / 70` rows
  with `68` `stop` finishes, `2` `length` finishes, and `0` API errors; it
  scores `92.86%` execution, `58.57%` structural match, and `91.43%` QASM3
  export.
- Groq/open-model API bridge: six hosted bridge rows are complete using the
  OpenAI-compatible chat runner and the dedicated Groq key file supplied locally
  outside the repository. Completed rows: `llama-3.3-70b-versatile`,
  `qwen/qwen3-32b`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`,
  `llama-3.1-8b-instant`, and
  `meta-llama/llama-4-scout-17b-16e-instruct`.
- Hugging Face Inference Providers: route tested and discarded for the final
  paper matrix unless all rows can later be completed with exact model
  resolution. `Qwen/Qwen2.5-Coder-7B-Instruct` is incomplete because `19`
  prompt rows hit a `402` included-credit depletion error.
  `Qwen/Qwen2.5-Coder-32B-Instruct` returned a smoke response but resolved to
  `qwen3-coder-30b-a3b-instruct`, so it should not be reported as exact
  Qwen2.5-Coder 32B. DeepSeek-Coder-V2-Lite and StarCoder2 are not supported
  by enabled HF router providers, and Devstral is not exposed as a chat model
  on that route. See `HF_HOSTED_OPEN_MODEL_RUNBOOK.md`.
- NVIDIA NIM / DeepInfra: non-HF hosted alternatives are now scaffolded through
  the OpenAI-compatible runner. NVIDIA credential discovery succeeds, and
  one-row smoke calls succeeded for `qwen/qwen3-next-80b-a3b-instruct` and
  `openai/gpt-oss-20b`. NVIDIA's exact Qwen coder routes are retired
  (`qwen/qwen2.5-coder-32b-instruct` EOL 2026-05-12;
  `qwen/qwen3-coder-480b-a35b-instruct` EOL 2026-06-11). NVIDIA code-model
  rows listed by `/v1/models` currently return account/function 404 errors.
  DeepInfra remains scaffolded for exact `Qwen/Qwen2.5-Coder-32B-Instruct`,
  `mistralai/Devstral-Small-2505`, and
  `bigcode/starcoder2-15b-instruct-v0.1`; the StarCoder2 row requires a smoke
  check because the provider page warns about possible redirection. See
  `OPEN_MODEL_ALTERNATIVE_ROUTES.md`.

## Core Model Matrix

| role | provider/run surface | model/API ID | access needed |
| --- | --- | --- | --- |
| frontier coding/reasoning | OpenAI official API | `gpt-5.5` | OpenAI API |
| cost/latency frontier comparison | OpenAI official API | `gpt-5.4-mini` | OpenAI API |
| independent frontier coding family | Anthropic official API | `claude-sonnet-4-6` | Anthropic API |
| higher-capability Anthropic frontier comparison | Anthropic official API | `claude-opus-4-8` | Anthropic API |
| independent frontier coding family | Google Gemini API | `gemini-2.5-pro` | Google API |
| newer Google frontier coding/reasoning comparison | Google Gemini API | `gemini-3.1-pro-preview` | Google API |
| independent DeepSeek frontier coding/reasoning row | DeepSeek official OpenAI-compatible API | `deepseek-v4-pro` | DeepSeek API |
| fast/cost DeepSeek frontier comparison | DeepSeek official OpenAI-compatible API | `deepseek-v4-flash` | DeepSeek API |
| open reproducible code model | local/HF/vLLM/SGLang | `Qwen/Qwen2.5-Coder-7B-Instruct` | no closed API required |
| strong open code model | local/HF/vLLM/SGLang | `Qwen/Qwen2.5-Coder-32B-Instruct` | no closed API required |
| open MoE/code-model contrast | local/HF/vLLM/SGLang | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | no closed API required |
| European/open coding-family contrast | local/HF/vLLM/SGLang | `mistralai/Devstral-Small-2-24B-Instruct-2512` | no closed API required |
| historical instruction-tuned code-model baseline | local/HF/vLLM/SGLang | `bigcode/starcoder2-15b-instruct-v0.1` | no closed API required |

Optional appendix contrast:

| role | provider/run surface | model/API ID | note |
| --- | --- | --- | --- |
| historical code-model contrast | local/HF/vLLM/SGLang | `bigcode/starcoder2-15b` | Appendix only unless an instruction-tuned serving wrapper is used. |

Interim API bridge targets while Anthropic and additional open-code rows are
being configured:

| role | provider/run surface | model/API ID | access needed |
| --- | --- | --- | --- |
| open-weight Llama API bridge | GroqCloud OpenAI-compatible API | `llama-3.3-70b-versatile` | Groq API key |
| open reasoning/code API bridge | GroqCloud OpenAI-compatible API | `qwen/qwen3-32b` | Groq API key |
| open-weight OpenAI-family API bridge | GroqCloud OpenAI-compatible API | `openai/gpt-oss-120b` | Groq API key |
| size-control against GPT-OSS 120B | GroqCloud OpenAI-compatible API | `openai/gpt-oss-20b` | Groq API key |
| small/fast open-weight API bridge | GroqCloud OpenAI-compatible API | `llama-3.1-8b-instant` | Groq API key |
| optional newer Llama-family contrast | GroqCloud OpenAI-compatible API | `meta-llama/llama-4-scout-17b-16e-instruct` | Groq API key; preview/exploratory |

These bridge rows are useful because they provide traceable open-weight model
evidence through a hosted API. They should be reported separately from the
closed frontier rows if the final paper uses them.

GitHub Models candidates:

| role | provider/run surface | model/API ID | access needed |
| --- | --- | --- | --- |
| GitHub Models coding-family contrast | GitHub Models OpenAI-compatible API | `deepseek/deepseek-v3-0324` | GitHub token with Models access |
| GitHub Models code-specialized Mistral contrast | GitHub Models OpenAI-compatible API | `mistral-ai/codestral-2501` | GitHub token with Models access |

After updating the GitHub API-version header to `2026-03-10`, the original
workspace token could list the GitHub Models catalog but could not run
inference. A dedicated `GITHUB_MODELS_API_KEY` configured outside the
repository fixes inference.
`mistral-ai/codestral-2501` now has a full `70 / 70` response log and
per-model evaluator report. `deepseek/deepseek-v3-0324` has a partial response
log with `24 / 70` prompt IDs carrying successful `stop` responses; the next
unresolved prompt is `pqid_bench_external_gen_0025`, which returned
`RateLimitError`. A 2026-06-21 00:28 KST retry still hit the same GitHub rate
limit, so the reset appears provider-side or rolling rather than
local-midnight based. Resume later with `--resume --retry-errors
--stop-on-error --max-retries 0 --request-timeout-seconds 45 --sleep-seconds
65 --max-new 8` only if this GitHub-provider row is retained as a separate
appendix contrast. The main named-model matrix now uses the official
`deepseek-v4-pro` API row for DeepSeek-family coverage. See
`GITHUB_AND_DEEPINFRA_ACCESS_RUNBOOK.md`.

Non-HF hosted alternatives:

| role | provider/run surface | model/API ID | access needed |
| --- | --- | --- | --- |
| Qwen-family sanity/breadth row | NVIDIA NIM OpenAI-compatible API | `qwen/qwen3-next-80b-a3b-instruct` | one-row smoke succeeded; not code-specialized |
| GPT-OSS provider cross-check | NVIDIA NIM OpenAI-compatible API | `openai/gpt-oss-20b` | one-row smoke succeeded |
| retired exact Qwen2.5-Coder route | NVIDIA NIM OpenAI-compatible API | `qwen/qwen2.5-coder-32b-instruct` | HTTP 410, EOL 2026-05-12 |
| retired Qwen coder successor route | NVIDIA NIM OpenAI-compatible API | `qwen/qwen3-coder-480b-a35b-instruct` | HTTP 410, EOL 2026-06-11 |
| blocked NVIDIA code-model alternatives | NVIDIA NIM OpenAI-compatible API | `google/codegemma-7b`; `deepseek-ai/deepseek-coder-6.7b-instruct`; `mistralai/codestral-22b-instruct-v0.1`; `bigcode/starcoder2-15b`; `ibm/granite-34b-code-instruct` | listed by `/v1/models`, but one-row smoke calls returned account/function 404 errors |
| exact hosted Qwen2.5-Coder 32B baseline | DeepInfra OpenAI-compatible API | `Qwen/Qwen2.5-Coder-32B-Instruct` | DeepInfra token |
| European/open coding-family contrast | DeepInfra OpenAI-compatible API | `mistralai/Devstral-Small-2505` | DeepInfra token |
| historical instruction-tuned code-model baseline | DeepInfra OpenAI-compatible API | `bigcode/starcoder2-15b-instruct-v0.1` | DeepInfra token; smoke-check returned model before reporting |
| exploratory free-router baseline | ApiFreeLLM non-OpenAI-compatible API | `apifreellm` | complete `70 / 70`; not a named-model row |

DeepInfra caveat: current model pages warn that these three rows may redirect
to replacement models. They must be smoke-checked and reported by returned
`model` field, not by requested model ID alone.

ApiFreeLLM caveat: the free endpoint accepts a single `message` field and does
not document a stable underlying model ID. It should be interpreted only as a
free-router availability baseline unless a stable model ID is returned in the
raw response. The paced run completed `70 / 70` responses on 2026-06-20
Asia/Seoul time, scoring `55.71%` execution, `34.29%` structural match, and
`54.29%` QASM3 export.

## Primary Source Links

- OpenAI model docs: https://platform.openai.com/docs/models
- Anthropic model docs: https://docs.anthropic.com/en/docs/about-claude/models/overview
- Google Gemini model docs: https://ai.google.dev/gemini-api/docs/models
- Google Gemini GenerateContent API docs: https://ai.google.dev/api/generate-content
- Google Gemini rate-limit docs: https://ai.google.dev/gemini-api/docs/rate-limits
- Qwen 7B model card: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- Qwen 32B model card: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
- DeepSeek-Coder-V2 Lite Instruct model card: https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct
- Devstral-Small model card: https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512
- StarCoder2-15B Instruct model card: https://huggingface.co/bigcode/starcoder2-15b-instruct-v0.1
- StarCoder2-15B model card: https://huggingface.co/bigcode/starcoder2-15b
- Groq model docs: https://console.groq.com/docs/models
- Groq free-plan rate limits: https://console.groq.com/docs/rate-limits
- Groq OpenAI compatibility: https://console.groq.com/docs/openai
- GitHub Models catalog: https://models.github.ai/catalog/models
- GitHub Models API docs: https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models
- GitHub Models REST catalog docs: https://docs.github.com/en/rest/models/catalog
- GitHub Models REST inference docs: https://docs.github.com/en/rest/models/inference
- NVIDIA Build / NIM APIs: https://build.nvidia.com/
- NVIDIA NIM model docs: https://docs.api.nvidia.com/nim/reference/models-1
- NVIDIA Qwen2.5-Coder 32B endpoint: https://docs.api.nvidia.com/nim/reference/qwen-qwen2_5-coder-32b-instruct-infer
- NVIDIA Qwen3-Coder endpoint: https://docs.api.nvidia.com/nim/reference/qwen-qwen3-coder-480b-a35b-instruct-infer
- NVIDIA live model list endpoint: https://integrate.api.nvidia.com/v1/models
- DeepInfra Qwen2.5-Coder endpoint: https://deepinfra.com/Qwen/Qwen2.5-Coder-32B-Instruct/api
- DeepInfra Devstral endpoint: https://deepinfra.com/mistralai/Devstral-Small-2505/api
- DeepInfra StarCoder2-Instruct endpoint: https://deepinfra.com/bigcode/starcoder2-15b-instruct-v0.1/api
- DeepInfra chat docs: https://docs.deepinfra.com/chat/overview
- ApiFreeLLM API access: https://apifreellm.com/en/api-access

## Frozen Prompt Source

The prompt manifest is:

`artifacts/pqid_bench_external_generation_prompts.jsonl`

It contains `70` held-out test prompts under the same deterministic
source-file-group split used by the retrieval-copy generation baseline.

Fair model calls must send only `prompt` or `messages`. The `target_metadata`
field in the prompt manifest is for scoring transparency only and must not be
sent to the model.

## Run Configuration

Primary single-pass generation:

- `temperature`: `0.0`
- `top_p`: `1.0`
- `max_output_tokens`: `2048`
- samples per prompt: `1`
- prompt style: system/user messages where supported
- output instruction: Python code only, no Markdown fences and no prose

If a provider does not support one of these parameters, record the omission in
the response log under `provider_metadata`.

## Traceability Files

Generate request and response templates with:

```powershell
python "scripts\export_pqid_bench_external_model_batches.py"
```

Add interim Groq bridge targets with:

```powershell
python "scripts\export_pqid_bench_external_model_batches.py" --include-bridge
```

Add the expanded open-model and GitHub Models scaffold with:

```powershell
python "scripts\export_pqid_bench_external_model_batches.py" --include-bridge --include-open-breadth --include-github-models --include-appendix
```

Add non-HF hosted alternatives with:

```powershell
python "scripts\export_pqid_bench_external_model_batches.py" --include-bridge --include-open-breadth --include-github-models --include-nvidia-nim --include-deepinfra --include-appendix
```

This writes:

- `artifacts/external_model_batches/external_model_run_matrix.md`
- `artifacts/external_model_batches/external_model_run_matrix.json`
- `artifacts/external_model_batches/requests/*_requests.jsonl`
- `artifacts/external_model_batches/responses/*_responses_template.jsonl`
- `artifacts/external_model_batches/manifests/external_model_traceability_manifest.md`
- `artifacts/external_model_batches/manifests/external_model_traceability_manifest.json`

Each request row stores the model input hash, request hash, prompt provenance
hash, model ID, provider, and decoding parameters. Each response-template row
is ready to store the raw response and `generated_code` used by the evaluator.

## OpenAI Batch Path

The OpenAI rows can be executed through the same `/v1/responses` Batch API
style used by the broader PQID seed/paraphrase pipeline.

Local preparation:

```powershell
python "scripts\export_pqid_bench_openai_batch_requests.py"
```

Run details are documented in:

`OPENAI_BATCH_RUNBOOK.md`

The OpenAI batch-preparation step writes:

- `artifacts/external_model_batches/openai_batch/openai_batch_request_manifest.md`
- `artifacts/external_model_batches/openai_batch/requests/openai_gpt-5_5_batch_requests.jsonl`
- `artifacts/external_model_batches/openai_batch/requests/openai_gpt-5_4-mini_batch_requests.jsonl`

The live API step should preserve state files, raw output files, raw error
files if present, materialized response logs, and evaluator reports.

OpenAI run status:

- First `gpt-5.5` attempt failed because explicit `temperature` was unsupported;
  the failed state and error log are preserved under
  `artifacts/external_model_batches/openai_batch/failed_attempts/`.
- Corrected OpenAI requests omit `temperature` and `top_p` from `/v1/responses`
  request bodies.
- Completed Batch API rows:
  - `gpt-5.5`: `70 / 70` completed, `0` failed.
  - `gpt-5.4-mini`: `70 / 70` completed, `0` failed.
- Summary artifact:
  `artifacts/pqid_bench_external_model_results_summary.md`.

## Groq / OpenAI-Compatible Chat Path

The Groq bridge rows and future GitHub Models / OpenRouter / local
OpenAI-compatible rows can be executed with:

`scripts/run_pqid_bench_openai_compatible_chat.py`

Run details are documented in:

`GROQ_AND_OPEN_MODEL_API_RUNBOOK.md`

Credential discovery for Groq:

```powershell
python "scripts\run_pqid_bench_openai_compatible_chat.py" `
  --request-file "artifacts\external_model_batches\requests\groq_llama-3_3-70b-versatile_requests.jsonl" `
  --check-credentials
```

Full runs should use `--resume` because free/low-cost hosted APIs may rate
limit before all 70 prompts complete.

Groq bridge run status:

- `llama-3.3-70b-versatile`: `70 / 70` responses, `0` API errors, `50.00%`
  structural match.
- `qwen/qwen3-32b`: `70 / 70` responses, `0` API errors, `38.57%`
  structural match; `13` responses ended with `length`.
- `openai/gpt-oss-120b`: `70 / 70` responses, `0` API errors, `52.86%`
  structural match.
- `llama-3.1-8b-instant`: `70 / 70` responses, `0` API errors, `22.86%`
  structural match.

## Response Log Requirements

For every model-output row, preserve:

- `prompt_id`
- `row_id`
- `provider`
- `model`
- `api_model_id`
- `run_id`
- `request_sha256`
- `model_input_sha256`
- `created_at_utc`
- `request_id` if the provider returns one
- `system_fingerprint` or model snapshot if available
- `generation_config`
- `finish_reason`
- `usage`
- `provider_metadata`
- `raw_response`
- `generated_code`

The existing evaluator needs only `prompt_id` or `row_id`, `provider`, `model`,
`generated_code`, `raw_response`, and `finish_reason`; the extra fields are
kept for auditability.

## Scoring Procedure

Score one model response file at a time so each provider/model gets its own
report directory. Example:

```powershell
python "scripts\run_pqid_bench_external_model_generation_harness.py" `
  --prompt-path "artifacts\pqid_bench_external_generation_prompts.jsonl" `
  --template-path "artifacts\pqid_bench_external_generation_response_template.jsonl" `
  --response-path "artifacts\external_model_batches\responses\openai_gpt-5_5_responses.jsonl" `
  --output-dir "artifacts\external_model_batches\evaluations\openai_gpt-5_5"
```

The report should be compared against the retrieval-copy lower bound:

- best non-oracle copy baseline: `24.29%` structural match, `90.00%`
  execution success;
- target-code oracle: `90.00%` structural match and execution success on the
  same held-out split.

## Publishability Gates

Minimum credible publication table:

- at least three closed frontier-family runs;
- at least two open reproducible model runs;
- no prompt leakage from `target_metadata`;
- raw response logs retained;
- per-model harness reports retained;
- hash manifest updated after response collection.

Strong publication table:

- the full core matrix above;
- one appendix/historical model if useful;
- failure taxonomy by execution error, width mismatch, gate-type mismatch,
  gate-count mismatch, and QASM 3 export failure;
- discussion of executable-but-structurally-wrong outputs as a benchmark
  finding, not just a score.
