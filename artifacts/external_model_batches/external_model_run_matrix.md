# PQID-Bench External Model Run Matrix

- prompt rows: `70`
- schema version: `pqid-bench-external-model-batch-v1`
- request rows intentionally exclude target metadata
- response templates are empty logs to be filled after actual provider/model calls

| provider | model | API/model ID | role | access path |
| --- | --- | --- | --- | --- |
| openai | GPT-5.5 | `gpt-5.5` | frontier coding/reasoning | official API |
| openai | GPT-5.4 mini | `gpt-5.4-mini` | cost/latency frontier comparison | official API |
| anthropic | Claude Sonnet 4.6 | `claude-sonnet-4-6` | independent frontier coding family | official API |
| anthropic | Claude Opus 4.8 | `claude-opus-4-8` | higher-capability Anthropic frontier comparison | official API |
| google | Gemini 2.5 Pro | `gemini-2.5-pro` | independent frontier coding family | official API |
| google | Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | newer Google frontier coding/reasoning comparison | official API |
| huggingface_or_local | Qwen2.5-Coder-7B-Instruct | `Qwen/Qwen2.5-Coder-7B-Instruct` | open reproducible code model | local, HF endpoint, vLLM, or SGLang |
| huggingface_or_local | Qwen2.5-Coder-32B-Instruct | `Qwen/Qwen2.5-Coder-32B-Instruct` | strong open code model | local, HF endpoint, vLLM, or SGLang |
| huggingface_or_local | DeepSeek-Coder-V2-Lite-Instruct | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | open MoE/code-model contrast | local, HF endpoint, vLLM, or SGLang |
| deepseek | DeepSeek V4 Pro | `deepseek-v4-pro` | official DeepSeek frontier coding/reasoning row | DeepSeek official OpenAI-compatible API |
| deepseek | DeepSeek V4 Flash | `deepseek-v4-flash` | official DeepSeek fast/cost frontier comparison | DeepSeek official OpenAI-compatible API |
| groq | Llama 3.3 70B Versatile | `llama-3.3-70b-versatile` | free/low-cost open-weight Llama API bridge | GroqCloud OpenAI-compatible API |
| groq | Qwen3 32B | `qwen/qwen3-32b` | free/low-cost open-weight reasoning/code API bridge | GroqCloud OpenAI-compatible API |
| groq | GPT-OSS 120B | `openai/gpt-oss-120b` | free/low-cost open-weight OpenAI-family API bridge | GroqCloud OpenAI-compatible API |
| groq | Llama 3.1 8B Instant | `llama-3.1-8b-instant` | fast small open-weight API bridge | GroqCloud OpenAI-compatible API |
| groq | GPT-OSS 20B | `openai/gpt-oss-20b` | size-control against GPT-OSS 120B | GroqCloud OpenAI-compatible API |
| groq | Llama 4 Scout 17B 16E Instruct | `meta-llama/llama-4-scout-17b-16e-instruct` | optional newer Llama-family contrast | GroqCloud OpenAI-compatible API |
| huggingface_or_local | Devstral-Small-2-24B-Instruct | `mistralai/Devstral-Small-2-24B-Instruct-2512` | European/open coding-family contrast | local, HF endpoint, vLLM, or SGLang |
| huggingface_or_local | StarCoder2-15B-Instruct | `bigcode/starcoder2-15b-instruct-v0.1` | historical instruction-tuned code-model baseline | local, HF endpoint, vLLM, or SGLang |
| github_models | DeepSeek-V3-0324 | `deepseek/deepseek-v3-0324` | GitHub Models coding-family contrast | GitHub Models OpenAI-compatible API |
| github_models | Codestral 25.01 | `mistral-ai/codestral-2501` | GitHub Models code-specialized Mistral contrast | GitHub Models OpenAI-compatible API |
| nvidia_nim | Qwen2.5-Coder-32B-Instruct (NVIDIA NIM) | `qwen/qwen2.5-coder-32b-instruct` | retired exact hosted Qwen2.5-Coder 32B route | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | Qwen3-Coder-480B-A35B-Instruct (NVIDIA NIM) | `qwen/qwen3-coder-480b-a35b-instruct` | retired hosted Qwen coder successor route | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | CodeGemma 7B (NVIDIA NIM) | `google/codegemma-7b` | live-catalog code-model row; account-blocked | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | DeepSeek-Coder 6.7B Instruct (NVIDIA NIM) | `deepseek-ai/deepseek-coder-6.7b-instruct` | live-catalog DeepSeek-family code row; account-blocked | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | Codestral 22B Instruct (NVIDIA NIM) | `mistralai/codestral-22b-instruct-v0.1` | live-catalog Mistral code row; account-blocked | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | StarCoder2 15B (NVIDIA NIM) | `bigcode/starcoder2-15b` | live-catalog historical code row; endpoint-blocked | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | Granite 34B Code Instruct (NVIDIA NIM) | `ibm/granite-34b-code-instruct` | live-catalog open code row; account-blocked | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | Qwen3 Next 80B A3B Instruct (NVIDIA NIM) | `qwen/qwen3-next-80b-a3b-instruct` | callable Qwen-family non-code sanity row | NVIDIA NIM OpenAI-compatible API |
| nvidia_nim | GPT-OSS 20B (NVIDIA NIM) | `openai/gpt-oss-20b` | callable GPT-OSS provider cross-check | NVIDIA NIM OpenAI-compatible API |
| deepinfra | Qwen2.5-Coder-32B-Instruct (DeepInfra) | `Qwen/Qwen2.5-Coder-32B-Instruct` | exact hosted Qwen2.5-Coder 32B code baseline | DeepInfra OpenAI-compatible API |
| deepinfra | Devstral-Small-2505 (DeepInfra) | `mistralai/Devstral-Small-2505` | European/open coding-family contrast | DeepInfra OpenAI-compatible API |
| deepinfra | StarCoder2-15B-Instruct (DeepInfra) | `bigcode/starcoder2-15b-instruct-v0.1` | historical instruction-tuned code-model baseline | DeepInfra OpenAI-compatible API |
| huggingface_or_local | StarCoder2-15B | `bigcode/starcoder2-15b` | appendix/historical code-model contrast | local, HF endpoint, vLLM, or SGLang |

