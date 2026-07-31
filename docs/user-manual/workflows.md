# End-To-End Workflows

## Workflow 0: Compact Benchmark Setup

### Goal

Acquire the frozen records, direct splits, model-facing prompts, schemas, and
isolated evaluator without downloading the complete study-evidence archive.

```bash
python -m pip install "pqid-bench==1.2.1"
pqid-bench download --version 1.0.0 --output-dir ./benchmarks
pqid-bench verify ./benchmarks/PQID-Bench-v1.0.0-core
```

Use this profile for `run-model`, `replay`, and `evaluate`. Use the Zenodo
evidence profile instead when the task is `reproduce`, `compare`, `dashboard`,
or `verify --full`.

## Workflow 1: First Installation And Frozen Reproduction

### Goal

Confirm that the package, evidence bundle, and published summary agree without
executing generated Python.

### Steps

1. Install the wheel or source distribution.
2. Extract the frozen evidence bundle.
3. Run the environment report.
4. verify file integrity.
5. reproduce the summary.

```bash
pqid-bench --version
pqid-bench doctor
pqid-bench verify RELEASE_DIR
pqid-bench reproduce \
  --release-dir RELEASE_DIR \
  --output reproduced-summary.json
```

### Accept when

- package version is `1.2.1` when using the current toolkit, or `1.0.0` when
  reproducing with the wheel preserved inside the frozen archive;
- manifest `valid` is true;
- `canonical_parity` is true;
- cells equal 3,234;
- executions equal 2,950; and
- signature matches equal 1,703.

This is the minimum scientific reproduction workflow.

## Workflow 2: Exhaustive Release Audit

### Goal

Check every manifested file, every frozen primary endpoint total, and the
repeatability design dimensions.

```bash
pqid-bench verify RELEASE_DIR --full
```

### Accept when

```json
{
  "valid": true,
  "release_parity_errors": [],
  "repeatability_parity_errors": []
}
```

This command checks the scientific contract from archived records. It does not
rerun the model APIs or generated programs.

## Workflow 3: Summarize A New Evaluation Bundle

### Goal

Calculate package metrics from already scored cells.

### Prepare the input

Create one JSON object per line. Each record needs:

- `model`;
- `prompt_id`;
- an execution endpoint; and
- a signature endpoint.

Example:

```json
{"model":"candidate-a","prompt_id":"pqid_bench_external_gen_0001","report_executable":true,"report_assembly_admissible":true,"report_signature_match":false}
{"model":"candidate-a","prompt_id":"pqid_bench_external_gen_0002","report_executable":true,"report_assembly_admissible":true,"report_signature_match":true}
```

### Run

```bash
pqid-bench evaluate \
  --evaluations EVALUATIONS.jsonl \
  --output candidate-summary.json
```

### Inspect

Check:

- `cells`, `models`, and `prompts`;
- whether assembly coverage is complete and the resulting AS-Gap;
- whether `ordered_count` or `parameter_count` is `null`;
- ES-Gap count and rate; and
- the source path written into the report.

`evaluate` does not attach the frozen identifiable-subset policy automatically.
Use `compare` when aligned candidate/frozen interpretation is required.

## Workflow 4: Compare A Complete Candidate

### Goal

Compare one or more candidate model rows with the frozen benchmark on all 154
prompts.

### Prepare evaluations

Every candidate model must have exactly one cell for each frozen prompt ID.
Candidate models must share the same prompt set.

### Prepare the run manifest

```json
{
  "package_version": "1.2.1",
  "benchmark_release": "1.0.0",
  "evaluator_version": "pqid-bench-evaluator-1.1.0-safe-builtins",
  "predicate_version": "pqid-bench-reference-signature-1.0.0-count-map",
  "schema_version": "1.0.0",
  "artifact_manifest_version": "1.0.0",
  "run_type": "supplied_evaluation"
}
```

### Run

```bash
pqid-bench compare \
  --evaluations EVALUATIONS.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --output comparison.json
```

### Inspect

Confirm:

- `comparison_scope.mode` is `full_test_set`;
- `comparison_scope.prompt_count` is 154;
- the expected candidate cell count equals candidate models times 154;
- `comparison_label` is `frozen 154-prompt comparison`; and
- the candidate and frozen prompt lists are identical by construction.

