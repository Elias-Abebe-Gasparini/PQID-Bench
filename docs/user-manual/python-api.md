# Python API

## Stable Top-Level Interface

The stable import surface is:

```python
from pqid_bench import (
    ARTIFACT_MANIFEST_VERSION,
    BENCHMARK_RELEASE,
    EVALUATOR_VERSION,
    PACKAGE_VERSION,
    PREDICATE_VERSION,
    REPORT_FORMATS,
    SCHEMA_VERSION,
    BenchmarkSummary,
    DashboardData,
    LiveRunConfig,
    LiveRunResult,
    PROVIDER_PRESETS,
    ProviderAttempt,
    ProviderPreset,
    ReplayPlan,
    canonicalize_harness_report,
    build_dashboard,
    execute_replay,
    load_dashboard_data,
    plan_live_model_run,
    provider_preset,
    render_comparison,
    render_summary,
    reproduce_release,
    replay_plan,
    run_live_model,
    summary_rows,
    summarize_evaluation_records,
    write_replay_derivatives,
    write_site_assets,
)
```

The command-line interface remains the recommended entry point for manifest
verification, live collection, denominator-safe comparison, and executable
replay.

## Version Constants

| Constant | Current value |
| --- | --- |
| `PACKAGE_VERSION` | `1.1.2` |
| `BENCHMARK_RELEASE` | `1.0.0` |
| `EVALUATOR_VERSION` | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| `PREDICATE_VERSION` | `pqid-bench-reference-signature-1.0.0-count-map` |
| `SCHEMA_VERSION` | `1.0.0` |
| `ARTIFACT_MANIFEST_VERSION` | `1.0.0` |

The package also exposes `pqid_bench.__version__`, equal to
`PACKAGE_VERSION`.

## `BenchmarkSummary`

`BenchmarkSummary` is an immutable dataclass containing:

| Field | Type | Meaning |
| --- | --- | --- |
| `cells` | `int` | number of supplied model-prompt records |
| `models` | `int` | distinct model identifiers |
| `prompts` | `int` | distinct prompt identifiers |
| `execution_count` | `int` | executable cells |
| `assembly_count` | optional integer | quantum-assembly-admissible cells |
| `signature_count` | `int` | reference-signature matches |
| `ordered_count` | optional integer | complete ordered matches when fully available |
| `parameter_count` | optional integer | parameter-aware matches when fully available |
| `es_gap_count` | `int` | executable signature disagreements |
| `execution_rate` | `float` | executions divided by all cells |
| `assembly_rate` | optional number | assembly-admissible cells divided by all cells |
| `signature_rate` | `float` | signature matches divided by all cells |
| `es_gap_rate` | `float` | ES-Gap count divided by all cells |
| `execution_to_assembly_attrition_count` | optional integer | execution count minus assembly count |
| `execution_to_assembly_attrition_rate` | optional number | operational attrition divided by all cells |
| `as_gap_count` | optional integer | signed assembly count minus signature count |
| `as_gap_rate` | optional number | AS-Gap count divided by all cells |
| `assembly_without_signature_count` | optional integer | assembly-admissible cells without signature match |
| `signature_without_assembly_count` | optional integer | signature matches without assembly admissibility |
| `as_gap_share_of_es_gap` | optional number | AS-Gap count divided by ES-Gap count |
| `executable_signature_disagreement_rate` | optional number | ES-Gap count divided by executions |
| `identifiable_cells` | optional integer | cells in supplied identifiable summary |
| `identifiable_execution_count` | optional integer | identifiable executions |
| `identifiable_signature_count` | optional integer | identifiable signature matches |
| `identifiable_disagreement_count` | optional integer | identifiable executable mismatches |
| `structural_hallucination_rate` | optional number | identifiable disagreement divided by identifiable executions |

`to_dict()` adds the independent version dimensions. Its default run type is
`canonical_reproduction`; callers summarizing new supplied data should pass
`run_type="supplied_evaluation"`.

### Printed and tabular reports

`print(summary)` produces the compact text report. Explicit methods are:

