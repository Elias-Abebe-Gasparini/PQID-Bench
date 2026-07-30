# `pqid-bench` v1.1.1

Release date: 2026-07-30

Version 1.1.1 is a provenance and repository-quality patch for the separately
versioned Python toolkit. It does not revise the frozen PQID-Bench v1.0.0
benchmark, evidence matrix, evaluator, structural predicate, or reported
scientific results.

## Provenance

- The PyPI long description now links Overview object O6 to the prospective
  PQID-Bench 2 preregistration at
  [OSF DOI 10.17605/OSF.IO/WDERQ](https://doi.org/10.17605/OSF.IO/WDERQ).
- PyPI project links expose the same preregistration directly.
- The link completes the public provenance chain from the frozen benchmark and
  retrospective audits to the prospectively registered follow-up contract.

## Repository Quality

- Added GitHub community-health and funding metadata.
- Added structured contribution templates and automated dependency monitoring.
- Added runnable offline examples and stronger repository quality gates.
- Added reproducible social-preview and navigation assets.
- Restricted Python publication to explicit `python-v*` release tags.

## Version Boundaries

| object | identifier |
| --- | --- |
| frozen benchmark | `PQID-Bench 1.0.0` |
| Python toolkit | `pqid-bench 1.1.1` |
| evaluator | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` |
| evaluator container | `ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0` |

## Scientific Impact

None. This patch changes package-facing provenance and repository presentation
only. The 734-row population, deterministic splits, 21-by-154 result matrix,
retrieval baselines, repeatability audit, and all frozen numerical outputs are
unchanged.
