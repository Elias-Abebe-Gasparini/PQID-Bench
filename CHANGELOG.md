# Changelog

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and records software-facing changes. PQID-Bench uses independent identifiers
for the benchmark, Python toolkit, evaluator, structural predicate, schema,
artifact manifest, and evaluator container. A change to one dimension does not
imply a change to the others.

## Unreleased

## Python Toolkit 1.2.1 - 2026-07-31

### Changed

- Added a reader-first ecosystem map that distinguishes the PyPI toolkit,
  Hugging Face benchmark distribution, Zenodo evidence archive, GitHub source,
  Docker evaluator, interactive explorer, and prospective OSF registration.
- Added a dedicated explanation of Open Science Framework preregistration,
  Overview object O6, and the two-stage PQID-Bench 2 governance boundary.
- Clarified that PQID-Bench 2 is a separate future semantic-validity study and
  that no PQID-Bench 2 model output or result is part of the current release.

### Scientific Impact

None. Version 1.2.1 is a documentation and package-metadata patch. The
PQID-Bench v1.0.0 records, splits, prompts, core archive, model responses,
evaluator behavior, structural predicate, model roster, denominators, and
reported findings are unchanged.

## Python Toolkit 1.2.0 - 2026-07-31

### Added

- A secure `pqid-bench download --version 1.0.0` acquisition command with a
  pinned archive digest, HTTPS enforcement, safe ZIP extraction, atomic
  installation, and internal manifest verification.
- A deterministic, 32-file `PQID-Bench-v1.0.0-core.zip` distribution for
  benchmark adoption without manuscript-reproduction evidence.
- An adoption-focused Hugging Face staging and publication adapter with an
  explicit data-only allowlist and reviewable pull-request publication.

### Changed

- Reorganized user guidance around two complementary distribution profiles:
  the compact benchmark-user core and the complete Zenodo evidence archive.
- Extended the public Python API with typed core-release acquisition objects.

### Scientific Impact

None. The benchmark v1.0.0 records, splits, prompts, model responses, evaluator
results, predicate, model roster, denominators, and reported findings are
unchanged.

## Python Toolkit 1.1.2 - 2026-07-30

### Changed

- Replaced premature venue-specific wording in current public documentation
  and package metadata with venue-neutral descriptions of the benchmark study.
- Updated current package, documentation, SBOM, and repository pointers to
  toolkit version 1.1.2.

### Added

- A public-release validation guard that rejects explicit venue associations
  from current release artifacts.

### Scientific Impact

None. The benchmark v1.0.0 prompts, splits, model responses, evaluator results,
predicate, model roster, denominators, and reported findings are unchanged.

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
