# PQID-Bench Item Difficulty And Failure Matrix

- prompts: `70`
- models: `15`
- prompt-model evaluations: `1050`
- structural matrix CSV: `artifacts\pqid_bench_model_by_prompt_structural_matrix.csv`

## Conditional Fidelity

| metric | value |
| --- | ---: |
| execution success | 87.71% |
| structural match | 53.71% |
| structural match given execution, P(M=1 given E=1) | 61.24% |
| runnable but structurally wrong | 34.00% |
| runnable wrong among executable outputs | 38.76% |
| QASM3-exportable but structurally wrong | 33.43% |

## Primary Failure Taxonomy

| primary outcome/failure | count | share |
| --- | ---: | ---: |
| `structural_match` | 564 | 53.71% |
| `gate_types_mismatch` | 296 | 28.19% |
| `execution_failure:NameError` | 61 | 5.81% |
| `num_clbits_mismatch` | 55 | 5.24% |
| `execution_failure:SyntaxError` | 27 | 2.57% |
| `execution_failure:AttributeError` | 25 | 2.38% |
| `execution_failure:ImportError` | 9 | 0.86% |
| `no_circuit_found` | 6 | 0.57% |
| `execution_failure:CircuitError` | 5 | 0.48% |
| `execution_failure:TypeError` | 2 | 0.19% |

## Component Mismatches Among Nonmatches

| component | all nonmatches | executed nonmatches |
| --- | ---: | ---: |
| `gate_types_match` failed | 431 | 302 |
| `num_clbits_match` failed | 236 | 107 |
| `num_qubits_match` failed | 172 | 43 |
| `gate_count_match` failed | 216 | 87 |

## Model Tiers
| group | n | execution | structural | M given E | runnable wrong | gate types | gate count | qubits | clbits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| frontier | 560 | 95.54% | 61.61% | 64.49% | 33.93% | 66.79% | 89.29% | 90.36% | 85.00% |
| low_experimental | 210 | 60.95% | 33.33% | 54.69% | 27.62% | 35.71% | 51.43% | 59.05% | 54.29% |
| strong_open_code | 280 | 92.14% | 53.21% | 57.75% | 38.93% | 60.71% | 80.71% | 88.57% | 80.00% |

## Model-Level Conditional Fidelity
| group | n | execution | structural | M given E | runnable wrong | gate types | gate count | qubits | clbits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.5 | 70 | 98.57% | 62.86% | 63.77% | 35.71% | 70.00% | 94.29% | 92.86% | 85.71% |
| gpt-5.4-mini | 70 | 97.14% | 64.29% | 66.18% | 32.86% | 70.00% | 92.86% | 94.29% | 87.14% |
| claude-sonnet-4-6 | 70 | 92.86% | 61.43% | 66.15% | 31.43% | 65.71% | 88.57% | 88.57% | 84.29% |
| claude-opus-4-8 | 70 | 100.00% | 61.43% | 61.43% | 38.57% | 68.57% | 94.29% | 94.29% | 87.14% |
| gemini-2.5-pro | 70 | 92.86% | 62.86% | 67.69% | 30.00% | 64.29% | 82.86% | 85.71% | 85.71% |
| gemini-3.1-pro-preview | 70 | 97.14% | 62.86% | 64.71% | 34.29% | 68.57% | 92.86% | 91.43% | 87.14% |
| deepseek-v4-pro | 70 | 92.86% | 58.57% | 63.08% | 34.29% | 64.29% | 85.71% | 88.57% | 80.00% |
| deepseek-v4-flash | 70 | 92.86% | 58.57% | 63.08% | 34.29% | 62.86% | 82.86% | 87.14% | 82.86% |
| mistral-ai/codestral-2501 | 70 | 95.71% | 58.57% | 61.19% | 37.14% | 64.29% | 87.14% | 92.86% | 85.71% |
| llama-3.3-70b-versatile | 70 | 94.29% | 50.00% | 53.03% | 44.29% | 64.29% | 78.57% | 90.00% | 77.14% |
| openai/gpt-oss-120b | 70 | 94.29% | 52.86% | 56.06% | 41.43% | 57.14% | 78.57% | 90.00% | 81.43% |
| openai/gpt-oss-20b | 70 | 84.29% | 51.43% | 61.02% | 32.86% | 57.14% | 78.57% | 81.43% | 75.71% |
| qwen/qwen3-32b | 70 | 65.71% | 38.57% | 58.70% | 27.14% | 44.29% | 61.43% | 65.71% | 52.86% |
| meta-llama/llama-4-scout-17b-16e-instruct | 70 | 70.00% | 38.57% | 55.10% | 31.43% | 40.00% | 55.71% | 67.14% | 64.29% |
| llama-3.1-8b-instant | 70 | 47.14% | 22.86% | 48.48% | 24.29% | 22.86% | 37.14% | 44.29% | 45.71% |

