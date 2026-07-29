# PQID-Bench Executable Validity And Small-Circuit Consistency Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- Qiskit available: `True`
- Qiskit version: `2.1.1`

## Clean Execution Pool

| slice | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |

## Headline Checks

| check | rows | rate |
| --- | ---: | ---: |
| snippet executed without exception | 665 | 90.60% |
| `QuantumCircuit` object found | 665 | 90.60% |
| structure matches stored metadata | 661 | 90.05% |
| OpenQASM 3 export succeeds | 659 | 89.78% |
| small-circuit simulation eligible | 165 | 22.48% |
| small-circuit simulation succeeds among eligible | 165 | 100.00% |

Note: scalar `gate_count` follows the stored PQID convention, where barriers are retained in `gate_types` but excluded from the scalar count.

## Slice Breakdown

| slice | rows | execution success | circuit found | structural match | QASM3 export | simulation eligible | simulation success / eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 415 | 89.16% | 89.16% | 88.92% | 87.95% | 95 | 95 / 95 (100.00%) |
| `extended_n8` | 319 | 92.48% | 92.48% | 91.54% | 92.16% | 70 | 70 / 70 (100.00%) |

## Execution Errors

| error type | rows |
| --- | ---: |
| `NameError` | 69 |

## Structural Mismatch Checks

| failed check | rows |
| --- | ---: |
| `gate_types_match` | 4 |

## QASM3 Export Errors

| error type | rows |
| --- | ---: |
| `QASM3ExporterError` | 6 |

## Small-Circuit Simulation Skip Reasons

| reason | rows |
| --- | ---: |
| `non_unitary_or_classical:measure` | 393 |
| `too_many_qubits` | 80 |
| `unbound_parameters` | 26 |
| `non_unitary_or_classical:m` | 1 |

## Representative Execution / Metadata Issues

### Issue 1

- row_id: `f22e333f6ad69dab59c339469b780689`
- label: `strict_n8`
- file_path: `notebooks/v1/ch-algorithms/bernstein-vazirani.ipynb`
- issue: `NameError`
- message: `name 'n' is not defined`

### Issue 2

- row_id: `aaf7672ea56b454c64001991cbbc573e`
- label: `strict_n8`
- file_path: `notebooks/v1/ch-algorithms/simon.ipynb`
- issue: `NameError`
- message: `name 'n' is not defined`

### Issue 3

- row_id: `c67144fc9d924405fc88829d0184abc0`
- label: `strict_n8`
- file_path: `translations/ja/v1/ch-algorithms/bernstein-vazirani.ipynb`
- issue: `NameError`
- message: `name 'n' is not defined`

### Issue 4

- row_id: `7544dc3b1be38e5f2396aa10c958770c`
- label: `strict_n8`
- file_path: `translations/ja/v1/ch-algorithms/simon.ipynb`
- issue: `NameError`
- message: `name 'n' is not defined`

### Issue 5

- row_id: `3940963950a677bb3374ae569c877a83`
- label: `strict_n8`
- file_path: `translations/es/v2/ch-algorithms/bernstein-vazirani.ipynb`
- issue: `NameError`
- message: `name 'n' is not defined`

### Issue 6

- row_id: `ecfbdd02bca48ca02de6cbc497e0e498`
- label: `strict_n8`
- file_path: `tutorials/operators/02_gradients_framework.ipynb`
- issue: `NameError`
- message: `name 'a' is not defined`

### Issue 7

- row_id: `a5637c60fb0455c1403fac5a4e446909`
- label: `strict_n8`
- file_path: `tutorials/operators/02_gradients_framework.ipynb`
- issue: `NameError`
- message: `name 'a' is not defined`

### Issue 8

- row_id: `640fdd4102f823fec59624b25dd2fd38`
- label: `strict_n8`
- file_path: `Coding_With_Qiskit/ep8_Noise_and_Error_Mitigation.ipynb`
- issue: `NameError`
- message: `name 'nqubits' is not defined`


## Representative QASM3 Export Issues

### QASM Issue 1

- row_id: `b5bb38a32abedc0697680dc4a69f372b`
- label: `strict_n8`
- file_path: `code/quantum_computing/CH02/prog_02.py`
- error: `QASM3ExporterError`

### QASM Issue 2

- row_id: `cff002da74517f76770feb0063003171`
- label: `strict_n8`
- file_path: `code/quantum_computing/CH02/prog_03.py`
- error: `QASM3ExporterError`

### QASM Issue 3

- row_id: `0f2b905a1da72bb0e409cf1d45f792be`
- label: `strict_n8`
- file_path: `code/quantum_computing/source_code/Code-Ch2.py`
- error: `QASM3ExporterError`

### QASM Issue 4

- row_id: `9a395c9a0b8bd576ad7fb1b12a460f4a`
- label: `strict_n8`
- file_path: `code/quantum_computing/source_code/Code-Ch2.py`
- error: `QASM3ExporterError`

