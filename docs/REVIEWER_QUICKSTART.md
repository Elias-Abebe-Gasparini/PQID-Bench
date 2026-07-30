# PQID-Bench Reviewer Quickstart

This guide separates fast integrity checking, deterministic scientific
reproduction, exhaustive parity, candidate comparison, and optional executable
replay. Only the last operation executes generated Python. None of these
commands contacts a model provider.

The package also includes an optional `run-model` replication command. It is
not needed for review or reproduction of the frozen results and is documented
separately in [Live Model Testing](user-manual/live-model-testing.md).

Let `RELEASE_DIR` denote the extracted `PQID-Bench-v1.0.0-frozen.zip`
directory.

## Install

From the published wheel:

```bash
python -m pip install pqid_bench-1.0.0-py3-none-any.whl
```

This archived wheel gives exact software-level reconstruction of the original
freeze. The current `pqid-bench 1.1.1` package is benchmark-compatible and may
be installed from PyPI when the interactive dashboard is also desired.

From a source checkout:

```bash
python -m pip install .
```

## One-Minute Environment And Integrity Check

```bash
pqid-bench doctor
pqid-bench verify RELEASE_DIR
```

`doctor` reports package, benchmark, evaluator, predicate, schema, manifest,
Python, optional dependency, and Docker status. `verify` checks every listed
manifest entry for existence, exact byte size, and SHA-256 equality.

Expected result:

```text
"valid": true
```

## Five-Minute Scientific Reproduction

```bash
pqid-bench reproduce \
  --release-dir RELEASE_DIR \
  --output reproduced-summary.json
```

For the same frozen calculation in a compact reader-oriented layout:

```bash
pqid-bench reproduce --release-dir RELEASE_DIR --format text
```

Expected canonical counts:

| Endpoint | Count |
| --- | ---: |
| primary cells | 3,234 |
| models | 21 |
| prompts | 154 |
| executions | 2,950 |
| reference-signature matches | 1,703 |
| executable signature disagreements | 1,247 |
| ordered matches | 1,576 |
| parameter-aware matches | 1,545 |
| identifiable-subset executions | 2,890 |
| identifiable-subset signature matches | 1,703 |
| identifiable-subset disagreements | 1,187 |

Expected result:

```text
"canonical_parity": true
```

This operation reads archived evaluator records. It does not execute generated
programs.

## Full Primary And Repeatability Parity

```bash
pqid-bench verify RELEASE_DIR --full
```

In addition to byte verification, this checks:

- all `21 x 154 = 3,234` primary cells;
- all `72 x 21 x 3 = 4,536` repeatability cells;
- the frozen split, endpoint totals, and stricter reconstruction counts.

Expected result:

```text
"valid": true
"release_parity_errors": []
"repeatability_parity_errors": []
```

## Summarize A Compatible Evaluation Bundle

```bash
pqid-bench evaluate \
  --evaluations evaluation_records.jsonl \
  --output candidate-summary.json
```

The evaluator rejects:

- malformed JSONL;
- missing model or prompt identifiers;
- duplicate model-prompt cells;
- conflicting aliases such as `report_executable=true` with
  `execution=false`;
- violations of `assembly <= execution` or
  `parameter <= ordered <= signature <= execution`.

The frozen release additionally checks `signature <= assembly` as a
release-parity invariant. Candidate records that do not satisfy this empirical
relation are reported through `signature_without_assembly_count` rather than
rejected as logically malformed.

## Compare A Candidate With The Frozen Benchmark

Create a versioned candidate run manifest:

```json
{
  "package_version": "1.0.0",
  "benchmark_release": "1.0.0",
  "evaluator_version": "pqid-bench-evaluator-1.1.0-safe-builtins",
  "predicate_version": "pqid-bench-reference-signature-1.0.0-count-map",
  "schema_version": "1.0.0",
  "artifact_manifest_version": "1.0.0",
  "run_type": "supplied_evaluation"
}
```

Then run:

```bash
pqid-bench compare \
  --evaluations evaluation_records.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --output comparison.json
```

The default comparison requires every candidate model to contain the same
complete frozen 154-prompt set. It rejects:

- unknown prompt IDs;
- missing prompt IDs;
- unequal prompt sets across candidate models;
- duplicate model-prompt cells;
- incompatible benchmark, evaluator, predicate, or schema versions.

A deliberately incomplete evaluation requires:

```bash
pqid-bench compare \
  --evaluations partial_evaluation_records.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --allow-partial \
  --output matched-subset-comparison.json
```

`--allow-partial` does not compare the partial candidate with the full frozen
matrix. It restricts the frozen records to the same prompt IDs and labels the
result a `matched-subset comparison`.

## Optional Executable Replay

Generated Python is untrusted. Start Docker Engine, inspect the plan, and run
the replay only if code execution is intended:

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses RESPONSES.jsonl \
  --output-dir replay-output \
  --build-image \
  --dry-run \
  --acknowledge-code-execution
```

Remove `--dry-run` to execute. The worker is nonroot, network-disabled,
read-only, capability-free, resource-limited, and credential-free. It copies
back only the expected JSON and Markdown reports.

Docker hardening reduces risk; it is not a formal proof that arbitrary Python
is safe.

## Trust Boundary

| Operation | Executes generated Python | Contacts providers | Intended claim |
| --- | ---: | ---: | --- |
| `doctor` | no | no | environment report |
| `verify` | no | no | byte integrity |
| `verify --full` | no | no | byte and scientific parity |
| `reproduce` | no | no | frozen-result reproduction |
| `evaluate` | no | no | compatible-bundle summary |
| `compare` | no | no | denominator-aligned comparison |
| `run-model` | no | yes | new timestamped stochastic replication |
| `replay` | yes, in Docker | no | archived or newly collected evaluator replay |

Fresh API generation is part of the package interface but not part of frozen
result reproduction. It constitutes a new, timestamped stochastic
replication rather than reproduction of the archived model text.

For field definitions, complete command behavior, worked workflows, and
troubleshooting, continue with the [PQID-Bench User
Manual](user-manual/index.md).
