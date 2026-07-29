# PQID-Bench Complexity-Difficulty Analysis

- prompts: `150`
- completed models: `21`
- prompt-model evaluations: `3150`
- pooled execution success: `91.75%`
- pooled structural match: `54.06%`

## Width
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 qubits | 51 | 1071 | 93.65% | 59.94% | 61.90% | 83.75% | 93.56% | 88.14% | 93.56% |
| 3 qubits | 57 | 1197 | 89.97% | 50.38% | 64.66% | 76.86% | 84.29% | 69.67% | 89.56% |
| 4 qubits | 22 | 462 | 88.74% | 46.32% | 54.11% | 69.05% | 81.17% | 69.05% | 88.74% |
| 5-8 qubits | 16 | 336 | 94.64% | 60.42% | 66.67% | 89.88% | 94.35% | 86.90% | 94.64% |
| 9+ qubits | 4 | 84 | 97.62% | 48.81% | 51.19% | 73.81% | 97.62% | 95.24% | 97.62% |

## Gate Count
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2-4 gates | 55 | 1155 | 92.90% | 58.18% | 66.49% | 78.53% | 88.66% | 78.35% | 92.90% |
| 5-8 gates | 65 | 1365 | 93.04% | 58.61% | 67.03% | 83.66% | 89.08% | 81.10% | 92.67% |
| 9-12 gates | 18 | 378 | 89.15% | 48.41% | 54.23% | 79.10% | 88.62% | 75.40% | 89.15% |
| 13-20 gates | 8 | 168 | 83.93% | 27.38% | 38.10% | 78.57% | 83.93% | 71.43% | 83.33% |
| 21+ gates | 4 | 84 | 82.14% | 2.38% | 2.38% | 23.81% | 82.14% | 61.90% | 82.14% |

## Gate-Type Diversity
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 gate types | 42 | 882 | 95.58% | 71.20% | 80.84% | 81.75% | 91.04% | 81.63% | 95.58% |
| 3-4 gate types | 82 | 1722 | 91.41% | 56.16% | 62.89% | 80.26% | 87.63% | 79.15% | 91.11% |
| 5+ gate types | 26 | 546 | 86.63% | 19.78% | 28.94% | 72.71% | 86.63% | 70.70% | 86.45% |

## Classical Bits
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 clbits | 30 | 630 | 89.52% | 68.25% | 78.10% | 79.21% | 89.21% | 73.81% | 89.52% |
| 1-2 clbits | 45 | 945 | 94.81% | 60.53% | 60.74% | 85.40% | 94.71% | 94.60% | 94.71% |
| 3 clbits | 58 | 1218 | 89.33% | 45.32% | 59.36% | 72.33% | 80.95% | 66.26% | 88.92% |
| 4+ clbits | 17 | 357 | 95.80% | 41.74% | 46.22% | 87.68% | 95.80% | 84.87% | 95.80% |

## Feature Presence
| feature group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| has_measure=False | 58 | 1218 | 90.15% | 54.11% | 69.95% | 70.69% | 85.22% | 67.41% | 89.82% |
| has_measure=True | 92 | 1932 | 92.75% | 54.04% | 57.04% | 84.83% | 90.42% | 85.30% | 92.65% |
| has_barrier=False | 99 | 2079 | 92.16% | 66.47% | 76.48% | 79.17% | 88.07% | 77.39% | 92.11% |
| has_barrier=True | 51 | 1071 | 90.94% | 29.97% | 33.99% | 79.74% | 89.08% | 80.30% | 90.48% |
| has_controlled_or_entangling=False | 47 | 987 | 92.30% | 60.18% | 62.51% | 71.53% | 86.93% | 82.78% | 91.89% |
| has_controlled_or_entangling=True | 103 | 2163 | 91.49% | 51.27% | 61.81% | 82.94% | 89.09% | 76.38% | 91.40% |
| has_rotation=False | 132 | 2772 | 92.86% | 55.81% | 62.45% | 80.66% | 89.07% | 80.84% | 92.64% |
| has_rotation=True | 18 | 378 | 83.60% | 41.27% | 58.99% | 69.84% | 83.60% | 60.32% | 83.60% |

