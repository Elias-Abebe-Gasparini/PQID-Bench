# PQID-Bench Retrieval Baseline Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code queries: `734`
- slice reconstruction: `seed_role == gold_generation` -> `strict_n8`; `seed_role == broad_generation` -> `extended_n8`

## Clean Retrieval Pool

| slice | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |

## BM25 Retrieval Baselines

`instruction_upper_bound` indexes the instruction text itself and is included only as a leakage/ceiling sanity check. The fair lightweight baselines index code and/or non-instruction metadata.

| baseline | indexed candidate text | queries | Recall@1 | Recall@5 | Recall@10 | MRR | median rank | mean rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `code_only_bm25` | code only | 734 | 10.76% | 20.84% | 25.48% | 0.1601 | 109.0 | 171.1 |
| `metadata_only_bm25` | non-instruction metadata only | 734 | 5.99% | 14.85% | 16.62% | 0.1133 | 62.0 | 153.7 |
| `code_plus_metadata_bm25` | code plus non-instruction metadata | 734 | 11.85% | 25.20% | 31.34% | 0.1869 | 71.5 | 151.9 |
| `instruction_upper_bound_bm25` | instruction text upper bound | 734 | 94.41% | 99.05% | 99.86% | 0.9645 | 1.0 | 1.1 |

## Slice Breakdown

| baseline | slice | Recall@1 | Recall@5 | Recall@10 | MRR | median rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `code_only_bm25` | `strict_n8` | 12.53% | 24.82% | 29.40% | 0.1858 | 74.0 |
| `code_only_bm25` | `extended_n8` | 8.46% | 15.67% | 20.38% | 0.1268 | 130.0 |
| `metadata_only_bm25` | `strict_n8` | 6.99% | 16.63% | 17.59% | 0.1277 | 44.0 |
| `metadata_only_bm25` | `extended_n8` | 4.70% | 12.54% | 15.36% | 0.0945 | 120.0 |
| `code_plus_metadata_bm25` | `strict_n8` | 14.46% | 30.12% | 36.63% | 0.2218 | 39.0 |
| `code_plus_metadata_bm25` | `extended_n8` | 8.46% | 18.81% | 24.45% | 0.1416 | 89.0 |
| `instruction_upper_bound_bm25` | `strict_n8` | 91.81% | 98.31% | 99.76% | 0.9467 | 1.0 |
| `instruction_upper_bound_bm25` | `extended_n8` | 97.81% | 100.00% | 100.00% | 0.9877 | 1.0 |

## Code+Metadata Top-1 Failure Taxonomy

The taxonomy is computed over all top-1 misses from the strongest fair lightweight baseline (`code_plus_metadata_bm25`). Categories are heuristic and mutually exclusive; they are intended to guide the manuscript failure-mode table and later embedding/model-based retrieval experiments.

| category | failures | share | strict_n8 | extended_n8 | interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| `gate_vocabulary_distractor` | 251 | 38.79% | 134 | 117 | shared low-level gate vocabulary without enough semantic information to recover the exact source record |
| `lexical_metadata_distractor` | 133 | 20.56% | 64 | 69 | remaining lexical or metadata attraction without a simple structural match |
| `size_or_complexity_distractor` | 97 | 14.99% | 48 | 49 | shared gate vocabulary but a large width/depth/gate-count mismatch |
| `scaled_family_variant` | 76 | 11.75% | 48 | 28 | same circuit family or gate vocabulary, but with different width, depth, parameter count, or repeated block scale |
| `exact_gate_signature_ambiguity` | 31 | 4.79% | 20 | 11 | different source context with the same gate multiset, leaving lexical BM25 unable to identify the intended register/name semantics |
| `same_source_lineage_neighbor` | 29 | 4.48% | 16 | 13 | same file, notebook lineage, or source context, but the retrieved fragment is not the requested target |
| `algorithm_family_confusion` | 20 | 3.09% | 18 | 2 | same named algorithm/protocol family, but the retrieved implementation is a different variant |
| `same_source_register_or_subcircuit` | 10 | 1.55% | 7 | 3 | same source lineage and same gate signature, but the retrieved subcircuit targets a different register, role, or named component |

## Representative Code+Metadata Top-1 Failures

These examples show cases where the best fair lightweight baseline retrieved the wrong top candidate. They are useful for later failure taxonomy work.

