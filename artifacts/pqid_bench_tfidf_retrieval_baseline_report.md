# PQID-Bench TF-IDF Retrieval Strengthening Report

- input file: `PQID/data/processed/seed_drafts_quality_aware_source_code_v1.jsonl`
- clean source-code queries: `734`
- scope: dependency-free sparse vector-space retrieval over the same clean pool as the BM25 baseline
- slice reconstruction: `seed_role == gold_generation` -> `strict_n8`; `seed_role == broad_generation` -> `extended_n8`

## Clean Retrieval Pool

| slice | rows |
| --- | ---: |
| `strict_n8` | 415 |
| `extended_n8` | 319 |

## Vector-Space And Fusion Baselines

These baselines do not use the target instruction as candidate text, except for the explicitly marked upper-bound sanity check. The reciprocal-rank fusion condition combines the original BM25 code+metadata ranker with TF-IDF word and character views.

| baseline | indexed candidate text | queries | Recall@1 | Recall@5 | Recall@10 | MRR | median rank | mean rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `word_tfidf_code_only` | word unigram/bigram TF-IDF over code only | 734 | 11.04% | 21.66% | 28.20% | 0.1679 | 78.5 | 159.2 |
| `word_tfidf_code_plus_metadata` | word unigram/bigram TF-IDF over code plus non-instruction metadata | 734 | 15.12% | 28.20% | 35.29% | 0.2172 | 50.5 | 134.3 |
| `char_tfidf_code_plus_metadata` | character 3-5 gram TF-IDF over code plus non-instruction metadata | 734 | 6.81% | 12.81% | 17.17% | 0.1049 | 156.5 | 204.2 |
| `rrf_bm25_word_char_code_plus_metadata` | reciprocal-rank fusion of BM25, word TF-IDF, and character TF-IDF over code plus non-instruction metadata | 734 | 11.17% | 23.02% | 31.47% | 0.1759 | 65.0 | 140.9 |
| `instruction_upper_bound_word_tfidf` | instruction text upper bound with word unigram/bigram TF-IDF | 734 | 95.91% | 99.32% | 100.00% | 0.9745 | 1.0 | 1.1 |

## Comparison With BM25 Code+Metadata

| comparison | Recall@1 | Recall@5 | Recall@10 | MRR | median rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| `code_plus_metadata_bm25` | 11.85% | 25.20% | 31.34% | 0.1869 | 71.5 |
| `word_tfidf_code_plus_metadata` | 15.12% (+3.27 pp) | 28.20% (+3.00 pp) | 35.29% (+3.95 pp) | 0.2172 (+0.0302) | 50.5 |

## Best Fair Baseline Slice Breakdown

Selected by Recall@1 among non-instruction candidate representations: `word_tfidf_code_plus_metadata`.

| slice | Recall@1 | Recall@5 | Recall@10 | MRR | median rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| `strict_n8` | 18.31% | 33.49% | 40.48% | 0.2574 | 26.0 |
| `extended_n8` | 10.97% | 21.32% | 28.53% | 0.1648 | 74.0 |

## Best Fair Baseline Top-1 Failure Taxonomy

| category | failures | share | strict_n8 | extended_n8 | interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| `gate_vocabulary_distractor` | 296 | 47.51% | 156 | 140 | shared low-level gate vocabulary without enough semantic information to recover the exact source record |
| `lexical_metadata_distractor` | 132 | 21.19% | 58 | 74 | remaining lexical or metadata attraction without a simple structural match |
| `size_or_complexity_distractor` | 76 | 12.20% | 43 | 33 | shared gate vocabulary but a large width/depth/gate-count mismatch |
| `scaled_family_variant` | 37 | 5.94% | 25 | 12 | same circuit family or gate vocabulary, but with different width, depth, parameter count, or repeated block scale |
| `algorithm_family_confusion` | 30 | 4.82% | 22 | 8 | same named algorithm/protocol family, but the retrieved implementation is a different variant |
| `exact_gate_signature_ambiguity` | 26 | 4.17% | 18 | 8 | different source context with the same gate multiset, leaving lexical BM25 unable to identify the intended register/name semantics |
| `same_source_lineage_neighbor` | 20 | 3.21% | 13 | 7 | same file, notebook lineage, or source context, but the retrieved fragment is not the requested target |
| `same_source_register_or_subcircuit` | 6 | 0.96% | 4 | 2 | same source lineage and same gate signature, but the retrieved subcircuit targets a different register, role, or named component |

