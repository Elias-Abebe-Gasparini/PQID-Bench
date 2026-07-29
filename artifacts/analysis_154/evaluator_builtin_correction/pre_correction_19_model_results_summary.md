# PQID-Bench External Model Results Summary

- prompt split: `154` held-out source-file-group test prompts
- response source: traceable provider batch/API logs
- evaluator: strict standalone execution with safe `math` / `numpy` / `qiskit` imports
- inclusion rule: completed `154 / 154` response rows only; partial rows are tracked separately

## Retrieval-Copy Lower Bound

| baseline | execution | structural | gate types | gate count | qubits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| word_tfidf_train_instruction_copy | 91.56% | 15.58% | 17.53% | 37.66% | 54.55% | 91.56% |

## External Model Results

| provider | requested model | resolved model | rows | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI | `gpt-5.6-sol` | `gpt-5.6-sol` | 154 | 99.35% | 62.99% | 70.78% | 88.96% | 95.45% | 87.01% | 99.35% |
| OpenAI | `gpt-5.5` | `gpt-5.5-2026-04-23` | 154 | 96.75% | 60.39% | 68.18% | 86.36% | 92.21% | 83.12% | 96.75% |
| OpenAI | `gpt-5.4-mini` | `gpt-5.4-mini-2026-03-17` | 154 | 98.05% | 60.39% | 68.18% | 86.36% | 95.45% | 86.36% | 97.40% |
| Anthropic | `claude-fable-5` | `claude-fable-5` | 154 | 96.10% | 62.99% | 70.13% | 88.96% | 92.21% | 85.06% | 96.10% |
| Anthropic | `claude-sonnet-4-6` | `claude-sonnet-4-6` | 154 | 88.31% | 56.49% | 62.99% | 79.87% | 85.06% | 76.62% | 88.31% |
| Anthropic | `claude-opus-4-8` | `claude-opus-4-8` | 154 | 100.00% | 59.74% | 67.53% | 86.36% | 96.75% | 85.71% | 99.35% |
| Google | `gemini-2.5-pro` | `gemini-2.5-pro` | 154 | 87.66% | 53.90% | 60.39% | 78.57% | 83.77% | 75.32% | 87.66% |
| Google | `gemini-3.1-pro-preview` | `gemini-3.1-pro-preview` | 154 | 96.75% | 61.04% | 67.53% | 86.36% | 92.21% | 85.06% | 96.75% |
| DeepSeek | `deepseek-v4-pro` | `deepseek-v4-pro` | 154 | 91.56% | 59.09% | 64.94% | 81.82% | 88.31% | 80.52% | 91.56% |
| DeepSeek | `deepseek-v4-flash` | `deepseek-v4-flash` | 154 | 88.96% | 52.60% | 59.09% | 76.62% | 85.71% | 77.92% | 88.96% |
| Groq | `llama-3.3-70b-versatile` | `llama-3.3-70b-versatile` | 154 | 93.51% | 46.10% | 61.04% | 75.32% | 89.61% | 71.43% | 93.51% |
| Groq | `qwen/qwen3-32b` | `qwen/qwen3-32b` | 154 | 57.14% | 34.42% | 38.96% | 52.60% | 56.49% | 45.45% | 57.14% |
| Groq | `openai/gpt-oss-120b` | `openai/gpt-oss-120b` | 154 | 88.96% | 51.95% | 57.79% | 74.68% | 86.36% | 77.92% | 88.31% |
| Groq | `openai/gpt-oss-20b` | `openai/gpt-oss-20b` | 154 | 84.42% | 47.40% | 55.84% | 72.73% | 82.47% | 73.38% | 83.77% |
| Groq | `llama-3.1-8b-instant` | `llama-3.1-8b-instant` | 154 | 41.56% | 16.88% | 18.83% | 29.22% | 40.91% | 36.36% | 41.56% |
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | `meta-llama/llama-4-scout-17b-16e-instruct` | 154 | 57.79% | 29.87% | 32.47% | 46.10% | 55.84% | 51.30% | 57.79% |
| GitHub Models | `mistral-ai/codestral-2501` | `codestral-2501` | 154 | 93.51% | 55.84% | 63.64% | 82.47% | 90.91% | 81.17% | 93.51% |
| Hugging Face / Novita | `qwen/qwen3-coder-next` | `qwen/qwen3-coder-next` | 154 | 85.71% | 50.65% | 58.44% | 74.03% | 83.77% | 74.68% | 85.71% |
| GitHub Models | `meta/llama-4-maverick-17b-128e-instruct-fp8` | `Llama-4-Maverick-17B-128E-Instruct-FP8` | 154 | 94.16% | 48.70% | 62.34% | 81.82% | 90.91% | 74.03% | 93.51% |

## Failure Notes

