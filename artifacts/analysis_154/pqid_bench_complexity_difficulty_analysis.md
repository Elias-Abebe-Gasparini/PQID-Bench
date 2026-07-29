# PQID-Bench Complexity-Difficulty Analysis

- prompts: `154`
- completed models: `21`
- prompt-model evaluations: `3234`
- pooled execution success: `91.22%`
- pooled structural match: `52.66%`

## Width
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 qubits | 51 | 1071 | 93.65% | 59.94% | 61.90% | 83.75% | 93.56% | 88.14% | 93.56% |
| 3 qubits | 60 | 1260 | 88.89% | 47.86% | 61.43% | 74.44% | 83.49% | 68.81% | 88.49% |
| 4 qubits | 22 | 462 | 88.74% | 46.32% | 54.11% | 69.05% | 81.17% | 69.05% | 88.74% |
| 5-8 qubits | 17 | 357 | 93.84% | 56.86% | 62.75% | 84.59% | 93.56% | 83.47% | 93.84% |
| 9+ qubits | 4 | 84 | 97.62% | 48.81% | 51.19% | 73.81% | 97.62% | 95.24% | 97.62% |

## Gate Count
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2-4 gates | 55 | 1155 | 92.90% | 58.18% | 66.49% | 78.53% | 88.66% | 78.35% | 92.90% |
| 5-8 gates | 66 | 1386 | 93.00% | 57.72% | 66.02% | 83.48% | 89.11% | 80.88% | 92.64% |
| 9-12 gates | 18 | 378 | 89.15% | 48.41% | 54.23% | 79.10% | 88.62% | 75.40% | 89.15% |
| 13-20 gates | 9 | 189 | 80.95% | 24.34% | 33.86% | 70.37% | 80.95% | 69.31% | 80.42% |
| 21+ gates | 6 | 126 | 77.78% | 1.59% | 1.59% | 17.46% | 77.78% | 52.38% | 77.78% |

## Gate-Type Diversity
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 gate types | 42 | 882 | 95.58% | 71.20% | 80.84% | 81.75% | 91.04% | 81.63% | 95.58% |
| 3-4 gate types | 85 | 1785 | 90.87% | 54.17% | 60.67% | 78.32% | 87.23% | 78.10% | 90.59% |
| 5+ gate types | 27 | 567 | 85.54% | 19.05% | 27.87% | 70.37% | 85.54% | 69.49% | 85.36% |

## Classical Bits
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 clbits | 33 | 693 | 88.31% | 62.05% | 71.00% | 74.31% | 88.02% | 71.57% | 88.31% |
| 1-2 clbits | 45 | 945 | 94.81% | 60.53% | 60.74% | 85.40% | 94.71% | 94.60% | 94.71% |
| 3 clbits | 59 | 1239 | 88.78% | 44.55% | 58.35% | 71.27% | 80.55% | 65.78% | 88.38% |
| 4+ clbits | 17 | 357 | 95.80% | 41.74% | 46.22% | 87.68% | 95.80% | 84.87% | 95.80% |

## Feature Presence
| feature group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| has_measure=False | 62 | 1302 | 88.94% | 50.61% | 65.44% | 67.51% | 84.33% | 66.05% | 88.63% |
| has_measure=True | 92 | 1932 | 92.75% | 54.04% | 57.04% | 84.83% | 90.42% | 85.30% | 92.65% |
| has_barrier=False | 101 | 2121 | 91.47% | 65.16% | 74.96% | 77.75% | 87.46% | 76.76% | 91.42% |
| has_barrier=True | 53 | 1113 | 90.75% | 28.84% | 32.70% | 78.08% | 88.95% | 79.07% | 90.30% |
| has_controlled_or_entangling=False | 48 | 1008 | 92.26% | 58.93% | 61.21% | 71.53% | 87.00% | 82.44% | 91.87% |
| has_controlled_or_entangling=True | 106 | 2226 | 90.75% | 49.82% | 60.06% | 80.73% | 88.41% | 75.34% | 90.66% |
| has_rotation=False | 134 | 2814 | 92.75% | 54.98% | 61.51% | 79.99% | 89.02% | 80.35% | 92.54% |
| has_rotation=True | 20 | 420 | 80.95% | 37.14% | 53.10% | 63.57% | 80.95% | 58.81% | 80.95% |

## Prompt-Derived Circuit Families
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pauli_measurement | 98 | 2058 | 92.27% | 52.67% | 55.69% | 81.92% | 89.89% | 84.16% | 91.98% |
| generic_or_low_level | 28 | 588 | 92.86% | 65.82% | 76.87% | 77.21% | 92.86% | 77.55% | 92.86% |
| bell_or_superdense | 25 | 525 | 94.48% | 52.38% | 62.29% | 86.48% | 86.67% | 76.76% | 94.48% |
| oracle_logic | 13 | 273 | 91.21% | 49.45% | 51.65% | 79.12% | 90.11% | 81.32% | 90.84% |
| arithmetic_toffoli | 12 | 252 | 80.95% | 16.67% | 35.32% | 57.54% | 80.16% | 55.95% | 80.95% |
| deutsch_jozsa | 8 | 168 | 90.48% | 27.38% | 30.95% | 85.12% | 90.48% | 76.19% | 89.88% |
| deep_mixed_rotation | 7 | 147 | 72.79% | 12.24% | 36.05% | 40.14% | 72.79% | 34.69% | 72.79% |
| ghz | 5 | 105 | 100.00% | 71.43% | 73.33% | 91.43% | 100.00% | 98.10% | 100.00% |
| bernstein_vazirani | 4 | 84 | 82.14% | 26.19% | 28.57% | 29.76% | 47.62% | 50.00% | 82.14% |
| fourier_qft_phase | 4 | 84 | 85.71% | 44.05% | 44.05% | 72.62% | 85.71% | 78.57% | 84.52% |
| teleportation | 4 | 84 | 83.33% | 46.43% | 48.81% | 78.57% | 83.33% | 78.57% | 83.33% |
| error_correction | 3 | 63 | 84.13% | 3.17% | 76.19% | 79.37% | 77.78% | 7.94% | 84.13% |
| vqc_ansatz | 2 | 42 | 69.05% | 57.14% | 66.67% | 66.67% | 69.05% | 57.14% | 69.05% |

Singleton family labels are retained in the JSON artifact but omitted from this table.

## Correlation With Per-Prompt Structural Rate

| descriptor | Pearson r |
| --- | ---: |
| `num_qubits` | -0.052 |
| `num_clbits` | -0.199 |
| `gate_count` | -0.231 |
| `gate_type_count` | -0.414 |
| `gate_entropy` | -0.433 |

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
