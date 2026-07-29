# PQID-Bench Retrieval-Copy Generation Baseline Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- split policy: deterministic 80/10/10 split by source-file group, stratified by majority clean-slice label
- group overlap: train/validation `0`, train/test `0`, validation/test `0`
- qiskit available: `True`; version: `2.1.1`

## Clean Pool

| slice | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |

## Split Summary

| split | rows | groups | strict_n8 | extended_n8 |
| --- | ---: | ---: | ---: | ---: |
| `train` | 598 | 470 | 342 | 256 |
| `validation` | 66 | 59 | 37 | 29 |
| `test` | 70 | 59 | 36 | 34 |

## Generation Baselines On Held-Out Test Instructions

Each non-oracle baseline generates code by copying one training example. The copied code is executed with the copied example's source metadata context, then compared against the held-out target metadata. The oracle row executes the held-out target code itself and is included only to calibrate the evaluator.

| baseline | test rows | exact code | execution | circuit found | structural match | gate types | gate count | qubits | QASM3 export |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `majority_train_code_copy` | 70 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| `bm25_code_metadata_copy` | 70 | 0.00% | 74.29% | 74.29% | 10.00% | 10.00% | 20.00% | 41.43% | 72.86% |
| `word_tfidf_code_metadata_copy` | 70 | 0.00% | 95.71% | 95.71% | 2.86% | 2.86% | 11.43% | 51.43% | 95.71% |
| `word_tfidf_train_instruction_copy` | 70 | 0.00% | 90.00% | 90.00% | 24.29% | 25.71% | 37.14% | 57.14% | 90.00% |
| `target_code_oracle` | 70 | 100.00% | 90.00% | 90.00% | 90.00% | 90.00% | 90.00% | 90.00% | 90.00% |

## Best Non-Oracle Baseline By Slice

Selected baseline: `word_tfidf_train_instruction_copy`.

| slice | rows | structural match | gate types | gate count | qubits | execution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 36 | 22.22% | 25.00% | 30.56% | 47.22% | 86.11% |
| `extended_n8` | 34 | 26.47% | 26.47% | 44.12% | 67.65% | 94.12% |

## Best Non-Oracle Failure Taxonomy

| category | failures | share | strict_n8 | extended_n8 |
| --- | ---: | ---: | ---: | ---: |
| `width_mismatch` | 23 | 43.40% | 14 | 9 |
| `gate_type_mismatch` | 22 | 41.51% | 8 | 14 |
| `execution_failed` | 7 | 13.21% | 5 | 2 |
| `classical_width_mismatch` | 1 | 1.89% | 1 | 0 |

## Representative Best-Baseline Failures

### Failure 1

- slice: `strict_n8`; category: `classical_width_mismatch`
- query: Create a 3-qubit, 3-classical-bit Qiskit circuit that prepares a GHZ state by applying a Hadamard to qubit 0, entangling it with qubits 1 and 2 via CNOTs, then adding a barrier ...
- target file: `AE.py`
- copied file: `ghz_state.py` (`strict_n8`)
- checks: `{'num_qubits_match': True, 'num_clbits_match': False, 'gate_count_match': True, 'gate_types_match': True, 'all_match': False}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 6, 'gate_types': {'measure': 3, 'cx': 2, 'h': 1, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 6, 'gate_count': 6, 'gate_types': {'measure': 3, 'cx': 2, 'h': 1, 'barrier': 1}}`

### Failure 2

- slice: `extended_n8`; category: `execution_failed`
- query: Create a small Qiskit Simon-algorithm setup for n=3 that initializes a 6-qubit circuit with 3 classical bits, applies Hadamards to the first register, and inserts a barrier befo...
- target file: `source/0/main_595497.py`
- copied file: `source/0/simon_0c9154.py` (`extended_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 6, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'h': 3, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 6, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'h': 3, 'barrier': 1}}`

### Failure 3

- slice: `extended_n8`; category: `execution_failed`
- query: Create a Qiskit circuit for a 3-qubit Bernstein–Vazirani setup where the last qubit is the oracle target: initialize that qubit in |1>, apply Hadamards to all qubits, use CNOTs ...
- target file: `docs/guides/custom-backend.ipynb`
- copied file: `source/0/bernstein_vazirani_forstrings_4d15d5.py` (`extended_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 2, 'gate_count': 11, 'gate_types': {'h': 6, 'cx': 2, 'measure': 2, 'x': 1}}`
- copied metadata: `{'num_qubits': 4, 'num_clbits': 3, 'gate_count': 5, 'gate_types': {'h': 4, 'barrier': 2, 'x': 1}}`

### Failure 4

- slice: `strict_n8`; category: `execution_failed`
- query: Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2 with two CNOTs, apply Hadamards to all three qubits, insert a Z err...
- target file: `Quantum Error Correction/Phase Flip code.py`
- copied file: `error_correction/threebitQecc.py` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 13, 'gate_types': {'h': 6, 'cx': 4, 'z': 1, 'ccx': 1, 'measure': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 7, 'gate_types': {'cx': 4, 'h': 1, 'x': 1, 'measure': 1}}`

### Failure 5

- slice: `strict_n8`; category: `execution_failed`
- query: Create a Qiskit circuit for the encoding step of the three-qubit bit-flip code: put q[0] into superposition with an H gate, copy it to q[1] and q[2] with two CNOTs, and then pla...
- target file: `17.Bit-Flip-Error-Correction.py`
- copied file: `error-correction/phase_flip.py` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 4, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'cx': 2, 'h': 1, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'cx': 2, 'h': 1}}`

### Failure 6

- slice: `strict_n8`; category: `execution_failed`
- query: Create a 2-qubit Qiskit circuit that applies a Hadamard to both qubits, then performs an RZ rotation of 3.14/4 on qubit 1.
- target file: `notebooks/v1/ch-states/old-states-many-qubits.ipynb`
- copied file: `4. Operators/qiskit_gradient_framework.py` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 2, 'num_clbits': 0, 'gate_count': 3, 'gate_types': {'h': 2, 'rz': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 0, 'gate_count': 5, 'gate_types': {'h': 3, 'rz': 1, 'rx': 1}}`

### Failure 7

- slice: `strict_n8`; category: `execution_failed`
- query: Create a Qiskit circuit with 14 qubits and 7 classical bits that prepares qubits 0 through 6 in uniform superposition with Hadamards, and initializes qubit 13 as an ancilla in t...
- target file: `grover_7qubit.py`
- copied file: `quantum_circuit_generator.py` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 14, 'num_clbits': 7, 'gate_count': 9, 'gate_types': {'h': 8, 'x': 1}}`
- copied metadata: `{'num_qubits': 4, 'num_clbits': 3, 'gate_count': 2, 'gate_types': {'x': 1, 'h': 1}}`

### Failure 8

- slice: `strict_n8`; category: `execution_failed`
- query: Create a 3-qubit Qiskit circuit with a 3-bit classical register that initializes the search space for Grover’s algorithm by applying a Hadamard gate to every qubit and nothing e...
- target file: `grover_sim_2.py`
- copied file: `src/theorem12.py` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'h': 3}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 0, 'gate_count': 3, 'gate_types': {'h': 3}}`

