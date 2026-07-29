# `pqid-bench` v1.1.0

Release date: 2026-07-30

## Scope

Version 1.1.0 is a software and documentation release for the frozen
PQID-Bench v1.0.0 study. It does not change any benchmark prompt, split,
response, target, evaluator result, structural predicate, model roster,
denominator, or reported numerical finding. The benchmark archive remains
identified by DOI
[`10.5281/zenodo.21649753`](https://doi.org/10.5281/zenodo.21649753).

## Added

- `pqid-bench dashboard`, which creates a standalone interactive Plotly report
  from the frozen evidence bundle;
- an importable visualization API:
  `load_dashboard_data`, `build_dashboard`, and `write_site_assets`;
- five coordinated evidence views covering the measurement ladder, model
  profiles, component recovery, stochastic repeatability, and provider-route
  aggregates;
- an accessible tabular representation of every plotted model row;
- a GitHub Pages documentation workflow that generates presentation assets
  after validating the source evidence tree;
- a navigable MkDocs Material manual, workflow diagram, and static README
  fallback; and
- a `visualization` optional dependency group based on Plotly 6.

## Boundaries

The explorer is a presentation layer. It neither contacts a model provider nor
executes generated code. Fresh provider collection remains the responsibility
of `pqid-bench run-model`; executable evaluation remains isolated in the
Docker-backed `pqid-bench replay` path.

Interactive HTML and generated SVG assets are Pages build products. They are
not inserted into the DOI-bound frozen evidence archive or the Hugging Face
dataset payload. PyPI renders the static README and links to the hosted
explorer because package indexes do not execute embedded JavaScript.

## Version Dimensions

| Dimension | Identifier |
| --- | --- |
| Python package | `1.1.0` |
| benchmark release | `1.0.0` |
| evaluator | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` |
| schema | `1.0.0` |
| frozen artifact manifest | `1.0.0` |
| container artifact | `1.0.0` |

