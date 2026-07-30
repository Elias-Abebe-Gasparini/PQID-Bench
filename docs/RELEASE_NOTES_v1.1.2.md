# `pqid-bench` v1.1.2

Release date: 2026-07-30

Version 1.1.2 is a venue-neutral metadata and documentation correction for the
separately versioned Python toolkit. It does not revise the frozen PQID-Bench
v1.0.0 benchmark, evidence matrix, evaluator, structural predicate, or reported
scientific results.

## Corrections

- Removed wording that prematurely associated the public artifact with a
  particular publication venue.
- Replaced venue-specific labels in the package README, reproducibility
  inventory, historical evaluation plan, publishing checklist, and script
  documentation with study- or publication-neutral descriptions.
- Added a release validation check that rejects explicit venue claims from
  current public artifacts.

## Version Boundaries

| object | identifier |
| --- | --- |
| frozen benchmark | `PQID-Bench 1.0.0` |
| Python toolkit | `pqid-bench 1.1.2` |
| evaluator | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` |
| evaluator container | `ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0` |

## Scientific Impact

None. This patch changes package-facing wording, provenance presentation, and
release validation only. The 734-row population, deterministic splits,
21-by-154 result matrix, retrieval baselines, repeatability audit, and all
frozen numerical outputs are unchanged.