### Failure 1

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `gate_vocabulary_distractor` - shared low-level gate vocabulary without enough semantic information to recover the exact source record
- query: Build a 3-qubit, 3-classical-bit quantum teleportation circuit that teleports the state |1⟩ from qubit 0 to qubit 2: initialize q0 with X, create a Bell pair on q1 and q2 with H and CX, apply Alice’s CX(q0,q1) and H(q...
- expected file: `Coding_With_Qiskit/ep5_Quantum_Teleportation.ipynb`
- retrieved file: `5.Quantum-Half-Adder.py`
- expected gates: `{'barrier': 4, 'cx': 3, 'measure': 3, 'h': 2, 'x': 1, 'cz': 1}`
- retrieved gates: `{'x': 2, 'barrier': 2, 'measure': 2, 'ccx': 1, 'cx': 1}`
- expected code: `circuit = QuantumCircuit(3,3) # QUBIT ORDERING # q0 = State |psi> that we want to teleport # q1 = Alice's half of the Bell pair # q2 = Bob's half of the Bell pair, the destination of the teleportation # ==============...`
- retrieved code: `qc = QuantumCircuit(3, 2) # --- Prepare Inputs --- # We want to compute 1 + 1, so we set q0 and q1 to |1> qc.x(0) qc.x(1) qc.barrier() # --- Half-Adder Logic --- # 1. Calculate the Carry bit (A AND B) # The Toffoli ga...`

### Failure 2

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `same_source_lineage_neighbor` - same file, notebook lineage, or source context, but the retrieved fragment is not the requested target
- query: Create a 2-qubit Qiskit circuit named "VQC Circuit" with four input parameters and four weight parameters: apply RY(input0) then RZ(input1) on qubit 0, RY(input2) then RZ(input3) on qubit 1, add a CX from qubit 0 to 1...
- expected file: `DEMOS/IRIS/2siamesecondensed.py`
- retrieved file: `DEMOS/IRIS/siamese_noncondensed.py`
- expected gates: `{'ry': 4, 'rz': 4, 'cx': 1, 'barrier': 1}`
- retrieved gates: `{'ry': 8, 'rz': 8, 'cx': 2, 'barrier': 1}`
- expected code: `qc = QuantumCircuit(2, name="VQC Circuit") input_params = [Parameter(f"input{i}") for i in range(4)] weight_params = [Parameter(f"weight{i}") for i in range(4)] # Feature map qc.ry(input_params[0],0) qc.rz(input_param...`
- retrieved code: `qc = QuantumCircuit(4, name="VQC Circuit") input_params = [Parameter(f"input{i}") for i in range(8)] weight_params = [Parameter(f"weight{i}") for i in range(8)] # Feature map part qc.ry(input_params[0], 0) qc.rz(input...`

### Failure 3

- slice: `strict_n8`; target rank: `9`; top-1 slice: `strict_n8`
- taxonomy: `lexical_metadata_distractor` - remaining lexical or metadata attraction without a simple structural match
- query: Create a 4-qubit, 4-classical-bit Qiskit circuit that tours basic gates in this order: h on q0, x on q1, y on q2, z on q3, then s on q0 and t on q1; apply rx(pi/4) to q0, ry(pi/3) to q1, and rz(pi/2) to q2; follow wit...
- expected file: `examples/02_gates_tour/gates_tour.py`
- retrieved file: `5.Quantum-Half-Adder.py`
- expected gates: `{'measure': 4, 'h': 1, 'x': 1, 'y': 1, 'z': 1, 's': 1, 't': 1, 'rx': 1, 'ry': 1, 'rz': 1, 'cx': 1, 'cz': 1, 'swap': 1, 'ccx': 1, 'barrier': 1}`
- retrieved gates: `{'x': 2, 'barrier': 2, 'measure': 2, 'ccx': 1, 'cx': 1}`
- expected code: `qc = QuantumCircuit(4, 4) # Single-qubit gates qc.h(0) qc.x(1) qc.y(2) qc.z(3) qc.s(0) qc.t(1) # Rotation gates qc.rx(math.pi / 4, 0) qc.ry(math.pi / 3, 1) qc.rz(math.pi / 2, 2) # Multi-qubit gates qc.cx(0, 1) qc.cz(2...`
- retrieved code: `qc = QuantumCircuit(3, 2) # --- Prepare Inputs --- # We want to compute 1 + 1, so we set q0 and q1 to |1> qc.x(0) qc.x(1) qc.barrier() # --- Half-Adder Logic --- # 1. Calculate the Carry bit (A AND B) # The Toffoli ga...`

### Failure 4

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `same_source_register_or_subcircuit` - same source lineage and same gate signature, but the retrieved subcircuit targets a different register, role, or named component
- query: Create a Qiskit subcircuit named `measureB1` on registers `qr` and `cr` that acts only on Bob's qubit `qr[1]` by applying `s`, `h`, `t`, and `h` in that order, then measuring it into `cr[1]`.
- expected file: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`
- retrieved file: `community/awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`
- expected gates: `{'h': 2, 's': 1, 't': 1, 'measure': 1}`
- retrieved gates: `{'h': 2, 's': 1, 't': 1, 'measure': 1}`
- expected code: `measureB1 = QuantumCircuit(qr, cr, name='measureB1') measureB1.s(qr[1]) measureB1.h(qr[1]) measureB1.t(qr[1]) measureB1.h(qr[1]) measureB1.measure(qr[1],cr[1]) # measure the spin projection of Bob's qubit onto the b_2...`
- retrieved code: `measureA1 = QuantumCircuit(qr, cr, name='measureA1') measureA1.h(qr[0]) measureA1.measure(qr[0],cr[0]) # measure the spin projection of Alice's qubit onto the a_2 direction (W basis) measureA2 = QuantumCircuit(qr, cr,...`

### Failure 5

- slice: `strict_n8`; target rank: `3`; top-1 slice: `strict_n8`
- taxonomy: `size_or_complexity_distractor` - shared gate vocabulary but a large width/depth/gate-count mismatch
- query: Build a 3-qubit Qiskit circuit where q0 and q1 start in superposition, then apply four barrier-separated blocks of the pattern CRY(pi/4) on (0,2), CX(0,1), CRY(-pi/4) on (1,2), CX(0,1), CRY(pi/4) on (1,2), with X togg...
- expected file: `Original_4_copy_aux_forking-Copy1.py`
- retrieved file: `5.Quantum-Half-Adder.py`
- expected gates: `{'cry': 12, 'cx': 8, 'barrier': 5, 'x': 4, 'measure': 3, 'h': 2}`
- retrieved gates: `{'x': 2, 'barrier': 2, 'measure': 2, 'ccx': 1, 'cx': 1}`
- expected code: `qc = QuantumCircuit(3) qc.h(0) qc.h(1) qc.barrier() # Pixel 1 qc.cry(theta, 0, 2) qc.cx(0, 1) qc.cry(-theta, 1, 2) qc.cx(0, 1) qc.cry(theta, 1, 2) qc.barrier() # Pixel 2 qc.x(1) qc.cry(theta, 0, 2) qc.cx(0, 1) qc.cry(...`
- retrieved code: `qc = QuantumCircuit(3, 2) # --- Prepare Inputs --- # We want to compute 1 + 1, so we set q0 and q1 to |1> qc.x(0) qc.x(1) qc.barrier() # --- Half-Adder Logic --- # 1. Calculate the Carry bit (A AND B) # The Toffoli ga...`

### Failure 6

- slice: `extended_n8`; target rank: `2`; top-1 slice: `extended_n8`
- taxonomy: `size_or_complexity_distractor` - shared gate vocabulary but a large width/depth/gate-count mismatch
- query: Create a 2-qubit Qiskit circuit that applies a CNOT with qubit 1 controlling qubit 0, then follows it with ry(pi/2) on qubit 1, rxx(pi/2) on qubits 1 and 0, ry(-pi/2) on qubit 1, rx(-pi/2) on qubit 0, and p(-pi/2) on ...
- expected file: `source/0/cx_841fdd.py`
- retrieved file: `source/0/ccx3_48ef26.py`
- expected gates: `{'ry': 2, 'cx': 1, 'rxx': 1, 'rx': 1, 'p': 1}`
- retrieved gates: `{'ry': 6, 'rx': 6, 'rxx': 5, 'p': 1}`
- expected code: `qc = QuantumCircuit(2) qc.cx(1,0) #MSB is control bit #CNOT is its own inverse, see if MS-based CNOT works qc.ry(np.pi/2,1) qc.rxx(np.pi/2,1,0) #bug?? works but should be qc.rxx(np.pi/4,1,0) qc.ry(-np.pi/2,1) qc.rx(-n...`
- retrieved code: `qc = QuantumCircuit(qr) #qc.ccx(2,1,0) #LSB is target bit #CNOT is its own inverse, see if MS-based CNOT works qc.ry(-np.pi/2,2) qc.ry(-np.pi/2,1) qc.rx(-np.pi/4,1) qc.rx(np.pi/4,0) qc.rxx(np.pi/4,2,0) #bug?? works bu...`

### Failure 7

- slice: `strict_n8`; target rank: `2`; top-1 slice: `extended_n8`
- taxonomy: `same_source_lineage_neighbor` - same file, notebook lineage, or source context, but the retrieved fragment is not the requested target
- query: Create a 2-qubit Qiskit circuit parameterized by theta that applies H to both qubits, a controlled-phase gate with angle -2*theta from qubit 0 to 1, RZ(theta) on each qubit, then H on both again, and set the circuit’s...
- expected file: `qiskit/synthesis/two_qubit/xx_decompose/embodiments.py`
- retrieved file: `qiskit/synthesis/two_qubit/xx_decompose/embodiments.py`
- expected gates: `{'h': 4, 'rz': 2, 'cp': 1}`
- retrieved gates: `{'h': 4, 's': 2, 'tdg': 1, 'sdg': 1, 'ch': 1, 't': 1, 'sx': 1}`
- expected code: `cphase_circuit = QuantumCircuit(2) cphase_circuit.h(0) cphase_circuit.h(1) cphase_circuit.cp(-2 * theta, 0, 1) cphase_circuit.rz(theta, 0) cphase_circuit.rz(theta, 1) cphase_circuit.h(0) cphase_circuit.h(1) cphase_cir...`
- retrieved code: `rxx_circuit = QuantumCircuit(2) theta = Parameter("θ") rxx_circuit.rxx(theta, 0, 1) rzz_circuit = QuantumCircuit(2) theta = Parameter("θ") rzz_circuit.h(0) rzz_circuit.h(1) rzz_circuit.rzz(theta, 0, 1) rzz_circuit.h(0...`

### Failure 8

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `scaled_family_variant` - same circuit family or gate vocabulary, but with different width, depth, parameter count, or repeated block scale
- query: Build a 3-qubit, 3-classical-bit quantum teleportation circuit in Qiskit: create a Bell pair on qubits 1 and 2, put qubit 0 into a Hadamard state, perform the Bell-basis steps on qubits 0 and 1, measure qubits 0 and 1...
- expected file: `quntumcircuit.py`
- retrieved file: `Coding_With_Qiskit/ep5_Quantum_Teleportation.ipynb`
- expected gates: `{'h': 3, 'cx': 3, 'measure': 3, 'cz': 1}`
- retrieved gates: `{'barrier': 4, 'cx': 3, 'measure': 3, 'h': 2, 'x': 1, 'cz': 1}`
- expected code: `qc = QuantumCircuit(3, 3) # Step 1: Create entanglement between qubit 1 & 2 (Bell pair) qc.h(1) # Hadamard gate on qubit 1 qc.cx(1, 2) # CNOT gate with qubit 1 as control and qubit 2 as target # Step 2: Apply a random...`
- retrieved code: `circuit = QuantumCircuit(3,3) # QUBIT ORDERING # q0 = State |psi> that we want to teleport # q1 = Alice's half of the Bell pair # q2 = Bob's half of the Bell pair, the destination of the teleportation # ==============...`

### Failure 9

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `gate_vocabulary_distractor` - shared low-level gate vocabulary without enough semantic information to recover the exact source record
- query: Create a Qiskit circuit for the Deutsch algorithm with two qubits and one classical bit: initialize the ancilla in |1>, apply Hadamards to both qubits, use a CNOT from the input qubit to the ancilla as the balanced or...
- expected file: `quantum_showcase.py`
- retrieved file: `awards/teach_me_qiskit_2018/hadamard_action/hadamard_action.ipynb`
- expected gates: `{'h': 3, 'x': 1, 'cx': 1, 'measure': 1}`
- retrieved gates: `{'measure': 2, 'cx': 1}`
- expected code: `qc = QuantumCircuit(2, 1) qc.x(1) # Ancilla qubit qc.h(0) # Input qubit qc.h(1) # Ancilla qubit qc.cx(0, 1) # Oracle (for balanced function) qc.h(0) # Interference qc.measure(0, 0) # Result: 0 = constant, 1 = balanced`
- retrieved code: `cnot_i_00 = QuantumCircuit(i_q, i_c, name="cnot_i_00") # Note: qubits are assumed by Qiskit # to be initialized in the |0> state # Apply gates according to diagram: cnot_i_00.cx(i_q[0], i_q[1]) # Apply CNOT on line 2 ...`

### Failure 10

- slice: `extended_n8`; target rank: `3`; top-1 slice: `strict_n8`
- taxonomy: `lexical_metadata_distractor` - remaining lexical or metadata attraction without a simple structural match
- query: Create a Qiskit circuit on 18 qubits that implements this fixed permutation layer with eight CNOTs: 0→11, 1→10, 2→13, 3→15, 4→17, 5→12, 6→14, and 7→16. Name the circuit `P8`.
- expected file: `source/0/simplified_des_quantum_test_e77515.py`
- retrieved file: `notebooks/legacy/qconvert_tmp_cache/bffaa053e3e33a5a1fda84a45c335f4d08e43924dd9da8ee407320eb.py`
- expected gates: `{'cx': 8}`
- retrieved gates: `{'cx': 58, 'ry': 20, 'measure': 20, 'rx': 18, 'rz': 18}`
- expected code: `permutation8 = QuantumCircuit(18, name = 'P8') permutation8.cx(0, 11) permutation8.cx(1, 10) permutation8.cx(2, 13) permutation8.cx(3, 15) permutation8.cx(4, 17) permutation8.cx(5, 12) permutation8.cx(6, 14) permutati...`
- retrieved code: `qc = QuantumCircuit() q = QuantumRegister(20, 'q') c = ClassicalRegister(20, 'c') qc.add_register(q) qc.add_register(c) qc.rx(6.209957416856063, q[0]) qc.rx(2.5009858166994063, q[1]) qc.rz(1.1023958963447806, q[3]) qc...`

### Failure 11

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `scaled_family_variant` - same circuit family or gate vocabulary, but with different width, depth, parameter count, or repeated block scale
- query: Build a 3-qubit, 3-classical-bit quantum teleportation circuit that prepares qubit 0 in the |+> state, creates a Bell pair between qubits 1 and 2, performs the Bell-basis step on qubits 0 and 1 with a barrier before m...
- expected file: `Src/Quantum_teleportation_protocol/Quantun_teleportation_protocol.py`
- retrieved file: `Coding_With_Qiskit/ep5_Quantum_Teleportation.ipynb`
- expected gates: `{'cx': 4, 'h': 3, 'measure': 3, 'barrier': 1}`
- retrieved gates: `{'barrier': 4, 'cx': 3, 'measure': 3, 'h': 2, 'x': 1, 'cz': 1}`
- expected code: `qc = QuantumCircuit(3,3) #Step 2: Prepare the state to teleport (say qubit 0 in |+>state) qc.h(0) # Create superposition on qubit 0 #Step 3: Create an entangled pair between qubits 1 and qubit 2 qc.h(1) qc.cx(1,2) #St...`
- retrieved code: `circuit = QuantumCircuit(3,3) # QUBIT ORDERING # q0 = State |psi> that we want to teleport # q1 = Alice's half of the Bell pair # q2 = Bob's half of the Bell pair, the destination of the teleportation # ==============...`

### Failure 12

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `same_source_register_or_subcircuit` - same source lineage and same gate signature, but the retrieved subcircuit targets a different register, role, or named component
- query: Create a Qiskit subcircuit named `measureA2` on existing registers `qr` and `cr` that acts only on `qr[0]` by applying `s`, `h`, `t`, and `h` in that order, then measuring into `cr[0]`.
- expected file: `awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`
- retrieved file: `community/awards/teach_me_qiskit_2018/e91_qkd/e91_quantum_key_distribution_protocol.ipynb`
- expected gates: `{'h': 2, 's': 1, 't': 1, 'measure': 1}`
- retrieved gates: `{'h': 2, 's': 1, 't': 1, 'measure': 1}`
- expected code: `measureA2 = QuantumCircuit(qr, cr, name='measureA2') measureA2.s(qr[0]) measureA2.h(qr[0]) measureA2.t(qr[0]) measureA2.h(qr[0]) measureA2.measure(qr[0],cr[0]) # measure the spin projection of Alice's qubit onto the a...`
- retrieved code: `measureA1 = QuantumCircuit(qr, cr, name='measureA1') measureA1.h(qr[0]) measureA1.measure(qr[0],cr[0]) # measure the spin projection of Alice's qubit onto the a_2 direction (W basis) measureA2 = QuantumCircuit(qr, cr,...`

