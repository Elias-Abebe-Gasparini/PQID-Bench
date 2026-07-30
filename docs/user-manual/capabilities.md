# Capability Guide

## Capability Matrix

| Capability | Command | Required input | Executes generated code | Contacts providers |
| --- | --- | --- | ---: | ---: |
| report environment and versions | `doctor` | installed package | no | no |
| verify file integrity | `verify` | evidence bundle | no | no |
| verify full scientific parity | `verify --full` | evidence bundle | no | no |
| reproduce frozen metrics | `reproduce` | evidence bundle | no | no |
| summarize supplied evaluations | `evaluate` | canonical evaluation JSONL | no | no |
| compare complete candidate | `compare` | evaluation JSONL, run manifest, evidence bundle | no | no |
| compare matched subset | `compare --allow-partial` | partial evaluation JSONL, run manifest, evidence bundle | no | no |
| build interactive report | `dashboard` | evidence bundle, Plotly extra | no | no |
| inspect live collection plan | `run-model --dry-run` | evidence bundle, route and model | no | no |
| collect fresh responses | `run-model` | evidence bundle, provider credential, acknowledgement | no | yes |
| inspect replay plan | `replay --dry-run` | response JSONL, evidence bundle, acknowledgement | no | no |
| evaluate generated responses | `replay` | response JSONL, evidence bundle, Docker, acknowledgement | yes, in Docker | no |

## Decision Guide

Use `doctor` when checking installation, optional dependencies, or Docker.

Use `verify` when checking whether a downloaded release is byte-identical to
its manifest.

Use `verify --full` when checking both byte integrity and the complete primary
and repeatability contracts.

Use `reproduce` when reconstructing the published headline quantities.

Use `evaluate` when evaluation cells have already been produced and only a
summary is needed.

Use `compare` when a candidate summary must be interpreted relative to the
frozen benchmark on the same prompt denominator.

Use `dashboard` when the frozen model, component, and repeatability results
should be inspected in one standalone interactive HTML report.

Use `run-model --dry-run` to validate a live collection contract without
reading credentials or contacting a provider.

Use `run-model` when creating a fresh, separately identified replication from
an OpenAI-compatible chat endpoint.

Use `replay --dry-run` before executing any archived or newly collected
generated code.

Use `replay` only when re-execution is scientifically necessary and Docker is
available.

## Capability Boundaries

Package version 1.1.2 does not:

- estimate provider cost;
- translate native Anthropic Messages or Google Gemini request protocols;
- hide provider retention, quota, or billing risk;
- convert arbitrary prose directly into an evaluation record;
- claim semantic equivalence from signature or tape equality;
- compare an incomplete candidate with the full frozen denominator silently;
- ship or execute an interactive Gradio evidence gateway; or
- expose provider credentials or live model execution through the Plotly
  explorer;
- mutate the frozen primary matrix.

The stable live interface targets OpenAI-compatible chat completions. Historical
native-provider scripts remain archival and are not promoted into the public
package API.

## Input And Output Summary

| Command | Principal output |
| --- | --- |
| `doctor` | JSON environment and version report |
| `verify` | JSON manifest verification |
| `verify --full` | JSON manifest plus primary and repeatability parity |
| `reproduce` | JSON, text, Markdown, or CSV summary with canonical parity |
| `evaluate` | JSON, text, Markdown, or CSV summary for supplied cells |
| `compare` | JSON, text, Markdown, or CSV aligned comparison and deltas |
| `dashboard` | standalone interactive HTML report |
| `run-model --dry-run` | credential-free JSON collection plan |
| `run-model` | canonical responses, attempts, raw payloads, hashes, and manifest |
| `replay --dry-run` | JSON Docker build and run command plan |
| `replay` | evaluator reports, canonical cells, and JSON/text/Markdown/CSV summaries |

JSON remains the default. `reproduce`, `evaluate`, and `compare` accept
`--format json|text|markdown|csv` and can additionally write the same rendered
report to a path supplied with `--output`. See
[Reporting And Numerical Exports](reporting-and-exports.md).

## Safety Levels

| Level | Operations | Trust requirement |
| --- | --- | --- |
| data-only | `doctor`, `verify`, `reproduce`, `evaluate`, `compare`, `dashboard` | read local metadata and records |
| network plan | `run-model --dry-run` | inspect prompt and route contract |
| network collection | `run-model` | accept third-party prompt export and billing |
| planned execution | `replay --dry-run` | inspect command without execution |
| isolated execution | `replay` | accept generated-code risk inside Docker |

Network collection and generated-code execution remain separate operations.
