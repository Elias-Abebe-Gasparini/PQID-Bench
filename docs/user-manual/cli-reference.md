# CLI Reference

## Global Interface

```text
pqid-bench [-h] [--version]
           {doctor,download,verify,reproduce,evaluate,compare,dashboard,run-model,replay} ...
```

The global `--version` option shows the installed package version:

```bash
pqid-bench --version
```

Show command help:

```bash
pqid-bench --help
pqid-bench compare --help
```

All commands retain machine-readable JSON as their default standard output.
`reproduce`, `evaluate`, and `compare` additionally support human-readable text,
copy-ready Markdown, and tidy CSV through `--format`. Error messages are
written to standard error.

### Statistical report formats

The three numerical summary commands share:

| Option | Values | Default | Meaning |
| --- | --- | --- | --- |
| `--format` | `json`, `text`, `markdown`, `csv` | `json` | select console and file representation |
| `--output` | path | none | also write the selected representation |

The extension of `--output` does not infer or override the format. See
[Reporting And Numerical Exports](reporting-and-exports.md) for the tabular
schemas and R/Python examples.

## `doctor`

### Purpose

Reports the installed version dimensions, Python and platform information,
Docker status, and optional package availability.

### Usage

```bash
pqid-bench doctor
```

### Output fields

| Field | Meaning |
| --- | --- |
| version fields | package, benchmark, evaluator, predicate, schema, manifest, and run type |
| `python` | current Python version |
| `platform` | operating-system and architecture description |
| `docker_cli` | resolved Docker executable path or `null` |
| `docker_daemon_available` | whether the Docker daemon responded |
| `optional_packages` | installed Qiskit, Qiskit Aer, JSON Schema, and Plotly versions or `null` |

Docker or optional-package absence does not make `doctor` fail.

### Exit status

`0` after producing the environment report.

## `download`

### Purpose

Downloads the compact PQID-Bench benchmark-user distribution, authenticates
the ZIP against a pinned SHA-256 digest, extracts it safely, and verifies its
internal artifact manifest.

### Usage

```bash
pqid-bench download --version 1.0.0
pqid-bench download --version 1.0.0 --output-dir ./benchmarks
```

### Arguments

| Argument | Required | Meaning |
| --- | ---: | --- |
| `--version` | no | frozen benchmark release; default `1.0.0` |
| `--output-dir` | no | parent for the retained ZIP and extracted directory |
| `--url` | no | custom HTTPS mirror; requires `--sha256` |
| `--sha256` | with `--url` | expected custom-archive digest |
| `--force` | no | atomically replace an existing local copy |
| `--timeout-seconds` | no | network timeout; default `120` |

Without `--output-dir`, files are stored below
`~/.cache/pqid-bench/releases/1.0.0`, or below `PQID_BENCH_CACHE_DIR` when that
environment variable is set. Existing valid releases are reused.

The extractor rejects absolute paths, parent traversal, Windows drive paths,
backslash member names, duplicate members, symbolic links, oversized archives,
and unexpected archive roots. A release is exposed only after
`benchmark.json` and every entry in `ARTIFACT_MANIFEST.tsv` pass validation.

### Principal output fields

| Field | Meaning |
| --- | --- |
| `release_dir` | verified extracted directory |
| `archive_path` | retained authenticated ZIP |
| `sha256` | expected and observed archive identity |
| `manifest_entries` | internally checked files |
| `downloaded` / `reused` | whether network acquisition occurred |

### Exit status

- `0`: the release was downloaded or a valid local copy was reused;
- `1`: route, digest, extraction, metadata, or manifest validation failed.

## `verify`

### Purpose

Checks every path in `ARTIFACT_MANIFEST.tsv`. With `--full`, also checks the
frozen primary summary and repeatability dimensions.

### Usage

```bash
pqid-bench verify RELEASE_DIR
pqid-bench verify RELEASE_DIR --full
```

### Arguments

| Argument | Required | Meaning |
| --- | ---: | --- |
| `RELEASE_DIR` | yes | extracted evidence-bundle root |
| `--full` | no | add primary and repeatability parity checks; requires the complete evidence profile |

### Integrity checks

For every manifest entry, verification checks:

- file existence;
- exact byte size; and
- SHA-256 equality.

Manifest parsing also rejects unexpected headers, empty paths, duplicate
paths, absolute paths, and parent traversal.

### Additional full checks

`--full` confirms:

- 3,234 primary cells;
- 21 models and 154 prompts;
- execution, assembly-admissibility, signature, ordered, and parameter-aware
  counts;
