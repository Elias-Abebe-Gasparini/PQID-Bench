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
---

# PQID-Bench

PQID-Bench is the frozen `v1.0.0` benchmark companion for validation-aware
quantum-program generation. It is derived from the archived PQID v1.0.2
dataset and separates executable validity from recovery of a frozen,
explicitly limited circuit reference structure.

## Frozen Benchmark

| object | value |
| --- | ---: |
| clean generation population | 734 |
| train / validation / test | 514 / 66 / 154 |
| distinct test-set reference signatures | 144 |
| completed model routes | 21 |
| primary model-prompt outputs | 3,234 |
| stochastic-repeatability design | 72 signatures x 21 models x 3 runs |

## Direct Split Loading

The frozen evaluator records are distributed directly as `514` training,
`66` validation, and `154` test rows. No parent PQID download or benchmark
reconstruction is required:

```python
from datasets import load_dataset

splits = load_dataset(
    "Elias-Abebe-Gasparini/PQID-Bench",
    "evaluator_records",
)
```

The authoritative deterministic assignments remain in
`artifacts/test_split_154/pqid_bench_split_154_manifest.json`. The three JSONL
files are lossless convenience views keyed by `metadata.content_hash`.

## Primary Results

| endpoint | result |
| --- | ---: |
| execution | 2,950 / 3,234 (91.22%) |
| quantum-assembly admissibility | 2,944 / 3,234 (91.03%) |
| reference-signature recovery | 1,703 / 3,234 (52.66%) |
| Assembly-Structure Gap | 1,241 / 3,234 (38.37 pp) |
| Execution-Structure Gap | 1,247 / 3,234 (38.56 pp) |
| executable signature disagreement | 1,247 / 2,950 (42.27%) |
| identifiable-subset structural-hallucination rate | 1,187 / 2,890 (41.07%) |
| ordered operation-and-operand recovery | 1,576 / 3,234 (48.73%) |
| parameter-aware recovery | 1,545 / 3,234 (47.77%) |

Only six cells are lost from executable-circuit materialization to OpenQASM 3
assembly admissibility. The AS-Gap therefore retains `99.52%` of the ES-Gap,
locating almost the entire measured separation between operational
admissibility and structural reconstruction.

The reference-signature predicate compares qubit count, classical-bit count,
and the complete evaluator-visible operation-type count map. Scalar
counted-operation agreement follows from count-map equality under the frozen
convention and is reported separately as a diagnostic. Ordered reconstruction,
parameter-aware reconstruction, and semantic equivalence remain distinct
levels.

## Repository Contents

- `data/`: the repository-cleared 734-row clean generation population;
- `artifacts/test_split_154/`: split manifest and model-facing prompts;
- `artifacts/external_model_batches_154/`: canonical requests, responses, and
  evaluator reports for the 21 completed routes;
- `artifacts/analysis_154/`: final matrix, inferential analyses, robustness
  checks, and ordered/parameter-aware replay;
- `artifacts/stochastic_repeatability_21x72/`: the sequentially frozen
  three-run repeatability audit;
- `scripts/`: evaluator, analysis, and publication-output regeneration code;
- `docs/REGENERATING_PUBLICATION_OUTPUTS.md`: commands for recreating
  intentionally excluded manuscript-facing derivatives;
- `ARTIFACT_MANIFEST.tsv`: byte counts and SHA-256 digests.

Unpublished manuscript source and manuscript-facing publication derivatives
are intentionally excluded from this public evidence release.

Canonical response logs are research trace artifacts. Re-running third-party
APIs can produce different text and is not required to reproduce the archived
tables.

## Loading The Clean Generation View

```python
from datasets import load_dataset

dataset = load_dataset(
    "Elias-Abebe-Gasparini/PQID-Bench",
    "clean_generation",
)
print(dataset["full"])
```

## Links

- GitHub: <https://github.com/Elias-Abebe-Gasparini/PQID-Bench>
- PQID-Bench v1.0.0 archive: <https://doi.org/10.5281/zenodo.21649753>
- Underlying PQID v1.0.2 DOI: <https://doi.org/10.5281/zenodo.20674853>
- Stable PQID dataset concept DOI: <https://doi.org/10.5281/zenodo.20019482>

The benchmark archive and its source PQID dataset are distinct versioned
research objects and require separate citations.

## Licensing

The repository uses scoped licensing. Benchmark-authored documentation,
metadata, and aggregate artifacts are CC BY 4.0; package, script, and platform
adapter code is MIT; source-derived rows retain their upstream provenance and
license obligations. See `LICENSE.md`.

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
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20674853},
  url       = {https://doi.org/10.5281/zenodo.20674853}
}
```
