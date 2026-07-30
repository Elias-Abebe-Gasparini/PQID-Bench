# PQID-Bench Item Difficulty And Failure Matrix

- prompts: `154`
- models: `21`
- prompt-model evaluations: `3234`
- structural matrix CSV: `artifacts\analysis_154\pqid_bench_model_by_prompt_structural_matrix.csv`

## Conditional Fidelity

| metric | value |
| --- | ---: |
| execution success | 91.22% |
| structural match | 52.66% |
| structural match given execution, P(M=1 given E=1) | 57.73% |
| runnable but structurally wrong | 38.56% |
| runnable wrong among executable outputs | 42.27% |
| QASM3-exportable but structurally wrong | 38.37% |

## Primary Failure Taxonomy

| primary outcome/failure | count | share |
| --- | ---: | ---: |
| `structural_match` | 1703 | 52.66% |
| `gate_types_mismatch` | 996 | 30.80% |
| `num_clbits_mismatch` | 250 | 7.73% |
| `execution_failure:SyntaxError` | 82 | 2.54% |
| `execution_failure:AttributeError` | 76 | 2.35% |
| `execution_failure:ImportError` | 51 | 1.58% |
| `empty_generation` | 27 | 0.83% |
| `execution_failure:CircuitError` | 14 | 0.43% |
| `no_circuit_found` | 13 | 0.40% |
| `execution_failure:NameError` | 9 | 0.28% |
| `execution_failure:TypeError` | 7 | 0.22% |
| `execution_failure:IndentationError` | 3 | 0.09% |
| `num_qubits_mismatch` | 1 | 0.03% |
| `execution_failure:QiskitError` | 1 | 0.03% |
| `execution_failure:ModuleNotFoundError` | 1 | 0.03% |

## Component Mismatches Among Nonmatches

| component | all nonmatches | executed nonmatches |
| --- | ---: | ---: |
| `gate_types_match` failed | 1280 | 996 |
| `num_clbits_match` failed | 726 | 442 |
| `num_qubits_match` failed | 389 | 105 |
| `gate_count_match` failed | 716 | 432 |

## Model Tiers
| group | n | execution | structural | M given E | runnable wrong | gate types | gate count | qubits | clbits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| frontier | 1540 | 95.78% | 59.22% | 61.83% | 36.56% | 66.30% | 84.55% | 92.08% | 83.38% |
| low_experimental | 462 | 73.81% | 38.31% | 51.91% | 35.50% | 43.94% | 59.52% | 71.00% | 61.26% |
| strong_open_code | 1232 | 92.05% | 49.84% | 54.14% | 42.21% | 59.25% | 76.38% | 89.20% | 76.38% |