## Prompt-Derived Circuit Families
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pauli_measurement | 98 | 2058 | 92.27% | 52.67% | 55.69% | 81.92% | 89.89% | 84.16% | 91.98% |
| generic_or_low_level | 27 | 567 | 93.30% | 68.25% | 79.72% | 80.07% | 93.30% | 79.37% | 93.30% |
| bell_or_superdense | 25 | 525 | 94.48% | 52.38% | 62.29% | 86.48% | 86.67% | 76.76% | 94.48% |
| oracle_logic | 13 | 273 | 91.21% | 49.45% | 51.65% | 79.12% | 90.11% | 81.32% | 90.84% |
| arithmetic_toffoli | 10 | 210 | 85.71% | 20.00% | 42.38% | 67.62% | 84.76% | 58.10% | 85.71% |
| deutsch_jozsa | 8 | 168 | 90.48% | 27.38% | 30.95% | 85.12% | 90.48% | 76.19% | 89.88% |
| deep_mixed_rotation | 5 | 105 | 79.05% | 17.14% | 50.48% | 53.33% | 79.05% | 30.48% | 79.05% |
| ghz | 5 | 105 | 100.00% | 71.43% | 73.33% | 91.43% | 100.00% | 98.10% | 100.00% |
| bernstein_vazirani | 4 | 84 | 82.14% | 26.19% | 28.57% | 29.76% | 47.62% | 50.00% | 82.14% |
| teleportation | 4 | 84 | 83.33% | 46.43% | 48.81% | 78.57% | 83.33% | 78.57% | 83.33% |
| error_correction | 3 | 63 | 84.13% | 3.17% | 76.19% | 79.37% | 77.78% | 7.94% | 84.13% |
| fourier_qft_phase | 3 | 63 | 84.13% | 58.73% | 58.73% | 73.02% | 84.13% | 82.54% | 82.54% |
| vqc_ansatz | 2 | 42 | 69.05% | 57.14% | 66.67% | 66.67% | 69.05% | 57.14% | 69.05% |

Singleton family labels are retained in the JSON artifact but omitted from this table.

## Correlation With Per-Prompt Structural Rate

| descriptor | Pearson r |
| --- | ---: |
| `num_qubits` | -0.051 |
| `num_clbits` | -0.232 |
| `gate_count` | -0.190 |
| `gate_type_count` | -0.414 |
| `gate_entropy` | -0.426 |

## Hardest Prompts By Mean Structural Match

| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0091` | `strict_n8` | 20 | 20 | 134 | 5 | 0.00% | pauli_measurement | Create a Qiskit circuit with 20 qubits and 20 classical bits that applies the given sequence of rx, ry, rz, an |
| `pqid_bench_external_gen_0060` | `extended_n8` | 3 | 3 | 25 | 12 | 0.00% | pauli_measurement, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep gate sequence that mixes single-qubit phase/Pauli operations with  |
| `pqid_bench_external_gen_0106` | `extended_n8` | 3 | 3 | 25 | 15 | 0.00% | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep, mixed gate pattern that includes Fredkin, Toffoli, CZ, SWAP, RZZ, |
| `pqid_bench_external_gen_0136` | `strict_n8` | 3 | 3 | 19 | 6 | 0.00% | fourier_qft_phase, pauli_measurement | Build a 3-qubit Qiskit circuit that prepares /101>, applies a 3-qubit QFT, inserts a barrier, then applies the |
| `pqid_bench_external_gen_0046` | `extended_n8` | 5 | 4 | 15 | 5 | 0.00% | deutsch_jozsa, oracle_logic, pauli_measurement | Create a Qiskit circuit for a 4-input balanced Deutsch–Jozsa oracle that uses 5 qubits total: prepare the anci |
| `pqid_bench_external_gen_0087` | `extended_n8` | 5 | 4 | 14 | 4 | 0.00% | deutsch_jozsa, pauli_measurement | Create a 5-qubit, 4-classical-bit Qiskit circuit in the style of a Deutsch–Jozsa setup: flip the last qubit to |
| `pqid_bench_external_gen_0022` | `strict_n8` | 3 | 3 | 13 | 5 | 0.00% | error_correction, arithmetic_toffoli, pauli_measurement | Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2  |
| `pqid_bench_external_gen_0050` | `extended_n8` | 4 | 4 | 12 | 5 | 0.00% | arithmetic_toffoli, pauli_measurement | Create a 4-qubit Qiskit circuit that starts with an X on qubit 0, applies a barrier, runs CX(0,1), CX(0,2), CC |
| `pqid_bench_external_gen_0036` | `extended_n8` | 4 | 3 | 10 | 5 | 0.00% | deutsch_jozsa, oracle_logic, pauli_measurement | Create a compact Qiskit circuit for a 4-qubit Deutsch–Jozsa-style setup: initialize the last qubit in /1>, app |
| `pqid_bench_external_gen_0095` | `extended_n8` | 4 | 0 | 9 | 4 | 0.00% | oracle_logic, arithmetic_toffoli | Create a 4-qubit quantum circuit that implements a phase oracle by computing a two-input logical condition ont |

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
