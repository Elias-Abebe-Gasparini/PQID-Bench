# PQID-Bench Retrieval-Copy Complementarity Cases

This report lists held-out generation prompts solved by at least one retrieval-copy baseline and by none of the 15 completed named external model rows.

## Summary

- unique prompt targets: `5`
- baseline-prompt hits: `7`
- external model attempts on these targets: `75`
- external execution success: `67/75`
- external QASM3 export success: `66/75`
- external gate-vocabulary matches: `0/75`
- external all-structure matches: `0/75`
- baseline hit counts: `{'BM25 Copy': 1, 'TF-IDF Code Copy': 1, 'TF-IDF Instr. Copy': 5}`
- external primary failures: `{'gate_types_mismatch': 66, 'execution_failure:NameError': 3, 'execution_failure:SyntaxError': 3, 'no_circuit_found': 1, 'execution_failure:ImportError': 2}`

## Prompt-Level Cases

| prompt | slice | family | target summary | successful copy baselines | copied source files | external failure summary | instruction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pqid_bench_external_gen_0004` | `strict_n8` | bell_or_superdense;pauli_measurement | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `deneme.py` | exec 13/15; QASM3 13/15; gate vocab 0/15; all-structure 0/15 | Create a 2-qubit Qiskit circuit that prepares a Bell state by applying a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit 1, and finally measures both qubits. |
| `pqid_bench_external_gen_0028` | `strict_n8` | bell_or_superdense;pauli_measurement | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `benchmarks/profile_adapter.py` | exec 15/15; QASM3 15/15; gate vocab 0/15; all-structure 0/15 | Create a 2-qubit Qiskit circuit that prepares a Bell pair by applying H to qubit 0, then CX from qubit 0 to qubit 1, and finally measures both qubits. |
| `pqid_bench_external_gen_0033` | `strict_n8` | qkd_e91;pauli_measurement | 3q/3c; 5 gates; h:2, measure:1, s:1, t:1 | BM25 Copy, TF-IDF Code Copy, TF-IDF Instr. Copy | BM25 Copy: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`<br>TF-IDF Code Copy: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`<br>TF-IDF Instr. Copy: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb` | exec 13/15; QASM3 12/15; gate vocab 0/15; all-structure 0/15 | Create Qiskit measurement subcircuits for the E91 QKD setup on a shared 2-qubit register and classical register: Alice’s three choices should be H then measure on qubit 0, S-H-T-H then measure on qubit 0, and direct Z-basis measurement on qubit 0; Bob’s three choices should be S-H-T-H then measure on qubit 1, direct Z-basis measurement on qubit 1, and S-H then measure on qubit 1, with circuit names measureA1, measureA2, measureA3, measureB1, measureB2, and measureB3. |
| `pqid_bench_external_gen_0052` | `extended_n8` | arithmetic_toffoli;pauli_measurement | 4q/2c; 7 gates; barrier:2, ccx:1, cx:2, measure:2, x:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `source/0/half_adder_ca0ad5.py` | exec 13/15; QASM3 13/15; gate vocab 0/15; all-structure 0/15 | Create a compact Qiskit circuit for a 1-bit quantum half-adder that uses 4 qubits and 2 classical bits, initializes both input bits to 1, computes sum and carry with CNOT and Toffoli gates, and measures the result qubits. |
| `pqid_bench_external_gen_0064` | `extended_n8` | bell_or_superdense;pauli_measurement | 2q/2c; 4 gates; barrier:1, cx:1, h:1, measure:2 | TF-IDF Instr. Copy | TF-IDF Instr. Copy: `source/0/test3_f96dd8.py` | exec 13/15; QASM3 13/15; gate vocab 0/15; all-structure 0/15 | Create a small Qiskit circuit that prepares a Bell pair on 2 qubits and measures both qubits, suitable for running on a local fake backend. |
