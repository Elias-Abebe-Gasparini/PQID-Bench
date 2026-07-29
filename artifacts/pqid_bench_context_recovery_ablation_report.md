# PQID-Bench Context-Recovery Ablation Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code rows: `734`
- Qiskit available: `True`
- Qiskit version: `2.1.1`

## Headline Recovery

| check | rows | rate |
| --- | ---: | ---: |
| strict isolated execution succeeds | 665 | 90.60% |
| strict `NameError` target rows | 69 | 9.40% |
| target rows execute after recovery | 69 | 100.00% |
| target rows produce `QuantumCircuit` after recovery | 69 | 100.00% |
| target rows structurally match after recovery | 67 | 97.10% |
| target rows export OpenQASM 3 after recovery | 67 | 97.10% |
| target rows pass small-circuit simulation after recovery | 18 | 26.09% |
| overall execution after strict + recovery | 734 | 100.00% |

Recovery is applied only to rows that failed strict isolated execution with `NameError`. The ablation supplies metadata-sized registers, common notebook aliases, symbolic angle parameters, and standard Qiskit gate classes.

## Recovery By Missing Symbol

| missing symbol | target rows | execution recovered | structural match | QASM3 export |
| --- | ---: | ---: | ---: | ---: |
| `n` | 20 | 20 | 19 | 20 |
| `qreg` | 16 | 16 | 15 | 16 |
| `q3` | 7 | 7 | 7 | 6 |
| `a` | 4 | 4 | 4 | 4 |
| `angle` | 4 | 4 | 4 | 4 |
| `i_q` | 4 | 4 | 4 | 4 |
| `n_qubits` | 2 | 2 | 2 | 2 |
| `num_qubits` | 2 | 2 | 2 | 2 |
| `HGate` | 1 | 1 | 1 | 1 |
| `SGate` | 1 | 1 | 1 | 1 |
| `anc` | 1 | 1 | 1 | 1 |
| `circ` | 1 | 1 | 1 | 1 |
| `crz` | 1 | 1 | 1 | 1 |
| `nqubits` | 1 | 1 | 1 | 1 |
| `qb` | 1 | 1 | 1 | 1 |
| `qreg2` | 1 | 1 | 1 | 1 |
| `sqrt` | 1 | 1 | 1 | 0 |
| `t` | 1 | 1 | 1 | 1 |

## Residual Recovery Errors

No residual execution errors among targeted rows.

## Residual Structural / Export Issues

| structural failed check | rows |
| --- | ---: |
| `num_clbits_match` | 2 |
| `num_qubits_match` | 2 |
| `gate_count_match` | 1 |
| `gate_types_match` | 1 |

| QASM3 export error | rows |
| --- | ---: |
| `QASM3ExporterError` | 2 |

## Representative Residual Structural / Export Issues

### Quality Issue 1

- row_id: `8c953f2d96d7c52ac14de6a4aa17490c`
- label: `strict_n8`
- file_path: `fuzzing/buggy_program/crash/fuzzing_0.py`
- baseline_missing_symbol: `qreg`
- structural_checks: `{'num_qubits_match': False, 'num_clbits_match': False, 'gate_count_match': True, 'gate_types_match': True, 'all_match': False}`
- qasm3_export: `True`
- qasm3_error: `None`

### Quality Issue 2

- row_id: `25058a481f8c44327813af6bd1060a97`
- label: `strict_n8`
- file_path: `qiskit/advanced_algorithms/phase_estimation.py`
- baseline_missing_symbol: `n`
- structural_checks: `{'num_qubits_match': False, 'num_clbits_match': False, 'gate_count_match': False, 'gate_types_match': False, 'all_match': False}`
- qasm3_export: `True`
- qasm3_error: `None`

### Quality Issue 3

- row_id: `068759c8d168073b4c12d729ee665d24`
- label: `strict_n8`
- file_path: `hello_world/bitstring_compression.ipynb`
- baseline_missing_symbol: `q3`
- structural_checks: `{'num_qubits_match': True, 'num_clbits_match': True, 'gate_count_match': True, 'gate_types_match': True, 'all_match': True}`
- qasm3_export: `False`
- qasm3_error: `QASM3ExporterError`

### Quality Issue 4

- row_id: `c75c14587819bb1f919a4eaede2638f4`
- label: `extended_n8`
- file_path: `source/0/simulation_qbits_9d646b.py`
- baseline_missing_symbol: `sqrt`
- structural_checks: `{'num_qubits_match': True, 'num_clbits_match': True, 'gate_count_match': True, 'gate_types_match': True, 'all_match': True}`
- qasm3_export: `False`
- qasm3_error: `QASM3ExporterError`


## Representative Recovered Rows

### Recovered 1

- row_id: `f22e333f6ad69dab59c339469b780689`
- label: `strict_n8`
- file_path: `notebooks/v1/ch-algorithms/bernstein-vazirani.ipynb`
- baseline_missing_symbol: `n`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `True`

### Recovered 2

- row_id: `aaf7672ea56b454c64001991cbbc573e`
- label: `strict_n8`
- file_path: `notebooks/v1/ch-algorithms/simon.ipynb`
- baseline_missing_symbol: `n`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `False`

### Recovered 3

- row_id: `c67144fc9d924405fc88829d0184abc0`
- label: `strict_n8`
- file_path: `translations/ja/v1/ch-algorithms/bernstein-vazirani.ipynb`
- baseline_missing_symbol: `n`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `True`

### Recovered 4

- row_id: `7544dc3b1be38e5f2396aa10c958770c`
- label: `strict_n8`
- file_path: `translations/ja/v1/ch-algorithms/simon.ipynb`
- baseline_missing_symbol: `n`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `False`

### Recovered 5

- row_id: `3940963950a677bb3374ae569c877a83`
- label: `strict_n8`
- file_path: `translations/es/v2/ch-algorithms/bernstein-vazirani.ipynb`
- baseline_missing_symbol: `n`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `True`

### Recovered 6

- row_id: `ecfbdd02bca48ca02de6cbc497e0e498`
- label: `strict_n8`
- file_path: `tutorials/operators/02_gradients_framework.ipynb`
- baseline_missing_symbol: `a`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `False`

### Recovered 7

- row_id: `a5637c60fb0455c1403fac5a4e446909`
- label: `strict_n8`
- file_path: `tutorials/operators/02_gradients_framework.ipynb`
- baseline_missing_symbol: `a`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `False`

### Recovered 8

- row_id: `640fdd4102f823fec59624b25dd2fd38`
- label: `strict_n8`
- file_path: `Coding_With_Qiskit/ep8_Noise_and_Error_Mitigation.ipynb`
- baseline_missing_symbol: `nqubits`
- structural_match: `True`
- qasm3_export: `True`
- simulation_eligible: `False`


## Representative Residual Failures

No residual failures.
