"""Export traceable external-model request and response-log templates.

This script does not call provider APIs. It converts the frozen PQID-Bench
held-out prompt manifest into per-model request JSONL files and matching
response templates. The request rows intentionally omit target metadata; the
original prompt manifest keeps target metadata only for downstream scoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
DEFAULT_PROMPT_PATH = ARTIFACTS_DIR / "pqid_bench_external_generation_prompts.jsonl"
DEFAULT_OUTPUT_DIR = ARTIFACTS_DIR / "external_model_batches"
HARNESS_SCRIPT = SUBMISSION_DIR / "scripts" / "run_pqid_bench_external_model_generation_harness.py"

SCHEMA_VERSION = "pqid-bench-external-model-batch-v1"

CORE_TARGETS = [
    {
        "provider": "openai",
        "model_label": "GPT-5.6 Sol",
        "api_model_id": "gpt-5.6-sol",
        "role": "newer OpenAI frontier coding/reasoning comparison",
        "access_path": "official API",
        "request_family": "openai_responses",
        "source_url": "https://platform.openai.com/docs/models",
        "source_note": "The live OpenAI model catalog lists gpt-5.6-sol for the current project, and a one-request invocation check succeeded on 2026-07-12.",
    },
    {
        "provider": "openai",
        "model_label": "GPT-5.5",
        "api_model_id": "gpt-5.5",
        "role": "frontier coding/reasoning",
        "access_path": "official API",
        "request_family": "openai_responses",
        "source_url": "https://platform.openai.com/docs/models",
        "source_note": "OpenAI docs list GPT-5.5 as the flagship model for complex reasoning and coding.",
    },
    {
        "provider": "openai",
        "model_label": "GPT-5.4 mini",
        "api_model_id": "gpt-5.4-mini",
        "role": "cost/latency frontier comparison",
        "access_path": "official API",
        "request_family": "openai_responses",
        "source_url": "https://platform.openai.com/docs/models",
        "source_note": "OpenAI docs list GPT-5.4 mini as a lower-cost coding-capable model.",
    },
    {
        "provider": "anthropic",
        "model_label": "Claude Fable 5",
        "api_model_id": "claude-fable-5",
        "role": "newer Anthropic frontier coding/reasoning comparison",
        "access_path": "official API",
        "request_family": "anthropic_messages",
        "source_url": "https://docs.anthropic.com/en/docs/about-claude/models/overview",
        "source_note": "The live Anthropic model catalog lists Claude Fable 5 for the current account, and a one-request invocation check succeeded on 2026-07-12.",
        "omit_sampling_controls": True,
    },
    {
        "provider": "anthropic",
        "model_label": "Claude Sonnet 4.6",
        "api_model_id": "claude-sonnet-4-6",
        "role": "independent frontier coding family",
        "access_path": "official API",
        "request_family": "anthropic_messages",
        "source_url": "https://docs.anthropic.com/en/docs/about-claude/models/overview",
        "source_note": "Anthropic docs list Claude Sonnet 4.6 with fast comparative latency and extended thinking.",
    },
    {
        "provider": "anthropic",
        "model_label": "Claude Opus 4.8",
        "api_model_id": "claude-opus-4-8",
        "role": "higher-capability Anthropic frontier comparison",
        "access_path": "official API",
        "request_family": "anthropic_messages",
        "source_url": "https://docs.anthropic.com/en/docs/about-claude/models/overview",
        "source_note": "Anthropic docs list Claude Opus 4.8 as the most capable Opus-tier model for complex reasoning and long-horizon agentic coding.",
    },
    {
        "provider": "google",
        "model_label": "Gemini 2.5 Pro",
        "api_model_id": "gemini-2.5-pro",
        "role": "independent frontier coding family",
        "access_path": "official API",
        "request_family": "gemini_generate_content",
        "source_url": "https://ai.google.dev/gemini-api/docs/models",
        "source_note": "Google docs describe Gemini 2.5 Pro as an advanced model for complex reasoning and coding.",
    },
    {
        "provider": "google",
        "model_label": "Gemini 3.1 Pro Preview",
        "api_model_id": "gemini-3.1-pro-preview",
        "role": "newer Google frontier coding/reasoning comparison",
        "access_path": "official API",
        "request_family": "gemini_generate_content",
        "source_url": "https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview",
        "source_note": "Google docs describe Gemini 3.1 Pro Preview as optimized for software-engineering behavior, agentic workflows, and complex problem solving.",
    },
    {
        "provider": "huggingface_or_local",
        "model_label": "Qwen2.5-Coder-7B-Instruct",
        "api_model_id": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "role": "open reproducible code model",
        "access_path": "local, HF endpoint, vLLM, or SGLang",
        "request_family": "openai_compatible_chat",
        "source_url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct",
        "source_note": "Hugging Face model card identifies an instruction-tuned 7B code model.",
    },
    {
        "provider": "huggingface_or_local",
        "model_label": "Qwen2.5-Coder-32B-Instruct",
        "api_model_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "role": "strong open code model",
        "access_path": "local, HF endpoint, vLLM, or SGLang",
        "request_family": "openai_compatible_chat",
        "source_url": "https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct",
        "source_note": "Hugging Face model card identifies an instruction-tuned 32B code model.",
    },
    {
        "provider": "huggingface_or_local",
        "model_label": "DeepSeek-Coder-V2-Lite-Instruct",
        "api_model_id": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        "role": "open MoE/code-model contrast",
        "access_path": "local, HF endpoint, vLLM, or SGLang",
        "request_family": "openai_compatible_chat",
        "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        "source_note": "Hugging Face model card identifies an instruct code model with OpenAI-compatible serving examples.",
    },
]

OFFICIAL_DEEPSEEK_TARGETS = [
    {
        "provider": "deepseek",
        "model_label": "DeepSeek V4 Pro",
        "api_model_id": "deepseek-v4-pro",
        "role": "official DeepSeek frontier coding/reasoning row",
        "access_path": "DeepSeek official OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "reasoning_effort": "high",
        "extra_body": {"thinking": {"type": "enabled"}},
        "source_url": "https://api-docs.deepseek.com/",
        "source_note": "DeepSeek docs list https://api.deepseek.com as the OpenAI-compatible base URL and deepseek-v4-pro as a current model ID.",
    },
    {
        "provider": "deepseek",
        "model_label": "DeepSeek V4 Flash",
        "api_model_id": "deepseek-v4-flash",
        "role": "official DeepSeek fast/cost frontier comparison",
        "access_path": "DeepSeek official OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "reasoning_effort": "high",
        "extra_body": {"thinking": {"type": "enabled"}},
        "source_url": "https://api-docs.deepseek.com/",
        "source_note": "DeepSeek docs list https://api.deepseek.com as the OpenAI-compatible base URL and deepseek-v4-flash as a current model ID.",
    },
]

BRIDGE_TARGETS = [
    {
        "provider": "groq",
        "model_label": "Llama 3.3 70B Versatile",
        "api_model_id": "llama-3.3-70b-versatile",
        "role": "free/low-cost open-weight Llama API bridge",
        "access_path": "GroqCloud OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://console.groq.com/docs/models",
        "source_note": "Groq model docs list llama-3.3-70b-versatile as a production chat model.",
    },
    {
        "provider": "groq",
        "model_label": "Qwen3 32B",
        "api_model_id": "qwen/qwen3-32b",
        "role": "free/low-cost open-weight reasoning/code API bridge",
        "access_path": "GroqCloud OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://console.groq.com/docs/rate-limits",
        "source_note": "Groq rate-limit docs list qwen/qwen3-32b among free-plan models.",
    },
    {
        "provider": "groq",
        "model_label": "GPT-OSS 120B",
        "api_model_id": "openai/gpt-oss-120b",
        "role": "free/low-cost open-weight OpenAI-family API bridge",
        "access_path": "GroqCloud OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://console.groq.com/docs/models",
        "source_note": "Groq model docs list openai/gpt-oss-120b as a production model.",
    },
    {
        "provider": "groq",
        "model_label": "Llama 3.1 8B Instant",
        "api_model_id": "llama-3.1-8b-instant",
        "role": "fast small open-weight API bridge",
        "access_path": "GroqCloud OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://console.groq.com/docs/models",
        "source_note": "Groq model docs list llama-3.1-8b-instant as a production chat model.",
    },
]

OPEN_BREADTH_TARGETS = [
    {
        "provider": "huggingface_router",
        "model_label": "Qwen3-Coder-Next",
        "api_model_id": "Qwen/Qwen3-Coder-Next:novita",
        "role": "current open-weight code-specialized comparison",
        "access_path": "Hugging Face Inference Providers routed to Novita",
        "request_family": "openai_compatible_chat",
        "source_url": "https://huggingface.co/Qwen/Qwen3-Coder-Next",
        "source_note": "The official model card identifies Qwen3-Coder-Next as an open-weight coding-agent model and lists Novita as its hosted Inference Provider.",
    },
    {
        "provider": "groq",
        "model_label": "GPT-OSS 20B",
        "api_model_id": "openai/gpt-oss-20b",
        "role": "size-control against GPT-OSS 120B",
        "access_path": "GroqCloud OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://console.groq.com/docs/models",
        "source_note": "Groq model docs list openai/gpt-oss-20b as a production model.",
    },
    {
        "provider": "groq",
        "model_label": "Llama 4 Scout 17B 16E Instruct",
        "api_model_id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "role": "optional newer Llama-family contrast",
        "access_path": "GroqCloud OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://console.groq.com/docs/models",
        "source_note": "Groq model docs list Llama 4 Scout as a preview model; report as exploratory if used.",
    },
    {
        "provider": "huggingface_or_local",
        "model_label": "Devstral-Small-2-24B-Instruct",
        "api_model_id": "mistralai/Devstral-Small-2-24B-Instruct-2512",
        "role": "European/open coding-family contrast",
        "access_path": "local, HF endpoint, vLLM, or SGLang",
        "request_family": "openai_compatible_chat",
        "source_url": "https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512",
        "source_note": "Hugging Face model card identifies an Apache-2.0 Devstral 24B instruct coding model.",
    },
    {
        "provider": "huggingface_or_local",
        "model_label": "StarCoder2-15B-Instruct",
        "api_model_id": "bigcode/starcoder2-15b-instruct-v0.1",
        "role": "historical instruction-tuned code-model baseline",
        "access_path": "local, HF endpoint, vLLM, or SGLang",
        "request_family": "openai_compatible_chat",
        "source_url": "https://huggingface.co/bigcode/starcoder2-15b-instruct-v0.1",
        "source_note": "Hugging Face model card identifies an instruction-tuned StarCoder2 15B code model.",
    },
]

QISKIT_SPECIALIST_TARGETS = [
    {
        "provider": "huggingface_router",
        "model_label": "Mistral Small 3.2 24B Qiskit",
        "api_model_id": "Qiskit/mistral-small-3.2-24b-qiskit:featherless-ai",
        "role": "official Qiskit-specialized transfer baseline",
        "access_path": "Hugging Face Inference Providers routed to Featherless AI",
        "request_family": "openai_compatible_completion",
        "source_url": "https://huggingface.co/Qiskit/mistral-small-3.2-24b-qiskit",
        "source_note": "The official Qiskit model card identifies a 24B Mistral model specialized with Qiskit code and instruction-tuning data and lists Featherless AI as an inference provider.",
    },
]

GITHUB_MODELS_TARGETS = [
    {
        "provider": "github_models",
        "model_label": "Llama 3.1 405B Instruct",
        "api_model_id": "meta/meta-llama-3.1-405b-instruct",
        "role": "Meta dense flagship-scale control",
        "access_path": "GitHub Models OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://models.github.ai/catalog/models",
        "source_note": "GitHub Models lists Meta-Llama-3.1-405B-Instruct as a text-output model with a 131,072-token input limit.",
    },
    {
        "provider": "github_models",
        "model_label": "Llama 4 Maverick 17B 128E Instruct FP8",
        "api_model_id": "meta/llama-4-maverick-17b-128e-instruct-fp8",
        "role": "Meta Llama 4 mixture-of-experts comparison",
        "access_path": "GitHub Models OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://models.github.ai/catalog/models",
        "source_note": "GitHub Models lists Llama 4 Maverick 17B 128E Instruct FP8 as a Meta multimodal model with text output and a 1,000,000-token input limit.",
    },
    {
        "provider": "github_models",
        "model_label": "DeepSeek-V3-0324",
        "api_model_id": "deepseek/deepseek-v3-0324",
        "role": "GitHub Models coding-family contrast",
        "access_path": "GitHub Models OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://models.github.ai/catalog/models",
        "source_note": "GitHub Models catalog lists DeepSeek-V3-0324 with coding and agent tags.",
    },
    {
        "provider": "github_models",
        "model_label": "Codestral 25.01",
        "api_model_id": "mistral-ai/codestral-2501",
        "role": "GitHub Models code-specialized Mistral contrast",
        "access_path": "GitHub Models OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://models.github.ai/catalog/models",
        "source_note": "GitHub Models catalog lists Codestral 25.01 as a Mistral AI code-generation model.",
    },
]

META_MODEL_API_TARGETS = [
    {
        "provider": "meta_model_api",
        "model_label": "Muse Spark 1.1",
        "api_model_id": "muse-spark-1.1",
        "role": "current proprietary Meta frontier coding and reasoning comparison",
        "access_path": "Meta Model API public preview",
        "request_family": "openai_compatible_chat",
        "source_url": "https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/",
        "source_note": "Meta announces Muse Spark 1.1 through the OpenAI-compatible Meta Model API public preview. Confirm the exact API model identifier and base URL in the authenticated developer console before the smoke run.",
    },
]

OPENROUTER_TARGETS = [
    {
        "provider": "openrouter",
        "model_label": "Mistral Small 3.2 24B Instruct 2506 (OpenRouter/Mistral)",
        "api_model_id": "mistralai/mistral-small-3.2-24b-instruct",
        "role": "exact parent-model control for the Qiskit-specialized Mistral row",
        "access_path": "OpenRouter OpenAI-compatible API pinned to Mistral",
        "request_family": "openai_compatible_chat",
        "source_url": "https://openrouter.ai/mistralai/mistral-small-3.2-24b-instruct/providers",
        "source_note": "The Qiskit model card identifies Mistral-Small-3.2-24B-Instruct-2506 as the exact parent checkpoint. OpenRouter listed a live Mistral-hosted endpoint for that checkpoint on 2026-07-14. Provider fallback is disabled so all responses use one serving backend.",
        "extra_body": {
            "provider": {
                "only": ["mistral"],
                "allow_fallbacks": False,
                "require_parameters": True,
                "data_collection": "deny",
            }
        },
    },
    {
        "provider": "openrouter",
        "model_label": "Llama 4 Maverick 17B 128E Instruct (OpenRouter/DeepInfra)",
        "api_model_id": "meta-llama/llama-4-maverick",
        "role": "Meta Llama 4 mixture-of-experts comparison through a fixed OpenRouter endpoint",
        "access_path": "OpenRouter OpenAI-compatible API pinned to DeepInfra",
        "request_family": "openai_compatible_chat",
        "source_url": "https://openrouter.ai/meta-llama/llama-4-maverick/providers",
        "source_note": "OpenRouter listed the exact Maverick model with a live DeepInfra endpoint on 2026-07-13. Provider fallback is disabled so all 154 responses use one serving backend.",
        "extra_body": {
            "provider": {
                "only": ["deepinfra"],
                "allow_fallbacks": False,
                "require_parameters": True,
                "data_collection": "deny",
            }
        },
    },
]

NVIDIA_NIM_TARGETS = [
    {
        "provider": "nvidia_nim",
        "model_label": "Llama 4 Maverick 17B 128E Instruct (NVIDIA API Catalog)",
        "api_model_id": "meta/llama-4-maverick-17b-128e-instruct",
        "role": "Meta Llama 4 mixture-of-experts comparison through NVIDIA",
        "access_path": "NVIDIA API Catalog OpenAI-compatible endpoint",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA API Catalog listed meta/llama-4-maverick-17b-128e-instruct on 2026-07-13. This provider-specific run is kept separate from the GitHub Models FP8 route.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "Qwen2.5-Coder-32B-Instruct (NVIDIA NIM)",
        "api_model_id": "qwen/qwen2.5-coder-32b-instruct",
        "role": "retired exact hosted Qwen2.5-Coder 32B route",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://docs.api.nvidia.com/nim/reference/qwen-qwen2_5-coder-32b-instruct-infer",
        "source_note": "NVIDIA NIM docs list qwen/qwen2.5-coder-32b-instruct, but a live smoke call on 2026-06-18 returned HTTP 410 because the model reached end of life on 2026-05-12.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "Qwen3-Coder-480B-A35B-Instruct (NVIDIA NIM)",
        "api_model_id": "qwen/qwen3-coder-480b-a35b-instruct",
        "role": "retired hosted Qwen coder successor route",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://docs.api.nvidia.com/nim/reference/qwen-qwen3-coder-480b-a35b-instruct-infer",
        "source_note": "NVIDIA NIM docs list qwen/qwen3-coder-480b-a35b-instruct, but a live smoke call on 2026-06-18 returned HTTP 410 because the model reached end of life on 2026-06-11.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "CodeGemma 7B (NVIDIA NIM)",
        "api_model_id": "google/codegemma-7b",
        "role": "live-catalog code-model row; account-blocked",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://docs.api.nvidia.com/nim/reference/models-1",
        "source_note": "NVIDIA NIM model docs and the live /v1/models endpoint list google/codegemma-7b, but one-row smoke returned account/function 404 for the current key.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "DeepSeek-Coder 6.7B Instruct (NVIDIA NIM)",
        "api_model_id": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "role": "live-catalog DeepSeek-family code row; account-blocked",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA NIM /v1/models endpoint listed deepseek-ai/deepseek-coder-6.7b-instruct on 2026-06-18, but one-row smoke returned account/function 404 for the current key.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "Codestral 22B Instruct (NVIDIA NIM)",
        "api_model_id": "mistralai/codestral-22b-instruct-v0.1",
        "role": "live-catalog Mistral code row; account-blocked",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA NIM /v1/models endpoint listed mistralai/codestral-22b-instruct-v0.1 on 2026-06-18, but one-row smoke returned account/function 404 for the current key.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "StarCoder2 15B (NVIDIA NIM)",
        "api_model_id": "bigcode/starcoder2-15b",
        "role": "live-catalog historical code row; endpoint-blocked",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA NIM /v1/models endpoint listed bigcode/starcoder2-15b on 2026-06-18, but one-row smoke returned 404 for the current key.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "Granite 34B Code Instruct (NVIDIA NIM)",
        "api_model_id": "ibm/granite-34b-code-instruct",
        "role": "live-catalog open code row; account-blocked",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA NIM /v1/models endpoint listed ibm/granite-34b-code-instruct on 2026-06-18, but one-row smoke returned account/function 404 for the current key.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "Qwen3 Next 80B A3B Instruct (NVIDIA NIM)",
        "api_model_id": "qwen/qwen3-next-80b-a3b-instruct",
        "role": "callable Qwen-family non-code sanity row",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA NIM /v1/models endpoint listed qwen/qwen3-next-80b-a3b-instruct on 2026-06-18, and one-row smoke succeeded with finish_reason=stop.",
    },
    {
        "provider": "nvidia_nim",
        "model_label": "GPT-OSS 20B (NVIDIA NIM)",
        "api_model_id": "openai/gpt-oss-20b",
        "role": "callable GPT-OSS provider cross-check",
        "access_path": "NVIDIA NIM OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://integrate.api.nvidia.com/v1/models",
        "source_note": "The live NVIDIA NIM /v1/models endpoint listed openai/gpt-oss-20b on 2026-06-18, and one-row smoke succeeded with finish_reason=stop.",
    },
]

DEEPINFRA_TARGETS = [
    {
        "provider": "deepinfra",
        "model_label": "Qwen2.5-Coder-32B-Instruct (DeepInfra)",
        "api_model_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "role": "exact hosted Qwen2.5-Coder 32B code baseline",
        "access_path": "DeepInfra OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://deepinfra.com/Qwen/Qwen2.5-Coder-32B-Instruct/api",
        "source_note": "DeepInfra docs expose Qwen/Qwen2.5-Coder-32B-Instruct through an OpenAI-compatible chat-completions endpoint.",
    },
    {
        "provider": "deepinfra",
        "model_label": "Devstral-Small-2505 (DeepInfra)",
        "api_model_id": "mistralai/Devstral-Small-2505",
        "role": "European/open coding-family contrast",
        "access_path": "DeepInfra OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://deepinfra.com/mistralai/Devstral-Small-2505/api",
        "source_note": "DeepInfra docs expose mistralai/Devstral-Small-2505 through an OpenAI-compatible chat-completions endpoint.",
    },
    {
        "provider": "deepinfra",
        "model_label": "StarCoder2-15B-Instruct (DeepInfra)",
        "api_model_id": "bigcode/starcoder2-15b-instruct-v0.1",
        "role": "historical instruction-tuned code-model baseline",
        "access_path": "DeepInfra OpenAI-compatible API",
        "request_family": "openai_compatible_chat",
        "source_url": "https://deepinfra.com/bigcode/starcoder2-15b-instruct-v0.1/api",
        "source_note": "DeepInfra docs expose bigcode/starcoder2-15b-instruct-v0.1 through an OpenAI-compatible chat-completions endpoint, with a low-usage redirect warning that must be checked before reporting.",
    },
]

APPENDIX_TARGETS = [
    {
        "provider": "huggingface_or_local",
        "model_label": "StarCoder2-15B",
        "api_model_id": "bigcode/starcoder2-15b",
        "role": "appendix/historical code-model contrast",
        "access_path": "local, HF endpoint, vLLM, or SGLang",
        "request_family": "openai_compatible_completion",
        "source_url": "https://huggingface.co/bigcode/starcoder2-15b",
        "source_note": "Hugging Face model card identifies a 15B code model; use as appendix because it is not the main instruction-tuned baseline.",
    },
]


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    value = value.replace("/", "_").replace(".", "_")
    value = re.sub(r"[^A-Za-z0-9_+-]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_").lower()


def model_input(prompt: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "prompt": prompt["prompt"],
        "messages": prompt["messages"],
    }


def request_body(
    target: dict[str, str],
    prompt: dict[str, Any],
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    anthropic_effort: str = "",
    frequency_penalty: float | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    messages = prompt["messages"]
    system_message = messages[0]["content"]
    user_message = messages[1]["content"]
    model_id = target["api_model_id"]
    request_family = target["request_family"]

    if request_family == "openai_responses":
        # Current GPT-5.x Responses API models reject explicit sampling
        # controls such as temperature. Keep these rows at provider defaults
        # and record the requested policy in the surrounding traceability row.
        return {
            "model": model_id,
            "input": messages,
            "max_output_tokens": max_output_tokens,
        }
    if request_family == "anthropic_messages":
        body = {
            "model": model_id,
            "system": system_message,
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": max_output_tokens,
        }
        if not target.get("omit_sampling_controls"):
            body.update({"temperature": temperature, "top_p": top_p})
        if anthropic_effort:
            body["output_config"] = {"effort": anthropic_effort}
        return body
    if request_family == "gemini_generate_content":
        return {
            "model": model_id,
            "system_instruction": {"parts": [{"text": system_message}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generation_config": {
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_output_tokens,
            },
        }
    if request_family == "openai_compatible_completion":
        return {
            "model": model_id,
            "prompt": prompt["prompt"],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_output_tokens,
        }
    body = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_output_tokens,
    }
    if frequency_penalty is not None:
        body["frequency_penalty"] = frequency_penalty
    if seed is not None:
        body["seed"] = seed
    if "reasoning_effort" in target:
        body["reasoning_effort"] = target["reasoning_effort"]
    if "extra_body" in target:
        body["extra_body"] = target["extra_body"]
    return body


def request_row(
    target: dict[str, str],
    prompt: dict[str, Any],
    generation_config: dict[str, Any],
    exported_at_utc: str,
) -> dict[str, Any]:
    target_slug = slugify(f"{target['provider']}_{target['api_model_id']}")
    run_id = f"{target_slug}_single_pass_temp0"
    model_input_payload = model_input(prompt)
    body = request_body(
        target=target,
        prompt=prompt,
        temperature=generation_config["temperature"],
        top_p=generation_config["top_p"],
        max_output_tokens=generation_config["max_output_tokens"],
        anthropic_effort=str(generation_config.get("anthropic_effort") or ""),
        frequency_penalty=generation_config.get("frequency_penalty"),
        seed=generation_config.get("seed"),
    )
    request_payload = {
        "provider": target["provider"],
        "api_model_id": target["api_model_id"],
        "request_family": target["request_family"],
        "body": body,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_request",
        "run_id": run_id,
        "provider": target["provider"],
        "model_label": target["model_label"],
        "model": target["api_model_id"],
        "api_model_id": target["api_model_id"],
        "model_role": target["role"],
        "access_path": target["access_path"],
        "request_family": target["request_family"],
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "model_input": model_input_payload,
        "request_body": body,
        "generation_config": generation_config,
        "exported_at_utc": exported_at_utc,
        "prompt_record_sha256": sha256_text(stable_json(prompt)),
        "model_input_sha256": sha256_text(stable_json(model_input_payload)),
        "request_sha256": sha256_text(stable_json(request_payload)),
        "target_metadata_policy": "not included in request; retained only in frozen prompt manifest for scoring",
    }


def response_template_row(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": request["provider"],
        "model": request["model"],
        "api_model_id": request["api_model_id"],
        "model_label": request["model_label"],
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request["request_sha256"],
        "model_input_sha256": request["model_input_sha256"],
        "prompt_record_sha256": request["prompt_record_sha256"],
        "generation_config": request["generation_config"],
        "created_at_utc": "",
        "request_id": "",
        "system_fingerprint": "",
        "model_snapshot": "",
        "finish_reason": "",
        "usage": {},
        "provider_metadata": {},
        "generated_code": "",
        "raw_response": "",
    }


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def matrix_rows(targets: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "provider": target["provider"],
            "model_label": target["model_label"],
            "api_model_id": target["api_model_id"],
            "role": target["role"],
            "access_path": target["access_path"],
            "request_family": target["request_family"],
            "source_url": target["source_url"],
            "source_note": target["source_note"],
        }
        for target in targets
    ]


def write_matrix_md(path: Path, targets: list[dict[str, str]], prompt_count: int) -> None:
    lines = [
        "# PQID-Bench External Model Run Matrix",
        "",
        f"- prompt rows: `{prompt_count}`",
        f"- schema version: `{SCHEMA_VERSION}`",
        "- request rows intentionally exclude target metadata",
        "- response templates are empty logs to be filled after actual provider/model calls",
        "",
        "| provider | model | API/model ID | role | access path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for target in targets:
        lines.append(
            f"| {target['provider']} | {target['model_label']} | `{target['api_model_id']}` | "
            f"{target['role']} | {target['access_path']} |"
        )
    lines.extend(
        [
            "",
            "## Primary Source Notes",
            "",
        ]
    )
    for target in targets:
        lines.append(f"- `{target['api_model_id']}`: {target['source_note']} Source: {target['source_url']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_traceability_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench External Model Traceability Manifest",
        "",
        f"- exported at UTC: `{manifest['exported_at_utc']}`",
        f"- prompt manifest: `{manifest['prompt_manifest']['path']}`",
        f"- prompt manifest SHA-256: `{manifest['prompt_manifest']['sha256']}`",
        f"- prompt rows: `{manifest['prompt_count']}`",
        f"- generation config: `{stable_json(manifest['generation_config'])}`",
        "",
        "## Files",
        "",
        "| kind | path | SHA-256 | rows |",
        "| --- | --- | --- | ---: |",
    ]
    for entry in manifest["files"]:
        lines.append(
            f"| {entry['kind']} | `{entry['path']}` | `{entry['sha256']}` | {entry.get('rows', '')} |"
        )
    lines.extend(
        [
            "",
            "## Evaluation Commands",
            "",
        ]
    )
    for command in manifest["evaluation_commands"]:
        lines.append(f"- `{command}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_batches(
    prompt_path: Path,
    output_dir: Path,
    include_bridge: bool,
    include_official_deepseek: bool,
    include_open_breadth: bool,
    include_qiskit_specialist: bool,
    include_github_models: bool,
    include_meta_model_api: bool,
    include_openrouter: bool,
    include_nvidia_nim: bool,
    include_deepinfra: bool,
    include_appendix: bool,
    overwrite_existing: bool,
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    anthropic_effort: str = "",
    frequency_penalty: float | None = None,
    seed: int | None = None,
    only_targets: list[str] | None = None,
) -> None:
    prompts = iter_jsonl(prompt_path)
    if not prompts:
        raise ValueError(f"No prompts found in {prompt_path}")

    targets = (
        CORE_TARGETS
        + (OFFICIAL_DEEPSEEK_TARGETS if include_official_deepseek else [])
        + (BRIDGE_TARGETS if include_bridge else [])
        + (OPEN_BREADTH_TARGETS if include_open_breadth else [])
        + (QISKIT_SPECIALIST_TARGETS if include_qiskit_specialist else [])
        + (GITHUB_MODELS_TARGETS if include_github_models else [])
        + (META_MODEL_API_TARGETS if include_meta_model_api else [])
        + (OPENROUTER_TARGETS if include_openrouter else [])
        + (NVIDIA_NIM_TARGETS if include_nvidia_nim else [])
        + (DEEPINFRA_TARGETS if include_deepinfra else [])
        + (APPENDIX_TARGETS if include_appendix else [])
    )
    if only_targets:
        requested = set(only_targets)
        available = {f"{target['provider']}:{target['api_model_id']}" for target in targets}
        missing = sorted(requested - available)
        if missing:
            raise ValueError(f"Requested targets are not enabled by the selected include flags: {missing}")
        targets = [
            target
            for target in targets
            if f"{target['provider']}:{target['api_model_id']}" in requested
        ]
    exported_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_output_tokens,
        "n": 1,
        "single_pass": True,
    }
    if anthropic_effort:
        generation_config["anthropic_effort"] = anthropic_effort
    if frequency_penalty is not None:
        generation_config["frequency_penalty"] = frequency_penalty
    if seed is not None:
        generation_config["seed"] = seed

    requests_dir = output_dir / "requests"
    responses_dir = output_dir / "responses"
    manifests_dir = output_dir / "manifests"
    evaluations_dir = output_dir / "evaluations"
    written_files: list[dict[str, Any]] = []
    evaluation_commands: list[str] = []

    for target in targets:
        target_slug = slugify(f"{target['provider']}_{target['api_model_id']}")
        request_rows = [
            request_row(
                target=target,
                prompt=prompt,
                generation_config=generation_config,
                exported_at_utc=exported_at_utc,
            )
            for prompt in prompts
        ]
        response_rows = [response_template_row(row) for row in request_rows]
        request_path = requests_dir / f"{target_slug}_requests.jsonl"
        response_template_path = responses_dir / f"{target_slug}_responses_template.jsonl"
        response_path = responses_dir / f"{target_slug}_responses.jsonl"
        evaluation_dir = evaluations_dir / target_slug

        if overwrite_existing or not request_path.exists():
            write_jsonl(request_path, request_rows)
        if overwrite_existing or not response_template_path.exists():
            write_jsonl(response_template_path, response_rows)

        written_files.extend(
            [
                {
                    "kind": "request_jsonl",
                    "provider": target["provider"],
                    "model": target["api_model_id"],
                    "path": display_path(request_path),
                    "sha256": sha256_file(request_path),
                    "rows": len(request_rows),
                },
                {
                    "kind": "response_template_jsonl",
                    "provider": target["provider"],
                    "model": target["api_model_id"],
                    "path": display_path(response_template_path),
                    "sha256": sha256_file(response_template_path),
                    "rows": len(response_rows),
                },
            ]
        )
        evaluation_commands.append(
            "python scripts/run_pqid_bench_external_model_generation_harness.py "
            f"--prompt-path {display_path(prompt_path)} "
            f"--template-path {display_path(response_template_path)} "
            f"--response-path {display_path(response_path)} "
            f"--output-dir {display_path(evaluation_dir)}"
        )

    matrix_json_path = output_dir / "external_model_run_matrix.json"
    matrix_md_path = output_dir / "external_model_run_matrix.md"
    write_json(matrix_json_path, matrix_rows(targets))
    write_matrix_md(matrix_md_path, targets, prompt_count=len(prompts))
    written_files.extend(
        [
            {
                "kind": "model_matrix_json",
                "path": display_path(matrix_json_path),
                "sha256": sha256_file(matrix_json_path),
                "rows": len(targets),
            },
            {
                "kind": "model_matrix_md",
                "path": display_path(matrix_md_path),
                "sha256": sha256_file(matrix_md_path),
                "rows": len(targets),
            },
        ]
    )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "exported_at_utc": exported_at_utc,
        "prompt_manifest": {
            "path": display_path(prompt_path),
            "sha256": sha256_file(prompt_path),
        },
        "prompt_count": len(prompts),
        "target_count": len(targets),
        "include_bridge": include_bridge,
        "include_official_deepseek": include_official_deepseek,
        "include_open_breadth": include_open_breadth,
        "include_qiskit_specialist": include_qiskit_specialist,
        "include_github_models": include_github_models,
        "include_meta_model_api": include_meta_model_api,
        "include_nvidia_nim": include_nvidia_nim,
        "include_deepinfra": include_deepinfra,
        "include_appendix": include_appendix,
        "overwrite_existing": overwrite_existing,
        "only_targets": only_targets or [],
        "generation_config": generation_config,
        "harness_script": {
            "path": display_path(HARNESS_SCRIPT),
            "sha256": sha256_file(HARNESS_SCRIPT),
        },
        "files": written_files,
        "evaluation_commands": evaluation_commands,
    }
    manifest_json_path = manifests_dir / "external_model_traceability_manifest.json"
    manifest_md_path = manifests_dir / "external_model_traceability_manifest.md"
    write_json(manifest_json_path, manifest)
    manifest["files"].extend(
        [
            {
                "kind": "traceability_manifest_json",
                "path": display_path(manifest_json_path),
                "sha256": sha256_file(manifest_json_path),
                "rows": 1,
            }
        ]
    )
    write_traceability_md(manifest_md_path, manifest)
    print(f"Wrote {display_path(matrix_md_path)}")
    print(f"Wrote {display_path(manifest_md_path)}")
    print(f"Wrote {len(targets)} request JSONL files under {display_path(requests_dir)}")
    print(f"Wrote {len(targets)} response templates under {display_path(responses_dir)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-path", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--include-bridge", action="store_true")
    parser.add_argument("--include-official-deepseek", action="store_true")
    parser.add_argument("--include-open-breadth", action="store_true")
    parser.add_argument("--include-qiskit-specialist", action="store_true")
    parser.add_argument("--include-github-models", action="store_true")
    parser.add_argument("--include-meta-model-api", action="store_true")
    parser.add_argument("--include-openrouter", action="store_true")
    parser.add_argument("--include-nvidia-nim", action="store_true")
    parser.add_argument("--include-deepinfra", action="store_true")
    parser.add_argument("--include-appendix", action="store_true")
    parser.add_argument("--overwrite-existing", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument(
        "--anthropic-effort",
        choices=["low", "medium", "high", "xhigh", "max"],
        default="",
        help="Optional Anthropic output_config.effort value.",
    )
    parser.add_argument(
        "--frequency-penalty",
        type=float,
        default=None,
        help="Optional OpenAI-compatible frequency penalty in [-2, 2].",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional best-effort deterministic seed for compatible providers.",
    )
    parser.add_argument(
        "--only-target",
        action="append",
        default=[],
        help="Retain only an enabled provider:model target; may be supplied repeatedly.",
    )
    args = parser.parse_args()
    if args.frequency_penalty is not None and not -2.0 <= args.frequency_penalty <= 2.0:
        parser.error("--frequency-penalty must be in [-2, 2]")

    export_batches(
        prompt_path=args.prompt_path,
        output_dir=args.output_dir,
        include_bridge=args.include_bridge,
        include_official_deepseek=args.include_official_deepseek,
        include_open_breadth=args.include_open_breadth,
        include_qiskit_specialist=args.include_qiskit_specialist,
        include_github_models=args.include_github_models,
        include_meta_model_api=args.include_meta_model_api,
        include_openrouter=args.include_openrouter,
        include_nvidia_nim=args.include_nvidia_nim,
        include_deepinfra=args.include_deepinfra,
        include_appendix=args.include_appendix,
        overwrite_existing=args.overwrite_existing,
        temperature=args.temperature,
        top_p=args.top_p,
        max_output_tokens=args.max_output_tokens,
        anthropic_effort=args.anthropic_effort,
        frequency_penalty=args.frequency_penalty,
        seed=args.seed,
        only_targets=args.only_target,
    )


if __name__ == "__main__":
    main()
