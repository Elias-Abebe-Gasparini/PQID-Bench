# PQID-Bench Complexity-Difficulty Analysis

- prompts: `154`
- completed models: `19`
- prompt-model evaluations: `2926`
- pooled execution success: `91.35%`
- pooled structural match: `53.28%`

## Width
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 qubits | 51 | 969 | 94.12% | 60.68% | 62.54% | 84.83% | 94.01% | 89.27% | 94.01% |
| 3 qubits | 60 | 1140 | 89.04% | 47.89% | 61.58% | 74.91% | 83.51% | 68.77% | 88.68% |
| 4 qubits | 22 | 418 | 88.28% | 47.85% | 55.50% | 70.81% | 81.10% | 69.86% | 88.28% |
| 5-8 qubits | 17 | 323 | 93.50% | 57.89% | 63.78% | 85.14% | 93.19% | 83.90% | 93.50% |
| 9+ qubits | 4 | 76 | 98.68% | 50.00% | 52.63% | 75.00% | 98.68% | 96.05% | 98.68% |

## Gate Count
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2-4 gates | 55 | 1045 | 93.21% | 59.43% | 67.56% | 79.81% | 88.90% | 79.71% | 93.21% |
| 5-8 gates | 66 | 1254 | 93.22% | 58.21% | 66.51% | 84.37% | 89.31% | 81.18% | 92.90% |
| 9-12 gates | 18 | 342 | 89.18% | 47.95% | 54.39% | 79.53% | 88.89% | 75.15% | 89.18% |
| 13-20 gates | 9 | 171 | 79.53% | 24.56% | 33.92% | 70.18% | 79.53% | 68.42% | 78.95% |
| 21+ gates | 6 | 114 | 78.07% | 1.75% | 1.75% | 17.54% | 78.07% | 52.63% | 78.07% |

## Gate-Type Diversity
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 gate types | 42 | 798 | 95.74% | 72.31% | 81.83% | 82.83% | 91.23% | 82.33% | 95.74% |
| 3-4 gate types | 85 | 1615 | 91.08% | 54.67% | 61.18% | 79.07% | 87.43% | 78.89% | 90.84% |
| 5+ gate types | 27 | 513 | 85.38% | 19.30% | 28.27% | 71.35% | 85.38% | 69.01% | 85.19% |

## Classical Bits
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 clbits | 33 | 627 | 89.31% | 65.39% | 73.52% | 77.03% | 89.15% | 75.28% | 89.31% |
| 1-2 clbits | 45 | 855 | 94.85% | 60.35% | 60.58% | 85.85% | 94.74% | 94.62% | 94.74% |
| 3 clbits | 59 | 1121 | 88.67% | 44.51% | 58.61% | 71.72% | 80.37% | 65.39% | 88.31% |
| 4+ clbits | 17 | 323 | 95.36% | 41.49% | 46.44% | 87.62% | 95.36% | 83.90% | 95.36% |

## Feature Presence
| feature group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| has_measure=False | 62 | 1178 | 89.30% | 52.38% | 67.23% | 69.44% | 84.80% | 67.40% | 89.05% |
| has_measure=True | 92 | 1748 | 92.73% | 53.89% | 56.86% | 85.01% | 90.33% | 85.30% | 92.62% |
| has_barrier=False | 101 | 1919 | 91.66% | 65.87% | 75.56% | 78.53% | 87.65% | 77.38% | 91.61% |
| has_barrier=True | 53 | 1007 | 90.76% | 29.29% | 33.37% | 79.15% | 88.98% | 79.44% | 90.37% |
| has_controlled_or_entangling=False | 48 | 912 | 92.32% | 59.21% | 61.73% | 72.15% | 87.06% | 82.89% | 92.00% |
| has_controlled_or_entangling=True | 106 | 2014 | 90.91% | 50.60% | 60.72% | 81.73% | 88.58% | 75.92% | 90.81% |
| has_rotation=False | 134 | 2546 | 92.62% | 55.46% | 61.90% | 80.64% | 88.88% | 80.75% | 92.42% |
| has_rotation=True | 20 | 380 | 82.89% | 38.68% | 55.26% | 66.05% | 82.89% | 60.26% | 82.89% |