```python
print(summary.to_text())
print(summary.to_markdown())
print(summary.to_csv())

rows = summary.to_rows()
```

Each method accepts an optional `run_type`. `to_rows()` returns ordinary
dictionaries and requires no dataframe package. `render_summary()` and
`summary_rows()` provide the equivalent functional interface. The available
format names are exposed as `REPORT_FORMATS`.

`render_comparison()` formats an aligned comparison payload produced under the
same contract as the CLI. Complete format and CSV-column definitions are in
[Reporting And Numerical Exports](reporting-and-exports.md).

## `reproduce_release`

Signature:

```python
reproduce_release(release_dir: pathlib.Path) -> BenchmarkSummary
```

Example:

```python
from pathlib import Path

from pqid_bench import reproduce_release

release_dir = Path("/path/to/PQID-Bench-v1.0.0")
summary = reproduce_release(release_dir)

print(summary.cells)
print(summary.execution_count)
print(summary.assembly_count)
print(summary.es_gap_rate)
```

This function reads the frozen ordered/operand cell audit and identifiability
artifact. It does not verify every manifest entry and does not execute
generated code. Use `pqid-bench verify RELEASE_DIR --full` when those checks
are required together.

For the frozen release, expected values include:

```python
assert summary.cells == 3234
assert summary.execution_count == 2950
assert summary.assembly_count == 2944
assert summary.signature_count == 1703
assert summary.execution_to_assembly_attrition_count == 6
assert summary.as_gap_count == 1241
assert summary.signature_without_assembly_count == 0
assert summary.es_gap_count == 1247
```

## `summarize_evaluation_records`

Signature:

```python
summarize_evaluation_records(
    rows,
    *,
    identifiable=None,
) -> BenchmarkSummary
```

`rows` may be any iterable of mapping-like record objects.

Example:

```python
from pqid_bench import summarize_evaluation_records

rows = [
    {
        "model": "example-model",
        "prompt_id": "prompt-001",
        "report_executable": True,
        "report_assembly_admissible": True,
        "report_signature_match": False,
        "ordered_wire_tape_match": False,
        "parameter_aware_tape_match": False,
    },
    {
        "model": "example-model",
        "prompt_id": "prompt-002",
        "report_executable": True,
        "report_assembly_admissible": True,
        "report_signature_match": True,
        "ordered_wire_tape_match": True,
        "parameter_aware_tape_match": True,
    },
]

summary = summarize_evaluation_records(rows)
assert summary.execution_count == 2
assert summary.assembly_count == 2
assert summary.signature_count == 1
assert summary.as_gap_count == 1
assert summary.es_gap_count == 1
```

The function enforces unique `(model, prompt_id)` keys, Boolean endpoint
consistency, and:

```text
parameter-aware => ordered => signature => execution
assembly admissibility => execution
```

The frozen release additionally validates `signature => assembly
admissibility`, but supplied future data are allowed to violate that empirical
relation and expose the count in `signature_without_assembly_count`. Assembly
must be present on every row or omitted from every row. If it is omitted, all
assembly and AS-Gap fields are `None`.

If an ordered or parameter-aware field is missing for any executable row, its
aggregate count is returned as `None`. This prevents an incomplete stricter
layer from being reported as though it covered the complete bundle.

### Identifiable summary

The optional `identifiable` mapping has these keys:

| Key | Meaning |
| --- | --- |
| `n` | identifiable cell count |
| `execution_count` | identifiable executions |
| `structural_count` | identifiable signature matches |
| `execution_structure_gap_count` | identifiable executable mismatches |

Example:

```python
identifiable = {
    "n": 2,
    "execution_count": 2,
    "structural_count": 1,
    "execution_structure_gap_count": 1,
}

summary = summarize_evaluation_records(rows, identifiable=identifiable)
assert summary.structural_hallucination_rate == 0.5
```

The function trusts the supplied aggregate mapping. The CLI's frozen
comparison path calculates the identifiable subset from the frozen exclusion
policy instead of requiring the user to supply these values manually.

## Visualization API

`load_dashboard_data(release_dir)` validates and returns a `DashboardData`
object containing the canonical pooled summary and 21 model-level records.
`build_dashboard(...)` writes a standalone Plotly HTML report.

