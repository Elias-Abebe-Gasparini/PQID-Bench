# Live Model Testing

## Purpose And Scope

`pqid-bench run-model` collects a fresh response panel from one model route
that implements OpenAI-compatible chat completions. It is a replication tool,
not part of historical reproduction: it creates a new `live_replication` run
and never replaces the frozen 21-model matrix.

The command performs networked generation only. It does not execute generated
Python. Evaluation remains a separate, explicitly acknowledged operation in
the network-disabled Docker worker:

```text
frozen prompts -> run-model -> responses.jsonl
               -> replay    -> canonical evaluations and summaries
               -> compare   -> denominator-aligned frozen comparison
```

This separation prevents provider credentials and generated Python from
sharing one runtime.

## Supported Routes

The package includes routing defaults for the following OpenAI-compatible
chat endpoints:

| Preset | Default credential variable | Notes |
| --- | --- | --- |
| `openai` | `OPENAI_API_KEY` | OpenAI chat-completions route |
| `groq` | `GROQ_API_KEY` | Groq OpenAI-compatible route |
| `github-models` | `GITHUB_TOKEN` | GitHub Models; token needs model-read access |
| `openrouter` | `OPENROUTER_API_KEY` | OpenRouter chat route |
| `hugging-face` | `HF_TOKEN` | Hugging Face Inference Providers router |
| `nvidia` | `NVIDIA_API_KEY` | NVIDIA API Catalog route |
| `deepinfra` | `DEEPINFRA_TOKEN` | DeepInfra OpenAI-compatible route |
| `deepseek` | `DEEPSEEK_API_KEY` | DeepSeek chat route |
| `local` | none | loopback server at `127.0.0.1:8000/v1` |

Use `--base-url` with any provider label for another compatible endpoint. The
stable runner does not translate native Anthropic Messages or Google Gemini
request formats. Those require a separately declared adapter rather than
pretending that unlike APIs are interchangeable.

Provider catalogs, model identifiers, prices, quotas, and accepted generation
parameters can change. Confirm them with the provider before a paid run.
Hugging Face can pin a serving provider in the model identifier, for example
`MODEL_ID:novita`. GitHub Models uses publisher-qualified identifiers.

## 1. Verify And Plan

Start with a dry run. It validates the evidence manifest, prompt selection,
route, and generation settings but does not read credentials, create output,
or contact the provider.

```bash
pqid-bench run-model \
  --release-dir RELEASE_DIR \
  --output-dir runs/MODEL_SLUG \
  --provider groq \
  --model MODEL_ID \
  --limit 1 \
  --dry-run
```

The plan reports `contacts_provider: false` and
`target_metadata_exported: false`. Only each prompt's model-facing `messages`
array is placed in the request body. The evaluator-only `target_metadata`
object remains local.

## 2. Supply A Credential

The preferred methods are an environment variable or an external text file:

```bash
export GROQ_API_KEY="..."
```

```bash
pqid-bench run-model ... --api-key-file /secure/path/groq-token.txt
```

PowerShell:

```powershell
$env:GROQ_API_KEY = (Get-Content -Raw "C:\secure\groq-token.txt").Trim()
```

The runner reads the value only when a networked run begins. It records the
credential source class or environment-variable name, never the credential
value or key-file path. A custom endpoint without authentication requires the
explicit `--no-auth` option.

Do not place credentials in `--base-url` or `--extra-body-json`. Routes with
embedded credentials or query strings are rejected, as are credential-like
fields in the extra request body.

## 3. Run A Smoke Test

Use a dedicated, empty output directory and acknowledge the provider's
retention, policy, quota, and billing risks:

```bash
pqid-bench run-model \
  --release-dir RELEASE_DIR \
  --output-dir runs/MODEL_SLUG \
  --provider groq \
  --model MODEL_ID \
  --limit 1 \
  --max-output-tokens 2048 \
  --acknowledge-third-party-prompt-export
```

Progress is printed to standard error before and after each request. The final
machine-readable run summary is printed to standard output. Use `--quiet` to
suppress progress without suppressing the final JSON.

Inspect the response, attempt history, and raw provider payload before
expanding the run. A successful HTTP response can still contain an empty,
truncated, refused, or non-code completion.

## 4. Run The Frozen Panel

Remove `--limit` and choose a new output directory:

```bash
pqid-bench run-model \
  --release-dir RELEASE_DIR \
  --output-dir runs/MODEL_SLUG-full \
  --provider groq \
  --model MODEL_ID \
  --max-output-tokens 2048 \
  --acknowledge-third-party-prompt-export
```

