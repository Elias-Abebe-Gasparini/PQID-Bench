# PQID-Bench Complexity-Difficulty Analysis

- prompts: `150`
- completed models: `19`
- prompt-model evaluations: `2850`
- pooled execution success: `91.89%`
- pooled structural match: `54.70%`

## Width
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 qubits | 51 | 969 | 94.12% | 60.68% | 62.54% | 84.83% | 94.01% | 89.27% | 94.01% |
| 3 qubits | 57 | 1083 | 90.12% | 50.42% | 64.82% | 77.29% | 84.30% | 69.62% | 89.75% |
| 4 qubits | 22 | 418 | 88.28% | 47.85% | 55.50% | 70.81% | 81.10% | 69.86% | 88.28% |
| 5-8 qubits | 16 | 304 | 94.41% | 61.51% | 67.76% | 90.46% | 94.08% | 87.17% | 94.41% |
| 9+ qubits | 4 | 76 | 98.68% | 50.00% | 52.63% | 75.00% | 98.68% | 96.05% | 98.68% |

## Gate Count
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2-4 gates | 55 | 1045 | 93.21% | 59.43% | 67.56% | 79.81% | 88.90% | 79.71% | 93.21% |
| 5-8 gates | 65 | 1235 | 93.28% | 59.11% | 67.53% | 84.53% | 89.31% | 81.38% | 92.96% |
| 9-12 gates | 18 | 342 | 89.18% | 47.95% | 54.39% | 79.53% | 88.89% | 75.15% | 89.18% |
| 13-20 gates | 8 | 152 | 82.24% | 27.63% | 38.16% | 78.29% | 82.24% | 70.39% | 81.58% |
| 21+ gates | 4 | 76 | 82.89% | 2.63% | 2.63% | 23.68% | 82.89% | 61.84% | 82.89% |

## Gate-Type Diversity
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 gate types | 42 | 798 | 95.74% | 72.31% | 81.83% | 82.83% | 91.23% | 82.33% | 95.74% |
| 3-4 gate types | 82 | 1558 | 91.66% | 56.68% | 63.41% | 81.00% | 87.87% | 79.91% | 91.40% |
| 5+ gate types | 26 | 494 | 86.44% | 20.04% | 29.35% | 73.68% | 86.44% | 70.24% | 86.23% |

## Classical Bits
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 clbits | 30 | 570 | 90.70% | 71.93% | 80.88% | 82.11% | 90.53% | 77.72% | 90.70% |
| 1-2 clbits | 45 | 855 | 94.85% | 60.35% | 60.58% | 85.85% | 94.74% | 94.62% | 94.74% |
| 3 clbits | 58 | 1102 | 89.20% | 45.28% | 59.62% | 72.78% | 80.76% | 65.88% | 88.84% |
| 4+ clbits | 17 | 323 | 95.36% | 41.49% | 46.44% | 87.62% | 95.36% | 83.90% | 95.36% |

## Feature Presence
| feature group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| has_measure=False | 58 | 1102 | 90.56% | 55.99% | 71.87% | 72.69% | 85.75% | 68.78% | 90.29% |
| has_measure=True | 92 | 1748 | 92.73% | 53.89% | 56.86% | 85.01% | 90.33% | 85.30% | 92.62% |
| has_barrier=False | 99 | 1881 | 92.34% | 67.20% | 77.09% | 79.96% | 88.25% | 78.04% | 92.29% |
| has_barrier=True | 51 | 969 | 91.02% | 30.44% | 34.67% | 80.80% | 89.16% | 80.60% | 90.61% |
| has_controlled_or_entangling=False | 47 | 893 | 92.39% | 60.47% | 63.05% | 72.12% | 87.01% | 83.20% | 92.05% |
| has_controlled_or_entangling=True | 103 | 1957 | 91.67% | 52.07% | 62.49% | 83.96% | 89.27% | 76.95% | 91.57% |
| has_rotation=False | 132 | 2508 | 92.74% | 56.30% | 62.84% | 81.30% | 88.96% | 81.22% | 92.54% |
| has_rotation=True | 18 | 342 | 85.67% | 42.98% | 61.40% | 72.51% | 85.67% | 61.99% | 85.67% |

## Prompt-Derived Circuit Families
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pauli_measurement | 98 | 1862 | 92.21% | 52.63% | 55.59% | 82.17% | 89.74% | 84.21% | 91.94% |
| generic_or_low_level | 27 | 513 | 94.15% | 70.57% | 81.87% | 82.26% | 94.15% | 81.09% | 94.15% |
| bell_or_superdense | 25 | 475 | 94.74% | 53.26% | 62.53% | 87.37% | 86.95% | 78.32% | 94.74% |
| oracle_logic | 13 | 247 | 90.69% | 48.99% | 51.42% | 79.35% | 89.88% | 80.97% | 90.28% |
| arithmetic_toffoli | 10 | 190 | 85.79% | 19.47% | 42.63% | 68.95% | 85.26% | 57.37% | 85.79% |
| deutsch_jozsa | 8 | 152 | 90.13% | 27.63% | 31.58% | 86.18% | 90.13% | 75.66% | 89.47% |
| deep_mixed_rotation | 5 | 95 | 78.95% | 15.79% | 49.47% | 52.63% | 78.95% | 29.47% | 78.95% |
| ghz | 5 | 95 | 100.00% | 71.58% | 73.68% | 91.58% | 100.00% | 97.89% | 100.00% |
| bernstein_vazirani | 4 | 76 | 80.26% | 26.32% | 28.95% | 30.26% | 47.37% | 50.00% | 80.26% |
| teleportation | 4 | 76 | 81.58% | 44.74% | 46.05% | 76.32% | 81.58% | 77.63% | 81.58% |
| error_correction | 3 | 57 | 82.46% | 3.51% | 75.44% | 78.95% | 75.44% | 7.02% | 82.46% |
| fourier_qft_phase | 3 | 57 | 82.46% | 57.89% | 57.89% | 73.68% | 82.46% | 80.70% | 80.70% |
| vqc_ansatz | 2 | 38 | 71.05% | 60.53% | 71.05% | 71.05% | 71.05% | 60.53% | 71.05% |

Singleton family labels are retained in the JSON artifact but omitted from this table.

## Correlation With Per-Prompt Structural Rate

| descriptor | Pearson r |
| --- | ---: |
| `num_qubits` | -0.045 |
| `num_clbits` | -0.251 |
| `gate_count` | -0.193 |
| `gate_type_count` | -0.418 |
| `gate_entropy` | -0.434 |

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
