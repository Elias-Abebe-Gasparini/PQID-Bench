# Troubleshooting

## 1. Installation Problems

### `pqid-bench` is not recognized

Cause:

- the virtual environment is not activated; or
- the environment's scripts directory is not on `PATH`.

Check:

```bash
python -m pip show pqid-bench
python -m pip --version
```

Run through the environment directly when needed:

```powershell
.\.venv\Scripts\pqid-bench.exe --version
```

### Unsupported Python version

The package requires Python 3.11 or newer. Create a new environment with a
supported interpreter.

### PowerShell blocks environment activation

Activation is optional. Call the environment executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\pqid-bench.exe doctor
```

Do not weaken system execution policy solely to run the package.

## 2. Release Directory Problems

### `Release directory not found`

Pass the extracted evidence-bundle root, not the ZIP file and not the Python
wheel. The directory must contain `ARTIFACT_MANIFEST.tsv`.

### `ARTIFACT_MANIFEST.tsv` is missing

The evidence bundle is incomplete or the wrong directory was supplied.
Re-extract the frozen ZIP into a new directory.

### Manifest reports missing files

The release is incomplete. Do not continue to a scientific parity claim.
Restore the published archive and verify its outer checksum.

### Manifest reports size or hash mismatches

At least one file differs from the frozen release. Common causes are:

- manual editing;
- line-ending conversion;
- partial synchronization;
- antivirus quarantine; or
- copying through a system that transformed text files.

Use a fresh extraction. Do not regenerate the manifest merely to make the
failure disappear.

## 3. Reproduction Problems

### `canonical_parity` is false

Inspect `errors`. Each message reports an expected and observed frozen count.
Confirm that:

- release integrity passes;
- the same benchmark release is being used; and
- canonical analysis files were not replaced by replay output.

### Repeatability parity fails

Check the consolidated repeatability CSV under:

```text
artifacts/stochastic_repeatability_21x72/consolidated/analysis/
```

Expected dimensions are 4,536 cells, 21 models, 72 prompts, and three runs.

## 4. Evaluation-Record Problems

### `No evaluation records supplied`

The JSONL file contains no nonblank object rows.

### `Invalid JSONL at FILE:LINE`

The named line is not valid JSON. JSONL requires one complete JSON object per
line and does not permit a comma between lines.

### `Expected an object at FILE:LINE`

The line contains a JSON scalar or array. Wrap the cell fields in a JSON
object.

### `Record N lacks model or prompt_id`

Both keys are required for every evaluation cell.

### `Duplicate model-prompt key`

Two records have the same `(model, prompt_id)`. Decide which record belongs to
the declared run. Preserve retries in provider-attempt history rather than as
duplicate canonical cells.

### `Field ... must be Boolean or 0/1`

Use JSON `true`/`false` or integer `1`/`0`. Strings such as `"true"` are not
accepted.

### `Conflicting aliases`

The same endpoint was supplied under multiple names with different values.
For example:

```json
{
  "report_executable": true,
  "execution": false
}
```

Remove redundant aliases or make them agree. Do not rely on field order.

### `violates signature => execution`

A cell reports signature success without execution. Correct the evaluator
record or use a compatible scoring contract.

### `violates assembly => execution`

A cell reports OpenQASM 3 assembly admissibility without executable-circuit
materialization. This violates the definition of \(A\); correct the record or
use a compatible scoring contract.

### Signature match without assembly admissibility

This state is not rejected universally. The frozen release has zero such cells,
but a future candidate bundle may expose them. Inspect
`signature_without_assembly_count` and the exporter trace before interpreting
the signed AS-Gap.

### `violates ordered => signature`

A cell reports ordered-tape success while failing the signature predicate.
The endpoints are not nested as required.

### `violates parameter => ordered`

A parameter-aware pass requires an ordered-tape pass.

### Ordered or parameter count is `null`

The stricter endpoint is missing from at least one executable row, or no value
was supplied. This is deliberate protection against reporting partial
coverage as a complete count.

### Assembly metrics are `null`

No assembly endpoint was supplied. Add `report_assembly_admissible` to every
record to compute assembly rates and the AS-Gap. Supplying it to only part of a
bundle is rejected because it would mix denominators.

## 5. Comparison Problems

### Candidate run manifest lacks required fields

Supply all seven run/version fields documented in the Data Dictionary.

### Unsupported `run_type`

Use one of:

```text
canonical_reproduction
archived_replay
supplied_evaluation
live_replication
```

For ordinary candidate comparison, use `supplied_evaluation`.

### Candidate run manifest is incompatible

The benchmark, evaluator, predicate, or schema differs from the frozen
contract. Do not force a direct delta. Either rescore under the compatible
contract or report the result as a separately versioned analysis.

### Candidate models do not share one common prompt denominator

At least two candidate models contain different prompt sets. Create a common
panel before comparison.

### Candidate contains prompt IDs outside the frozen test set

`compare` only accepts the frozen prompt universe. Use `evaluate` for a
standalone summary of another benchmark.

### Candidate is missing frozen prompts

Default comparison requires all 154 prompts. If the partial panel is
intentional and common across models, rerun with `--allow-partial` and report
it as a matched-subset comparison.

### Structural-hallucination rate is `null`

The selected prompt set may contain no prompts after applying the frozen
identifiability exclusions, or no executable identifiable cells. Choose an
interpretable panel and inspect `comparison_scope.identifiable_exclusions`.

## 6. Live Collection Problems

### Live generation refuses without acknowledgement

Add `--acknowledge-third-party-prompt-export` only after accepting the
provider's retention, policy, quota, and billing risks. `run-model --dry-run`
does not require the flag because it exports nothing.

### API key environment variable is unset or empty

Set the preset variable, pass another variable name with `--api-key-env`, or
use `--api-key-file`. Do not add the credential to the repository or request
body.

### Output directory is not empty

Choose a new directory or use `--resume` for the exact same provider, route,
model, prompt source, and request set. The runner deliberately has no
overwrite mode.

### Resume configuration does not match

One or more frozen run-contract fields differ. Restore the original command or
start a new output directory and run ID. Do not merge unlike generation
settings into one canonical response panel.

### Prompt has an uncertain in-flight attempt

The previous process stopped after marking a request in flight. The provider
may have completed it. Use `--retry-uncertain` only after accepting a possible
additional stochastic draw; the interrupted attempt remains in the audit
history.

### A stored error is skipped on resume

This is the default. Add `--retry-errors` to request a new attempt while
retaining the failed attempt.

### HTTP 402, 403, or 429

Inspect the raw error body and provider account. Typical causes are depleted
credits, missing model permissions, or rate limits. Retryable responses use
bounded backoff, but the package cannot purchase credits or change provider
quotas.

### Provider rejects a generation parameter

Use `--omit-temperature`, `--omit-top-p`, or
`--max-output-field max_completion_tokens` as required by that route. Record
the change because it is part of the request-set hash.

### Native Anthropic or Gemini endpoint does not work

Package version 1.1.0 supports OpenAI-compatible chat completions. A native Messages
or GenerateContent endpoint requires a declared adapter and cannot be supplied
as a mere `--base-url` substitution.

## 7. Docker Problems

### Docker daemon is unavailable

Start Docker Engine and check:

```bash
docker version
pqid-bench doctor
```

`docker_cli` can be non-null while `docker_daemon_available` is false.

### Replay refuses without acknowledgement

Add `--acknowledge-code-execution` only after accepting the generated-code
risk. The requirement is intentional.

### Replay refuses because manifest verification failed

Replay requires an intact scientific bundle. Resolve the manifest discrepancy
instead of bypassing it.

### Image is missing

Either load the published archive:

```bash
docker load --input pqid-bench-evaluator-1.0.0-linux-amd64.tar.gz
```

or add `--build-image`.

### Replay times out

Increase `--timeout-seconds` only after checking Docker health and the response
bundle size. Preserve partial logs. A timeout is not a successful evaluation.

### Replay did not produce expected regular files

The worker failed, wrote an unexpected path, or produced a symlink. Inspect
Docker output and evaluator logs. The package intentionally refuses to copy
unexpected objects back.

### Windows bind-mount or long-path error

Use the packaged `replay` command rather than invoking the raw Docker command.
It stages input/output through short temporary paths.

## 8. Output And Interpretation Problems

### Candidate-minus-frozen sign seems reversed

Deltas are:

```text
candidate rate - frozen rate
```

A positive execution delta means higher candidate execution. A positive
ES-Gap delta means a larger separation, which is generally not an improvement.

### ES-Gap and executable disagreement differ

They use different denominators:

- ES-Gap rate divides by all cells.
- executable disagreement divides by executions.

### AS-Gap and ES-Gap differ

The ES-Gap uses execution as its operational baseline; the AS-Gap uses
quantum-assembly admissibility. On the frozen panel,

```text
ES-Gap = execution-to-assembly attrition + AS-Gap
```

because signature recovery is nested inside assembly admissibility there.
Future `signature_without_assembly_count` values must be inspected before
interpreting the AS-Gap as a one-directional cell count.

### Signature match is being interpreted as semantic correctness

That interpretation is outside the predicate. Signature, ordered, and
parameter-aware recovery are exact reference-reconstruction diagnostics, not
semantic-equivalence proofs.

### The 150-prompt result is confused with the primary result

The 154-prompt matrix is primary. The 150-prompt set is the prespecified
identifiability sensitivity used for the structural-hallucination terminology.

## 9. Exit Status Summary

| Status | General meaning |
| ---: | --- |
| `0` | requested operation completed successfully |
| `1` | data, integrity, compatibility, parity, Docker, or runtime failure |
| `2` | command-line usage error or missing required acknowledgement |

For automation, inspect both the process status and the JSON `valid` or parity
fields where applicable.

## 10. Reporting A Reproducible Issue

Include:

- command with secrets removed;
- package and version fields from `doctor`;
- operating system and Python version;
- Docker version when relevant;
- exact error output;
- manifest verification status;
- input schema/run type;
- whether the problem reproduces in a clean environment; and
- hashes of non-sensitive input artifacts.

Never attach provider credentials or private raw payloads to a public issue.