## Representative Best-Fair Top-1 Failures

### Failure 1

- slice: `strict_n8`; target rank: `2`; top-1 slice: `extended_n8`
- taxonomy: `lexical_metadata_distractor` - remaining lexical or metadata attraction without a simple structural match
- query: Create the Bernstein–Vazirani setup circuit that initializes an n+1 qubit register with the last qubit as the ancilla in the |-> state, using a Hadamard followed by a Z on qubit n, and include n classical bits.
- expected file: `translations/ja/v1/ch-algorithms/bernstein-vazirani.ipynb`
- retrieved file: `source/0/bernstein_vazirani_703dff.py`
- expected gates: `{'h': 1, 'z': 1}`
- retrieved gates: `{'x': 1, 'h': 1}`

### Failure 2

- slice: `strict_n8`; target rank: `3`; top-1 slice: `strict_n8`
- taxonomy: `exact_gate_signature_ambiguity` - different source context with the same gate multiset, leaving lexical BM25 unable to identify the intended register/name semantics
- query: Create a minimal 2-qubit Bell-state circuit: apply a Hadamard to qubit 0, then a CNOT from qubit 0 to qubit 1, and measure both qubits into two classical bits.
- expected file: `examples/bell_state.py`
- retrieved file: `script/BellState.py`
- expected gates: `{'measure': 2, 'h': 1, 'cx': 1}`
- retrieved gates: `{'measure': 2, 'h': 1, 'cx': 1}`

### Failure 3

- slice: `strict_n8`; target rank: `3`; top-1 slice: `strict_n8`
- taxonomy: `exact_gate_signature_ambiguity` - different source context with the same gate multiset, leaving lexical BM25 unable to identify the intended register/name semantics
- query: Create a 3-qubit Qiskit circuit for state preparation that applies an RY rotation by π/4 on qubit 0, then a controlled-H from qubit 0 to qubit 1, followed by an X on qubit 1 and an H on qubit 2.
- expected file: `3. Algorithms/grovers_algorithm_and_amplitude_amplification.py`
- retrieved file: `tutorials/algorithms/06_grover.ipynb`
- expected gates: `{'ry': 1, 'ch': 1, 'x': 1, 'h': 1}`
- retrieved gates: `{'ry': 1, 'ch': 1, 'x': 1, 'h': 1}`

### Failure 4

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `same_source_register_or_subcircuit` - same source lineage and same gate signature, but the retrieved subcircuit targets a different register, role, or named component
- query: Create a Qiskit subcircuit on 4 qubits with RZ(-0.691) on qubit 2, then U(0,0,0.269) and U(0,0,0.036) applied in sequence to qubit 1, and finally RZ(-0.633) on qubit 3.
- expected file: `qutefuzz/qiskit_result/qiskit200/circuit59537.py`
- retrieved file: `qutefuzz/qiskit_result/qiskit200/circuit59537.py`
- expected gates: `{'rz': 2, 'u': 2}`
- retrieved gates: `{'rz': 2, 'u': 2}`

### Failure 5

- slice: `strict_n8`; target rank: `2`; top-1 slice: `extended_n8`
- taxonomy: `gate_vocabulary_distractor` - shared low-level gate vocabulary without enough semantic information to recover the exact source record
- query: Create a 2-qubit Qiskit circuit named qc_triad that applies H on qubit 0, then CX from 0 to 1, then another H on qubit 0, and finally measures both qubits.
- expected file: `trinity_core_phase2.py`
- retrieved file: `source/0/qiskit_ex3_015978.py`
- expected gates: `{'h': 2, 'measure': 2, 'cx': 1, 'barrier': 1}`
- retrieved gates: `{'h': 4, 'measure': 2, 'cx': 1}`

