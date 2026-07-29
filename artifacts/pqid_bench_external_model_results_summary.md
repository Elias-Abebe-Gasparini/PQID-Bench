# PQID-Bench External Model Results Summary

- prompt split: `70` held-out source-file-group test prompts
- response source: traceable provider batch/API logs
- evaluator: strict standalone execution with safe `math` / `numpy` / `qiskit` imports
- inclusion rule: completed `70 / 70` response rows only; partial rows are tracked in their own runbooks

## Retrieval-Copy Lower Bound

| baseline | execution | structural | gate types | gate count | qubits | QASM3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| word_tfidf_train_instruction_copy | 90.00% | 24.29% | 25.71% | 37.14% | 57.14% | 90.00% |

## External Model Results

| provider | requested model | resolved model | rows | execution | structural | gate types | gate count | qubits | clbits | QASM3 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI | `gpt-5.5` | `gpt-5.5-2026-04-23` | 70 | 98.57% | 62.86% | 70.00% | 94.29% | 92.86% | 85.71% | 98.57% |
| OpenAI | `gpt-5.4-mini` | `gpt-5.4-mini-2026-03-17` | 70 | 97.14% | 64.29% | 70.00% | 92.86% | 94.29% | 87.14% | 97.14% |
| Anthropic | `claude-sonnet-4-6` | `claude-sonnet-4-6` | 70 | 92.86% | 61.43% | 65.71% | 88.57% | 88.57% | 84.29% | 92.86% |
| Anthropic | `claude-opus-4-8` | `claude-opus-4-8` | 70 | 100.00% | 61.43% | 68.57% | 94.29% | 94.29% | 87.14% | 100.00% |
| Google | `gemini-2.5-pro` | `gemini-2.5-pro` | 70 | 92.86% | 62.86% | 64.29% | 82.86% | 85.71% | 85.71% | 90.00% |
| Google | `gemini-3.1-pro-preview` | `gemini-3.1-pro-preview` | 70 | 97.14% | 62.86% | 68.57% | 92.86% | 91.43% | 87.14% | 97.14% |
| DeepSeek | `deepseek-v4-pro` | `deepseek-v4-pro` | 70 | 92.86% | 58.57% | 64.29% | 85.71% | 88.57% | 80.00% | 91.43% |
| DeepSeek | `deepseek-v4-flash` | `deepseek-v4-flash` | 70 | 92.86% | 58.57% | 62.86% | 82.86% | 87.14% | 82.86% | 91.43% |
| Groq | `llama-3.3-70b-versatile` | `llama-3.3-70b-versatile` | 70 | 94.29% | 50.00% | 64.29% | 78.57% | 90.00% | 77.14% | 94.29% |
| Groq | `qwen/qwen3-32b` | `qwen/qwen3-32b` | 70 | 65.71% | 38.57% | 44.29% | 61.43% | 65.71% | 52.86% | 65.71% |
| Groq | `openai/gpt-oss-120b` | `openai/gpt-oss-120b` | 70 | 94.29% | 52.86% | 57.14% | 78.57% | 90.00% | 81.43% | 92.86% |
| Groq | `openai/gpt-oss-20b` | `openai/gpt-oss-20b` | 70 | 84.29% | 51.43% | 57.14% | 78.57% | 81.43% | 75.71% | 84.29% |
| Groq | `llama-3.1-8b-instant` | `llama-3.1-8b-instant` | 70 | 47.14% | 22.86% | 22.86% | 37.14% | 44.29% | 45.71% | 45.71% |
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | `meta-llama/llama-4-scout-17b-16e-instruct` | 70 | 70.00% | 38.57% | 40.00% | 55.71% | 67.14% | 64.29% | 70.00% |
| GitHub Models | `mistral-ai/codestral-2501` | `codestral-2501` | 70 | 95.71% | 58.57% | 64.29% | 87.14% | 92.86% | 85.71% | 95.71% |
| ApiFreeLLM | `apifreellm` | `apifreellm` | 70 | 55.71% | 34.29% | 35.71% | 42.86% | 52.86% | 51.43% | 54.29% |

## Failure Notes

