# PQID-Bench Retrieval-Copy Generation Baseline Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- split policy: frozen split manifest `artifacts/test_split_154/pqid_bench_split_154_manifest.json`
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
| `train` | 514 | 386 | 301 | 213 |
| `validation` | 66 | 59 | 37 | 29 |
| `test` | 154 | 143 | 77 | 77 |

## Generation Baselines On Held-Out Test Instructions

Each non-oracle baseline generates code by copying one training example. The copied code is executed with the copied example's source metadata context, then compared against the held-out target metadata. The oracle row executes the held-out target code itself and is included only to calibrate the evaluator.

| baseline | test rows | exact code | execution | circuit found | structural match | gate types | gate count | qubits | QASM3 export |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `majority_train_code_copy` | 154 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| `bm25_code_metadata_copy` | 154 | 0.00% | 75.32% | 75.32% | 5.84% | 5.84% | 14.29% | 31.82% | 75.32% |
| `word_tfidf_code_metadata_copy` | 154 | 0.00% | 94.81% | 94.81% | 1.30% | 1.30% | 18.83% | 40.91% | 94.81% |
| `word_tfidf_train_instruction_copy` | 154 | 0.00% | 91.56% | 91.56% | 15.58% | 17.53% | 37.66% | 54.55% | 91.56% |
| `target_code_oracle` | 154 | 100.00% | 91.56% | 91.56% | 91.56% | 91.56% | 91.56% | 91.56% | 90.91% |

## Best Non-Oracle Baseline By Slice

Selected baseline: `word_tfidf_train_instruction_copy`.

| slice | rows | structural match | gate types | gate count | qubits | execution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 77 | 15.58% | 19.48% | 35.06% | 51.95% | 89.61% |
| `extended_n8` | 77 | 15.58% | 15.58% | 40.26% | 57.14% | 93.51% |

## Best Non-Oracle Failure Taxonomy

| category | failures | share | strict_n8 | extended_n8 |
| --- | ---: | ---: | ---: | ---: |
| `gate_type_mismatch` | 58 | 44.62% | 26 | 32 |
| `width_mismatch` | 57 | 43.85% | 29 | 28 |
| `execution_failed` | 13 | 10.00% | 8 | 5 |
| `classical_width_mismatch` | 2 | 1.54% | 2 | 0 |

## Representative Best-Baseline Failures

### Failure 1

- slice: `strict_n8`; category: `classical_width_mismatch`
- query: Create a 2-qubit Qiskit circuit that prepares a Bell state by applying a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit 1, and finally measures both qubits.
- target file: `blockchainApp_local/backend/enhance_course_content.py`
- copied file: `deneme.py` (`strict_n8`)
- checks: `{'num_qubits_match': True, 'num_clbits_match': False, 'gate_count_match': True, 'gate_types_match': True, 'all_match': False}`
- target metadata: `{'num_qubits': 2, 'num_clbits': 4, 'gate_count': 4, 'gate_types': {'measure': 2, 'h': 1, 'cx': 1, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 2, 'num_clbits': 2, 'gate_count': 4, 'gate_types': {'measure': 2, 'h': 1, 'cx': 1, 'barrier': 1}}`

### Failure 2

- slice: `strict_n8`; category: `classical_width_mismatch`
- query: Create a 3-qubit, 3-classical-bit Qiskit circuit that prepares a GHZ state by applying a Hadamard to qubit 0, entangling it with qubits 1 and 2 via CNOTs, then adding a barrier ...
- target file: `AE.py`
- copied file: `ghz_state.py` (`strict_n8`)
- checks: `{'num_qubits_match': True, 'num_clbits_match': False, 'gate_count_match': True, 'gate_types_match': True, 'all_match': False}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 6, 'gate_types': {'measure': 3, 'cx': 2, 'h': 1, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 6, 'gate_count': 6, 'gate_types': {'measure': 3, 'cx': 2, 'h': 1, 'barrier': 1}}`

