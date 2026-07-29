# PQID-Bench Operational Assembly-Layer Audit

Frozen panel: `21 x 154 = 3,234` model-prompt cells.

## Endpoint Definitions

- `E`: executable-circuit materialization; generated Python completes and the evaluator selects a `QuantumCircuit`.
- `A`: quantum-assembly admissibility; `E=1` and the selected circuit serializes successfully to OpenQASM 3 under the frozen evaluator.
- `M_sig`: recovery of the frozen qubit count, classical-bit count, and complete operation-type count map.
- Scope: `A` does not mean that the emitted OpenQASM 3 program was executed on a simulator or hardware backend.

## Frozen-Panel Results

| endpoint or contrast | count | rate |
| --- | ---: | ---: |
| Python program completes | 2,963 | 91.62% |
| executable-circuit materialization, `E` | 2,950 | 91.22% |
| quantum-assembly admissibility, `A` | 2,944 | 91.03% |
| reference-signature recovery, `M_sig` | 1,703 | 52.66% |
| `E=1, A=0` | 6 | 0.19 pp |
| `A=1, M_sig=0` | 1,241 | 38.37 pp |
| `E=1, M_sig=0` | 1,247 | 38.56 pp |

The pointwise chain `M_sig <= A <= E` has zero violations. The Assembly-Structure Gap (AS-Gap) retains `99.52%` of the signature-level ES-Gap.

## Six Executable Circuits Without Assembly Admissibility

| model | prompt | provider | export error |
| --- | --- | --- | --- |
| Claude Opus 4.8 | `pqid_bench_external_gen_0136` | `anthropic` | `QASM3ExporterError` |
| Llama 4 Maverick | `pqid_bench_external_gen_0083` | `github_models` | `QASM3ExporterError` |
| GPT-OSS 120B | `pqid_bench_external_gen_0082` | `groq` | `QASM3ExporterError` |
| GPT-OSS 20B | `pqid_bench_external_gen_0082` | `groq` | `QASM3ExporterError` |
| GPT-5.4 mini | `pqid_bench_external_gen_0082` | `openai` | `QASM3ExporterError` |
| Qiskit Mistral 3.2 24B | `pqid_bench_external_gen_0082` | `huggingface_router` | `QASM3ExporterError` |

The audit reads the canonical evaluator reports only. It does not change prompts, outputs, targets, evaluator policy, or structural predicates.