## Model-Level Conditional Fidelity
| group | n | execution | structural | M given E | runnable wrong | gate types | gate count | qubits | clbits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-sol | 154 | 99.35% | 62.99% | 63.40% | 36.36% | 70.78% | 88.96% | 95.45% | 87.01% |
| gpt-5.5 | 154 | 97.40% | 60.39% | 62.00% | 37.01% | 68.18% | 86.36% | 92.86% | 83.77% |
| gpt-5.4-mini | 154 | 98.05% | 60.39% | 61.59% | 37.66% | 68.18% | 86.36% | 95.45% | 86.36% |
| claude-fable-5 | 154 | 98.05% | 62.99% | 64.24% | 35.06% | 70.13% | 89.61% | 94.16% | 86.36% |
| claude-sonnet-4-6 | 154 | 99.35% | 59.09% | 59.48% | 40.26% | 66.23% | 84.42% | 95.45% | 85.06% |
| claude-opus-4-8 | 154 | 100.00% | 59.74% | 59.74% | 40.26% | 67.53% | 86.36% | 96.75% | 85.71% |
| gemini-2.5-pro | 154 | 88.31% | 53.90% | 61.03% | 34.42% | 60.39% | 78.57% | 84.42% | 75.97% |
| gemini-3.1-pro-preview | 154 | 96.75% | 61.04% | 63.09% | 35.71% | 67.53% | 86.36% | 92.21% | 85.06% |
| deepseek-v4-pro | 154 | 91.56% | 59.09% | 64.54% | 32.47% | 64.94% | 81.82% | 88.31% | 80.52% |
| deepseek-v4-flash | 154 | 88.96% | 52.60% | 59.12% | 36.36% | 59.09% | 76.62% | 85.71% | 77.92% |
| mistral-ai/codestral-2501 | 154 | 93.51% | 55.84% | 59.72% | 37.66% | 63.64% | 82.47% | 90.91% | 81.17% |
| qwen/qwen3-coder-next | 154 | 85.71% | 50.65% | 59.09% | 35.06% | 58.44% | 74.03% | 83.77% | 74.68% |
| meta/llama-4-maverick-17b-128e-instruct-fp8 | 154 | 94.16% | 48.70% | 51.72% | 45.45% | 62.34% | 81.82% | 90.91% | 74.03% |
| llama-3.3-70b-versatile | 154 | 93.51% | 46.10% | 49.31% | 47.40% | 61.04% | 75.32% | 89.61% | 71.43% |
| openai/gpt-oss-120b | 154 | 96.75% | 53.25% | 55.03% | 43.51% | 59.74% | 79.87% | 94.16% | 84.42% |
| openai/gpt-oss-20b | 154 | 92.86% | 50.65% | 54.55% | 42.21% | 59.74% | 78.57% | 90.91% | 80.52% |
| mistralai/mistral-small-3.2-24b-instruct | 154 | 90.26% | 48.70% | 53.96% | 41.56% | 57.79% | 74.68% | 87.66% | 72.73% |
| qiskit/mistral-small-3.2-24b-qiskit | 154 | 89.61% | 44.81% | 50.00% | 44.81% | 51.30% | 64.29% | 85.71% | 72.08% |
| qwen/qwen3-32b | 154 | 57.79% | 35.06% | 60.67% | 22.73% | 39.61% | 53.25% | 57.14% | 46.10% |
| meta-llama/llama-4-scout-17b-16e-instruct | 154 | 82.47% | 44.81% | 54.33% | 37.66% | 49.35% | 64.94% | 78.57% | 72.08% |
| llama-3.1-8b-instant | 154 | 81.17% | 35.06% | 43.20% | 46.10% | 42.86% | 60.39% | 77.27% | 65.58% |

## Item Difficulty Buckets

| bucket | prompts |
| --- | ---: |
| `universal_easy` | 16 |
| `universal_hard` | 36 |
| `frontier_only` | 4 |
| `non_frontier_only` | 10 |
| `mixed_disagreement` | 102 |

## Hardest Items

