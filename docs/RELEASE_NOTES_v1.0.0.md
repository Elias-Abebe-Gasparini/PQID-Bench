# PQID-Bench v1.0.0

Release date: 2026-07-23

This is the first frozen public release of PQID-Bench. The versioned software
and evidence archive is identified by
[`10.5281/zenodo.21649753`](https://doi.org/10.5281/zenodo.21649753).

## Reproducibility And Replication Toolkit

The release includes the installable `pqid-bench 1.0.0` Python package. It
verifies the artifact manifest, safely reproduces published metrics from
archived evaluations, summarizes and compares canonical evaluation bundles,
and exposes executable replay through a separately isolated Docker worker.
Full release parity covers the 3,234 primary cells and 4,536 repeatability
cells. The dependency-free core is tested on Python 3.11--3.14; the frozen
Docker replay worker remains on Python 3.13 and pins Qiskit 2.1.1, Qiskit Aer
0.17.0, and python-dateutil 2.9.0.post0.

The initial release also includes `run-model`, a traceable OpenAI-compatible
live replication path. It requires explicit third-party prompt-export
acknowledgement, excludes evaluator target metadata, keeps credential values
out of artifacts, records raw and normalized attempts by hash, and supports
bounded retries and atomic resume. Live collection and generated-code
execution remain separate trust boundaries.

Candidate comparisons are denominator-safe by default. They require a
compatible versioned run manifest, reject duplicate cells and conflicting
endpoint aliases, and require the complete frozen 154-prompt set for every
candidate model. An explicit `--allow-partial` mode compares only with the same
frozen prompt subset and labels the result as a matched-subset comparison.

The release also includes a complete user manual, data dictionary, CLI and
Python API references, metric and invariant definitions, worked workflows,
security and governance guidance, troubleshooting, a glossary, strict MkDocs
navigation, and a software-paper validation blueprint. Documentation contract
tests keep parser options, schema fields, navigation, and local links aligned.

The numerical interface retains JSON as its machine-readable default and adds
dependency-free text, Markdown, and tidy CSV renderers for summaries and
aligned comparisons. `BenchmarkSummary` supports direct printing and row-based
export for R, pandas, spreadsheets, and manuscript workflows. Rendering changes
presentation only; it does not change the evaluator, predicate, cells, or
frozen denominators.

## Included

- repository-cleared 734-row clean generation population;
- deterministic 514/66/154 source-lineage-aware split;
- 154 held-out prompts representing 144 reference signatures;
- canonical requests, outputs, and evaluations for 21 completed model routes;
- three retrieval-copy baselines;
- final 3,234-cell model-by-prompt matrix;
- prompt-identifiability, signature-weighting, pilot-extension, crossed
  model-by-signature, family-balanced, and leave-one-developer-out checks;
- exact ordered operation-and-operand and parameter-aware replay audits;
- versioned safe-built-in evaluator impact audit;
- sequentially frozen three-run stochastic-repeatability study over 72 unique
  signatures;
- complete user manual and documentation-site configuration;
- reproducibility documentation and publication-output regeneration scripts;
- upload-ready GitHub, Zenodo, and Hugging Face Dataset metadata.

Unpublished manuscript source, rendered publication figures, captions,
editable authoring files, copy-ready manuscript tables, the manuscript
walkthrough notebook, and the undeployed gateway bundle are outside the scope
of the public release.

The release test suite includes negative-path coverage for malformed JSONL,
duplicate model-prompt cells, conflicting aliases, incompatible predicate and
schema versions, corrupted manifests, incomplete comparison denominators, and
corrupted repeatability dimensions. Live-run tests inject provider failures
without making network calls and cover retry, terminal-error recovery,
resume, uncertain in-flight requests, credential non-persistence, target
metadata exclusion, and route validation. GitHub Actions also performs a
clean source-distribution installation test.

## Frozen Headline

Across `21 x 154 = 3,234` model-prompt outputs, `2,950` execute (91.22%),
`2,944` are OpenQASM 3 assembly admissible (91.03%), and `1,703` recover the
frozen reference signature (52.66%). The pooled Execution-Structure Gap is
`1,247 / 3,234 = 38.56` percentage points. Its nested Assembly-Structure Gap is
`1,241 / 3,234 = 38.37` points and retains `99.52%` of the ES-Gap.

## Compatibility Boundary

The reference-signature predicate compares qubit count, classical-bit count,
and the complete operation-type count map. Ordered reconstruction,
parameter-aware reconstruction, and semantic equivalence are distinct layers.
No live API rerun is required to reproduce the archived tables.

## Source Dataset

PQID-Bench is derived from:

> PQID: Parallel Quantum Instruction Dataset (v1.0.2), Zenodo,
> https://doi.org/10.5281/zenodo.20674853