The default generation contract is `temperature=0`, `top_p=1`, and
`max_tokens=2048`. Provider or model constraints take precedence. Available
controls include:

- `--omit-temperature` or `--omit-top-p` when a route rejects a field;
- `--max-output-field max_completion_tokens` for models that require that
  spelling;
- `--seed` when the provider accepts a best-effort seed; and
- `--extra-body-json SETTINGS.json` for non-secret provider controls.

Every effective request body is persisted and hashed. Changing a setting
therefore creates a measurably different run contract.

## 5. Resume And Recover

The runner writes one atomic prompt record after marking a request in flight.
Reusing a nonempty output directory is refused unless `--resume` is supplied.

```bash
pqid-bench run-model \
  --release-dir RELEASE_DIR \
  --output-dir runs/MODEL_SLUG-full \
  --provider groq \
  --model MODEL_ID \
  --resume \
  --acknowledge-third-party-prompt-export
```

Resume behavior is explicit:

| Existing state | Default resume action | Additional option |
| --- | --- | --- |
| successful response | skip | none |
| canonical terminal error | skip | `--retry-errors` |
| no record | run | none |
| request marked in flight after interruption | refuse | `--retry-uncertain` |

An interrupted in-flight request may have completed at the provider even when
the local process did not receive it. `--retry-uncertain` therefore accepts a
possible additional stochastic draw. The uncertain attempt remains in the
history rather than being erased.

`--max-new N` bounds newly attempted prompts in one invocation without
changing the frozen selected request set. This supports quota-aware chunks.
Retryable HTTP and network failures use bounded exponential backoff controlled
by `--max-retries` and `--retry-backoff-seconds`.

## 6. Inspect The Run Artifacts

Each output directory contains:

| Path | Purpose |
| --- | --- |
| `run-manifest.json` | version, route, model, prompt-set, request-set, and generation contract |
| `requests.jsonl` | exact credential-free request bodies and hashes |
| `responses.jsonl` | canonical model responses accepted by `replay` |
| `provider-attempts.jsonl` | normalized attempt history, including retries |
| `records/` | atomic per-prompt state used for safe resume |
| `raw/` | raw provider response body for each completed attempt |
| `run-summary.json` | success, error, pending, attempted, and skipped counts |

Raw provider payloads can contain provider-specific metadata. Inspect them
before publication. The manifest confirms that evaluator-only target metadata
was not exported, but it does not override a provider's retention policy.

## 7. Evaluate In Docker

Generated code is untrusted. Start Docker Engine and run:

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses runs/MODEL_SLUG-full/responses.jsonl \
  --output-dir runs/MODEL_SLUG-full/evaluation \
  --build-image \
  --acknowledge-code-execution
```

In addition to the evaluator's JSON and Markdown reports, replay writes:

- `pqid_bench_canonical_evaluations.jsonl`;
- `pqid_bench_candidate_summary.json`;
- `pqid_bench_candidate_summary.txt`;
- `pqid_bench_candidate_summary.md`; and
- `pqid_bench_candidate_summary.csv`.

The text, Markdown, and tidy CSV outputs provide the R-style numerical
reporting layer without requiring pandas or R in the package runtime.

## 8. Compare With The Frozen Benchmark

For a complete 154-prompt run:

```bash
pqid-bench compare \
  --release-dir RELEASE_DIR \
  --evaluations runs/MODEL_SLUG-full/evaluation/pqid_bench_canonical_evaluations.jsonl \
  --candidate-run-manifest runs/MODEL_SLUG-full/run-manifest.json \
  --format text
```

For a deliberately partial panel, add `--allow-partial`. The comparator then
restricts the frozen rows to the exact same prompt IDs; it never compares a
partial candidate against the complete 154-prompt denominator.

## Python API

```python
from pathlib import Path

from pqid_bench import LiveRunConfig, plan_live_model_run, run_live_model

config = LiveRunConfig(
    release_dir=Path("RELEASE_DIR"),
    output_dir=Path("runs/model-a"),
    provider="groq",
    model="MODEL_ID",
    acknowledge_prompt_export=True,
)

print(plan_live_model_run(config))
result = run_live_model(config)
print(result.to_dict())
```

Applications can pass a progress callback. Tests can inject a transport
callable, which is how retry and recovery behavior is validated without
contacting a real provider.
