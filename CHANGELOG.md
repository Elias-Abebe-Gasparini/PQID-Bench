# Changelog

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and records software-facing changes. PQID-Bench uses independent identifiers
for the benchmark, Python toolkit, evaluator, structural predicate, schema,
artifact manifest, and evaluator container. A change to one dimension does not
imply a change to the others.

## Unreleased

## Python Toolkit 1.1.1 - 2026-07-30

### Added

- GitHub community-health files, structured issue forms, a pull-request
  checklist, and automated dependency monitoring.
- Runnable offline reproduction, dashboard, and live-run planning examples.
- Repository quality gates for Ruff, mypy, branch coverage, documentation, and
  example execution.
- A reproducible GitHub social-preview asset.
- A prominent Overview object O6 link to the prospective PQID-Bench 2
  preregistration in the PyPI long description and package project links.

### Changed

- Python publication is now keyed to explicit `python-v*` tags so creating a
  GitHub release cannot accidentally republish an existing PyPI version.
- Repository navigation and metadata more clearly distinguish the frozen
  benchmark from the evolving package and documentation surfaces.

### Scientific Impact

None. The benchmark v1.0.0 prompts, splits, model responses, evaluator results,
predicate, model roster, denominators, and reported findings are unchanged.

## Python Toolkit 1.1.0 - 2026-07-30

### Added

- Standalone Plotly dashboard generation and static evidence graphics.
- Importable visualization and site-asset APIs.
- A navigable MkDocs user manual and GitHub Pages deployment.
- Python 3.14 compatibility and provider-facing live-model workflow guidance.

### Scientific Impact

None. Package 1.1.0 implements the frozen benchmark 1.0.0 contract.

## Benchmark 1.0.0 - 2026-07-23

### Added

- Frozen 734-row clean generation population and deterministic `514/66/154`
  split.
- Complete 21-model by 154-prompt external-model evidence matrix.
- Validation-aware evaluator, replay audits, robustness analyses, and
  stochastic-repeatability evidence.
- Versioned archive and reproducibility manifest.

See [benchmark release notes](docs/RELEASE_NOTES_v1.0.0.md) for the scientific
freeze and [package release notes](docs/RELEASE_NOTES_v1.1.0.md) for the
software update.
