"""Canonical model registries for the 154-prompt PQID-Bench evaluation."""

from __future__ import annotations


INITIAL_19_MODEL_ORDER = [
    "gpt-5.6-sol",
    "gpt-5.5",
    "gpt-5.4-mini",
    "claude-fable-5",
    "claude-sonnet-4-6",
    "claude-opus-4-8",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "mistral-ai/codestral-2501",
    "qwen/qwen3-coder-next",
    "meta/llama-4-maverick-17b-128e-instruct-fp8",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]

QISKIT_SPECIALIST_MODEL = "qiskit/mistral-small-3.2-24b-qiskit"
MISTRAL_PARENT_MODEL = "mistralai/mistral-small-3.2-24b-instruct"

MATCHED_SPECIALIZATION_MODELS = [
    MISTRAL_PARENT_MODEL,
    QISKIT_SPECIALIST_MODEL,
]

# The final primary roster includes the matched parent-specialist pair. Keep
# the historical expanded name as an alias so older commands remain valid.
PRIMARY_MODEL_ORDER = [
    *INITIAL_19_MODEL_ORDER[:16],
    *MATCHED_SPECIALIZATION_MODELS,
    *INITIAL_19_MODEL_ORDER[16:],
]
MODEL_ORDER = list(PRIMARY_MODEL_ORDER)
EXPANDED_MODEL_ORDER = list(PRIMARY_MODEL_ORDER)

MODEL_LABELS = {
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "gpt-5.5": "GPT-5.5",
    "gpt-5.4-mini": "GPT-5.4 mini",
    "claude-fable-5": "Claude Fable 5",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "claude-opus-4-8": "Claude Opus 4.8",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview",
    "deepseek-v4-pro": "DeepSeek V4 Pro",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "mistral-ai/codestral-2501": "Codestral 25.01",
    "qwen/qwen3-coder-next": "Qwen3-Coder-Next",
    "meta/llama-4-maverick-17b-128e-instruct-fp8": "Llama 4 Maverick",
    "llama-3.3-70b-versatile": "Llama 3.3 70B",
    "openai/gpt-oss-120b": "GPT-OSS 120B",
    "openai/gpt-oss-20b": "GPT-OSS 20B",
    "qwen/qwen3-32b": "Qwen3 32B",
    "meta-llama/llama-4-scout-17b-16e-instruct": "Llama 4 Scout",
    "llama-3.1-8b-instant": "Llama 3.1 8B",
    MISTRAL_PARENT_MODEL: "Mistral Small 3.2 24B",
    QISKIT_SPECIALIST_MODEL: "Qiskit Mistral 3.2 24B",
}

FRONTIER_MODELS = {
    "gpt-5.6-sol",
    "gpt-5.5",
    "gpt-5.4-mini",
    "claude-fable-5",
    "claude-sonnet-4-6",
    "claude-opus-4-8",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
}

STRONG_OPEN_CODE_MODELS = {
    "mistral-ai/codestral-2501",
    "qwen/qwen3-coder-next",
    "meta/llama-4-maverick-17b-128e-instruct-fp8",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    MISTRAL_PARENT_MODEL,
    QISKIT_SPECIALIST_MODEL,
}

LOW_EXPERIMENTAL_MODELS = {
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
}

REPORT_DIR_TO_MODEL = {
    "anthropic_claude-fable-5": "claude-fable-5",
    "anthropic_claude-opus-4-8": "claude-opus-4-8",
    "anthropic_claude-sonnet-4-6": "claude-sonnet-4-6",
    "deepseek_deepseek-v4-flash": "deepseek-v4-flash",
    "deepseek_deepseek-v4-pro": "deepseek-v4-pro",
    "github_models_mistral-ai_codestral-2501": "mistral-ai/codestral-2501",
    "github_models_meta_llama-4-maverick-17b-128e-instruct-fp8": "meta/llama-4-maverick-17b-128e-instruct-fp8",
    "huggingface_router_qwen_qwen3-coder-next_novita": "qwen/qwen3-coder-next",
    "google_gemini-2_5-pro": "gemini-2.5-pro",
    "google_gemini-3_1-pro-preview": "gemini-3.1-pro-preview",
    "groq_llama-3_1-8b-instant": "llama-3.1-8b-instant",
    "groq_llama-3_3-70b-versatile": "llama-3.3-70b-versatile",
    "groq_meta-llama_llama-4-scout-17b-16e-instruct": "meta-llama/llama-4-scout-17b-16e-instruct",
    "groq_openai_gpt-oss-120b": "openai/gpt-oss-120b",
    "groq_openai_gpt-oss-20b": "openai/gpt-oss-20b",
    "groq_qwen_qwen3-32b": "qwen/qwen3-32b",
    "openai_gpt-5_4-mini": "gpt-5.4-mini",
    "openai_gpt-5_5": "gpt-5.5",
    "openai_gpt-5_6-sol": "gpt-5.6-sol",
    "openrouter_mistralai_mistral-small-3_2-24b-instruct": MISTRAL_PARENT_MODEL,
    "huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai": QISKIT_SPECIALIST_MODEL,
}


def model_from_report_dir(name: str) -> str:
    return REPORT_DIR_TO_MODEL.get(name, name)


def model_order(*, expanded: bool = False, initial: bool = False) -> list[str]:
    """Return a defensive copy of the final or archival initial roster."""

    if initial:
        return list(INITIAL_19_MODEL_ORDER)
    return list(PRIMARY_MODEL_ORDER)


def is_matched_specialization_model(model: str) -> bool:
    return model in MATCHED_SPECIALIZATION_MODELS


def model_tier(model: str, *, underscored: bool = True) -> str:
    if model in FRONTIER_MODELS:
        return "frontier_api" if underscored else "frontier"
    if model in STRONG_OPEN_CODE_MODELS:
        return "strong_open_or_code" if underscored else "strong_open_code"
    if model in LOW_EXPERIMENTAL_MODELS:
        return "low_or_experimental" if underscored else "low_experimental"
    return "other"
