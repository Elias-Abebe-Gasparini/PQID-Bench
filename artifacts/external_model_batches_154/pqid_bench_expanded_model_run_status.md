# PQID-Bench Expanded Model Run Status

- audited at UTC: `2026-07-14T03:58:56+00:00`
- expected prompts per model: `154`
- complete rows: `19`
- pending rows: `0`

| provider | requested model | status | requests | unique responses | evaluation rows | execution | structural | finish reasons |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| anthropic | `claude-fable-5` | complete | 154 | 154 | 154 | 96.10% | 62.99% | `{"end_turn": 151, "max_tokens": 1, "refusal": 2}` |
| anthropic | `claude-opus-4-8` | complete | 154 | 154 | 154 | 100.00% | 59.74% | `{"end_turn": 154}` |
| anthropic | `claude-sonnet-4-6` | complete | 154 | 154 | 154 | 88.31% | 56.49% | `{"end_turn": 154}` |
| deepseek | `deepseek-v4-flash` | complete | 154 | 154 | 154 | 88.96% | 52.60% | `{"length": 7, "stop": 147}` |
| deepseek | `deepseek-v4-pro` | complete | 154 | 154 | 154 | 91.56% | 59.09% | `{"length": 6, "stop": 148}` |
| github_models | `meta/llama-4-maverick-17b-128e-instruct-fp8` | complete | 154 | 154 | 154 | 94.16% | 48.70% | `{"stop": 154}` |
| github_models | `mistral-ai/codestral-2501` | complete | 154 | 154 | 154 | 93.51% | 55.84% | `{"length": 2, "stop": 152}` |
| google | `gemini-2.5-pro` | complete | 154 | 154 | 154 | 87.66% | 53.90% | `{"MAX_TOKENS": 10, "STOP": 144}` |
| google | `gemini-3.1-pro-preview` | complete | 154 | 154 | 154 | 96.75% | 61.04% | `{"MAX_TOKENS": 5, "STOP": 149}` |
| groq | `llama-3.1-8b-instant` | complete | 154 | 154 | 154 | 41.56% | 16.88% | `{"length": 3, "stop": 151}` |
| groq | `llama-3.3-70b-versatile` | complete | 154 | 154 | 154 | 93.51% | 46.10% | `{"stop": 154}` |
| groq | `meta-llama/llama-4-scout-17b-16e-instruct` | complete | 154 | 154 | 154 | 57.79% | 29.87% | `{"stop": 154}` |
| groq | `openai/gpt-oss-120b` | complete | 154 | 154 | 154 | 88.96% | 51.95% | `{"stop": 154}` |
| groq | `openai/gpt-oss-20b` | complete | 154 | 154 | 154 | 84.42% | 47.40% | `{"length": 5, "stop": 149}` |
| groq | `qwen/qwen3-32b` | complete | 154 | 154 | 154 | 57.14% | 34.42% | `{"length": 39, "stop": 115}` |
| huggingface_router | `Qwen/Qwen3-Coder-Next:novita` | complete | 154 | 154 | 154 | 85.71% | 50.65% | `{"length": 1, "stop": 153}` |
| openai | `gpt-5.4-mini` | complete | 154 | 154 | 154 | 98.05% | 60.39% | `{"completed": 154}` |
| openai | `gpt-5.5` | complete | 154 | 154 | 154 | 96.75% | 60.39% | `{"completed": 153, "incomplete:max_output_tokens": 1}` |
| openai | `gpt-5.6-sol` | complete | 154 | 154 | 154 | 99.35% | 62.99% | `{"completed": 153, "incomplete:max_output_tokens": 1}` |