## Prompt-Derived Circuit Families
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pauli_measurement | 98 | 1862 | 92.21% | 52.63% | 55.59% | 82.17% | 89.74% | 84.21% | 91.94% |
| generic_or_low_level | 28 | 532 | 93.61% | 68.05% | 78.95% | 79.32% | 93.61% | 79.32% | 93.61% |
| bell_or_superdense | 25 | 475 | 94.74% | 53.26% | 62.53% | 87.37% | 86.95% | 78.32% | 94.74% |
| oracle_logic | 13 | 247 | 90.69% | 48.99% | 51.42% | 79.35% | 89.88% | 80.97% | 90.28% |
| arithmetic_toffoli | 12 | 228 | 81.14% | 16.23% | 35.53% | 58.77% | 80.70% | 55.26% | 81.14% |
| deutsch_jozsa | 8 | 152 | 90.13% | 27.63% | 31.58% | 86.18% | 90.13% | 75.66% | 89.47% |
| deep_mixed_rotation | 7 | 133 | 72.93% | 11.28% | 35.34% | 39.85% | 72.93% | 33.83% | 72.93% |
| ghz | 5 | 95 | 100.00% | 71.58% | 73.68% | 91.58% | 100.00% | 97.89% | 100.00% |
| bernstein_vazirani | 4 | 76 | 80.26% | 26.32% | 28.95% | 30.26% | 47.37% | 50.00% | 80.26% |
| fourier_qft_phase | 4 | 76 | 84.21% | 43.42% | 43.42% | 73.68% | 84.21% | 77.63% | 82.89% |
| teleportation | 4 | 76 | 81.58% | 44.74% | 46.05% | 76.32% | 81.58% | 77.63% | 81.58% |
| error_correction | 3 | 57 | 82.46% | 3.51% | 75.44% | 78.95% | 75.44% | 7.02% | 82.46% |
| vqc_ansatz | 2 | 38 | 71.05% | 60.53% | 71.05% | 71.05% | 71.05% | 60.53% | 71.05% |

Singleton family labels are retained in the JSON artifact but omitted from this table.

## Correlation With Per-Prompt Structural Rate

| descriptor | Pearson r |
| --- | ---: |
| `num_qubits` | -0.046 |
| `num_clbits` | -0.217 |
| `gate_count` | -0.233 |
| `gate_type_count` | -0.418 |
| `gate_entropy` | -0.440 |

## Hardest Prompts By Mean Structural Match

| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0091` | `strict_n8` | 20 | 20 | 134 | 5 | 0.00% | pauli_measurement | Create a Qiskit circuit with 20 qubits and 20 classical bits that applies the given sequence of rx, ry, rz, an |
| `pqid_bench_external_gen_0141` | `extended_n8` | 5 | 0 | 88 | 4 | 0.00% | generic_or_low_level | Create a 5-qubit quantum circuit with q4 prepared in superposition, q0-q2 initially flipped to /1>, and then a |
| `pqid_bench_external_gen_0060` | `extended_n8` | 3 | 3 | 25 | 12 | 0.00% | pauli_measurement, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep gate sequence that mixes single-qubit phase/Pauli operations with  |
| `pqid_bench_external_gen_0106` | `extended_n8` | 3 | 3 | 25 | 15 | 0.00% | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep, mixed gate pattern that includes Fredkin, Toffoli, CZ, SWAP, RZZ, |
| `pqid_bench_external_gen_0142` | `extended_n8` | 3 | 3 | 25 | 14 | 0.00% | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep mix of swap-family and controlled operations, including at least o |
| `pqid_bench_external_gen_0136` | `strict_n8` | 3 | 3 | 19 | 6 | 0.00% | fourier_qft_phase, pauli_measurement | Build a 3-qubit Qiskit circuit that prepares /101>, applies a 3-qubit QFT, inserts a barrier, then applies the |
| `pqid_bench_external_gen_0040` | `extended_n8` | 3 | 0 | 18 | 4 | 0.00% | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit that implements the shown CCX-style decomposition using only single-qubit rota |
| `pqid_bench_external_gen_0046` | `extended_n8` | 5 | 4 | 15 | 5 | 0.00% | deutsch_jozsa, oracle_logic, pauli_measurement | Create a Qiskit circuit for a 4-input balanced Deutsch–Jozsa oracle that uses 5 qubits total: prepare the anci |
| `pqid_bench_external_gen_0087` | `extended_n8` | 5 | 4 | 14 | 4 | 0.00% | deutsch_jozsa, pauli_measurement | Create a 5-qubit, 4-classical-bit Qiskit circuit in the style of a Deutsch–Jozsa setup: flip the last qubit to |
| `pqid_bench_external_gen_0022` | `strict_n8` | 3 | 3 | 13 | 5 | 0.00% | error_correction, arithmetic_toffoli, pauli_measurement | Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2  |

## Easiest Prompts By Mean Structural Match

| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0059` | `extended_n8` | 1 | 1 | 2 | 2 | 100.00% | pauli_measurement | Create a minimal 1-qubit quantum circuit that applies a Z gate to qubit 0 and then measures it into a 1-bit cl |
| `pqid_bench_external_gen_0037` | `extended_n8` | 2 | 2 | 3 | 2 | 100.00% | pauli_measurement | Create a small 2-qubit Qiskit circuit that applies a CNOT with qubit 0 as control and qubit 1 as target, then  |
| `pqid_bench_external_gen_0019` | `strict_n8` | 2 | 2 | 4 | 3 | 100.00% | bell_or_superdense, pauli_measurement | Create a 2-qubit Bell-state circuit in Qiskit: apply a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit  |
| `pqid_bench_external_gen_0055` | `extended_n8` | 2 | 2 | 4 | 3 | 100.00% | bell_or_superdense, pauli_measurement | Create a small Qiskit circuit that prepares a Bell pair on two qubits with a Hadamard on qubit 0, a CNOT from  |
| `pqid_bench_external_gen_0013` | `strict_n8` | 2 | 2 | 5 | 2 | 100.00% | pauli_measurement | Create a 2-qubit, 2-classical-bit Qiskit circuit that applies a Hadamard to qubit 0, applies two consecutive H |
| `pqid_bench_external_gen_0014` | `strict_n8` | 2 | 2 | 5 | 3 | 100.00% | bell_or_superdense, pauli_measurement | Create a 2-qubit Qiskit circuit with 2 classical bits that prepares a Bell pair, then applies a Hadamard to qu |
| `pqid_bench_external_gen_0056` | `extended_n8` | 2 | 2 | 5 | 4 | 100.00% | bell_or_superdense, pauli_measurement | Create a 2-qubit quantum circuit that makes a Bell pair with an H on qubit 0 and a CNOT from qubit 0 to qubit  |
| `pqid_bench_external_gen_0101` | `extended_n8` | 2 | 2 | 5 | 3 | 100.00% | pauli_measurement | Create a small 2-qubit Qiskit circuit that applies a Hadamard to qubit 0, then a CNOT from 0 to 1 followed by  |
| `pqid_bench_external_gen_0003` | `strict_n8` | 3 | 3 | 5 | 2 | 100.00% | pauli_measurement | Create a 3-qubit, 3-classical-bit Qiskit circuit where qubit 0 gets two consecutive Hadamard gates and then al |
| `pqid_bench_external_gen_0121` | `strict_n8` | 2 | 1 | 6 | 4 | 100.00% | pauli_measurement | Create a 2-qubit Qiskit circuit with 1 classical bit that applies Hadamards to both qubits, inserts a barrier, |

## Interpretation

The clearest complexity signal is gate-type diversity: targets with five or more gate types have substantially lower structural-match rates than targets with one or two gate types. Width and gate count are not monotone in this split because many wider circuits are regular Hadamard/CX templates, while some short circuits contain classical-control or gate-order traps. The benchmark therefore supports a refined version of the complexity hypothesis: structural difficulty increases most clearly with heterogeneity and semantic specificity, not with raw qubit count alone.
