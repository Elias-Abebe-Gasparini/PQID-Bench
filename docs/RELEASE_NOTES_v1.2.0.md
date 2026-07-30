# `pqid-bench` v1.2.0

Release date: 2026-07-31

Version 1.2.0 adds a benchmark-adoption path without changing the frozen
PQID-Bench v1.0.0 scientific object.

## Compact Distribution

The deterministic `PQID-Bench-v1.0.0-core.zip` contains 32 operational files:
the 734 evaluator records, materialized `514 / 66 / 154` splits, 154
model-facing prompts and response template, schemas, evaluator source,
container specification, and the scripts required for isolated replay. It
excludes archived model responses, robustness analyses, manuscript material,
figures, and repository administration.

Its SHA-256 is:

```text
74379d743d73c5401257fc48844f598fc17199c0fdccf5e1f647d10ac67b8a99
```

## Verified Acquisition

Users can install the compact release without reconstructing it from PQID:

```bash
python -m pip install "pqid-bench==1.2.0"
pqid-bench download --version 1.0.0
```

The command requires HTTPS, authenticates the archive against the pinned
digest, rejects path traversal and symbolic links, extracts into a temporary
directory, verifies `ARTIFACT_MANIFEST.tsv`, and then installs atomically.
Custom mirrors require both `--url` and `--sha256`.

## Hugging Face Distribution

The Hugging Face adapter now stages an explicit data-only repository instead
of mirroring the GitHub source tree. It contains the benchmark records, direct
splits, prompts, response template, schemas, citation and license files,
benchmark metadata, and the compact ZIP. Publication opens a reviewable pull
request by default.

## Version Crosswalk

| Dimension | Identifier |
| --- | --- |
| Python toolkit | `pqid-bench 1.2.0` |
| frozen benchmark | `PQID-Bench 1.0.0` |
| evaluator | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| structural predicate | `pqid-bench-reference-signature-1.0.0-count-map` |
| evaluator container | `1.0.0` |

No score, model output, target, denominator, or inferential result changed.