### Failure 3

- slice: `extended_n8`; category: `execution_failed`
- query: Create a small Qiskit Simon-algorithm setup for n=3 that initializes a 6-qubit circuit with 3 classical bits, applies Hadamards to the first register, and inserts a barrier befo...
- target file: `source/0/main_595497.py`
- copied file: `source/0/simon_0c9154.py` (`extended_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 6, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'h': 3, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 6, 'num_clbits': 3, 'gate_count': 3, 'gate_types': {'h': 3, 'barrier': 1}}`

### Failure 4

- slice: `extended_n8`; category: `execution_failed`
- query: Create a Qiskit circuit for a 3-qubit Bernstein–Vazirani setup where the last qubit is the oracle target: initialize that qubit in |1>, apply Hadamards to all qubits, use CNOTs ...
- target file: `docs/guides/custom-backend.ipynb`
- copied file: `source/0/bernstein_vazirani_forstrings_4d15d5.py` (`extended_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 2, 'gate_count': 11, 'gate_types': {'h': 6, 'cx': 2, 'measure': 2, 'x': 1}}`
- copied metadata: `{'num_qubits': 4, 'num_clbits': 3, 'gate_count': 5, 'gate_types': {'h': 4, 'barrier': 2, 'x': 1}}`

### Failure 5

- slice: `extended_n8`; category: `execution_failed`
- query: Create a small 3-qubit Qiskit circuit that prepares all qubits in the X basis with Hadamards, includes a barrier before readout, then applies Hadamards again and measures each q...
- target file: `source/0/t2_echo_bbbd4d.py`
- copied file: `community/terra/qis_intro/entanglement_testing.ipynb` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 6, 'gate_types': {'h': 3, 'measure': 3, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 6, 'gate_types': {'h': 3, 'measure': 3}}`

### Failure 6

- slice: `extended_n8`; category: `execution_failed`
- query: Create a Qiskit circuit with 3 qubits and 3 classical bits that applies a Hadamard gate to each qubit, measures each one into the matching classical bit via small reusable subci...
- target file: `source/0/roc_fixed_59eb18.py`
- copied file: `community/terra/qis_intro/entanglement_testing.ipynb` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 6, 'gate_types': {'H': 3, 'M': 3, 'barrier': 1}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 3, 'gate_count': 6, 'gate_types': {'h': 3, 'measure': 3}}`

### Failure 7

- slice: `extended_n8`; category: `execution_failed`
- query: Create a small Bernstein–Vazirani circuit that initializes the last qubit as the ancilla in the |-⟩ state by applying X then H, with the remaining qubits reserved for the query ...
- target file: `source/0/bernstein_vazirani_703dff.py`
- copied file: `source/0/bernstein_f06145.py` (`extended_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 4, 'num_clbits': 3, 'gate_count': 2, 'gate_types': {'x': 1, 'h': 1}}`
- copied metadata: `{'num_qubits': 4, 'num_clbits': 3, 'gate_count': 2, 'gate_types': {'h': 1, 'z': 1}}`

### Failure 8

- slice: `strict_n8`; category: `execution_failed`
- query: Build a 4-qubit Qiskit circuit that puts every qubit into equal superposition, applies an RZ rotation of π/4 on qubit 0 and π/3 on qubit 1, then entangles 0→2 and 1→3 with CNOT ...
- target file: `main.py`
- copied file: `4. Operators/qiskit_gradient_framework.py` (`strict_n8`)
- checks: `{}`
- target metadata: `{'num_qubits': 4, 'num_clbits': 0, 'gate_count': 8, 'gate_types': {'h': 4, 'rz': 2, 'cx': 2}}`
- copied metadata: `{'num_qubits': 3, 'num_clbits': 0, 'gate_count': 5, 'gate_types': {'h': 3, 'rz': 1, 'rx': 1}}`