- execution-to-assembly attrition, AS-Gap, and directional assembly-signature
  discordance;
- the identifiable-subset counts; and
- 4,536 repeatability cells across 21 models, 72 prompts, and three runs.

### Principal output fields

| Field | Meaning |
| --- | --- |
| `manifest` | checked count and file-integrity discrepancies |
| `summary` | present only with `--full` |
| `release_parity_errors` | primary frozen-count discrepancies |
| `repeatability_parity_errors` | repeatability-dimension discrepancies |
| `valid` | true only when all requested checks pass |
| `errors` | combined human-readable failures |

### Exit status

- `0`: all requested checks passed.
- `1`: manifest or scientific parity failed, or input was invalid.
- `2`: command-line parsing error.

## `reproduce`

### Purpose

Recomputes the canonical study summary from the archived ordered/operand cell
audit and attaches the frozen identifiability sensitivity.

### Usage

```bash
pqid-bench reproduce \
  --release-dir RELEASE_DIR \
  --format markdown \
  --output reproduced-summary.md
```

### Arguments

| Argument | Required | Meaning |
| --- | ---: | --- |
| `--release-dir` | yes | extracted evidence-bundle root |
| `--format` | no | `json`, `text`, `markdown`, or `csv`; default `json` |
| `--output` | no | also write the selected representation to this path |

Parent directories for `--output` are created automatically.

### Output

The command emits all `BenchmarkSummary` fields plus:

- `canonical_parity`;
- `errors`; and
- the independent version dimensions.

### Exit status

- `0`: the recomputed summary matches the frozen counts.
- `1`: input or canonical parity failed.
- `2`: command-line parsing error.

## `evaluate`

### Purpose

Summarizes an already scored canonical evaluation JSONL bundle. It does not
execute generated code.

### Usage

```bash
pqid-bench evaluate \
  --evaluations EVALUATIONS.jsonl \
  --format text \
  --output candidate-summary.txt
```

### Arguments

| Argument | Required | Meaning |
| --- | ---: | --- |
| `--evaluations` | yes | canonical evaluation JSONL file |
| `--format` | no | `json`, `text`, `markdown`, or `csv`; default `json` |
| `--output` | no | also write the selected representation to this path |

### Required cell information

Every record must identify `model` and `prompt_id`, and provide at least one
accepted alias for execution and signature status. The accepted aliases are
listed in the [Data Dictionary](data-dictionary.md).

### Rejected inputs

The command rejects:

- an empty file;
- malformed JSONL or a non-object row;
- missing model or prompt identifiers;
- duplicate `(model, prompt_id)` keys;
- non-Boolean endpoint values other than integer `0` or `1`;
- conflicting values supplied through endpoint aliases; and
- violations of the endpoint nesting invariants.

### Exit status

- `0`: summary produced.
- `1`: file, record, or invariant failure.
- `2`: command-line parsing error.

## `compare`

### Purpose

Compares supplied canonical evaluations with the frozen benchmark on an
explicitly aligned prompt denominator.

### Full-test usage

```bash
pqid-bench compare \
  --evaluations EVALUATIONS.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --format text \
  --output comparison.txt
```

### Matched-subset usage

```bash
pqid-bench compare \
  --evaluations PARTIAL_EVALUATIONS.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --allow-partial \
  --output matched-subset-comparison.json
```

### Arguments

| Argument | Required | Meaning |
| --- | ---: | --- |
| `--evaluations` | yes | candidate evaluation JSONL |
| `--candidate-run-manifest` | yes | versioned run identity and compatibility record |
| `--release-dir` | yes | extracted frozen evidence bundle |
| `--allow-partial` | no | permit one common strict prompt subset |
| `--format` | no | `json`, `text`, `markdown`, or `csv`; default `json` |
| `--output` | no | also write the selected comparison representation |

### Default denominator contract

Without `--allow-partial`:

- every candidate model must contain all 154 frozen prompt IDs;
- all candidate models must share the same prompt set;
- no unknown prompt ID is permitted; and
- frozen and candidate summaries use the same 154-prompt denominator.

### Matched-subset contract

With `--allow-partial`:

- all candidate models must still share one prompt set;
- every prompt must belong to the frozen test set;
- the frozen comparator is restricted to those exact prompt IDs; and
- the output is labelled `matched-subset comparison`.

The option does not compare a partial candidate against the complete frozen
matrix.

### Run-manifest compatibility

The run manifest must contain all seven version/run fields. Comparison
requires exact agreement on:

- benchmark release;
- evaluator version;
- structural-predicate version; and
- schema version.

Package and artifact-manifest versions remain recorded even when they are not
the compatibility gate.

### Output sections

| Section | Meaning |
| --- | --- |
| `comparison_scope` | mode, prompt IDs and digest, dimensions, exclusions |
| `comparison_label` | full frozen or matched-subset label |
| `candidate_run_manifest` | supplied run identity |
| `candidate` | aligned candidate summary |
| `frozen` | frozen summary on the same prompt set |
| `candidate_minus_frozen` | rate differences |

The delta fields are execution rate, signature rate, ES-Gap rate,
executable-signature disagreement rate, and structural-hallucination rate.

### Exit status

- `0`: aligned comparison produced.
- `1`: manifest, record, version, prompt, denominator, or invariant failure.
- `2`: command-line parsing error.

## `dashboard`

### Purpose

Builds a standalone interactive Plotly report from the frozen evaluator,
ordered-structure, and stochastic-repeatability artifacts. The command
validates the 21 model rows against the canonical pooled counts before writing
the report. It does not contact providers or execute generated code.

### Usage

```bash
pqid-bench dashboard \
  --release-dir RELEASE_DIR \
  --output pqid-bench-dashboard.html
```

### Arguments

| Argument | Required | Meaning |
| --- | ---: | --- |
| `--release-dir` | yes | extracted frozen evidence bundle |
| `--output` | yes | destination HTML path |
| `--plotlyjs` | no | `embed` for offline use or `cdn` for a smaller file; default `embed` |

Install the optional dependency before running the command:

```bash
python -m pip install "pqid-bench[visualization]"
```

The report includes the measurement ladder, model profiles, component
heatmap, three-run repeatability view, provider-route aggregates, and an
accessible model-level table.

### Exit status

- `0`: dashboard generated and cross-checks passed.
- `1`: dependency, artifact, model-identity, or aggregate-parity failure.
- `2`: command-line parsing error.

## `run-model`

### Purpose

Collects a fresh prompt panel from one OpenAI-compatible chat-completions
route. This command contacts a provider but does not execute generated code.
It creates a new `live_replication` run and does not alter the frozen matrix.

### Dry Run

```bash
pqid-bench run-model \
  --release-dir RELEASE_DIR \
  --output-dir runs/model-a \
  --provider groq \
  --model MODEL_ID \
  --limit 1 \
  --dry-run
```

Dry run validates the release, route, prompt selection, and generation
configuration. It does not read a credential, contact the route, or create a
run directory.

### Networked Run

```bash
pqid-bench run-model \
  --release-dir RELEASE_DIR \
  --output-dir runs/model-a \
  --provider groq \
  --model MODEL_ID \
  --api-key-file /secure/path/provider-token.txt \
  --acknowledge-third-party-prompt-export
```

### Route And Credential Arguments

| Option | Required | Default | Meaning |
| --- | ---: | --- | --- |
| `--release-dir` | yes | none | verified evidence-bundle root |
| `--output-dir` | yes | none | new or resumable run directory |
| `--provider` | yes | none | preset or custom provider label |
| `--model` | yes | none | requested provider model ID |
| `--base-url` | custom routes only | preset route | OpenAI-compatible base URL |
| `--api-key-env` | no | preset variable | environment variable holding the key |
| `--api-key-file` | no | none | external text file containing the key |
| `--no-auth` | no | false | send no Authorization header |
| `--allow-insecure-http` | no | false | permit non-loopback plain HTTP |

Preset names are `openai`, `groq`, `github-models`, `openrouter`,
`hugging-face`, `nvidia`, `deepinfra`, `deepseek`, and `local`. A custom
provider label requires `--base-url`. Plain HTTP is accepted automatically
only for loopback.

### Prompt And Invocation Arguments

| Option | Required | Default | Meaning |
| --- | ---: | --- | --- |
| `--prompt-path` | no | frozen 154-prompt JSONL | alternate prompt JSONL |
| `--prompt-id` | no | all selected rows | one prompt ID; repeatable |
| `--limit` | no | `0` | select the first N rows; zero means no limit |
| `--max-new` | no | `0` | attempt at most N pending rows this invocation |
| `--run-id` | no | generated timestamped ID | explicit stable run ID |
| `--resume` | no | false | continue the frozen request set in `--output-dir` |
| `--retry-errors` | no | false | retry stored terminal-error responses |
| `--retry-uncertain` | no | false | accept possible duplicate draw after interruption |
| `--quiet` | no | false | suppress prompt progress on standard error |