```python
from pathlib import Path

from pqid_bench import build_dashboard

data = build_dashboard(
    Path("RELEASE_DIR"),
    Path("pqid-bench-dashboard.html"),
    plotlyjs="embed",
)
assert len(data.models) == 21
```

Plotly is imported only when a dashboard is rendered. Install the
`visualization` extra for this interface. `write_site_assets(...)` additionally
writes the Pages-only workflow and measurement SVG fallbacks plus the
validated dashboard data as JSON.

## Live Collection API

`LiveRunConfig` is the immutable run contract. `plan_live_model_run(config)`
validates and returns a credential-free plan without contacting the provider.
`run_live_model(config)` performs the acknowledged collection and returns a
`LiveRunResult`.

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

plan = plan_live_model_run(config)
result = run_live_model(config)
assert result.selected_prompts == 154
print(result.to_dict())
```

`PROVIDER_PRESETS` exposes the non-secret routing defaults.
`provider_preset(name)` resolves one normalized preset. A custom route is
declared through `base_url`. Applications may pass `progress=CALLBACK` to
`run_live_model`; tests may inject a `transport` callable and `sleep` callable
without network access.

The Python API enforces the same acknowledgement, route, target-metadata,
credential, output-directory, and resume rules as the CLI. See
[Live Model Testing](live-model-testing.md) for the complete contract.

## Replay Derivative API

`replay_plan(...)` creates an immutable `ReplayPlan` containing the exact
Docker build and execution commands. `execute_replay(plan,
timeout_seconds=...)` then runs the evaluator under the package's
network-disabled, read-only, capability-dropped container boundary.

```python
from pathlib import Path

from pqid_bench import execute_replay, replay_plan

plan = replay_plan(
    release_dir=Path("RELEASE_DIR"),
    response_file=Path("runs/model-a/responses.jsonl"),
    output_dir=Path("runs/model-a/evaluation"),
    build_image=True,
)
execute_replay(plan, timeout_seconds=7200)
```

`canonicalize_harness_report(path)` converts the evaluator's nested JSON report
to canonical evaluation-cell dictionaries. `write_replay_derivatives(path)`
writes canonical JSONL and JSON, text, Markdown, and tidy CSV summaries in the
given evaluator-output directory. The `replay` CLI calls this automatically
after validating Docker outputs.

## Loading Installed Schemas

The supporting schema interface is:

```python
from pqid_bench.schemas import SCHEMA_NAMES, load_schema

evaluation_schema = load_schema("evaluation")
print(evaluation_schema["$id"])
```

Allowed schema names are:

```text
benchmark-record
prompt
response
evaluation
run-manifest
provider-attempt
```

An unknown name raises `KeyError`.

With the optional `schema` dependency:

```python
from jsonschema import Draft202012Validator
from pqid_bench.schemas import load_schema

validator = Draft202012Validator(load_schema("evaluation"))
validator.validate(
    {
        "prompt_id": "prompt-001",
        "model": "example-model",
        "report_executable": True,
        "report_signature_match": False,
    }
)
```

## Supporting Record Type

`ProviderAttempt` is the normalized boundary used by the live runner. It
records request identity, route, requested and resolved models, timestamps,
usage, response/error metadata, and raw payload digests.

Raw provider payloads remain separate files. They are not embedded directly
into the shared record.

The type and the live-run interfaces are top-level package-version 1.1.2
exports.

## Supporting Manifest Interface

Advanced users may import:

```python
from pathlib import Path

from pqid_bench.manifest import read_manifest, sha256_file, verify_manifest

verification = verify_manifest(Path("/path/to/release"))
assert verification.valid
```

These functions back the CLI but are not re-exported at the package top level.

## Compatibility Guidance

Depend on top-level exports for application code. Treat unexported functions
from `pqid_bench.metrics`, `pqid_bench.manifest`, `pqid_bench.records`,
`pqid_bench.live`, and `pqid_bench.replay` as supporting interfaces.

Do not import historical collection scripts as a stable API. Use the exported
live runner instead.