### Failure 6

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `size_or_complexity_distractor` - shared gate vocabulary but a large width/depth/gate-count mismatch
- query: Create a Qiskit circuit named `wavefunction` with 8 qubits, and apply Pauli-X gates to qubits 0, 1, 2, and 3 only.
- expected file: `CodeforTest.py`
- retrieved file: `gates/pauli_x_gate.py`
- expected gates: `{'x': 4}`
- retrieved gates: `{'x': 1, 'barrier': 1, 'measure': 1}`

### Failure 7

- slice: `strict_n8`; target rank: `2`; top-1 slice: `extended_n8`
- taxonomy: `size_or_complexity_distractor` - shared gate vocabulary but a large width/depth/gate-count mismatch
- query: Create a 1-qubit Qiskit circuit that applies, in order, an H gate, a Y gate, an S gate, and a T gate to qubit 0.
- expected file: `Exercises/Medium_Single_Qubit_Gates.ipynb`
- retrieved file: `Effect_of_bugs_on_Entropy/Testcases/shallow/shallow_0.py`
- expected gates: `{'h': 1, 'y': 1, 's': 1, 't': 1}`
- retrieved gates: `{'t': 1, 'ccx': 1, 'cswap': 1, 'y': 1, 's': 1}`

### Failure 8

- slice: `strict_n8`; target rank: `4`; top-1 slice: `strict_n8`
- taxonomy: `same_source_lineage_neighbor` - same file, notebook lineage, or source context, but the retrieved fragment is not the requested target
- query: Create a Qiskit circuit for a 3-qubit phase-flip error-correction example: encode qubit 0 onto qubits 1 and 2 with two CNOTs, apply Hadamards to all three qubits, insert a Z error on qubit 0, apply Hadamards again, de...
- expected file: `Quantum Error Correction/Phase Flip code.py`
- retrieved file: `Quantum Error Correction/Shor code.py`
- expected gates: `{'h': 6, 'cx': 4, 'z': 1, 'ccx': 1, 'measure': 1}`
- retrieved gates: `{'h': 2, 'x': 1, 'z': 1, 'barrier': 1, 'measure': 1}`

### Failure 9

- slice: `strict_n8`; target rank: `2`; top-1 slice: `strict_n8`
- taxonomy: `same_source_lineage_neighbor` - same file, notebook lineage, or source context, but the retrieved fragment is not the requested target
- query: Create a 4-qubit Qiskit variational circuit named "VQC Circuit" with eight input Parameters and eight weight Parameters: apply RY then RZ feature-encoding rotations on qubits 0 through 3 using input0..input7 in order,...
- expected file: `DEMOS/IRIS/siamese_noncondensed.py`
- retrieved file: `DEMOS/IRIS/2siamesecondensed.py`
- expected gates: `{'ry': 8, 'rz': 8, 'cx': 2, 'barrier': 1}`
- retrieved gates: `{'ry': 4, 'rz': 4, 'cx': 1, 'barrier': 1}`

### Failure 10

- slice: `strict_n8`; target rank: `2`; top-1 slice: `extended_n8`
- taxonomy: `lexical_metadata_distractor` - remaining lexical or metadata attraction without a simple structural match
- query: Create a 2-qubit Qiskit circuit that applies H on qubit 0; on qubit 1 applies Tdg, H, and Sdg; then a controlled-H from qubit 0 to qubit 1; then S on both qubits; then H, T, and SX on qubit 1; finishes with H on qubit...
- expected file: `qiskit/synthesis/two_qubit/xx_decompose/embodiments.py`
- retrieved file: `source/0/qiskit_ex3_015978.py`
- expected gates: `{'h': 4, 's': 2, 'tdg': 1, 'sdg': 1, 'ch': 1, 't': 1, 'sx': 1}`
- retrieved gates: `{'h': 4, 'measure': 2, 'cx': 1}`