Rate deltas are candidate minus frozen. A positive ES-Gap delta means a larger
execution-to-signature separation in the candidate.

## Workflow 5: Compare A Deliberately Partial Candidate

### Goal

Compare an incomplete but common candidate prompt panel without using the full
frozen denominator as the control.

### Preconditions

- Every candidate model has the same prompt IDs.
- Every prompt belongs to the frozen 154-prompt test set.
- The reduced scope is scientifically justified and reported.

### Run

```bash
pqid-bench compare \
  --evaluations PARTIAL_EVALUATIONS.jsonl \
  --candidate-run-manifest candidate-run-manifest.json \
  --release-dir RELEASE_DIR \
  --allow-partial \
  --output matched-subset-comparison.json
```

### Inspect

Confirm:

- `comparison_scope.mode` is `matched_subset`;
- `comparison_label` is `matched-subset comparison`;
- `prompt_count` matches the intended panel;
- `prompt_ids_sha256` is retained with the report; and
- frozen cells equal 21 times the selected prompt count.

Do not describe this output as a complete 154-prompt benchmark comparison.

## Workflow 6: Inspect A Replay Without Execution

### Goal

See the exact Docker build and run plan before allowing generated-code
execution.

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses RESPONSES.jsonl \
  --output-dir replay-output \
  --build-image \
  --dry-run \
  --acknowledge-code-execution
```

Inspect:

- image tag;
- Dockerfile path;
- input and output mounts;
- `--network none`;
- read-only and resource-limit flags; and
- response-file location.

No generated code runs in dry-run mode.

## Workflow 7: Execute An Archived Replay

### Goal

Re-evaluate archived generated code under the frozen Docker environment.

### Preconditions

- Docker Engine is running.
- Release integrity verifies.
- The response file is known and archived.
- The output directory is separate from canonical frozen results.
- The user accepts generated-code execution risk.

### Run

```bash
pqid-bench replay \
  --release-dir RELEASE_DIR \
  --responses RESPONSES.jsonl \
  --output-dir replay-output \
  --build-image \
  --timeout-seconds 3600 \
  --acknowledge-code-execution
```

Omit `--build-image` when the exact image has already been loaded.

### Outputs

The package copies back only:

```text
pqid_bench_external_model_generation_harness_report.json
pqid_bench_external_model_generation_harness_report.md
```

Compare replay output with the archived canonical evaluation before making a
parity claim. A completed process alone does not establish cell-level parity.

## Workflow 8: Programmatic Summary

```python
from pathlib import Path

from pqid_bench import reproduce_release

release = Path("/path/to/PQID-Bench-v1.0.0")
summary = reproduce_release(release)

print(
    {
        "cells": summary.cells,
        "execution_rate": summary.execution_rate,
        "signature_rate": summary.signature_rate,
        "es_gap_rate": summary.es_gap_rate,
    }
)
```

For a publication script, serialize `summary.to_dict()` so every version
dimension accompanies the metrics.

## Workflow 9: Prepare An Independent Reviewer Bundle

Include:

- frozen evidence ZIP and checksum sidecar;
- wheel and sdist with `SHA256SUMS.txt`;
- Docker archive and checksum when replay is requested;
- `docs/REVIEWER_QUICKSTART.md`;
- this user manual;
- citation and licensing files; and
- a short statement identifying which checks have already run publicly.

Ask the reviewer to:

1. verify distribution checksums;
2. install into a new environment;
3. run `doctor`;
4. run `verify --full`;
5. run `reproduce`; and
6. record platform, Python version, output hashes, and any deviations.

Do not supply private credentials or require provider access for frozen-result
reproduction.

## Workflow 10: Test A New External Model

1. Run `run-model --dry-run` against a new output directory.
2. Perform an acknowledged one-prompt smoke run.
3. Inspect the canonical response, raw payload, attempt history, and manifest.
4. Start the complete panel or a declared subset.
5. Resume incomplete work with `--resume`; add `--retry-errors` only for
   recorded terminal failures.
6. Start Docker and evaluate `responses.jsonl` with `replay`.
7. Use the automatically produced text, Markdown, or CSV summary.
8. Run `compare` with the live run manifest and canonical evaluation JSONL.
9. Preserve the new run without replacing frozen v1.0.0 artifacts.

The exact commands, provider presets, retry states, output files, and trust
boundaries are in [Live Model Testing](live-model-testing.md).
