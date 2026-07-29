# PQID-Bench External Model Run Matrix

- prompt rows: `154`
- schema version: `pqid-bench-external-model-batch-v1`
- request rows intentionally exclude target metadata
- response templates are empty logs to be filled after actual provider/model calls

| provider | model | API/model ID | role | access path |
| --- | --- | --- | --- | --- |
| openai | GPT-5.6 Sol | `gpt-5.6-sol` | newer OpenAI frontier coding/reasoning comparison | official API |
| openai | GPT-5.5 | `gpt-5.5` | frontier coding/reasoning | official API |
| openai | GPT-5.4 mini | `gpt-5.4-mini` | cost/latency frontier comparison | official API |
| anthropic | Claude Fable 5 | `claude-fable-5` | newer Anthropic frontier coding/reasoning comparison | official API |
| anthropic | Claude Sonnet 4.6 | `claude-sonnet-4-6` | independent frontier coding family | official API |
| anthropic | Claude Opus 4.8 | `claude-opus-4-8` | higher-capability Anthropic frontier comparison | official API |
| google | Gemini 2.5 Pro | `gemini-2.5-pro` | independent frontier coding family | official API |
| google | Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | newer Google frontier coding/reasoning comparison | official API |
| deepseek | DeepSeek V4 Pro | `deepseek-v4-pro` | official DeepSeek frontier coding/reasoning row | DeepSeek official OpenAI-compatible API |
| deepseek | DeepSeek V4 Flash | `deepseek-v4-flash` | official DeepSeek fast/cost frontier comparison | DeepSeek official OpenAI-compatible API |
| groq | Llama 3.3 70B Versatile | `llama-3.3-70b-versatile` | free/low-cost open-weight Llama API bridge | GroqCloud OpenAI-compatible API |
| groq | Qwen3 32B | `qwen/qwen3-32b` | free/low-cost open-weight reasoning/code API bridge | GroqCloud OpenAI-compatible API |
| groq | GPT-OSS 120B | `openai/gpt-oss-120b` | free/low-cost open-weight OpenAI-family API bridge | GroqCloud OpenAI-compatible API |
| groq | Llama 3.1 8B Instant | `llama-3.1-8b-instant` | fast small open-weight API bridge | GroqCloud OpenAI-compatible API |
| groq | GPT-OSS 20B | `openai/gpt-oss-20b` | size-control against GPT-OSS 120B | GroqCloud OpenAI-compatible API |
| groq | Llama 4 Scout 17B 16E Instruct | `meta-llama/llama-4-scout-17b-16e-instruct` | optional newer Llama-family contrast | GroqCloud OpenAI-compatible API |
| github_models | Codestral 25.01 | `mistral-ai/codestral-2501` | GitHub Models code-specialized Mistral contrast | GitHub Models OpenAI-compatible API |

## Primary Source Notes

- `gpt-5.6-sol`: The live OpenAI model catalog lists gpt-5.6-sol for the current project, and a one-request invocation check succeeded on 2026-07-12. Source: https://platform.openai.com/docs/models
- `gpt-5.5`: OpenAI docs list GPT-5.5 as the flagship model for complex reasoning and coding. Source: https://platform.openai.com/docs/models
- `gpt-5.4-mini`: OpenAI docs list GPT-5.4 mini as a lower-cost coding-capable model. Source: https://platform.openai.com/docs/models
- `claude-fable-5`: The live Anthropic model catalog lists Claude Fable 5 for the current account, and a one-request invocation check succeeded on 2026-07-12. Source: https://docs.anthropic.com/en/docs/about-claude/models/overview
- `claude-sonnet-4-6`: Anthropic docs list Claude Sonnet 4.6 with fast comparative latency and extended thinking. Source: https://docs.anthropic.com/en/docs/about-claude/models/overview
- `claude-opus-4-8`: Anthropic docs list Claude Opus 4.8 as the most capable Opus-tier model for complex reasoning and long-horizon agentic coding. Source: https://docs.anthropic.com/en/docs/about-claude/models/overview
- `gemini-2.5-pro`: Google docs describe Gemini 2.5 Pro as an advanced model for complex reasoning and coding. Source: https://ai.google.dev/gemini-api/docs/models
- `gemini-3.1-pro-preview`: Google docs describe Gemini 3.1 Pro Preview as optimized for software-engineering behavior, agentic workflows, and complex problem solving. Source: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview
- `deepseek-v4-pro`: DeepSeek docs list https://api.deepseek.com as the OpenAI-compatible base URL and deepseek-v4-pro as a current model ID. Source: https://api-docs.deepseek.com/
- `deepseek-v4-flash`: DeepSeek docs list https://api.deepseek.com as the OpenAI-compatible base URL and deepseek-v4-flash as a current model ID. Source: https://api-docs.deepseek.com/
- `llama-3.3-70b-versatile`: Groq model docs list llama-3.3-70b-versatile as a production chat model. Source: https://console.groq.com/docs/models
- `qwen/qwen3-32b`: Groq rate-limit docs list qwen/qwen3-32b among free-plan models. Source: https://console.groq.com/docs/rate-limits
- `openai/gpt-oss-120b`: Groq model docs list openai/gpt-oss-120b as a production model. Source: https://console.groq.com/docs/models
- `llama-3.1-8b-instant`: Groq model docs list llama-3.1-8b-instant as a production chat model. Source: https://console.groq.com/docs/models
- `openai/gpt-oss-20b`: Groq model docs list openai/gpt-oss-20b as a production model. Source: https://console.groq.com/docs/models
- `meta-llama/llama-4-scout-17b-16e-instruct`: Groq model docs list Llama 4 Scout as a preview model; report as exploratory if used. Source: https://console.groq.com/docs/models
- `mistral-ai/codestral-2501`: GitHub Models catalog lists Codestral 25.01 as a Mistral AI code-generation model. Source: https://models.github.ai/catalog/models
