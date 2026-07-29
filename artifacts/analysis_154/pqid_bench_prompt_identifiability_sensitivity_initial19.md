# PQID-Bench Prompt-Identifiability Sensitivity

The frozen 154-prompt result remains the primary analysis. This sensitivity removes four high-confidence exceptions where the strict target signature depends on source details that are not stated in the model input.

| analysis | prompts | prompt-model rows | executable circuit | structural match | ES-gap | signature-wrong given execution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frozen primary | 154 | 2926 | 2673 (91.35%) | 1559 (53.28%) | 1114 (38.07%) | 41.68% |
| identifiable sensitivity | 150 | 2850 | 2619 (91.89%) | 1559 (54.70%) | 1060 (37.19%) | 40.47% |

The sensitivity changes executable-circuit success by +0.54 pp and structural match by +1.42 pp. The structural numerator remains unchanged because all four exception prompts are missed structurally by every model row.

## High-Confidence Exceptions

| prompt | exception class | executable / 19 | structural / 19 | reason |
| --- | --- | ---: | ---: | --- |
| `pqid_bench_external_gen_0040` | `unavailable_external_reference` | 11 | 0 | The prompt refers to a shown decomposition and source gate order that are not included in the model input. |
| `pqid_bench_external_gen_0117` | `underspecified_operation_multiplicity` | 17 | 0 | QFT-style staging does not determine the target's eight barrier operations. |
| `pqid_bench_external_gen_0141` | `underspecified_repetition_pattern` | 15 | 0 | A long CNOT pattern does not determine 77 CNOTs, 40 barriers, and 10 X operations. |
| `pqid_bench_external_gen_0142` | `minimum_constraints_scored_as_exact` | 11 | 0 | At-least constraints do not determine the exact 25-gate, 14-type target multiset or three classical bits. |

## Per-Model Sensitivity

| model | structural, 154 | structural, 150 | change |
| --- | ---: | ---: | ---: |
| GPT-5.6 Sol | 62.99% | 64.67% | +1.68 pp |
| GPT-5.5 | 60.39% | 62.00% | +1.61 pp |
| GPT-5.4 mini | 60.39% | 62.00% | +1.61 pp |
| Claude Fable 5 | 62.99% | 64.67% | +1.68 pp |
| Claude Sonnet 4.6 | 59.09% | 60.67% | +1.58 pp |
| Claude Opus 4.8 | 59.74% | 61.33% | +1.59 pp |
| Gemini 2.5 Pro | 53.90% | 55.33% | +1.44 pp |
| Gemini 3.1 Pro Preview | 61.04% | 62.67% | +1.63 pp |
| DeepSeek V4 Pro | 59.09% | 60.67% | +1.58 pp |
| DeepSeek V4 Flash | 52.60% | 54.00% | +1.40 pp |
| Codestral 25.01 | 55.84% | 57.33% | +1.49 pp |
| Qwen3-Coder-Next | 50.65% | 52.00% | +1.35 pp |
| Llama 4 Maverick | 48.70% | 50.00% | +1.30 pp |
| Llama 3.3 70B | 46.10% | 47.33% | +1.23 pp |
| GPT-OSS 120B | 53.25% | 54.67% | +1.42 pp |
| GPT-OSS 20B | 50.65% | 52.00% | +1.35 pp |
| Qwen3 32B | 35.06% | 36.00% | +0.94 pp |
| Llama 4 Scout | 44.81% | 46.00% | +1.19 pp |
| Llama 3.1 8B | 35.06% | 36.00% | +0.94 pp |

The direction and ordering of the main capability gradient are preserved. This check therefore separates a small prompt-identifiability limitation from the broader execution-structure gap without discarding the frozen challenge cases.
