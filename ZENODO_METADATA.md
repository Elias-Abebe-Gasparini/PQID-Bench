# PQID-Bench v1.0.0 Zenodo Metadata

This document is the human-readable counterpart of `.zenodo.json`. It explains
the record without requiring prior knowledge of the manuscript's notation or
the wider PQID ecosystem.

## Core Fields

| field | value |
| --- | --- |
| title | PQID-Bench: A Validation-Aware Benchmark Suite for Quantum-Program Generation |
| frozen benchmark version | `1.0.0` |
| version DOI | `10.5281/zenodo.21649753` |
| concept DOI | `10.5281/zenodo.21649752` |
| publication date | 2026-07-23 |
| upload type | Software |
| language | English (`eng`) |
| access | Open |
| record-level license | Creative Commons Attribution 4.0 International |
| creator | Gasparini, Elias Abebe |
| parent PQID dataset | `10.5281/zenodo.20674853` |
| GitHub | <https://github.com/Elias-Abebe-Gasparini/PQID-Bench> |
| Python package | <https://pypi.org/project/pqid-bench/> |
| documentation | <https://elias-abebe-gasparini.github.io/PQID-Bench/> |
| Hugging Face benchmark distribution | <https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench> |
| evidence explorer | <https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html> |
| prospective O6 preregistration | <https://doi.org/10.17605/OSF.IO/WDERQ> |

## Start Here: Role Of This Record

This Zenodo deposit is the **scientific evidence and reproducibility archive**
for the completed PQID-Bench v1.0.0 study. It is intentionally larger than the
download needed to benchmark a new model.