## Item Difficulty Buckets

| bucket | prompts |
| --- | ---: |
| `universal_easy` | 6 |
| `universal_hard` | 18 |
| `frontier_only` | 2 |
| `non_frontier_only` | 1 |
| `mixed_disagreement` | 46 |

## Hardest Items

| prompt | solved / 15 | difficulty | q | c | gates | gate types | families | instruction excerpt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0060` | 0 | 1.000 | 3 | 3 | 25 | 12 | pauli_measurement, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep gate sequence that mixes single-qubit phase/Pauli operations with entangling |
| `pqid_bench_external_gen_0002` | 0 | 1.000 | 3 | 3 | 10 | 6 | teleportation, bell_or_superdense, pauli_measurement | Build a 3-qubit, 3-classical-bit quantum teleportation circuit that teleports the state /1⟩ from qubit 0 to qubit 2: ini |
| `pqid_bench_external_gen_0046` | 0 | 1.000 | 5 | 4 | 15 | 5 | deutsch_jozsa, oracle_logic, pauli_measurement | Create a Qiskit circuit for a 4-input balanced Deutsch–Jozsa oracle that uses 5 qubits total: prepare the ancilla in /1> |
| `pqid_bench_external_gen_0022` | 0 | 1.000 | 3 | 3 | 13 | 5 | error_correction, arithmetic_toffoli, pauli_measurement | Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2 with two C |
| `pqid_bench_external_gen_0050` | 0 | 1.000 | 4 | 4 | 12 | 5 | arithmetic_toffoli, pauli_measurement | Create a 4-qubit Qiskit circuit that starts with an X on qubit 0, applies a barrier, runs CX(0,1), CX(0,2), CCX(2,1,0),  |
| `pqid_bench_external_gen_0036` | 0 | 1.000 | 4 | 3 | 10 | 5 | deutsch_jozsa, oracle_logic, pauli_measurement | Create a compact Qiskit circuit for a 4-qubit Deutsch–Jozsa-style setup: initialize the last qubit in /1>, apply Hadamar |
| `pqid_bench_external_gen_0069` | 0 | 1.000 | 3 | 3 | 9 | 5 | pauli_measurement | Create a Qiskit circuit on 3 qubits that applies H on qubit 0, then a controlled-S from qubit 1 to 0, a controlled-T fro |
| `pqid_bench_external_gen_0052` | 0 | 1.000 | 4 | 2 | 7 | 5 | arithmetic_toffoli, pauli_measurement | Create a compact Qiskit circuit for a 1-bit quantum half-adder that uses 4 qubits and 2 classical bits, initializes both |
| `pqid_bench_external_gen_0038` | 0 | 1.000 | 2 | 1 | 6 | 5 | pauli_measurement | Create a Qiskit circuit with 2 qubits and 1 classical bit that applies X on qubit 1, then barriers around a layer of H o |
| `pqid_bench_external_gen_0040` | 0 | 1.000 | 3 | 0 | 18 | 4 | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit that implements the shown CCX-style decomposition using only single-qubit rotations, RXX |

## Easiest Items

| prompt | solved / 15 | difficulty | q | c | gates | gate types | families | instruction excerpt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0055` | 15 | 0.000 | 2 | 2 | 4 | 3 | bell_or_superdense, pauli_measurement | Create a small Qiskit circuit that prepares a Bell pair on two qubits with a Hadamard on qubit 0, a CNOT from qubit 0 to |
| `pqid_bench_external_gen_0003` | 15 | 0.000 | 3 | 3 | 5 | 2 | pauli_measurement | Create a 3-qubit, 3-classical-bit Qiskit circuit where qubit 0 gets two consecutive Hadamard gates and then all three qu |
| `pqid_bench_external_gen_0013` | 15 | 0.000 | 2 | 2 | 5 | 2 | pauli_measurement | Create a 2-qubit, 2-classical-bit Qiskit circuit that applies a Hadamard to qubit 0, applies two consecutive Hadamards t |
| `pqid_bench_external_gen_0008` | 15 | 0.000 | 3 | 3 | 6 | 4 | ghz | Create a 3-qubit, 3-classical-bit Qiskit circuit that prepares a GHZ state by applying a Hadamard to qubit 0, entangling |
| `pqid_bench_external_gen_0006` | 15 | 0.000 | 14 | 7 | 9 | 2 | generic_or_low_level | Create a Qiskit circuit with 14 qubits and 7 classical bits that prepares qubits 0 through 6 in uniform superposition wi |
| `pqid_bench_external_gen_0029` | 15 | 0.000 | 4 | 4 | 11 | 3 | pauli_measurement | Create a 4-qubit, 4-classical-bit Qiskit circuit that puts every qubit into superposition with Hadamards, then applies a |
| `pqid_bench_external_gen_0059` | 14 | 0.067 | 1 | 1 | 2 | 2 | pauli_measurement | Create a minimal 1-qubit quantum circuit that applies a Z gate to qubit 0 and then measures it into a 1-bit classical re |
| `pqid_bench_external_gen_0009` | 14 | 0.067 | 4 | 0 | 4 | 2 | pauli_measurement | Create a 4-qubit quantum circuit that applies Pauli-X to qubits 0, 1, and 3, and a Hadamard to qubit 2. |
| `pqid_bench_external_gen_0019` | 14 | 0.067 | 2 | 2 | 4 | 3 | bell_or_superdense, pauli_measurement | Create a 2-qubit Bell-state circuit in Qiskit: apply a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit 1, and mea |
| `pqid_bench_external_gen_0057` | 14 | 0.067 | 3 | 3 | 4 | 2 | arithmetic_toffoli, pauli_measurement | Create a small Qiskit circuit with three qubits and three classical bits that applies a Toffoli gate using the first two |

