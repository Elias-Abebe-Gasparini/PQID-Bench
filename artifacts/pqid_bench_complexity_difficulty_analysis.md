# PQID-Bench Complexity-Difficulty Analysis

- prompts: `70`
- completed models: `15`
- prompt-model evaluations: `1050`
- pooled execution success: `87.14%`
- pooled structural match: `53.71%`

## Width
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 qubits | 27 | 405 | 92.10% | 63.21% | 63.95% | 87.41% | 92.10% | 91.36% | 92.10% |
| 3 qubits | 24 | 360 | 82.50% | 45.00% | 55.28% | 70.00% | 74.72% | 64.17% | 82.50% |
| 4 qubits | 11 | 165 | 82.42% | 39.39% | 47.27% | 73.33% | 77.58% | 64.85% | 82.42% |
| 5-8 qubits | 6 | 90 | 88.89% | 71.11% | 73.33% | 86.67% | 87.78% | 85.56% | 88.89% |
| 9+ qubits | 2 | 30 | 96.67% | 56.67% | 56.67% | 96.67% | 96.67% | 96.67% | 96.67% |

## Gate Count
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2-4 gates | 30 | 450 | 86.67% | 53.11% | 62.00% | 80.00% | 82.22% | 76.67% | 86.67% |
| 5-8 gates | 26 | 390 | 90.51% | 66.15% | 66.67% | 83.59% | 86.15% | 84.87% | 90.51% |
| 9-12 gates | 8 | 120 | 89.17% | 45.83% | 47.50% | 84.17% | 89.17% | 77.50% | 89.17% |
| 13-20 gates | 5 | 75 | 73.33% | 16.00% | 30.67% | 62.67% | 73.33% | 56.00% | 73.33% |
| 21+ gates | 1 | 15 | 66.67% | 0.00% | 0.00% | 0.00% | 66.67% | 20.00% | 66.67% |

## Gate-Type Diversity
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1-2 gate types | 19 | 285 | 90.53% | 74.39% | 84.21% | 85.26% | 85.61% | 78.95% | 90.53% |
| 3-4 gate types | 40 | 600 | 86.67% | 58.00% | 60.50% | 78.50% | 82.83% | 80.50% | 86.67% |
| 5+ gate types | 11 | 165 | 83.03% | 2.42% | 9.70% | 72.73% | 83.03% | 64.24% | 83.03% |

## Classical Bits
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 clbits | 10 | 150 | 80.67% | 67.33% | 72.67% | 73.33% | 80.67% | 74.00% | 80.67% |
| 1-2 clbits | 27 | 405 | 92.35% | 60.00% | 60.25% | 86.17% | 92.35% | 92.10% | 92.35% |
| 3 clbits | 26 | 390 | 82.82% | 44.36% | 55.90% | 72.05% | 73.33% | 60.26% | 82.82% |
| 4+ clbits | 7 | 105 | 92.38% | 44.76% | 45.71% | 89.52% | 92.38% | 90.48% | 92.38% |

## Feature Presence
| feature group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| has_measure=False | 24 | 360 | 82.78% | 57.22% | 68.33% | 68.61% | 76.67% | 67.22% | 82.78% |
| has_measure=True | 46 | 690 | 89.42% | 51.88% | 54.06% | 85.07% | 87.25% | 82.90% | 89.42% |
| has_barrier=False | 43 | 645 | 87.13% | 70.54% | 76.90% | 77.98% | 82.79% | 76.28% | 87.13% |
| has_barrier=True | 27 | 405 | 87.16% | 26.91% | 30.37% | 81.73% | 84.94% | 79.51% | 87.16% |
| has_controlled_or_entangling=False | 21 | 315 | 89.84% | 67.62% | 68.25% | 77.78% | 84.13% | 83.17% | 89.84% |
| has_controlled_or_entangling=True | 49 | 735 | 85.99% | 47.76% | 54.97% | 80.14% | 83.40% | 75.10% | 85.99% |
| has_rotation=False | 64 | 960 | 88.02% | 55.00% | 60.42% | 81.35% | 84.17% | 78.65% | 88.02% |
| has_rotation=True | 6 | 90 | 77.78% | 40.00% | 43.33% | 58.89% | 77.78% | 65.56% | 77.78% |

