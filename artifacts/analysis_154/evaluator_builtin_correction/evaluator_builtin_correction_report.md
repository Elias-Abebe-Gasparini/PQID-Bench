# PQID-Bench Evaluator Version And Safe-Built-In Correction

- superseded evaluator: `pqid-bench-evaluator-1.0.0-restricted-builtins`
- canonical evaluator: `pqid-bench-evaluator-1.1.0-safe-builtins`
- unchanged structural predicate: `pqid-bench-reference-signature-1.0.0-count-map`
- canonical model reports carrying both version labels: `21`

The audit counterfactually evaluates every frozen response under both policies. The only difference is that the canonical restricted namespace admits `print` and `reversed`; `print` is a silent no-op with the ordinary `None` return value. No provider call is repeated.

## Aggregate Impact

| metric | restricted built-ins | canonical safe built-ins | status changes |
| --- | ---: | ---: | ---: |
| executable circuit | 2726/3234 (84.29%) | 2950/3234 (91.22%) | 224 (224 gained, 0 lost) |
| reference-signature match | 1603/3234 (49.57%) | 1703/3234 (52.66%) | 100 (100 gained, 0 lost) |
| execution-structure gap | 1123/3234 (34.72%) | 1247/3234 (38.56%) | +3.83 pp |

## Per-Model Impact

| model | execution before -> after | execution cells changed | signature before -> after | signature cells changed |
| --- | ---: | ---: | ---: | ---: |
| GPT-5.6 Sol | 153 -> 153 | 0 | 97 -> 97 | 0 |
| GPT-5.5 | 149 -> 150 | 1 | 93 -> 93 | 0 |
| GPT-5.4 mini | 151 -> 151 | 0 | 93 -> 93 | 0 |
| Claude Fable 5 | 148 -> 151 | 3 | 97 -> 97 | 0 |
| Claude Sonnet 4.6 | 136 -> 153 | 17 | 87 -> 91 | 4 |
| Claude Opus 4.8 | 154 -> 154 | 0 | 92 -> 92 | 0 |
| Gemini 2.5 Pro | 135 -> 136 | 1 | 83 -> 83 | 0 |
| Gemini 3.1 Pro Preview | 149 -> 149 | 0 | 94 -> 94 | 0 |
| DeepSeek V4 Pro | 141 -> 141 | 0 | 91 -> 91 | 0 |
| DeepSeek V4 Flash | 137 -> 137 | 0 | 81 -> 81 | 0 |
| Codestral 25.01 | 144 -> 144 | 0 | 86 -> 86 | 0 |
| Qwen3-Coder-Next | 132 -> 132 | 0 | 78 -> 78 | 0 |
| Llama 4 Maverick | 145 -> 145 | 0 | 75 -> 75 | 0 |
| Llama 3.3 70B | 144 -> 144 | 0 | 71 -> 71 | 0 |
| GPT-OSS 120B | 137 -> 149 | 12 | 80 -> 82 | 2 |
| GPT-OSS 20B | 130 -> 143 | 13 | 73 -> 78 | 5 |
| Mistral Small 3.2 24B | 95 -> 139 | 44 | 52 -> 75 | 23 |
| Qiskit Mistral 3.2 24B | 105 -> 138 | 33 | 55 -> 69 | 14 |
| Qwen3 32B | 88 -> 89 | 1 | 53 -> 54 | 1 |
| Llama 4 Scout | 89 -> 127 | 38 | 46 -> 69 | 23 |
| Llama 3.1 8B | 64 -> 125 | 61 | 26 -> 54 | 28 |

## Frozen-Input Invariants

- prompt JSONL SHA-256: `cc6ba5c8a1fbf8677bd016d3cad47c7934981a685cc51052bdc3beb03f99b6eb`
- normalized prompt-text SHA-256: `075382feacb497334f00930afbae8f56e38f0148d5dc14f6e01d0d7eb8b940ed`
- normalized target-metadata SHA-256: `f2188c348ea894879af80e70efdfd1da773e50f74deca1677c1cc873ec803a26`
- response-log manifest SHA-256: `fb40b2406d17be6455cc99fb3d808c40db5c20d8eb9e916bacd38424b14f6640`
- structural-predicate source SHA-256: `cc0b92423941b2fc7da925386f3f2cb495687ab9113d6f3db88fa38cad094fcd`
- canonical replay disagreements with the published report matrix: `0`

These hashes are evaluated once and shared by both policy branches. The correction changes evaluator admissibility only; prompts, responses, targets, split assignments, request/response artifacts, and the reference-signature predicate are unchanged.
