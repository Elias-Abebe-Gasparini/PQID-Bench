# PQID-Bench Documentation

Distribution status: **PQID-Bench v1.0.0 frozen evidence release with
`pqid-bench` v1.1.0 software tooling**.
The versioned benchmark archive is identified by
[`10.5281/zenodo.21649753`](https://doi.org/10.5281/zenodo.21649753).

PQID-Bench is a reproducibility and replication toolkit plus a frozen evidence
bundle for validation-aware quantum-program generation research. The package
keeps seven activities separate:

1. checking release-file integrity;
2. reproducing published metrics from archived evaluations;
3. summarizing compatible evaluation records;
4. comparing a candidate on an aligned prompt denominator;
5. rendering an interactive report from frozen local evidence;
6. collecting a new traceable model-response panel; and
7. evaluating generated programs inside an isolated Docker worker.

Offline reproduction never contacts a provider. `run-model` does so only after
explicit prompt-export acknowledgement. Only `replay` executes generated
Python, and it requires a separate code-execution acknowledgement.

## Choose A Starting Point

| Goal | Start here |
| --- | --- |
| Install and run the package for the first time | [Installation](user-manual/installation.md) |
| Reproduce the paper quickly | [Reviewer Quickstart](REVIEWER_QUICKSTART.md) |
| Understand what each command can do | [Capability Guide](user-manual/capabilities.md) |
| Test a new external model | [Live Model Testing](user-manual/live-model-testing.md) |
| Look up a command or option | [CLI Reference](user-manual/cli-reference.md) |
| Print a readable report or export to R/pandas | [Reporting And Numerical Exports](user-manual/reporting-and-exports.md) |
| Explore the frozen results interactively | [Interactive Explorer](INTERACTIVE_EXPLORER.md) |
| Use the importable Python interface | [Python API](user-manual/python-api.md) |
| Run small end-to-end Python examples | [Worked Examples](EXAMPLES.md) |
| Prepare or inspect JSON/JSONL records | [Data Dictionary](user-manual/data-dictionary.md) |
| Understand ES-Gap, AS-Gap, and related metrics | [Metrics And Invariants](user-manual/metrics-and-invariants.md) |
| Follow an end-to-end task | [Workflows](user-manual/workflows.md) |
| Diagnose an error | [Troubleshooting](user-manual/troubleshooting.md) |
| Check a term or abbreviation | [Glossary](user-manual/glossary.md) |

## Documentation Sets

The [User Manual](user-manual/index.md) is the operational source of truth for
installation, commands, records, metrics, workflows, and error handling.

The following documents have narrower purposes:

- [Python Package Contract](PYTHON_PACKAGE.md) specifies the software and
  scientific boundary of package version 1.1.0 against benchmark v1.0.0.
- [Security And Privacy](SECURITY_AND_PRIVACY.md) records the trust boundary
  and release privacy controls.
- [Docker Replay Validation](DOCKER_REPLAY_VALIDATION.md) records the completed
  container replay audit.
- [Reviewer Quickstart](REVIEWER_QUICKSTART.md) is the shortest route through
  integrity and parity checking.
- [Package v1.1.0 Release Notes](RELEASE_NOTES_v1.1.0.md) describe the
  visualization and documentation update; [benchmark v1.0.0 release
  notes](RELEASE_NOTES_v1.0.0.md) remain the scientific freeze record.
- [Package Paper Blueprint](PACKAGE_PAPER_BLUEPRINT.md) separates a future
  software paper from both this manual and the benchmark-results paper.
- The repository-level
  [changelog](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/blob/main/CHANGELOG.md)
  separates software evolution from the frozen benchmark release, while the
  [contribution guide](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/blob/main/CONTRIBUTING.md)
  defines the scientific freeze boundary for proposed changes.

## Ecosystem Boundaries

The complete ecosystem contains several related but non-interchangeable
objects:

| object | responsibility |
| --- | --- |
| archived PQID dataset | immutable upstream source dataset, DOI `10.5281/zenodo.20674853` |
| PQID-Bench v1.0.0 archive | immutable benchmark software and evidence release, DOI `10.5281/zenodo.21649753` |
| benchmark authoring workspace | canonical manuscript sources and complete research evidence |
| this `PQID-Bench` tree | standalone package source, manual, schemas, tests, and selected frozen evidence |
| frozen ZIP | complete downloadable scientific evidence bundle |
| wheel | installable command and Python interface, without the evidence bundle |
| source distribution | package source and documentation, without large scientific artifacts |
| container archive | optional isolated executable-replay worker |
| Hugging Face adapter | dataset publication view derived from this standalone tree |

The upstream dataset and benchmark release require separate citations and
version identifiers. Generated distribution files are rebuilt from source and
must not be hand-edited.

Rendered manuscript outputs remain outside this public release. Their
scientific inputs and regeneration scripts remain available; see
[Regenerating Publication Outputs](REGENERATING_PUBLICATION_OUTPUTS.md).
The package-facing Plotly explorer is generated only during the Pages build and
is not inserted into the frozen evidence archive.

## Version Dimensions

| Dimension | Identifier |
| --- | --- |
| Python package | `1.1.0` |
| benchmark release | `1.0.0` |
| evaluator | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` |
| schema | `1.0.0` |
| artifact manifest | `1.0.0` |
| container artifact | `1.0.0` |

These identifiers describe different contracts. A change to one must not be
reported as though every other dimension changed with it. The replay container
currently has local image ID
`sha256:849bf53e449fd618633199c0b622abeca270591dff248cd0bf3a0fd461abf2e2`.
It is published separately from the Python toolkit as
[`ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0`](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/pkgs/container/pqid-bench-evaluator).
Its immutable OCI registry manifest digest is
`sha256:39825f5635cd6273e9e23c2848f2c88a2ff9d461e16a263fd89f22c6e664ac8f`;
it is distinct from the local image ID.

## Documentation Site

The public manual is available at
<https://elias-abebe-gasparini.github.io/PQID-Bench/>. Every source page is
also readable as ordinary Markdown. Install the documentation extra to build
the navigable site locally:

```bash
python -m pip install ".[docs]"
python scripts/build_pqid_bench_ecosystem_site.py
mkdocs serve
```

Use `mkdocs build --strict` when validating a documentation release.
