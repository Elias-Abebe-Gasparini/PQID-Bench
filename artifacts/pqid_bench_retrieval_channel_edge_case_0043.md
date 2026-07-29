# PQID-Bench Retrieval-Channel Edge Case 0043

Source JSON: `artifacts/pqid_bench_retrieval_channel_edge_case_0043.json`

This artifact documents the Figure 2 retrieval-channel edge case for
`pqid_bench_external_gen_0043`. The case is not one of the prompts missed by
all models: `20 / 21` completed model rows match
the target. Its role is narrower. It shows that the sparse retrieval-copy
channels do not have identical errors: BM25 and TF-IDF over code/metadata
recover a source neighbor with the same evaluator-facing signature, while
TF-IDF over instruction text retrieves a same-width but gate-vocabulary-wrong
neighbor.

## Target Prompt

| field | value |
| --- | --- |
| prompt id | `pqid_bench_external_gen_0043` |
| row id | `3ca2e35fe48b1a2c21eb9a79a7da388b` |
| label | `extended_n8` |
| source path | `source/0/cruzados_0e0e72.py` |
| source group | `backordinary\|QDP-FSL\|source/0/cruzados_0e0e72.py` |
| GitHub anchor | `https://github.com/backordinary/QDP-FSL/blob/main/source/0/cruzados_0e0e72.py#L15-L29` |
| model-roster reference-signature matches | `20 / 21` |
| item difficulty | `0.047619` |
| target signature | `2q/2c`; `5` counted gates; `{x:2, cx:1, measure:2}` |
| target ordered gate tape | `x(q0)`, `cx(q0,q1)`, `x(q0)`, `measure(q0,c0)`, `measure(q1,c1)` |

Instruction:

```text
Create a compact 2-qubit Qiskit circuit that applies X on qubit 0, then a CNOT from qubit 0 to qubit 1, then X on qubit 0 again, and finally measures both qubits into two classical bits.
```

## Retrieval-Channel Comparison

| retrieval channel | retrieved row | retrieved source path | source group match | signature match | ordered-tape caveat | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| BM25 code/metadata copy | `98d799abcf6f433879a866d4edd3e10e` | `qiskit_src/cnot.py` | no | yes: `2q/2c`; `5` gates; `{x:2, cx:1, measure:2}` | retrieved tape is `cx`, `x(q0)`, `x(q1)`, measurements | code/metadata retrieval finds a metadata-neighbor structural match |
| TF-IDF code/metadata copy | `98d799abcf6f433879a866d4edd3e10e` | `qiskit_src/cnot.py` | no | yes: `2q/2c`; `5` gates; `{x:2, cx:1, measure:2}` | same retrieved tape as BM25 code/metadata copy | same code/metadata-only hit |
| TF-IDF instruction copy | `7d516050c806be7fce65a6edea09f10d` | `source/0/main_c5ddaa.py` | no | no: `2q/2c`; `6` gates; `{h:3, cx:1, measure:2}` | Hadamard/CX neighbor, not an X/CX/X neighbor | instruction retrieval misses gate count and gate vocabulary |

## Interpretation

This case supports the manuscript's narrower claim of metadata-neighbor
complementarity. It does not show full ordered-circuit equivalence. Under the
current reference-signature predicate, a copied circuit is scored against qubit count,
classical-bit count, counted gate total, and gate-type multiset. It is not yet
scored against ordered gate tape or operand sequence. The case therefore
motivates the ordered-gate-tape and simulation-equivalence diagnostics discussed
in the limitations and future-work sections.