- `gpt-5.5` execution errors: `{"NameError": 1}`; structural mismatches: `{"gate_count_match": 3, "gate_types_match": 20, "num_clbits_match": 9, "num_qubits_match": 4}`; finish reasons: `{"completed": 69, "incomplete:max_output_tokens": 1}`.
- `gpt-5.4-mini` execution errors: `{"AttributeError": 2}`; structural mismatches: `{"gate_count_match": 3, "gate_types_match": 19, "num_clbits_match": 7, "num_qubits_match": 2}`; finish reasons: `{"completed": 70}`.
- `claude-sonnet-4-6` execution errors: `{"NameError": 5}`; structural mismatches: `{"gate_count_match": 3, "gate_types_match": 19, "num_clbits_match": 6, "num_qubits_match": 3}`; finish reasons: `{"end_turn": 70}`.
- `claude-opus-4-8` execution errors: `{}`; structural mismatches: `{"gate_count_match": 4, "gate_types_match": 22, "num_clbits_match": 9, "num_qubits_match": 4}`; finish reasons: `{"end_turn": 70}`.
- `gemini-2.5-pro` execution errors: `{"AttributeError": 5}`; structural mismatches: `{"gate_count_match": 5, "gate_types_match": 18, "num_clbits_match": 3, "num_qubits_match": 3}`; finish reasons: `{"MAX_TOKENS": 3, "STOP": 67}`.
- `gemini-3.1-pro-preview` execution errors: `{"AttributeError": 1, "SyntaxError": 1}`; structural mismatches: `{"gate_count_match": 3, "gate_types_match": 20, "num_clbits_match": 7, "num_qubits_match": 4}`; finish reasons: `{"MAX_TOKENS": 2, "STOP": 68}`.
- `deepseek-v4-pro` execution errors: `{"AttributeError": 3, "NameError": 2}`; structural mismatches: `{"gate_count_match": 4, "gate_types_match": 19, "num_clbits_match": 8, "num_qubits_match": 2}`; finish reasons: `{"length": 2, "stop": 68}`.
- `deepseek-v4-flash` execution errors: `{"AttributeError": 2, "ImportError": 1, "NameError": 2}`; structural mismatches: `{"gate_count_match": 6, "gate_types_match": 20, "num_clbits_match": 6, "num_qubits_match": 3}`; finish reasons: `{"length": 2, "stop": 68}`.
- `llama-3.3-70b-versatile` execution errors: `{"AttributeError": 2, "NameError": 1, "TypeError": 1}`; structural mismatches: `{"gate_count_match": 11, "gate_types_match": 21, "num_clbits_match": 12, "num_qubits_match": 3}`; finish reasons: `{"stop": 70}`.
- `qwen/qwen3-32b` execution errors: `{"AttributeError": 1, "SyntaxError": 23}`; structural mismatches: `{"gate_count_match": 3, "gate_types_match": 15, "num_clbits_match": 9}`; finish reasons: `{"length": 13, "stop": 57}`.
- `openai/gpt-oss-120b` execution errors: `{"AttributeError": 1, "ImportError": 1, "NameError": 2}`; structural mismatches: `{"gate_count_match": 10, "gate_types_match": 25, "num_clbits_match": 8, "num_qubits_match": 2}`; finish reasons: `{"stop": 70}`.
- `openai/gpt-oss-20b` execution errors: `{"AttributeError": 2, "NameError": 9}`; structural mismatches: `{"gate_count_match": 4, "gate_types_match": 19, "num_clbits_match": 6, "num_qubits_match": 2}`; finish reasons: `{"length": 2, "stop": 68}`.
- `llama-3.1-8b-instant` execution errors: `{"AttributeError": 2, "CircuitError": 1, "ImportError": 4, "NameError": 27, "SyntaxError": 3}`; structural mismatches: `{"gate_count_match": 6, "gate_types_match": 16, "num_qubits_match": 1}`; finish reasons: `{"length": 2, "stop": 68}`.
- `meta-llama/llama-4-scout-17b-16e-instruct` execution errors: `{"AttributeError": 2, "CircuitError": 4, "ImportError": 3, "NameError": 11, "TypeError": 1}`; structural mismatches: `{"gate_count_match": 10, "gate_types_match": 21, "num_clbits_match": 4, "num_qubits_match": 2}`; finish reasons: `{"stop": 70}`.
- `mistral-ai/codestral-2501` execution errors: `{"AttributeError": 2, "NameError": 1}`; structural mismatches: `{"gate_count_match": 6, "gate_types_match": 22, "num_clbits_match": 7, "num_qubits_match": 2}`; finish reasons: `{"stop": 70}`.
- `apifreellm` execution errors: `{"AttributeError": 19, "CircuitError": 6, "ImportError": 4, "TypeError": 2}`; structural mismatches: `{"gate_count_match": 8, "gate_types_match": 13, "num_clbits_match": 2, "num_qubits_match": 1}`; finish reasons: `{"stop": 70}`.
