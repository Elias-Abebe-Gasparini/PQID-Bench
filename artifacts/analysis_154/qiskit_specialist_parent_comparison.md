# Qiskit Specialist Versus Exact Mistral Parent

- paired prompts: `154`
- target-signature clusters: `144`
- cluster bootstrap samples: `20000`
- cluster sign-flip samples: `50000`
- paired request rows with identical model-input hashes: `154`
- model-input hash mismatches: `0`
- prompt-record hash mismatches: `0`
- generation configuration identical: `True`
- reported differences are specialist minus parent

| metric | specialist | parent | difference (95% cluster interval) | specialist wins / parent wins / ties | cluster p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| execution | 138/154 (89.61%) | 139/154 (90.26%) | -0.65 pp [-6.21 pp, +4.76 pp] | 9 / 10 / 135 | 1.0000 | 1.0000 |
| reference signature | 69/154 (44.81%) | 75/154 (48.70%) | -3.90 pp [-10.26 pp, +2.47 pp] | 9 / 15 / 130 | 0.3077 | 1.0000 |
| gate types | 79/154 (51.30%) | 89/154 (57.79%) | -6.49 pp [-13.07 pp, +0.00 pp] | 8 / 18 / 128 | 0.0740 | 0.4439 |
| gate count | 99/154 (64.29%) | 115/154 (74.68%) | -10.39 pp [-17.22 pp, -3.82 pp] | 7 / 23 / 124 | 0.0049 | 0.0346 |
| qubits | 132/154 (85.71%) | 135/154 (87.66%) | -1.95 pp [-7.84 pp, +3.95 pp] | 9 / 12 / 133 | 0.6608 | 1.0000 |
| classical bits | 111/154 (72.08%) | 112/154 (72.73%) | -0.65 pp [-7.48 pp, +6.12 pp] | 14 / 15 / 125 | 1.0000 | 1.0000 |
| qasm3 | 137/154 (88.96%) | 139/154 (90.26%) | -1.30 pp [-6.92 pp, +4.55 pp] | 9 / 11 / 134 | 0.8263 | 1.0000 |

The exact parent has the higher reference-signature point estimate. The paired cluster interval and sign-flip test determine whether that release-bound difference is distinguishable from zero. Because the specialist and parent were served through different provider routes, the result does not isolate the fine-tuning intervention from every serving-stack difference.
