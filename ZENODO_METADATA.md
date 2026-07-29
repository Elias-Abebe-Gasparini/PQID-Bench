# PQID-Bench v1.0.0 Zenodo Metadata

This sheet is the human-readable counterpart of `.zenodo.json`.

## Core Fields

| field | value |
| --- | --- |
| title | PQID-Bench: A Validation-Aware Benchmark Suite for Quantum-Program Generation |
| version | 1.0.0 |
| reserved version DOI | `10.5281/zenodo.21649753` |
| publication date | 2026-07-23 |
| upload type | Software |
| access | Open |
| primary package license | Creative Commons Attribution 4.0 International |
| creator | Gasparini, Elias Abebe |
| derived-from DOI | `10.5281/zenodo.20674853` |
| GitHub | `https://github.com/Elias-Abebe-Gasparini/PQID-Bench` |

## Description

PQID-Bench is a frozen, validation-aware benchmark suite for quantum-program
generation derived from the PQID v1.0.2 dataset. The release contains the
repository-cleared 734-row clean generation population, its deterministic
514/66/154 split, 154 held-out prompts, canonical outputs for 21 model routes,
three retrieval-copy baselines, evaluator and predicate implementations,
ordered and parameter-aware replay audits, cluster-aware inferential analyses,
a three-run stochastic-repeatability audit over 72 unique signatures,
publication-output regeneration scripts, and reproducibility documentation.
Unpublished manuscript source and manuscript-facing publication derivatives
are intentionally excluded.

Across the complete 21 x 154 matrix, executable-circuit materialization
succeeds for 2,950 of 3,234 outputs (91.22%), 2,944 are OpenQASM 3 assembly
admissible (91.03%), and 1,703 recover the frozen reference signature (52.66%).
The 38.56-percentage-point Execution-Structure Gap decomposes into 0.19 points
of execution-to-assembly attrition and a 38.37-point Assembly-Structure Gap,
which retains 99.52% of the ES-Gap. The package preserves exact trace artifacts
and SHA-256 manifests; it does not claim that exact reference reconstruction is
equivalent to semantic circuit equivalence.

## Keywords

- quantum computing
- quantum programming
- Qiskit
- quantum code generation
- large language models
- benchmark
- structural evaluation
- reproducibility

## Reserved Identifier And Publication Procedure

The direct Zenodo software-deposit draft reserved version DOI
`10.5281/zenodo.21649753` on 2026-07-29. The draft must not be deleted before
publication because deletion would discard the reservation.

1. Record the reserved benchmark DOI in `CITATION.cff`, `README.md`,
   `HUGGINGFACE_DATASET_CARD.md`, and the manuscript artifact-availability
   statement.
2. Rebuild the public bundle and Python distributions, rerun all release
   gates, regenerate checksums, and commit the DOI-complete byte-final state.
3. Create the annotated `v1.0.0` tag and GitHub release from that exact commit.
4. Publish the existing Zenodo draft with the same frozen ZIP and checksum
   sidecar, then verify the downloaded bytes.
5. Keep `10.5281/zenodo.20674853` as the distinct source-dataset DOI.

The archive checksum is recorded in
`PQID-Bench-v1.0.0-frozen.zip.sha256`. The reserved benchmark DOI is embedded
before the immutable tag and public deposits are created.
