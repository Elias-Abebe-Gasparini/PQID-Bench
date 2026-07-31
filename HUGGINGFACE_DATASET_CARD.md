---
pretty_name: PQID-Bench
license: other
language:
  - en
task_categories:
  - text-generation
tags:
  - quantum-computing
  - qiskit
  - quantum-programming
  - code-generation
  - benchmark
  - large-language-models
  - reproducibility
size_categories:
  - n<1K
configs:
  - config_name: clean_generation
    data_files:
      - split: full
        path: data/pqid_bench_clean_generation_734.jsonl
  - config_name: evaluator_records
    data_files:
      - split: train
        path: data/splits/train.jsonl
      - split: validation
        path: data/splits/validation.jsonl
      - split: test
        path: data/splits/test.jsonl
  - config_name: model_prompts
    data_files:
      - split: test
        path: prompts/test_prompts_154.jsonl
  - config_name: response_template
    data_files:
      - split: test
        path: templates/response_template_154.jsonl
---

# PQID-Bench

PQID-Bench is a frozen benchmark for validation-aware quantum-program
generation. It separates operational admissibility from recovery of an
explicitly bounded circuit reference structure. The `v1.0.0` distribution
contains `734` benchmark records with deterministic `514 / 66 / 154`
train-validation-test splits and a ready-to-use 154-prompt generation panel.
No parent PQID download or split reconstruction is required.

## Start Here: Which Object Do You Need?

PQID-Bench is a coordinated stack whose components serve different jobs:

| Goal | Use |
| --- | --- |
| evaluate a new model | this Hugging Face distribution for the data, plus [`pqid-bench` on PyPI](https://pypi.org/project/pqid-bench/) for collection, isolated replay, and scoring |
| reproduce or audit the completed 21-model study | the [Zenodo evidence archive](https://doi.org/10.5281/zenodo.21649753) |
| inspect source, tests, examples, and manuals | the [GitHub repository](https://github.com/Elias-Abebe-Gasparini/PQID-Bench) |
| read the prospectively fixed plan for the next study | the [PQID-Bench 2 OSF registration](https://doi.org/10.17605/OSF.IO/WDERQ) |

This repository is the adoption-focused benchmark distribution. It supplies
the ready-to-use data contract without requiring users to download the larger
study-reproduction archive.

## Fastest Start

Install the toolkit and download the authenticated compact distribution:

```bash
python -m pip install "pqid-bench>=1.2,<2"
pqid-bench download --version 1.0.0
```

The package checks the archive against a pinned SHA-256 digest, rejects unsafe
ZIP members, extracts atomically, and verifies every file against the internal
artifact manifest. The same compact ZIP is available under
`downloads/PQID-Bench-v1.0.0-core.zip`.

The core distribution contains the splits, model-facing prompts, response
template, schemas, evaluator source, and isolated Docker replay files. It
excludes manuscript material, archived model responses, publication figures,
repository administration, and historical analysis outputs.

## Load With Datasets

Load the benchmark records directly:

```python
from datasets import load_dataset

splits = load_dataset(
    "Elias-Abebe-Gasparini/PQID-Bench",
    "evaluator_records",
)
print(splits)
```

Load the exact model-facing test prompts:

```python
prompts = load_dataset(
    "Elias-Abebe-Gasparini/PQID-Bench",
    "model_prompts",
    split="test",
)
```

The richer 734-row clean-generation view remains available as the
`clean_generation` configuration.

## Benchmark Workflow

```bash
# Verify an extracted release.
pqid-bench verify PATH_TO/PQID-Bench-v1.0.0-core

# Inspect a credential-free request plan.
pqid-bench run-model \
  --release-dir PATH_TO/PQID-Bench-v1.0.0-core \
  --output-dir candidate-run \
  --provider local \
  --model MODEL_ID \
  --dry-run

# Evaluate supplied responses only in the isolated Docker worker.
pqid-bench replay \
  --release-dir PATH_TO/PQID-Bench-v1.0.0-core \
  --responses candidate-run/responses.jsonl \
  --output-dir candidate-evaluation \
  --build-image \
  --acknowledge-code-execution

# Print a numerical summary.
pqid-bench evaluate \
  --evaluations candidate-evaluation/pqid_bench_canonical_evaluations.jsonl \
  --format text
```

Live calls to third-party providers require explicit acknowledgement of prompt
export. Generated Python is never evaluated in the caller process.

## Measurement Contract

The frozen reference-signature predicate compares qubit count, classical-bit
count, and the complete evaluator-visible operation-type count map. Execution,
OpenQASM 3 assembly admissibility, signature recovery, ordered reconstruction,
parameter-aware reconstruction, and semantic equivalence remain distinct
levels. See `benchmark.json`, the schemas, and the documentation for exact
version identifiers and boundaries.

## What Is The PQID-Bench 2 OSF Registration?

PQID-Bench 2 is a separate future study, not a newer version of the data on
this page. Its
[Open Science Framework registration](https://doi.org/10.17605/OSF.IO/WDERQ)
is a timestamped, immutable preregistration: it records hypotheses, constructs,
eligibility rules, semantic-oracle classes, and analysis decisions before any
future model outputs are collected.

The Stage 1 protocol plans an extension from reference-structure recovery to
semantic validity. Its primary estimand concerns the model-level Semantic Void
state, where an output executes but fails a preregistered semantic oracle. It
also fixes the hierarchy for algorithm-family, audited-scope, and
name-visibility contrasts. Stage 2 must freeze the exact prompts, qualified
oracles, model routes, sample size, and analysis code before any model call.

No PQID-Bench 2 output or result is included here. The registration neither
changes nor is required to use PQID-Bench v1.0.0. In the research supplement,
**O6** is simply the overview-object label that points readers to this future
protocol.

## Evidence And Results

This Hugging Face repository is the benchmark-user distribution. The complete
frozen evidence archive, model responses, evaluator reports, robustness
analyses, and repeatability audit are preserved separately on Zenodo:
<https://doi.org/10.5281/zenodo.21649753>.

For parity checking, the frozen `21 x 154` panel contains `3,234` cells:

| endpoint | frozen anchor |
| --- | ---: |
| Python execution | 2,950 (91.22%) |
| OpenQASM 3 assembly admissibility | 2,944 (91.03%) |
| reference-signature recovery | 1,703 (52.66%) |
| Assembly-Structure Gap | 38.37 percentage points |
| Execution-Structure Gap | 38.56 percentage points |

The Assembly-Structure Gap retains 99.52% of the Execution-Structure Gap.
These values identify the archived reference panel; they are not required
inputs for evaluating a new model.

The separation lets users adopt the benchmark without downloading the full
manuscript-reproduction archive.

## Links

- Documentation: <https://elias-abebe-gasparini.github.io/PQID-Bench/>
- GitHub: <https://github.com/Elias-Abebe-Gasparini/PQID-Bench>
- Python package: <https://pypi.org/project/pqid-bench/>
- Frozen evidence archive: <https://doi.org/10.5281/zenodo.21649753>
- Prospective PQID-Bench 2 registration: <https://doi.org/10.17605/OSF.IO/WDERQ>
- Underlying PQID v1.0.2: <https://doi.org/10.5281/zenodo.20674853>

## Licensing

Licensing is scoped. Benchmark-authored documentation and aggregate metadata
are CC BY 4.0; package and evaluator code are MIT; source-derived rows retain
their upstream provenance and license obligations. See `LICENSE.md`.

## Citation

Please cite both the benchmark release and its source dataset:

```bibtex
@software{gasparini_2026_pqid_bench,
  author    = {Gasparini, Elias Abebe},
  title     = {PQID-Bench: A Validation-Aware Benchmark Suite for Quantum-Program Generation},
  version   = {1.0.0},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.21649753},
  url       = {https://doi.org/10.5281/zenodo.21649753}
}

@dataset{gasparini_2026_pqid,
  author    = {Gasparini, Elias Abebe},
  title     = {PQID: Parallel Quantum Instruction Dataset (v1.0.2)},
  version   = {1.0.2},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20674853},
  url       = {https://doi.org/10.5281/zenodo.20674853}
}
```
