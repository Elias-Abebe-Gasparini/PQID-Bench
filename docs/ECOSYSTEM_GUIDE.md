# Ecosystem And Study Roadmap

PQID-Bench is distributed through several coordinated research objects. They
serve different audiences and should not be interpreted as duplicate or
competing versions.

## Which Object Should I Use?

| Objective | Primary object | Why |
| --- | --- | --- |
| evaluate a new model | [Hugging Face benchmark distribution](https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench) | ready-to-use records, fixed splits, test prompts, response template, schemas, and compact core archive |
| install commands or use Python | [`pqid-bench` on PyPI](https://pypi.org/project/pqid-bench/) | lightweight CLI and importable API for acquisition, planning, collection, isolated replay, scoring, comparison, and reporting |
| reproduce or audit the completed study | [PQID-Bench v1.0.0 on Zenodo](https://doi.org/10.5281/zenodo.21649753) | frozen model responses, evaluator traces, analyses, checksums, and repeatability evidence |
| inspect or contribute to the implementation | [GitHub](https://github.com/Elias-Abebe-Gasparini/PQID-Bench) | maintained source, tests, examples, manuals, CI, and selected evidence |
| reproduce generated-code execution | [GHCR evaluator container](https://github.com/Elias-Abebe-Gasparini/PQID-Bench/pkgs/container/pqid-bench-evaluator) | pinned, network-disabled Docker execution environment |
| browse results without running code | [interactive evidence explorer](https://elias-abebe-gasparini.github.io/PQID-Bench/interactive/overview.html) | read-only Plotly presentation generated from frozen evidence |
| inspect the plan for the next study | [PQID-Bench 2 OSF registration](https://doi.org/10.17605/OSF.IO/WDERQ) | immutable prospective protocol; no PQID-Bench 2 observations or results |

The shortest adoption path is:

```bash
python -m pip install "pqid-bench>=1.2,<2"
pqid-bench download --version 1.0.0
```

The shortest evidence-reproduction path instead begins with the Zenodo archive
or GitHub evidence repository. A user does not need the full Zenodo archive to
benchmark a new model.

## Current Study: PQID-Bench v1.0.0

PQID-Bench v1.0.0 is the completed, frozen study object. It contains a
734-record generation population, deterministic `514 / 66 / 154` splits, a
154-prompt held-out panel, the frozen 21-model matrix, and the current
operational and reference-structure scoring contract.

Software can evolve without changing those scientific objects. For that
reason, benchmark version `1.0.0`, Python-package version `1.2.1`, evaluator
identifier `pqid-bench-evaluator-1.1.0-safe-builtins`, and container version
`1.0.0` are separate identifiers.

## Future Study: PQID-Bench 2

PQID-Bench 2 is not a patch release, an extra split, or an unreported result
from the current study. It is a separately governed future investigation that
extends the measurement ladder from operational admissibility and
reference-structure recovery to semantic validity.

Its primary registered question concerns the model-level **Semantic Void**
state: an output executes but fails a preregistered semantic oracle. Secondary
questions examine semantically valid structural divergence and controlled
contrasts across quantum-algorithm family, audited prompt scope, and explicit
algorithm-name visibility. These are descriptive and inferential questions
within a future frozen panel, not causal claims.

## What Does OSF Preregistration Mean?

The [Open Science Framework registration](https://doi.org/10.17605/OSF.IO/WDERQ)
is an immutable, timestamped snapshot of the study plan. It records what will
be tested and how key decisions will be made before the relevant outputs are
observed. This protects the distinction between:

- **confirmatory analysis**, whose hypotheses and decision rules were fixed in
  advance; and
- **exploratory analysis**, whose questions may arise after observing data.

The Stage 1 registration fixes the research questions, constructs, eligibility
principles, semantic-oracle classes, contrast families, analysis hierarchy,
and noncontamination rules. It explicitly states that no PQID-Bench 2 model
output has been collected.

A second public registration is required before data collection. Stage 2 must
freeze the exact prompt identities and hashes, qualified semantic oracles,
sample size and precision target, model-provider routes, collection rules, and
executable analysis-code commit. No PQID-Bench 2 model call is permitted until
that gate is complete.

## What Is O6?

The current research supplement labels the prospective registration pointer
**Overview object O6**. The `O` prefix distinguishes administrative overview
objects from the frozen analytical sequence of Supplemental Tables S1-S34.
O6 does not contain another analysis of the current benchmark. It tells
readers where to inspect the independently timestamped contract for the future
PQID-Bench 2 study.

## Citation Boundary

Cite the object actually used:

- cite PQID-Bench v1.0.0 for the benchmark and completed evidence;
- cite PQID v1.0.2 separately for the upstream source dataset;
- cite the software package when its tooling is material to the work; and
- cite the OSF DOI only when discussing the prospective PQID-Bench 2 protocol.

The OSF registration should not be cited as evidence that a PQID-Bench 2
hypothesis has already been supported.