## Primary Source Notes

- `gpt-5.5`: OpenAI docs list GPT-5.5 as the flagship model for complex reasoning and coding. Source: https://platform.openai.com/docs/models
- `gpt-5.4-mini`: OpenAI docs list GPT-5.4 mini as a lower-cost coding-capable model. Source: https://platform.openai.com/docs/models
- `claude-sonnet-4-6`: Anthropic docs list Claude Sonnet 4.6 with fast comparative latency and extended thinking. Source: https://docs.anthropic.com/en/docs/about-claude/models/overview
- `claude-opus-4-8`: Anthropic docs list Claude Opus 4.8 as the most capable Opus-tier model for complex reasoning and long-horizon agentic coding. Source: https://docs.anthropic.com/en/docs/about-claude/models/overview
- `gemini-2.5-pro`: Google docs describe Gemini 2.5 Pro as an advanced model for complex reasoning and coding. Source: https://ai.google.dev/gemini-api/docs/models
- `gemini-3.1-pro-preview`: Google docs describe Gemini 3.1 Pro Preview as optimized for software-engineering behavior, agentic workflows, and complex problem solving. Source: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview
- `Qwen/Qwen2.5-Coder-7B-Instruct`: Hugging Face model card identifies an instruction-tuned 7B code model. Source: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
- `Qwen/Qwen2.5-Coder-32B-Instruct`: Hugging Face model card identifies an instruction-tuned 32B code model. Source: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
- `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`: Hugging Face model card identifies an instruct code model with OpenAI-compatible serving examples. Source: https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct
- `deepseek-v4-pro`: DeepSeek docs list https://api.deepseek.com as the OpenAI-compatible base URL and deepseek-v4-pro as a current model ID. Source: https://api-docs.deepseek.com/
- `deepseek-v4-flash`: DeepSeek docs list https://api.deepseek.com as the OpenAI-compatible base URL and deepseek-v4-flash as a current model ID. Source: https://api-docs.deepseek.com/
- `llama-3.3-70b-versatile`: Groq model docs list llama-3.3-70b-versatile as a production chat model. Source: https://console.groq.com/docs/models
- `qwen/qwen3-32b`: Groq rate-limit docs list qwen/qwen3-32b among free-plan models. Source: https://console.groq.com/docs/rate-limits
- `openai/gpt-oss-120b`: Groq model docs list openai/gpt-oss-120b as a production model. Source: https://console.groq.com/docs/models
- `llama-3.1-8b-instant`: Groq model docs list llama-3.1-8b-instant as a production chat model. Source: https://console.groq.com/docs/models
- `openai/gpt-oss-20b`: Groq model docs list openai/gpt-oss-20b as a production model. Source: https://console.groq.com/docs/models
- `meta-llama/llama-4-scout-17b-16e-instruct`: Groq model docs list Llama 4 Scout as a preview model; report as exploratory if used. Source: https://console.groq.com/docs/models
- `mistralai/Devstral-Small-2-24B-Instruct-2512`: Hugging Face model card identifies an Apache-2.0 Devstral 24B instruct coding model. Source: https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512
- `bigcode/starcoder2-15b-instruct-v0.1`: Hugging Face model card identifies an instruction-tuned StarCoder2 15B code model. Source: https://huggingface.co/bigcode/starcoder2-15b-instruct-v0.1
- `deepseek/deepseek-v3-0324`: GitHub Models catalog lists DeepSeek-V3-0324 with coding and agent tags. Source: https://models.github.ai/catalog/models
- `mistral-ai/codestral-2501`: GitHub Models catalog lists Codestral 25.01 as a Mistral AI code-generation model. Source: https://models.github.ai/catalog/models
- `qwen/qwen2.5-coder-32b-instruct`: NVIDIA NIM docs list qwen/qwen2.5-coder-32b-instruct, but a live smoke call on 2026-06-18 returned HTTP 410 because the model reached end of life on 2026-05-12. Source: https://docs.api.nvidia.com/nim/reference/qwen-qwen2_5-coder-32b-instruct-infer
- `qwen/qwen3-coder-480b-a35b-instruct`: NVIDIA NIM docs list qwen/qwen3-coder-480b-a35b-instruct, but a live smoke call on 2026-06-18 returned HTTP 410 because the model reached end of life on 2026-06-11. Source: https://docs.api.nvidia.com/nim/reference/qwen-qwen3-coder-480b-a35b-instruct-infer
- `google/codegemma-7b`: NVIDIA NIM model docs and the live /v1/models endpoint list google/codegemma-7b, but one-row smoke returned account/function 404 for the current key. Source: https://docs.api.nvidia.com/nim/reference/models-1
- `deepseek-ai/deepseek-coder-6.7b-instruct`: The live NVIDIA NIM /v1/models endpoint listed deepseek-ai/deepseek-coder-6.7b-instruct on 2026-06-18, but one-row smoke returned account/function 404 for the current key. Source: https://integrate.api.nvidia.com/v1/models
- `mistralai/codestral-22b-instruct-v0.1`: The live NVIDIA NIM /v1/models endpoint listed mistralai/codestral-22b-instruct-v0.1 on 2026-06-18, but one-row smoke returned account/function 404 for the current key. Source: https://integrate.api.nvidia.com/v1/models
- `bigcode/starcoder2-15b`: The live NVIDIA NIM /v1/models endpoint listed bigcode/starcoder2-15b on 2026-06-18, but one-row smoke returned 404 for the current key. Source: https://integrate.api.nvidia.com/v1/models
- `ibm/granite-34b-code-instruct`: The live NVIDIA NIM /v1/models endpoint listed ibm/granite-34b-code-instruct on 2026-06-18, but one-row smoke returned account/function 404 for the current key. Source: https://integrate.api.nvidia.com/v1/models
- `qwen/qwen3-next-80b-a3b-instruct`: The live NVIDIA NIM /v1/models endpoint listed qwen/qwen3-next-80b-a3b-instruct on 2026-06-18, and one-row smoke succeeded with finish_reason=stop. Source: https://integrate.api.nvidia.com/v1/models
- `openai/gpt-oss-20b`: The live NVIDIA NIM /v1/models endpoint listed openai/gpt-oss-20b on 2026-06-18, and one-row smoke succeeded with finish_reason=stop. Source: https://integrate.api.nvidia.com/v1/models
- `Qwen/Qwen2.5-Coder-32B-Instruct`: DeepInfra docs expose Qwen/Qwen2.5-Coder-32B-Instruct through an OpenAI-compatible chat-completions endpoint. Source: https://deepinfra.com/Qwen/Qwen2.5-Coder-32B-Instruct/api
- `mistralai/Devstral-Small-2505`: DeepInfra docs expose mistralai/Devstral-Small-2505 through an OpenAI-compatible chat-completions endpoint. Source: https://deepinfra.com/mistralai/Devstral-Small-2505/api
- `bigcode/starcoder2-15b-instruct-v0.1`: DeepInfra docs expose bigcode/starcoder2-15b-instruct-v0.1 through an OpenAI-compatible chat-completions endpoint, with a low-usage redirect warning that must be checked before reporting. Source: https://deepinfra.com/bigcode/starcoder2-15b-instruct-v0.1/api
- `bigcode/starcoder2-15b`: Hugging Face model card identifies a 15B code model; use as appendix because it is not the main instruction-tuned baseline. Source: https://huggingface.co/bigcode/starcoder2-15b