| prompt | solved / 21 | difficulty | q | c | gates | gate types | families | instruction excerpt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0106` | 0 | 1.000 | 3 | 3 | 25 | 15 | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep, mixed gate pattern that includes Fredkin, Toffoli, CZ, SWAP, RZZ, RXX, and  |
| `pqid_bench_external_gen_0142` | 0 | 1.000 | 3 | 3 | 25 | 14 | arithmetic_toffoli, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep mix of swap-family and controlled operations, including at least one cswap,  |
| `pqid_bench_external_gen_0060` | 0 | 1.000 | 3 | 3 | 25 | 12 | pauli_measurement, deep_mixed_rotation | Create a 3-qubit Qiskit circuit with a deep gate sequence that mixes single-qubit phase/Pauli operations with entangling |
| `pqid_bench_external_gen_0136` | 0 | 1.000 | 3 | 3 | 19 | 6 | fourier_qft_phase, pauli_measurement | Build a 3-qubit Qiskit circuit that prepares /101>, applies a 3-qubit QFT, inserts a barrier, then applies the matching  |
| `pqid_bench_external_gen_0091` | 0 | 1.000 | 20 | 20 | 134 | 5 | pauli_measurement | Create a Qiskit circuit with 20 qubits and 20 classical bits that applies the given sequence of rx, ry, rz, and cx opera |
| `pqid_bench_external_gen_0046` | 0 | 1.000 | 5 | 4 | 15 | 5 | deutsch_jozsa, oracle_logic, pauli_measurement | Create a Qiskit circuit for a 4-input balanced Deutsch–Jozsa oracle that uses 5 qubits total: prepare the ancilla in /1> |
| `pqid_bench_external_gen_0022` | 0 | 1.000 | 3 | 3 | 13 | 5 | error_correction, arithmetic_toffoli, pauli_measurement | Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2 with two C |
| `pqid_bench_external_gen_0050` | 0 | 1.000 | 4 | 4 | 12 | 5 | arithmetic_toffoli, pauli_measurement | Create a 4-qubit Qiskit circuit that starts with an X on qubit 0, applies a barrier, runs CX(0,1), CX(0,2), CCX(2,1,0),  |
| `pqid_bench_external_gen_0036` | 0 | 1.000 | 4 | 3 | 10 | 5 | deutsch_jozsa, oracle_logic, pauli_measurement | Create a compact Qiskit circuit for a 4-qubit Deutsch–Jozsa-style setup: initialize the last qubit in /1>, apply Hadamar |
| `pqid_bench_external_gen_0069` | 0 | 1.000 | 3 | 3 | 9 | 5 | pauli_measurement | Create a Qiskit circuit on 3 qubits that applies H on qubit 0, then a controlled-S from qubit 1 to 0, a controlled-T fro |

## Easiest Items

| prompt | solved / 21 | difficulty | q | c | gates | gate types | families | instruction excerpt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `pqid_bench_external_gen_0059` | 21 | 0.000 | 1 | 1 | 2 | 2 | pauli_measurement | Create a minimal 1-qubit quantum circuit that applies a Z gate to qubit 0 and then measures it into a 1-bit classical re |
| `pqid_bench_external_gen_0037` | 21 | 0.000 | 2 | 2 | 3 | 2 | pauli_measurement | Create a small 2-qubit Qiskit circuit that applies a CNOT with qubit 0 as control and qubit 1 as target, then measures b |
| `pqid_bench_external_gen_0019` | 21 | 0.000 | 2 | 2 | 4 | 3 | bell_or_superdense, pauli_measurement | Create a 2-qubit Bell-state circuit in Qiskit: apply a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit 1, and mea |
| `pqid_bench_external_gen_0055` | 21 | 0.000 | 2 | 2 | 4 | 3 | bell_or_superdense, pauli_measurement | Create a small Qiskit circuit that prepares a Bell pair on two qubits with a Hadamard on qubit 0, a CNOT from qubit 0 to |
| `pqid_bench_external_gen_0003` | 21 | 0.000 | 3 | 3 | 5 | 2 | pauli_measurement | Create a 3-qubit, 3-classical-bit Qiskit circuit where qubit 0 gets two consecutive Hadamard gates and then all three qu |
| `pqid_bench_external_gen_0013` | 21 | 0.000 | 2 | 2 | 5 | 2 | pauli_measurement | Create a 2-qubit, 2-classical-bit Qiskit circuit that applies a Hadamard to qubit 0, applies two consecutive Hadamards t |
| `pqid_bench_external_gen_0014` | 21 | 0.000 | 2 | 2 | 5 | 3 | bell_or_superdense, pauli_measurement | Create a 2-qubit Qiskit circuit with 2 classical bits that prepares a Bell pair, then applies a Hadamard to qubit 1 so i |
| `pqid_bench_external_gen_0056` | 21 | 0.000 | 2 | 2 | 5 | 4 | bell_or_superdense, pauli_measurement | Create a 2-qubit quantum circuit that makes a Bell pair with an H on qubit 0 and a CNOT from qubit 0 to qubit 1, then ap |
| `pqid_bench_external_gen_0101` | 21 | 0.000 | 2 | 2 | 5 | 3 | pauli_measurement | Create a small 2-qubit Qiskit circuit that applies a Hadamard to qubit 0, then a CNOT from 0 to 1 followed by another CN |
| `pqid_bench_external_gen_0008` | 21 | 0.000 | 3 | 3 | 6 | 4 | ghz | Create a 3-qubit, 3-classical-bit Qiskit circuit that prepares a GHZ state by applying a Hadamard to qubit 0, entangling |

## Tier-Feature Interactions

| feature | value | tier | n | structural | M given E | runnable wrong |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `high_gate_diversity` | `False` | `frontier` | 1270 | 67.09% | 69.44% | 29.53% |
| `high_gate_diversity` | `True` | `frontier` | 270 | 22.22% | 24.19% | 69.63% |
| `high_gate_diversity` | `False` | `strong_open_code` | 1016 | 56.79% | 61.06% | 36.22% |
| `high_gate_diversity` | `True` | `strong_open_code` | 216 | 17.13% | 19.58% | 70.37% |
| `high_gate_diversity` | `False` | `low_experimental` | 381 | 43.57% | 56.66% | 33.33% |
| `high_gate_diversity` | `True` | `low_experimental` | 81 | 13.58% | 22.92% | 45.68% |
| `has_barrier` | `False` | `frontier` | 1010 | 72.97% | 76.29% | 22.67% |
| `has_barrier` | `True` | `frontier` | 530 | 33.02% | 34.38% | 63.02% |
| `has_barrier` | `False` | `strong_open_code` | 808 | 62.00% | 66.98% | 30.57% |
| `has_barrier` | `True` | `strong_open_code` | 424 | 26.65% | 29.27% | 64.39% |
| `has_barrier` | `False` | `low_experimental` | 303 | 47.52% | 63.72% | 27.06% |
| `has_barrier` | `True` | `low_experimental` | 159 | 20.75% | 28.70% | 51.57% |
| `has_controlled_or_entangling` | `False` | `frontier` | 480 | 65.62% | 67.02% | 32.29% |
| `has_controlled_or_entangling` | `True` | `frontier` | 1060 | 56.32% | 59.40% | 38.49% |
| `has_controlled_or_entangling` | `False` | `strong_open_code` | 384 | 57.55% | 62.43% | 34.64% |
| `has_controlled_or_entangling` | `True` | `strong_open_code` | 848 | 46.34% | 50.38% | 45.64% |
| `has_controlled_or_entangling` | `False` | `low_experimental` | 144 | 40.28% | 54.72% | 33.33% |
| `has_controlled_or_entangling` | `True` | `low_experimental` | 318 | 37.42% | 50.64% | 36.48% |
| `has_rotation` | `False` | `frontier` | 1340 | 61.19% | 63.47% | 35.22% |
| `has_rotation` | `True` | `frontier` | 200 | 46.00% | 50.27% | 45.50% |
| `has_rotation` | `False` | `strong_open_code` | 1072 | 52.80% | 56.15% | 41.23% |
| `has_rotation` | `True` | `strong_open_code` | 160 | 30.00% | 38.10% | 48.75% |
| `has_rotation` | `False` | `low_experimental` | 402 | 40.05% | 51.94% | 37.06% |
| `has_rotation` | `True` | `low_experimental` | 60 | 26.67% | 51.61% | 25.00% |

## Interpretation

The matrix confirms that PQID-Bench is not only separating executable from non-executable outputs. Among executable outputs, only about three fifths are structurally correct, so a large share of model behavior is runnable but scientifically wrong. The primary failure taxonomy shows that gate-type mismatch is the dominant structural failure after execution succeeds, followed by classical-bit, qubit, and gate-count mismatches. Item difficulty is highly concentrated: several prompts are solved by all models, while several protocol-like or heterogeneous prompts are solved by none.
