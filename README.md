# PQID-Bench

**A validation-aware benchmark suite for quantum-program generation**

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21649753-1682D4?logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.21649753)
[![PyPI](https://img.shields.io/pypi/v/pqid-bench.svg)](https://pypi.org/project/pqid-bench/)
[![Python](https://img.shields.io/pypi/pyversions/pqid-bench.svg)](https://pypi.org/project/pqid-bench/)
[![CI](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/actions/workflows/ci.yml)
[![GHCR](https://img.shields.io/badge/GHCR-evaluator_1.0.0-2496ed.svg?logo=docker&logoColor=white)](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/pkgs/container/pqid-bench-evaluator)
[![Documentation](https://img.shields.io/badge/docs-interactive-13756d.svg)](https://elias-abebe-gasparini.github.io/PQID-Bench/)

- Benchmark release: `v1.0.0`
- Python package: `v1.1.2`
- Scientific freeze: `2026-07-23`
- Distribution status: frozen evidence release with a compatible software update
- Evaluator: `pqid-bench-evaluator-1.1.0-safe-builtins`
- Structural predicate: `pqid-bench-reference-signature-1.0.0-count-map`
- Prospective contract (Overview object O6): [PQID-Bench 2 preregistration,
  OSF DOI `10.17605/OSF.IO/WDERQ`](https://doi.org/10.17605/OSF.IO/WDERQ)

PQID-Bench is a frozen research artifact derived from the archived PQID v1.0.2
dataset. It tests whether generated Qiskit programs merely execute or recover
an explicitly limited reference structure. The benchmark does not treat
execution as structural or semantic correctness.

## Ecosystem Workflow

[![PQID-Bench reproducibility workflow](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/assets/ecosystem-flow.svg)](https://elias-abebe-gasparini.github.io/PQID-Bench/)

The evidence path keeps governed source data, deterministic splits, provider
collection, isolated replay, numerical reporting, and interactive
presentation as separate stages. The hosted explorer reads the final frozen
artifacts; it is not part of scoring.

## Frozen Design

| object | frozen value |
| --- | ---: |
| clean generation population | 734 prompts |
| train / validation / test | 514 / 66 / 154 |
| test-set reference signatures | 144 |
| completed model routes | 21 |
| primary model-prompt cells | 3,234 |
| retrieval-copy baselines | 3 |
| stochastic-repeatability panel | 72 unique signatures x 21 models x 3 runs |

[![PQID-Bench frozen split composition](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/assets/benchmark-split.svg)](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html)

The clean generation population is partitioned deterministically into `514`
training, `66` validation, and `154` held-out test prompts. The primary external
model comparison uses only the frozen test split.

## 60-Second Reproduction

Clone the evidence repository, install the published toolkit, and reproduce the
headline matrix without contacting a provider or executing generated code:

```bash
git clone https://github.com/Elias-Abebe-Gasparini/PQID-Bench.git
cd PQID-Bench
python -m pip install "pqid-bench==1.1.2"
pqid-bench verify . --full
pqid-bench reproduce --release-dir . --format text
```

Expected anchors are `21` models, `154` prompts, `3,234` cells, `91.22%`
execution, `91.03%` assembly admissibility, and `52.66%` signature recovery.
See the [worked examples](docs/EXAMPLES.md) for the importable API, dashboard,
and outcome-blind live-run planning.

The primary reference-signature predicate compares qubit count, classical-bit
count, and the complete evaluator-visible operation-type count map. Equality of
that map implies scalar counted-operation equality under the frozen convention,
so scalar operation count remains a separately reported diagnostic rather than
a fourth conjunct. Ordered operation-and-operand tape equality and
parameter-aware equality are stricter replay layers. None of these exact
reference-reconstruction predicates proves semantic equivalence.

## Visual Evidence Map

[![PQID-Bench operational and structural measurement ladder](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/assets/measurement-ladder.svg)](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html)

The [interactive evidence explorer](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html)
provides hoverable model profiles, a component-recovery heatmap, the complete
operational-to-structural ladder, three-run repeatability estimates, and
provider-route summaries. It is generated from the frozen artifacts on GitHub
Pages and does not contact model providers or execute generated code.

## Headline Results

| endpoint | count | rate |
| --- | ---: | ---: |
| execution | 2,950 / 3,234 | 91.22% |
| quantum-assembly admissibility | 2,944 / 3,234 | 91.03% |
| reference-signature recovery | 1,703 / 3,234 | 52.66% |
| pooled Assembly-Structure Gap | 1,241 / 3,234 | 38.37 pp |
| pooled Execution-Structure Gap | 1,247 / 3,234 | 38.56 pp |
| executable signature disagreement | 1,247 / 2,950 | 42.27% |
| identifiable-subset structural-hallucination rate | 1,187 / 2,890 | 41.07% |
| ordered operation-and-operand recovery | 1,576 / 3,234 | 48.73% |
| parameter-aware recovery | 1,545 / 3,234 | 47.77% |

[![PQID-Bench endpoint rates](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/assets/endpoint-rates.svg)](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html)

The bar chart makes the study object visible at a glance: operational
admissibility remains above `91%`, whereas every frozen structural-recovery
endpoint remains below `53%`.

Only six cells are lost from execution to assembly admissibility. On the
frozen panel, the AS-Gap is the assembly-admissible subset of the ES-Gap and
accounts for 99.52% of it. Assembly admissibility means successful OpenQASM 3
serialization under the evaluator, not backend execution.

The complete `154`-prompt matrix remains primary. Four prompts whose wording
does not uniquely specify every frozen signature component are removed only in
the prespecified `150`-prompt identifiability sensitivity analysis.

## Repository Layout

| path | purpose |
| --- | --- |
| `data/` | repository-cleared 734-row clean generation population |
| `artifacts/test_split_154/` | deterministic split, prompts, templates, and retrieval-copy results |
| `artifacts/external_model_batches_154/` | canonical requests, responses, evaluator reports, and trace manifests |
| `artifacts/analysis_154/` | final matrix, inference, robustness, identifiability, and replay audits |
| `artifacts/stochastic_repeatability_21x72/` | preregistered sequential repeatability design and consolidated three-run audit |
| `docs/` | complete user manual, reviewer guide, contracts, and release documentation |
| `examples/` | runnable offline reproduction, dashboard, and request-planning examples |
| `scripts/` | evaluator, analysis, validation, and figure/table builders |

`ARTIFACT_MANIFEST.tsv` records the byte size and SHA-256 digest of every
public file. The response logs are frozen trace artifacts. Re-running live APIs
may produce different text and is not required to reproduce the reported
tables from the archived outputs.

Rendered publication figures, captions, editable figure sources, copy-ready
manuscript tables, the manuscript walkthrough notebook, and the undeployed
gateway bundle are intentionally excluded. Their numerical inputs and
generation scripts remain available; see
[`docs/REGENERATING_PUBLICATION_OUTPUTS.md`](docs/REGENERATING_PUBLICATION_OUTPUTS.md).

## Python Package

The repository is also the source distribution for `pqid-bench 1.1.2`. The
package separates eight operations that must not be conflated:

- `doctor` reports the local runtime and optional dependencies;
- `verify` checks release bytes against `ARTIFACT_MANIFEST.tsv`;
- `reproduce` recomputes published metrics from archived evaluation records
  without executing generated code;
- `evaluate` summarizes a supplied canonical evaluation JSONL file;
- `compare` aligns a compatible candidate with the same frozen prompt
  denominator;
- `dashboard` builds a standalone interactive Plotly report from frozen
  evidence;
- `run-model` collects a new, traceable response panel from an
  OpenAI-compatible endpoint without executing generated code; and
- `replay` executes archived or newly collected generated programs only inside
  the credential-free, network-disabled Docker evaluator.

The dependency-free package core and archived-analysis workflows are tested on
Python 3.11--3.14. The optional replay container retains the frozen Python 3.13,
Qiskit 2.1.1, Qiskit Aer 0.17.0, and python-dateutil 2.9.0.post0 environment
used by the evaluator audit.

### GitHub evaluator package

GitHub Packages hosts the pinned evaluator runtime as an OCI image:

```bash
docker pull ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0
```

Immutable OCI manifest:
`sha256:39825f5635cd6273e9e23c2848f2c88a2ff9d461e16a263fd89f22c6e664ac8f`.

The GHCR image is the isolated execution environment used by
`pqid-bench replay`; it is not another Python distribution and does not change
the frozen benchmark version. The importable Python toolkit remains
authoritative on PyPI.

Install the toolkit from a checkout or wheel:

```bash
python -m pip install .
pqid-bench doctor
pqid-bench verify . --full
pqid-bench reproduce --release-dir . --format text
```

Install the optional visualization layer and create an offline HTML report:

```bash
python -m pip install "pqid-bench[visualization]"
pqid-bench dashboard --release-dir . --output pqid-bench-dashboard.html
```

The importable interface uses `pqid_bench`. Version dimensions are independent:
package `1.1.2` implements benchmark release `1.0.0`, evaluator
`pqid-bench-evaluator-1.1.0-safe-builtins`, and structural predicate
`pqid-bench-reference-signature-1.0.0-count-map`. The optional replay
container is a separate distribution artifact at version `1.0.0`; its image
identity does not replace the evaluator identifier.

Candidate comparison is denominator-safe by default: it requires a compatible
run manifest and one complete 154-prompt set per candidate model. Partial
results require `--allow-partial` and are compared only with the same frozen
prompt subset.

Numerical commands retain JSON as the default for automation and additionally
support `--format text`, `--format markdown`, and `--format csv`. The Python
`BenchmarkSummary` object likewise supports direct printing, copy-ready
Markdown, and tidy rows without adding a dataframe dependency. See the
[reporting guide](docs/user-manual/reporting-and-exports.md).

Fresh API generation always produces a new timestamped `live_replication`
rather than reproducing the archived model texts. The live runner exports only
the frozen model-facing messages, requires explicit third-party export
acknowledgement, never persists credential values, and supports bounded
retries and atomic resume. The separate Docker replay automatically emits
canonical evaluation cells and JSON, text, Markdown, and tidy CSV summaries.
See [Live Model Testing](docs/user-manual/live-model-testing.md).

## Reproduction Entry Points

Start with:

- [documentation home](docs/index.md);
- [interactive explorer](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html);
- [complete user manual](docs/user-manual/index.md);
- [reviewer quickstart](docs/REVIEWER_QUICKSTART.md);
- [data dictionary](docs/user-manual/data-dictionary.md);
- [worked examples](docs/EXAMPLES.md);
- [software-paper blueprint](docs/PACKAGE_PAPER_BLUEPRINT.md);
- [software changelog](CHANGELOG.md);
- [contribution guide](CONTRIBUTING.md);
- [reproducibility artifact map](REPRODUCIBILITY_ARTIFACTS.md).

The public evidence release deliberately excludes unpublished manuscript,
supplement, and bibliography source files.

The Markdown manual works directly from the repository or installed source
distribution. When MkDocs is available, serve the navigable local site from
the release root:

```bash
mkdocs serve
```

Key checks:

```bash
pqid-bench verify . --full
pqid-bench reproduce --release-dir .
python scripts/test_pqid_bench_stochastic_repeatability.py
python scripts/analyze_pqid_bench_prompt_identifiability.py
python scripts/analyze_pqid_bench_ordered_operand_validation.py
python scripts/analyze_pqid_bench_evaluator_builtin_correction.py
```

Rebuild the synchronized public package and its archive from the parent PQID
repository:

```bash
python scripts/build_pqid_bench_public_release.py --archive
```

## Public Endpoints

- GitHub: <https://github.com/Elias-Abebe-Gasparini/PQID-Bench>
- Documentation: <https://elias-abebe-gasparini.github.io/PQID-Bench/>
- Interactive explorer: <https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html>
- Python package: <https://pypi.org/project/pqid-bench/>
- Evaluator container: <https://github.com/Elias-Abebe-Gasparini/PQID-Bench/pkgs/container/pqid-bench-evaluator>
- PQID-Bench v1.0.0 archive: <https://doi.org/10.5281/zenodo.21649753>
- Hugging Face Dataset: <https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench>
- Source PQID dataset v1.0.2: <https://doi.org/10.5281/zenodo.20674853>
- Stable PQID dataset concept DOI: <https://doi.org/10.5281/zenodo.20019482>

The benchmark archive and its source PQID dataset are separate versioned
research objects and require separate citations.

## Licensing And Citation

Benchmark-authored documentation, metadata, and aggregate analysis artifacts
are released under CC BY 4.0. Code under `src/`, `scripts/`, and `platforms/`
is released under the MIT License. Source-derived rows retain their row-level
provenance and upstream license obligations; the package-level licenses do not
override those terms. See `LICENSE.md`.

Please cite the benchmark release:

> Elias Abebe Gasparini. 2026. *PQID-Bench: A Validation-Aware Benchmark
> Suite for Quantum-Program Generation (v1.0.0)* [Software]. Zenodo.
> https://doi.org/10.5281/zenodo.21649753

The underlying dataset must be cited separately:

> Elias Abebe Gasparini. 2026. *PQID: Parallel Quantum Instruction Dataset
> (v1.0.2)* [Data set]. Zenodo.
> https://doi.org/10.5281/zenodo.20674853
