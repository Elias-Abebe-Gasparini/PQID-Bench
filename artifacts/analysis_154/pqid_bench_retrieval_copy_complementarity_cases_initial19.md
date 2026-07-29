# PQID-Bench Retrieval-Copy Complementarity Cases

This report lists held-out generation prompts solved by at least one retrieval-copy baseline and by none of the 19 completed named external model rows.

## Summary

- unique prompt targets: `6`
- baseline-prompt hits: `8`
- external model attempts on these targets: `114`
- external execution success: `102/114`
- external QASM3 export success: `102/114`
- external gate-vocabulary matches: `15/114`
- external all-structure matches: `0/114`
- baseline hit counts: `{'BM25 Copy': 1, 'TF-IDF Code Copy': 1, 'TF-IDF Instr. Copy': 6}`
- external primary failures: `{'gate_types_mismatch': 87, 'execution_failure:SyntaxError': 4, 'num_clbits_mismatch': 15, 'empty_generation': 3, 'no_circuit_found': 1, 'execution_failure:ImportError': 2, 'execution_failure:TypeError': 1, 'execution_failure:CircuitError': 1}`

## Prompt-Level Cases

| prompt | slice | family | target summary | successful copy baselines | copied source files | external failure summary | instruction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pqid_bench_external_gen_0004` | `strict_n8` | bell_or_superdense;pauli_measurement | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `deneme.py` | exec 18/19; QASM3 18/19; gate vocab 0/19; all-structure 0/19 | Create a 2-qubit Qiskit circuit that prepares a Bell state by applying a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit 1, and finally measures both qubits. |
| `pqid_bench_external_gen_0022` | `strict_n8` | error_correction;arithmetic_toffoli;pauli_measurement | 3q/3c; 13 gates; ccx:1, cx:4, h:6, measure:1, z:1 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `source/0/task_202_20q4_b4970b.py` | exec 16/19; QASM3 16/19; gate vocab 15/19; all-structure 0/19 | Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2 with two CNOTs, apply Hadamards to all three qubits, insert a Z error on qubit 0, apply Hadamards again, decode with the same two CNOTs, correct with a Toffoli using qubits 2 and 1 as controls on qubit 0, and measure qubit 0 into classical bit 0. |
| `pqid_bench_external_gen_0028` | `strict_n8` | bell_or_superdense;pauli_measurement | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `benchmarks/profile_adapter.py` | exec 19/19; QASM3 19/19; gate vocab 0/19; all-structure 0/19 | Create a 2-qubit Qiskit circuit that prepares a Bell pair by applying H to qubit 0, then CX from qubit 0 to qubit 1, and finally measures both qubits. |
| `pqid_bench_external_gen_0033` | `strict_n8` | qkd_e91;pauli_measurement | 3q/3c; 5 gates; h:2, measure:1, s:1, t:1 | BM25 Copy, TF-IDF Code Copy, TF-IDF Instr. Copy | BM25 Copy: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`<br>TF-IDF Code Copy: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`<br>TF-IDF Instr. Copy: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb` | exec 17/19; QASM3 17/19; gate vocab 0/19; all-structure 0/19 | Create Qiskit measurement subcircuits for the E91 QKD setup on a shared 2-qubit register and classical register: Alice’s three choices should be H then measure on qubit 0, S-H-T-H then measure on qubit 0, and direct Z-basis measurement on qubit 0; Bob’s three choices should be S-H-T-H then measure on qubit 1, direct Z-basis measurement on qubit 1, and S-H then measure on qubit 1, with circuit names measureA1, measureA2, measureA3, measureB1, measureB2, and measureB3. |
| `pqid_bench_external_gen_0064` | `extended_n8` | bell_or_superdense;pauli_measurement | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `source/0/test3_f96dd8.py` | exec 17/19; QASM3 17/19; gate vocab 0/19; all-structure 0/19 | Create a small Qiskit circuit that prepares a Bell pair on 2 qubits and measures both qubits, suitable for running on a local fake backend. |
| `pqid_bench_external_gen_0108` | `extended_n8` | pauli_measurement | 3q/3c; 9 gates; barrier:1, h:3, measure:3, sdg:3 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `source/0/quantum_phase_bloch_19c255.py` | exec 15/19; QASM3 15/19; gate vocab 0/19; all-structure 0/19 | Create a small Qiskit example for three qubits that prepares each qubit in a superposition, then builds separate measurement circuits for the X, Y, and Z bases using the usual basis-change gates before measuring all qubits. |
