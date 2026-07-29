# PQID-Bench User Manual

This manual guides a user from installation through scientific reproduction,
live model collection, candidate comparison, isolated replay, numerical
reporting, troubleshooting, and citation. It documents `pqid-bench 1.0.0` as
implemented.

## Manual Chapters

1. [Installation](installation.md)
2. [Core Concepts](core-concepts.md)
3. [Capability Guide](capabilities.md)
4. [Live Model Testing](live-model-testing.md)
5. [CLI Reference](cli-reference.md)
6. [Reporting And Numerical Exports](reporting-and-exports.md)
7. [Python API](python-api.md)
8. [Data Dictionary](data-dictionary.md)
9. [Metrics And Invariants](metrics-and-invariants.md)
10. [End-To-End Workflows](workflows.md)
11. [Reproducibility Contract](reproducibility-contract.md)
12. [Security And Governance](security-governance.md)
13. [Troubleshooting](troubleshooting.md)
14. [Glossary](glossary.md)

## Reading Paths

**First-time user**

Read Installation, Core Concepts, and Capability Guide, then complete Workflow
1 in the workflow chapter.

**Paper reviewer**

Use the [Reviewer Quickstart](../REVIEWER_QUICKSTART.md), followed by the
Reproducibility Contract when auditing claims and denominators.

**Researcher with new model outputs**

Read Live Model Testing and the evaluation and run-manifest portions of the
Data Dictionary, then the candidate-summary and comparison workflows. Use
Reporting And Numerical Exports when moving results into R, pandas, or a
manuscript.

**Package integrator**

Read the Reporting And Numerical Exports, Python API, Data Dictionary, Metrics
And Invariants, and Security And Governance chapters.

**Maintainer or software-paper author**

Read the complete manual and the
[Package Paper Blueprint](../PACKAGE_PAPER_BLUEPRINT.md).

## Conventions

- `RELEASE_DIR` means the root of the extracted frozen evidence bundle. It is
  the directory containing `ARTIFACT_MANIFEST.tsv`.
- `EVALUATIONS.jsonl` means newline-delimited canonical evaluation objects.
- `RESPONSES.jsonl` means archived canonical model-response objects accepted by
  the replay harness.
- Shell examples use `\` for line continuation. In PowerShell, place the
  command on one line or replace `\` with the PowerShell backtick.
- Counts and rates in this manual refer to the frozen version 1.0.0 release
  unless a candidate or matched subset is explicitly named.

## Scope

The manual covers offline verification, reproduction, live OpenAI-compatible
collection, summarization, comparison, and archived or newly collected code
replay. Live calls always create a new replication rather than reproducing
archived model text. Native non-compatible provider protocols and automatic
cost estimation remain outside version 1.0.0.