`--max-new` controls one invocation; it does not truncate the selected request
set in the run manifest. Completed prompts are skipped on resume.

### Generation And Transport Arguments

| Option | Required | Default | Meaning |
| --- | ---: | --- | --- |
| `--max-output-tokens` | no | `2048` | maximum generated tokens |
| `--max-output-field` | no | `max_tokens` | use `max_tokens` or `max_completion_tokens` |
| `--temperature` | no | `0.0` | request temperature |
| `--omit-temperature` | no | false | remove temperature from the body |
| `--top-p` | no | `1.0` | request nucleus-sampling probability |
| `--omit-top-p` | no | false | remove top-p from the body |
| `--seed` | no | none | provider-supported best-effort seed |
| `--extra-body-json` | no | none | JSON object with additional non-secret fields |
| `--timeout-seconds` | no | `120` | per-request network timeout |
| `--max-retries` | no | `2` | retries after retryable failures |
| `--retry-backoff-seconds` | no | `1` | exponential-backoff base |
| `--sleep-seconds` | no | `0` | delay after a successful prompt |

The effective request body and its SHA-256 digest are recorded. Extra fields
cannot override `model`, `messages`, or the selected maximum-token field.
Credential-like keys are rejected because the request body is persisted.

### Consent And Planning Arguments

| Option | Required | Meaning |
| --- | ---: | --- |
| `--acknowledge-third-party-prompt-export` | yes for a networked run | accept retention, policy, quota, and billing risks |
| `--dry-run` | no | print a credential-free plan without contacting the provider |

The acknowledgement is deliberately not required for `--dry-run`, because
that operation exports nothing.

### Output

The run directory contains `run-manifest.json`, `requests.jsonl`,
`responses.jsonl`, `provider-attempts.jsonl`, atomic `records/`, raw provider
bodies under `raw/`, and `run-summary.json`. Credentials and evaluator-only
target metadata are not written to requests or sent to providers.

### Exit Status

- `0`: plan produced, run completed without canonical errors, or a bounded
  `--max-new` invocation ended with pending rows.
- `1`: validation, transport, provider, or terminal prompt error.
- `2`: acknowledgement missing or command-line parsing error.

See [Live Model Testing](live-model-testing.md) for provider setup, recovery,
evaluation, and comparison.

## `replay`

### Purpose

Executes supplied archived or newly collected generated programs inside the
Docker evaluator. This is the only command that executes generated Python.

### Inspect The Plan

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses RESPONSES.jsonl \
  --output-dir replay-output \
  --build-image \
  --dry-run \
  --acknowledge-code-execution
```

### Execute

Remove `--dry-run`:

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses RESPONSES.jsonl \
  --output-dir replay-output \
  --build-image \
  --acknowledge-code-execution
```

### Arguments

| Argument | Required | Default | Meaning |
| --- | ---: | --- | --- |
| `--release-dir` | yes | none | extracted evidence bundle |
| `--responses` | yes | none | canonical response JSONL |
| `--output-dir` | yes | none | destination for evaluator reports |
| `--build-image` | no | false | build the pinned image before running |
| `--dry-run` | no | false | print build/run plan without execution |
| `--timeout-seconds` | no | `3600` | timeout applied to build and run |
| `--acknowledge-code-execution` | yes for replay | false | explicit acceptance of generated-code execution |

The acknowledgement is required even for `--dry-run`. This keeps executable
replay visibly distinct from data-only commands.

### Preconditions

Replay refuses to proceed when:

- acknowledgement is absent;
- the release manifest does not verify;
- the Dockerfile or response file is missing; or
- Docker Engine is unavailable.

### Isolation

The planned worker uses:

- no network;
- a read-only root filesystem;
- read-only release and response mounts;
- all Linux capabilities dropped;
- `no-new-privileges`;
- a 128-process limit;
- 2 GiB memory and two CPU limits;
- a 256 MiB `noexec,nosuid` temporary filesystem; and
- no provider credentials.

Inputs and outputs are staged through temporary short paths for host
portability. Only expected regular files are copied back. Replay also derives
canonical evaluation JSONL and JSON, text, Markdown, and tidy CSV summaries
from the evaluator JSON report.

### Exit status

- `0`: dry-run plan produced or replay completed.
- `1`: manifest, file, Docker, evaluator, or output failure.
- `2`: acknowledgement missing or command-line parsing error.

Docker hardening reduces risk. It is not a proof that arbitrary Python is
intrinsically safe.