## Prompt-Derived Circuit Families
| group | prompts | evaluations | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pauli_measurement | 48 | 720 | 88.33% | 50.56% | 52.64% | 82.36% | 86.25% | 81.11% | 88.33% |
| bell_or_superdense | 13 | 195 | 89.23% | 48.21% | 53.85% | 88.21% | 82.56% | 82.56% | 89.23% |
| generic_or_low_level | 12 | 180 | 88.89% | 71.67% | 80.56% | 80.56% | 88.89% | 79.44% | 88.89% |
| oracle_logic | 7 | 105 | 86.67% | 55.24% | 56.19% | 78.10% | 85.71% | 75.24% | 86.67% |
| arithmetic_toffoli | 5 | 75 | 82.67% | 18.67% | 33.33% | 64.00% | 82.67% | 64.00% | 82.67% |
| ghz | 4 | 60 | 93.33% | 58.33% | 61.67% | 81.67% | 93.33% | 90.00% | 93.33% |
| bernstein_vazirani | 2 | 30 | 73.33% | 46.67% | 46.67% | 46.67% | 56.67% | 56.67% | 73.33% |
| deep_mixed_rotation | 2 | 30 | 60.00% | 0.00% | 0.00% | 3.33% | 60.00% | 33.33% | 60.00% |
| deutsch_jozsa | 2 | 30 | 76.67% | 0.00% | 3.33% | 76.67% | 76.67% | 36.67% | 76.67% |
| error_correction | 2 | 30 | 76.67% | 6.67% | 73.33% | 73.33% | 66.67% | 6.67% | 76.67% |

Singleton family labels are retained in the JSON artifact but omitted from this table.

## Correlation With Per-Prompt Structural Rate

| descriptor | Pearson r |
| --- | ---: |
| `num_qubits` | 0.040 |
| `num_clbits` | -0.145 |
| `gate_count` | -0.270 |
| `gate_type_count` | -0.527 |
| `gate_entropy` | -0.559 |

## Hardest Prompts By Mean Structural Match

| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0060` | `extended_n8` | 3 | 3 | 25 | 12 | 0.00% | pauli_measurement, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep gate sequence that mixes single-qubit phase/Pauli operations with  |
| `pqid_bench_external_gen_0040` | `extended_n8` | 3 | 0 | 18 | 4 | 0.00% | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit that implements the shown CCX-style decomposition using only single-qubit rota |
| `pqid_bench_external_gen_0046` | `extended_n8` | 5 | 4 | 15 | 5 | 0.00% | deutsch_jozsa, oracle_logic, pauli_measurement | Create a Qiskit circuit for a 4-input balanced Deutsch–Jozsa oracle that uses 5 qubits total: prepare the anci |
| `pqid_bench_external_gen_0022` | `strict_n8` | 3 | 3 | 13 | 5 | 0.00% | error_correction, arithmetic_toffoli, pauli_measurement | Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2  |
| `pqid_bench_external_gen_0050` | `extended_n8` | 4 | 4 | 12 | 5 | 0.00% | arithmetic_toffoli, pauli_measurement | Create a 4-qubit Qiskit circuit that starts with an X on qubit 0, applies a barrier, runs CX(0,1), CX(0,2), CC |
| `pqid_bench_external_gen_0036` | `extended_n8` | 4 | 3 | 10 | 5 | 0.00% | deutsch_jozsa, oracle_logic, pauli_measurement | Create a compact Qiskit circuit for a 4-qubit Deutsch–Jozsa-style setup: initialize the last qubit in /1>, app |
| `pqid_bench_external_gen_0002` | `strict_n8` | 3 | 3 | 10 | 6 | 0.00% | teleportation, bell_or_superdense, pauli_measurement | Build a 3-qubit, 3-classical-bit quantum teleportation circuit that teleports the state /1⟩ from qubit 0 to qu |
| `pqid_bench_external_gen_0069` | `strict_n8` | 3 | 3 | 9 | 5 | 0.00% | pauli_measurement | Create a Qiskit circuit on 3 qubits that applies H on qubit 0, then a controlled-S from qubit 1 to 0, a contro |
| `pqid_bench_external_gen_0052` | `extended_n8` | 4 | 2 | 7 | 5 | 0.00% | arithmetic_toffoli, pauli_measurement | Create a compact Qiskit circuit for a 1-bit quantum half-adder that uses 4 qubits and 2 classical bits, initia |
| `pqid_bench_external_gen_0038` | `extended_n8` | 2 | 1 | 6 | 5 | 0.00% | pauli_measurement | Create a Qiskit circuit with 2 qubits and 1 classical bit that applies X on qubit 1, then barriers around a la |

## Easiest Prompts By Mean Structural Match

| prompt | label | q | c | gates | gate types | structural | families | instruction excerpt |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0055` | `extended_n8` | 2 | 2 | 4 | 3 | 100.00% | bell_or_superdense, pauli_measurement | Create a small Qiskit circuit that prepares a Bell pair on two qubits with a Hadamard on qubit 0, a CNOT from  |
| `pqid_bench_external_gen_0013` | `strict_n8` | 2 | 2 | 5 | 2 | 100.00% | pauli_measurement | Create a 2-qubit, 2-classical-bit Qiskit circuit that applies a Hadamard to qubit 0, applies two consecutive H |
| `pqid_bench_external_gen_0003` | `strict_n8` | 3 | 3 | 5 | 2 | 100.00% | pauli_measurement | Create a 3-qubit, 3-classical-bit Qiskit circuit where qubit 0 gets two consecutive Hadamard gates and then al |
| `pqid_bench_external_gen_0008` | `strict_n8` | 3 | 3 | 6 | 4 | 100.00% | ghz | Create a 3-qubit, 3-classical-bit Qiskit circuit that prepares a GHZ state by applying a Hadamard to qubit 0,  |
| `pqid_bench_external_gen_0006` | `strict_n8` | 14 | 7 | 9 | 2 | 100.00% | generic_or_low_level | Create a Qiskit circuit with 14 qubits and 7 classical bits that prepares qubits 0 through 6 in uniform superp |
| `pqid_bench_external_gen_0029` | `strict_n8` | 4 | 4 | 11 | 3 | 100.00% | pauli_measurement | Create a 4-qubit, 4-classical-bit Qiskit circuit that puts every qubit into superposition with Hadamards, then |
| `pqid_bench_external_gen_0059` | `extended_n8` | 1 | 1 | 2 | 2 | 93.33% | pauli_measurement | Create a minimal 1-qubit quantum circuit that applies a Z gate to qubit 0 and then measures it into a 1-bit cl |
| `pqid_bench_external_gen_0019` | `strict_n8` | 2 | 2 | 4 | 3 | 93.33% | bell_or_superdense, pauli_measurement | Create a 2-qubit Bell-state circuit in Qiskit: apply a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit  |
| `pqid_bench_external_gen_0058` | `extended_n8` | 2 | 2 | 4 | 3 | 93.33% | bell_or_superdense, pauli_measurement | Create a small 2-qubit circuit that prepares a Bell pair with a Hadamard on qubit 0, a CNOT from qubit 0 to qu |
| `pqid_bench_external_gen_0057` | `extended_n8` | 3 | 3 | 4 | 2 | 93.33% | arithmetic_toffoli, pauli_measurement | Create a small Qiskit circuit with three qubits and three classical bits that applies a Toffoli gate using the |

## Interpretation

The clearest complexity signal is gate-type diversity: targets with five or more gate types have substantially lower structural-match rates than targets with one or two gate types. Width and gate count are not monotone in this split because many wider circuits are regular Hadamard/CX templates, while some short circuits contain classical-control or gate-order traps. The benchmark therefore supports a refined version of the complexity hypothesis: structural difficulty increases most clearly with heterogeneity and semantic specificity, not with raw qubit count alone.