| Need | Correct entry point |
| --- | --- |
| run PQID-Bench like a standard code-generation benchmark | [Hugging Face data](https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench) and the [PyPI toolkit](https://pypi.org/project/pqid-bench/) |
| reproduce the completed 21-model evidence and robustness audits | this Zenodo record |
| inspect maintained code, tests, documentation, and examples | [GitHub](https://github.com/Elias-Abebe-Gasparini/PQID-Bench) |
| inspect the prespecified plan for the future semantic-validity study | [PQID-Bench 2 on OSF](https://doi.org/10.17605/OSF.IO/WDERQ) |

These are complementary research objects rather than duplicate releases. Most
new benchmark users should begin with PyPI and Hugging Face; reviewers and
reproducers should begin here.

## Overview

**PQID-Bench v1.0.0** is a frozen, validation-aware benchmark, evidence bundle,
and reproducibility suite for evaluating quantum-program generation. It was
derived from PQID v1.0.2 through explicit validation, cleanliness, and
benchmark-readiness rules rather than by flattening every source record into
one test set.

The deposit is self-contained. It includes materialized training, validation,
and test JSONL files, so users do not need to download or reconstruct the
benchmark from the parent PQID dataset. PQID-Bench supports three main uses:

1. reproducing the frozen 21-model study;
2. inspecting its prompt-level evidence and robustness audits; and
3. evaluating additional model outputs under the same scoring contract.

## Release Contents

- A 734-row clean quantum-program generation population: 415 strict rows and
  319 extended rows.
- A deterministic 514/66/154 train/validation/test split in `data/splits/`.
- A held-out test set of 154 prompts representing 144 evaluator-facing target
  signatures.
- Canonical responses and evaluator traces for 21 named model routes over all
  154 prompts, yielding 3,234 model-prompt cells.
- Three retrieval-copy baselines.
- Ordered-operand and parameter-aware replay audits.
- Clustered inferential analyses, sensitivity analyses, and a three-run
  stochastic-repeatability audit over 72 signature-unique prompts.
- Evaluator and structural-predicate implementations, exact manifests,
  SHA-256 checksums, software bills of materials, documentation, and scripts
  that regenerate the public analytical outputs.

The public archive intentionally excludes unpublished manuscript source and
manuscript-facing publication derivatives.

## Measurement Nomenclature

The main symbols name increasingly restrictive checks:

- **`E` - Python execution.** The generated response executes in the pinned
  Python/Qiskit environment and yields an extractable quantum circuit.
- **`A` - quantum assembly execution.** `E=1` and the extracted circuit
  serializes successfully to OpenQASM 3 under the frozen evaluator. This is an
  assembly-admissibility layer; it does not mean that the emitted OpenQASM
  program was run by a separate quantum-assembly runtime.
- **`M^sig` - reference-signature recovery.** The executable output agrees
  with the frozen target on qubit count, classical-bit count, and the complete
  operation-type count map. Scalar counted-operation agreement follows from
  count-map equality in this release and is also reported as a diagnostic.
- **ES-Gap - Execution-Structure Gap.** The pooled Python-execution rate minus
  the pooled reference-signature recovery rate.
- **AS-Gap - Assembly-Structure Gap.** The pooled quantum-assembly rate minus
  the pooled reference-signature recovery rate. On the frozen panel, it is the
  assembly-admissible part of the ES-Gap.

Ordered-operand and parameter-aware replay predicates are stricter
reconstruction checks. None of these predicates is a direct test of unitary,
measurement-distribution, or semantic equivalence.

## Frozen Headline Evidence

| endpoint | count | rate |
| --- | ---: | ---: |
| Python execution, `E` | 2,950 / 3,234 | 91.22% |
| quantum assembly execution, `A` | 2,944 / 3,234 | 91.03% |
| reference-signature recovery, `M^sig` | 1,703 / 3,234 | 52.66% |
| ES-Gap | 1,247 / 3,234 | 38.56 pp |
| AS-Gap | 1,241 / 3,234 | 38.37 pp |

Only six executable outputs fail the assembly layer. The AS-Gap therefore
retains 99.52% of the ES-Gap: the observed separation is concentrated between
operational admissibility and measured structural recovery, not between Python
execution and OpenQASM 3 serialization.

## Python Package

The maintained command-line and Python interface is the separately versioned
[`pqid-bench` package](https://pypi.org/project/pqid-bench/). This Zenodo record
preserves the software distributions that accompanied the frozen deposit. The
current backward-compatible package is `pqid-bench 1.2.0`; it adds compact,
authenticated benchmark acquisition to the numerical summaries, comparisons,
interactive Plotly reporting, and live-model workflows without changing the
frozen benchmark data, responses, or scoring contract.

Install the current package and verify an extracted release:

```console
python -m pip install "pqid-bench==1.2.0"
pqid-bench download --version 1.0.0
pqid-bench verify RELEASE_DIR --full
pqid-bench reproduce --release-dir RELEASE_DIR --format text
```

The principal interfaces are:

| command | purpose |
| --- | --- |
| `pqid-bench doctor` | inspect the local runtime and optional dependencies |
| `pqid-bench download` | acquire and authenticate the compact benchmark-user distribution |
| `pqid-bench verify` | verify release structure, manifests, and optionally every file hash |
| `pqid-bench reproduce` | print or export the frozen numerical report |
| `pqid-bench evaluate` | summarize evaluation records in machine-readable or R-style text form |
| `pqid-bench compare` | compare a candidate run with the frozen reference |
| `pqid-bench dashboard` | create a standalone interactive Plotly report |
| `pqid-bench run-model` | run an explicitly authorized live model evaluation |
| `pqid-bench replay` | evaluate generated code through the isolated Docker worker |

Install `pqid-bench[visualization]==1.2.0` for the dashboard. Consult the
[documentation](https://elias-abebe-gasparini.github.io/PQID-Bench/) before
using live providers or replaying generated code.

## PQID-Bench 2 And The OSF Preregistration

PQID-Bench 2 is a separate prospective study; it is not an update to the
frozen v1.0.0 benchmark and it contributes no result to this deposit. The
[Open Science Framework registration](https://doi.org/10.17605/OSF.IO/WDERQ)
is a public, timestamped preregistration. Such a registration preserves the
questions and analytical decisions made before outcomes exist, allowing later
readers to distinguish confirmatory tests from post-outcome exploration.

The registered Stage 1 protocol extends the current operational-versus-
structural measurement system toward semantic validity. It prespecifies the
model-level Semantic Void state, in which a program executes but fails a
qualified semantic oracle, together with controlled algorithm-family,
audited-scope, and algorithm-name-visibility contrasts. The protocol states
that no PQID-Bench 2 output has been collected. A required Stage 2
registration must freeze the exact prompt panel, validated oracle code and
thresholds, sample size, model-provider routes, and executable analysis code
before the first model call.

The current supplement calls this pointer **Overview object O6**. O6 is an
administrative cross-reference to the future contract, not an additional
analysis of the current `734 / 154` benchmark.

## Version Crosswalk

| object | identifier or version | role |
| --- | --- | --- |
| benchmark and evidence release | `PQID-Bench 1.0.0` | frozen data, outputs, analyses, and manifests |
| current Python interface | `pqid-bench 1.2.0` | acquisition, CLI, library, reports, dashboard, and live workflows |
| archived Python interface | `pqid-bench 1.1.2` | exact wheel preserved in this deposit |
| evaluator implementation | `pqid-bench-evaluator-1.1.0-safe-builtins` | frozen executable-evaluation policy |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` | frozen signature-recovery rule |
| evaluator container | `ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0` | reproducible Docker execution image |

The independent version numbers are intentional. Updating the software
interface does not revise the frozen benchmark or its canonical evidence.

## Interpretive And Safety Boundaries

Reference-signature, ordered-operand, or parameter-aware agreement does not by
itself establish unitary, measurement-distribution, or semantic equivalence.
Conversely, signature disagreement establishes disagreement with the measured
frozen target but not general physical invalidity.

Live provider evaluation transmits benchmark prompts to the selected third
party and requires explicit user acknowledgement. Generated code should be
replayed only through the pinned Docker evaluator, not in the caller process.

PQID-Bench uses scoped licensing:

- benchmark-authored documentation, metadata, and aggregate analyses are
  licensed under CC BY 4.0;
- package and evaluator code are MIT-licensed; and
- source-derived rows retain row-level provenance and upstream licensing
  obligations.

## Keywords

- quantum computing
- quantum programming
- Qiskit
- OpenQASM 3
- quantum program synthesis
- quantum code generation
- large language models
- LLM evaluation
- code generation benchmark
- benchmark dataset
- structural evaluation
- model evaluation
- reproducible research
- Python package

## Metadata Status

The version DOI `10.5281/zenodo.21649753` was published on 2026-07-29. The
metadata may be clarified in place while preserving the DOI and the frozen
file inventory. Any future change to benchmark data, canonical evidence, or
scoring behavior requires a separately versioned release rather than a
metadata correction.