## Tier-Feature Interactions

| feature | value | tier | n | structural | M given E | runnable wrong |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `high_gate_diversity` | `False` | `frontier` | 472 | 72.67% | 75.38% | 23.73% |
| `high_gate_diversity` | `True` | `frontier` | 88 | 2.27% | 2.50% | 88.64% |
| `high_gate_diversity` | `False` | `strong_open_code` | 236 | 62.71% | 68.20% | 29.24% |
| `high_gate_diversity` | `True` | `strong_open_code` | 44 | 2.27% | 2.44% | 90.91% |
| `high_gate_diversity` | `False` | `low_experimental` | 177 | 38.98% | 63.30% | 22.60% |
| `high_gate_diversity` | `True` | `low_experimental` | 33 | 3.03% | 5.26% | 54.55% |
| `has_barrier` | `False` | `frontier` | 344 | 81.10% | 84.55% | 14.83% |
| `has_barrier` | `True` | `frontier` | 216 | 30.56% | 32.20% | 64.35% |
| `has_barrier` | `False` | `strong_open_code` | 172 | 69.19% | 75.32% | 22.67% |
| `has_barrier` | `True` | `strong_open_code` | 108 | 27.78% | 30.00% | 64.81% |
| `has_barrier` | `False` | `low_experimental` | 129 | 44.19% | 74.03% | 15.50% |
| `has_barrier` | `True` | `low_experimental` | 81 | 16.05% | 25.49% | 46.91% |
| `has_controlled_or_entangling` | `False` | `frontier` | 168 | 79.17% | 80.12% | 19.64% |
| `has_controlled_or_entangling` | `True` | `frontier` | 392 | 54.08% | 57.45% | 40.05% |
| `has_controlled_or_entangling` | `False` | `strong_open_code` | 84 | 64.29% | 70.13% | 27.38% |
| `has_controlled_or_entangling` | `True` | `strong_open_code` | 196 | 48.47% | 52.49% | 43.88% |
| `has_controlled_or_entangling` | `False` | `low_experimental` | 63 | 41.27% | 60.47% | 26.98% |
| `has_controlled_or_entangling` | `True` | `low_experimental` | 147 | 29.93% | 51.76% | 27.89% |
| `has_rotation` | `False` | `frontier` | 512 | 62.70% | 65.11% | 33.59% |
| `has_rotation` | `True` | `frontier` | 48 | 50.00% | 57.14% | 37.50% |
| `has_rotation` | `False` | `strong_open_code` | 256 | 54.69% | 59.57% | 37.11% |
| `has_rotation` | `True` | `strong_open_code` | 24 | 37.50% | 39.13% | 58.33% |
| `has_rotation` | `False` | `low_experimental` | 192 | 34.90% | 54.92% | 28.65% |
| `has_rotation` | `True` | `low_experimental` | 18 | 16.67% | 50.00% | 16.67% |

## Interpretation

The matrix confirms that PQID-Bench is not only separating executable from non-executable outputs. Among executable outputs, only about three fifths are structurally correct, so a large share of model behavior is runnable but scientifically wrong. The primary failure taxonomy shows that gate-type mismatch is the dominant structural failure after execution succeeds, followed by classical-bit, qubit, and gate-count mismatches. Item difficulty is highly concentrated: several prompts are solved by all models, while several protocol-like or heterogeneous prompts are solved by none.
