# Docker Replay Validation

The isolated evaluator path was validated on 2026-07-23 with Docker Engine
29.3.1, the `python:3.13-slim` base image, Qiskit 2.1.1, and Qiskit Aer
0.17.0. A 2026-07-28 release-candidate rebuild additionally pins
python-dateutil 2.9.0.post0, which Qiskit Aer imports at runtime, and enforces
an import smoke test during image construction. No provider API was called and
no credential was mounted.

The corrected image was then replayed over the same complete 154-response
bundle. Its canonical and replay summaries were identical, and all execution,
QASM3, and structural indicators matched cell by cell with zero differences.

The validation proceeded in two stages:

1. one archived Qwen3-Coder-Next response was replayed as a smoke test;
2. the complete 154-response Qwen3-Coder-Next bundle was replayed and compared
   with its frozen canonical evaluator report.

The full response bundle had SHA-256
`86e3b48a7e625da0b862a15d8f4d8292bf78276e9084538090bb9a4ccf930b53`.
All 154 execution outcomes, error classes, QASM3-export outcomes, and
reference-signature component outcomes matched the canonical report. The
aggregate summaries were identical: 136 Python-execution successes, 132
extracted-circuit and QASM3 operational successes, and 78 joint
reference-signature matches.

Of the 154 complete record objects, 145 were identical after JSON parsing.
Seven differed only in the platform-specific absolute module path embedded in
an `ImportError` message. Two differed only in the statevector norm at
floating-point roundoff scale. These nine differences did not affect any
scoring indicator or aggregate statistic.

On 2026-07-29, the integrated live-replication release candidate was also
validated from its installed Python 3.14 wheel. The installed `replay` command
processed the archived 154-response Groq Llama 3.1 8B bundle through the same
network-disabled image and produced all seven required files: the evaluator
JSON and Markdown reports, canonical evaluation JSONL, and JSON, text,
Markdown, and CSV numerical summaries. The derived one-model report contained
154 cells, 125 executions, 125 assembly-admissible outputs, 54
reference-signature matches, and a 71-cell ES-Gap. This test validates the
installed-package `responses -> replay -> canonical evaluations -> R-style
summaries` path. Provider collection itself was tested with injected
transports and failure responses, so no third-party API or credential was used
for this validation.

The replay worker ran with networking disabled, a read-only root filesystem,
read-only release inputs, all Linux capabilities dropped,
`no-new-privileges`, and explicit CPU, memory, process, and temporary-filesystem
limits. This validates scientific replay parity and the package's isolation
boundary; it is not a claim that Docker makes arbitrary generated programs
intrinsically safe.
