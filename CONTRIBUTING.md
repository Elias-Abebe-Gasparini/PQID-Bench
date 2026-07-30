# Contributing to PQID-Bench

Thank you for helping improve PQID-Bench. Contributions are welcome when they
preserve the distinction between the frozen scientific evidence and the
evolving software, documentation, and replication tooling.

## Before Opening a Change

Use the issue forms to report:

- software defects or unexpected command behavior;
- documentation gaps;
- possible evidence, evaluator, or research-integrity problems.

Report suspected credential exposure or another security vulnerability
privately as described in [SECURITY.md](SECURITY.md).

## Scientific Freeze

PQID-Bench v1.0.0 is a frozen benchmark release. Pull requests must not silently
change any of the following:

- the 734-row clean generation population;
- the `514/66/154` train, validation, and test assignment;
- held-out prompts, reference targets, provider responses, or hashes;
- the 21-model primary matrix or its denominators;
- evaluator or structural-predicate semantics;
- reported benchmark results.

A proposed scientific change needs a new, explicitly versioned release and a
documented migration path. Documentation, tests, examples, presentation code,
and backward-compatible package improvements may evolve independently.

## Development Setup

PQID-Bench supports Python 3.11 through 3.14.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[visualization,schema]"
python -m pip install -r requirements/quality.txt
```

Run the local quality checks:

```bash
ruff check src tests examples scripts/build_social_preview.py
mypy src/pqid_bench
coverage erase
coverage run --branch --source=pqid_bench -m unittest discover -s tests/unit -v
coverage run --branch --source=pqid_bench --append -m unittest discover -s tests/integration -v
coverage report --show-missing
```

Run the scientific parity checks before changing release-facing material:

```bash
python -m unittest discover -s tests/release_parity -v
python scripts/validate_pqid_bench_public_release.py
pqid-bench verify . --full
```

Build documentation and distributions when the change affects either surface:

```bash
mkdocs build --strict
python -m build
```

## Pull Requests

Keep each pull request focused. Explain:

1. the problem and intended user;
2. the files and contracts affected;
3. whether frozen scientific evidence changes;
4. the checks you ran;
5. any new provider, credential, retention, or code-execution risk.

Do not commit API keys, provider responses collected without authorization,
local absolute paths, unpublished manuscripts, or generated publication
figures. Use ASCII in source files unless the surrounding file already requires
Unicode mathematical notation.

By contributing, you agree that code contributions are licensed under the MIT
terms used by this repository and documentation contributions under CC BY 4.0,
subject to the row-level provenance and upstream licensing boundaries described
in [LICENSE.md](LICENSE.md).