- `gpt-5.6-sol` execution errors: `{"EmptyGeneration": 1}`; structural mismatches: `{"gate_count_match": 16, "gate_types_match": 44, "num_clbits_match": 19, "num_qubits_match": 6}`; finish reasons: `{"completed": 153, "incomplete:max_output_tokens": 1}`.
- `gpt-5.5` execution errors: `{"EmptyGeneration": 1, "NameError": 1, "SyntaxError": 2, "TypeError": 1}`; structural mismatches: `{"gate_count_match": 16, "gate_types_match": 44, "num_clbits_match": 21, "num_qubits_match": 7}`; finish reasons: `{"completed": 153, "incomplete:max_output_tokens": 1}`.
- `gpt-5.4-mini` execution errors: `{"AttributeError": 3}`; structural mismatches: `{"gate_count_match": 18, "gate_types_match": 46, "num_clbits_match": 18, "num_qubits_match": 4}`; finish reasons: `{"completed": 154}`.
- `claude-fable-5` execution errors: `{"EmptyGeneration": 3, "NameError": 3}`; structural mismatches: `{"gate_count_match": 11, "gate_types_match": 40, "num_clbits_match": 17, "num_qubits_match": 6}`; finish reasons: `{"end_turn": 151, "max_tokens": 1, "refusal": 2}`.
- `claude-sonnet-4-6` execution errors: `{"NameError": 18}`; structural mismatches: `{"gate_count_match": 13, "gate_types_match": 39, "num_clbits_match": 18, "num_qubits_match": 5}`; finish reasons: `{"end_turn": 154}`.
- `claude-opus-4-8` execution errors: `{}`; structural mismatches: `{"gate_count_match": 21, "gate_types_match": 50, "num_clbits_match": 22, "num_qubits_match": 5}`; finish reasons: `{"end_turn": 154}`.
- `gemini-2.5-pro` execution errors: `{"AttributeError": 9, "EmptyGeneration": 5, "NameError": 1, "NoCircuitReturned": 1, "SyntaxError": 3}`; structural mismatches: `{"gate_count_match": 14, "gate_types_match": 42, "num_clbits_match": 19, "num_qubits_match": 6}`; finish reasons: `{"MAX_TOKENS": 10, "STOP": 144}`.
- `gemini-3.1-pro-preview` execution errors: `{"AttributeError": 1, "SyntaxError": 4}`; structural mismatches: `{"gate_count_match": 16, "gate_types_match": 45, "num_clbits_match": 18, "num_qubits_match": 7}`; finish reasons: `{"MAX_TOKENS": 5, "STOP": 149}`.
- `deepseek-v4-pro` execution errors: `{"AttributeError": 5, "EmptyGeneration": 6, "ImportError": 1, "NoCircuitReturned": 1}`; structural mismatches: `{"gate_count_match": 15, "gate_types_match": 41, "num_clbits_match": 17, "num_qubits_match": 5}`; finish reasons: `{"length": 6, "stop": 148}`.
- `deepseek-v4-flash` execution errors: `{"AttributeError": 5, "EmptyGeneration": 5, "ImportError": 6, "NoCircuitReturned": 1}`; structural mismatches: `{"gate_count_match": 19, "gate_types_match": 46, "num_clbits_match": 17, "num_qubits_match": 5}`; finish reasons: `{"length": 7, "stop": 147}`.
- `llama-3.3-70b-versatile` execution errors: `{"AttributeError": 5, "ImportError": 1, "NameError": 2, "TypeError": 2}`; structural mismatches: `{"gate_count_match": 28, "gate_types_match": 50, "num_clbits_match": 34, "num_qubits_match": 6}`; finish reasons: `{"stop": 154}`.
- `qwen/qwen3-32b` execution errors: `{"AttributeError": 2, "NameError": 1, "SyntaxError": 63}`; structural mismatches: `{"gate_count_match": 7, "gate_types_match": 28, "num_clbits_match": 18, "num_qubits_match": 1}`; finish reasons: `{"length": 39, "stop": 115}`.
- `openai/gpt-oss-120b` execution errors: `{"AttributeError": 2, "ImportError": 1, "NameError": 12, "NoCircuitReturned": 2}`; structural mismatches: `{"gate_count_match": 22, "gate_types_match": 48, "num_clbits_match": 17, "num_qubits_match": 4}`; finish reasons: `{"stop": 154}`.
- `openai/gpt-oss-20b` execution errors: `{"AttributeError": 5, "EmptyGeneration": 5, "ImportError": 1, "NameError": 13}`; structural mismatches: `{"gate_count_match": 18, "gate_types_match": 44, "num_clbits_match": 17, "num_qubits_match": 3}`; finish reasons: `{"length": 5, "stop": 149}`.
- `llama-3.1-8b-instant` execution errors: `{"AttributeError": 8, "CircuitError": 5, "ImportError": 7, "NameError": 61, "NoCircuitReturned": 2, "SyntaxError": 5, "TypeError": 2}`; structural mismatches: `{"gate_count_match": 19, "gate_types_match": 35, "num_clbits_match": 8, "num_qubits_match": 1}`; finish reasons: `{"length": 3, "stop": 151}`.
- `meta-llama/llama-4-scout-17b-16e-instruct` execution errors: `{"AttributeError": 9, "CircuitError": 6, "ImportError": 8, "NameError": 39, "SyntaxError": 1, "TypeError": 2}`; structural mismatches: `{"gate_count_match": 18, "gate_types_match": 39, "num_clbits_match": 10, "num_qubits_match": 3}`; finish reasons: `{"stop": 154}`.
- `mistral-ai/codestral-2501` execution errors: `{"AttributeError": 6, "ImportError": 1, "NameError": 2, "SyntaxError": 1}`; structural mismatches: `{"gate_count_match": 17, "gate_types_match": 46, "num_clbits_match": 19, "num_qubits_match": 4}`; finish reasons: `{"length": 2, "stop": 152}`.
- `qwen/qwen3-coder-next` execution errors: `{"AttributeError": 6, "CircuitError": 1, "ImportError": 7, "IndentationError": 2, "NoCircuitReturned": 4, "QiskitError": 1, "SyntaxError": 1}`; structural mismatches: `{"gate_count_match": 18, "gate_types_match": 42, "num_clbits_match": 17, "num_qubits_match": 3}`; finish reasons: `{"length": 1, "stop": 153}`.
- `meta/llama-4-maverick-17b-128e-instruct-fp8` execution errors: `{"AttributeError": 4, "CircuitError": 1, "ImportError": 4}`; structural mismatches: `{"gate_count_match": 19, "gate_types_match": 49, "num_clbits_match": 31, "num_qubits_match": 5}`; finish reasons: `{"stop": 154}`.
