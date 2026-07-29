"""Traceable live generation through OpenAI-compatible chat endpoints."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .manifest import sha256_file, verify_manifest
from .records import ProviderAttempt
from .version import PACKAGE_VERSION, version_record

DEFAULT_PROMPT_PATH = (
    "artifacts/test_split_154/"
    "pqid_bench_external_generation_prompts_154.jsonl"
)
RESPONSES_NAME = "responses.jsonl"
ATTEMPTS_NAME = "provider-attempts.jsonl"
REQUESTS_NAME = "requests.jsonl"
RUN_MANIFEST_NAME = "run-manifest.json"
RUN_SUMMARY_NAME = "run-summary.json"
RECORDS_DIR_NAME = "records"
RAW_DIR_NAME = "raw"
SAFE_PROMPT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,179}\Z")
SAFE_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass(frozen=True, slots=True)
class ProviderPreset:
    """Public routing defaults that never contain credentials."""

    name: str
    base_url: str
    api_key_env: str | None
    headers: Mapping[str, str] = field(default_factory=dict)
    authenticated: bool = True


PROVIDER_PRESETS: dict[str, ProviderPreset] = {
    "openai": ProviderPreset(
        name="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
    ),
    "groq": ProviderPreset(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
    ),
    "github-models": ProviderPreset(
        name="github-models",
        base_url="https://models.github.ai/inference",
        api_key_env="GITHUB_TOKEN",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
    ),
    "openrouter": ProviderPreset(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
    ),
    "hugging-face": ProviderPreset(
        name="hugging-face",
        base_url="https://router.huggingface.co/v1",
        api_key_env="HF_TOKEN",
    ),
    "nvidia": ProviderPreset(
        name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key_env="NVIDIA_API_KEY",
    ),
    "deepinfra": ProviderPreset(
        name="deepinfra",
        base_url="https://api.deepinfra.com/v1/openai",
        api_key_env="DEEPINFRA_TOKEN",
    ),
    "deepseek": ProviderPreset(
        name="deepseek",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
    ),
    "local": ProviderPreset(
        name="local",
        base_url="http://127.0.0.1:8000/v1",
        api_key_env=None,
        authenticated=False,
    ),
}

PROVIDER_ALIASES = {
    "github": "github-models",
    "github-models": "github-models",
    "huggingface": "hugging-face",
    "huggingface-router": "hugging-face",
    "hf": "hugging-face",
    "nvidia-nim": "nvidia",
}


class ProviderTransportError(RuntimeError):
    """Provider or transport failure with retry and raw-payload metadata."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        status_code: int | None = None,
        raw_body: bytes = b"",
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code
        self.raw_body = raw_body


Transport = Callable[[str, Mapping[str, str], bytes, float], bytes]
Progress = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True, slots=True)
class LiveRunConfig:
    """Complete, credential-free configuration for one live model run."""

    release_dir: Path
    output_dir: Path
    provider: str
    model: str
    base_url: str | None = None
    api_key_env: str | None = None
    api_key_file: Path | None = None
    no_auth: bool = False
    prompt_path: Path | None = None
    prompt_ids: tuple[str, ...] = ()
    limit: int = 0
    max_new: int = 0
    max_output_tokens: int = 2048
    max_output_field: str = "max_tokens"
    temperature: float | None = 0.0
    top_p: float | None = 1.0
    seed: int | None = None
    extra_body: Mapping[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 120.0
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0
    sleep_seconds: float = 0.0
    run_id: str | None = None
    resume: bool = False
    retry_errors: bool = False
    retry_uncertain: bool = False
    acknowledge_prompt_export: bool = False
    allow_insecure_http: bool = False


@dataclass(frozen=True, slots=True)
class LiveRunResult:
    """Stable collection result returned by the Python API."""

    run_id: str
    provider: str
    model: str
    route: str
    selected_prompts: int
    successful_prompts: int
    error_prompts: int
    pending_prompts: int
    attempted_this_invocation: int
    skipped_this_invocation: int
    output_dir: str
    response_file: str
    attempt_file: str
    run_manifest: str

    @property
    def complete(self) -> bool:
        return self.pending_prompts == 0 and self.error_prompts == 0

    def to_dict(self, *, portable_paths: bool = False) -> dict[str, Any]:
        payload = {
            **version_record(run_type="live_replication"),
            "run_id": self.run_id,
            "provider": self.provider,
            "model": self.model,
            "route": self.route,
            "selected_prompts": self.selected_prompts,
            "successful_prompts": self.successful_prompts,
            "error_prompts": self.error_prompts,
            "pending_prompts": self.pending_prompts,
            "attempted_this_invocation": self.attempted_this_invocation,
            "skipped_this_invocation": self.skipped_this_invocation,
            "complete": self.complete,
            "output_dir": self.output_dir,
            "response_file": self.response_file,
            "attempt_file": self.attempt_file,
            "run_manifest": self.run_manifest,
        }
        if portable_paths:
            payload.update(
                {
                    "output_dir": ".",
                    "response_file": RESPONSES_NAME,
                    "attempt_file": ATTEMPTS_NAME,
                    "run_manifest": RUN_MANIFEST_NAME,
                }
            )
        return payload


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp_id() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%SZ")


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized or "model"


def _normalize_provider(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    return PROVIDER_ALIASES.get(normalized, normalized)


def provider_preset(name: str) -> ProviderPreset | None:
    """Return one normalized provider preset, if known."""

    return PROVIDER_PRESETS.get(_normalize_provider(name))


def _route_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return normalized + "/chat/completions"


def _validate_route(route: str, *, allow_insecure_http: bool) -> None:
    parsed = urllib.parse.urlparse(route)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid provider route: {route!r}")
    if parsed.username or parsed.password:
        raise ValueError("Provider route must not embed credentials")
    if parsed.query or parsed.fragment:
        raise ValueError(
            "Provider route must not contain query parameters or fragments; "
            "credentials belong in an API-key source"
        )
    if parsed.scheme == "https":
        return
    loopback = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
    if not loopback and not allow_insecure_http:
        raise ValueError(
            "Plain HTTP is allowed only for a loopback endpoint unless "
            "--allow-insecure-http is supplied"
        )


def _sensitive_extra_body_keys(
    value: Any,
    *,
    prefix: str = "",
) -> list[str]:
    sensitive = re.compile(
        r"(^|[_-])(api[_-]?key|authorization|bearer|password|secret|token)($|[_-])",
        re.IGNORECASE,
    )
    matches: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if sensitive.search(key_text):
                matches.append(path)
            matches.extend(_sensitive_extra_body_keys(nested, prefix=path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            path = f"{prefix}[{index}]"
            matches.extend(_sensitive_extra_body_keys(nested, prefix=path))
    return matches


def _validate_config(
    config: LiveRunConfig,
    *,
    require_acknowledgement: bool,
) -> None:
    if require_acknowledgement and not config.acknowledge_prompt_export:
        raise ValueError(
            "Live generation requires explicit third-party prompt-export "
            "acknowledgement"
        )
    if not config.provider.strip():
        raise ValueError("Provider name must not be empty")
    if not config.model.strip():
        raise ValueError("Model ID must not be empty")
    if any(character in config.provider + config.model for character in "\r\n"):
        raise ValueError("Provider and model identifiers must be single-line values")
    if config.run_id is not None and (
        not config.run_id.strip()
        or any(character in config.run_id for character in "\r\n")
    ):
        raise ValueError("run_id must be a nonempty single-line value")
    if config.api_key_env is not None and not SAFE_ENV_NAME.fullmatch(
        config.api_key_env
    ):
        raise ValueError("api_key_env must be a valid environment-variable name")
    if config.limit < 0 or config.max_new < 0 or config.max_retries < 0:
        raise ValueError("Limits and retry count must be nonnegative")
    if config.max_output_tokens <= 0:
        raise ValueError("max_output_tokens must be positive")
    if config.max_output_field not in {"max_tokens", "max_completion_tokens"}:
        raise ValueError(
            "max_output_field must be max_tokens or max_completion_tokens"
        )
    if config.temperature is not None and config.temperature < 0:
        raise ValueError("temperature must be nonnegative when supplied")
    if config.top_p is not None and not 0 <= config.top_p <= 1:
        raise ValueError("top_p must be between 0 and 1 when supplied")
    if config.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if config.retry_backoff_seconds < 0 or config.sleep_seconds < 0:
        raise ValueError("Retry backoff and inter-request sleep must be nonnegative")
    if len(config.prompt_ids) != len(set(config.prompt_ids)):
        raise ValueError("prompt_ids must not contain duplicates")
    sensitive = _sensitive_extra_body_keys(config.extra_body)
    if sensitive:
        raise ValueError(
            "Extra request body contains credential-like field names that would "
            "be persisted: " + ", ".join(sensitive)
        )
    try:
        _canonical_bytes(config.extra_body)
    except (TypeError, ValueError) as exc:
        raise ValueError("extra_body must be JSON-serializable") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}"
                ) from exc
            if not isinstance(row, dict):
                raise ValueError(
                    f"Expected a JSON object on line {line_number} of {path}"
                )
            rows.append(row)
    return rows


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_bytes(
        path,
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )


def _atomic_write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    payload = b"".join(_canonical_bytes(row) + b"\n" for row in rows)
    _atomic_write_bytes(path, payload)


def _load_prompts(config: LiveRunConfig) -> tuple[Path, list[dict[str, Any]]]:
    prompt_path = (
        config.prompt_path.resolve()
        if config.prompt_path is not None
        else (config.release_dir.resolve() / DEFAULT_PROMPT_PATH)
    )
    rows = _read_jsonl(prompt_path)
    seen: set[str] = set()
    for row in rows:
        prompt_id = str(row.get("prompt_id") or "")
        row_id = str(row.get("row_id") or "")
        messages = row.get("messages")
        if not prompt_id or not row_id:
            raise ValueError(f"Prompt row lacks prompt_id or row_id in {prompt_path}")
        if not SAFE_PROMPT_ID.fullmatch(prompt_id) or ".." in prompt_id:
            raise ValueError(
                f"Prompt ID is not safe for portable artifact paths: {prompt_id!r}"
            )
        if prompt_id in seen:
            raise ValueError(f"Duplicate prompt_id {prompt_id!r} in {prompt_path}")
        if not isinstance(messages, list) or not messages:
            raise ValueError(f"Prompt {prompt_id} lacks a nonempty messages array")
        seen.add(prompt_id)

    if config.prompt_ids:
        requested = set(config.prompt_ids)
        missing = sorted(requested - seen)
        if missing:
            raise ValueError(f"Requested prompt IDs are absent: {missing}")
        rows = [row for row in rows if str(row["prompt_id"]) in requested]
    if config.limit > 0:
        rows = rows[: config.limit]
    if not rows:
        raise ValueError("No prompts were selected")
    return prompt_path, rows


def _resolve_route(config: LiveRunConfig) -> tuple[str, ProviderPreset | None]:
    preset = provider_preset(config.provider)
    base_url = config.base_url or (preset.base_url if preset else None)
    if not base_url:
        raise ValueError(
            "Unknown provider requires --base-url for an OpenAI-compatible endpoint"
        )
    route = _route_url(base_url)
    _validate_route(route, allow_insecure_http=config.allow_insecure_http)
    return route, preset


def _resolve_api_key(
    config: LiveRunConfig,
    preset: ProviderPreset | None,
) -> tuple[str | None, str]:
    if config.no_auth or (preset is not None and not preset.authenticated):
        return None, "none"
    if config.api_key_file is not None:
        key = config.api_key_file.expanduser().read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError("API key file is empty")
        return key, "file"
    env_name = config.api_key_env or (preset.api_key_env if preset else None)
    if not env_name:
        raise ValueError(
            "Authenticated route requires --api-key-env or --api-key-file"
        )
    key = os.environ.get(env_name, "").strip()
    if not key:
        raise ValueError(f"API key environment variable is unset or empty: {env_name}")
    return key, f"environment:{env_name}"


def _request_body(prompt: Mapping[str, Any], config: LiveRunConfig) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": config.model,
        "messages": prompt["messages"],
        config.max_output_field: config.max_output_tokens,
    }
    if config.temperature is not None:
        body["temperature"] = config.temperature
    if config.top_p is not None:
        body["top_p"] = config.top_p
    if config.seed is not None:
        body["seed"] = config.seed
    reserved = {"model", "messages", config.max_output_field}
    overlap = sorted(reserved & set(config.extra_body))
    if overlap:
        raise ValueError(
            "Extra request body cannot override protected fields: "
            + ", ".join(overlap)
        )
    body.update(config.extra_body)
    return body


def _request_record(
    prompt: Mapping[str, Any],
    config: LiveRunConfig,
    *,
    run_id: str,
    route: str,
) -> dict[str, Any]:
    body = _request_body(prompt, config)
    messages = body["messages"]
    prompt_without_target = {
        key: value
        for key, value in prompt.items()
        if key != "target_metadata"
    }
    return {
        "schema_version": "1.0.0",
        "record_type": "live_model_request",
        "run_id": run_id,
        "provider": _normalize_provider(config.provider),
        "route": route,
        "requested_model": config.model,
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "request_body": body,
        "request_sha256": _sha256_bytes(_canonical_bytes(body)),
        "model_input_sha256": _sha256_bytes(_canonical_bytes(messages)),
        "prompt_record_sha256": _sha256_bytes(
            _canonical_bytes(prompt_without_target)
        ),
        "target_metadata_policy": "not exported",
    }


def _headers(
    api_key: str | None,
    preset: ProviderPreset | None,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": f"pqid-bench/{PACKAGE_VERSION}",
    }
    if preset is not None:
        headers.update(preset.headers)
    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"
    if preset is not None and preset.name == "openrouter":
        referer = os.environ.get("OPENROUTER_HTTP_REFERER", "").strip()
        title = os.environ.get("OPENROUTER_APP_TITLE", "").strip()
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-OpenRouter-Title"] = title
    return headers


def _http_transport(
    route: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: float,
) -> bytes:
    request = urllib.request.Request(
        route,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raw_body = exc.read()
        retryable = exc.code in {408, 409, 425, 429, 500, 502, 503, 504}
        raise ProviderTransportError(
            f"HTTP {exc.code}: {exc.reason}",
            retryable=retryable,
            status_code=exc.code,
            raw_body=raw_body,
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ProviderTransportError(
            f"{type(exc).__name__}: {exc}",
            retryable=True,
        ) from exc


def _parse_response(raw_body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderTransportError(
            "Provider returned a non-JSON response",
            retryable=False,
            raw_body=raw_body,
        ) from exc
    if not isinstance(payload, dict):
        raise ProviderTransportError(
            "Provider response must be a JSON object",
            retryable=False,
            raw_body=raw_body,
        )
    return payload


def _first_choice(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderTransportError(
            "Provider response has no completion choice",
            retryable=False,
            raw_body=_canonical_bytes(payload),
        )
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ProviderTransportError(
            "Provider completion choice is not an object",
            retryable=False,
            raw_body=_canonical_bytes(payload),
        )
    return choice


def _generated_text(payload: Mapping[str, Any]) -> str:
    choice = _first_choice(payload)
    message = choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    if text is not None:
                        parts.append(str(text))
                elif item is not None:
                    parts.append(str(item))
            return "\n".join(parts).strip()
        if content is not None:
            return str(content).strip()
    if choice.get("text") is not None:
        return str(choice["text"]).strip()
    return ""


def _token_usage(payload: Mapping[str, Any]) -> tuple[int | None, int | None]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None
    input_value = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_value = usage.get("completion_tokens", usage.get("output_tokens"))
    return (
        int(input_value) if isinstance(input_value, (int, float)) else None,
        int(output_value) if isinstance(output_value, (int, float)) else None,
    )


def _record_path(output_dir: Path, prompt_id: str) -> Path:
    return output_dir / RECORDS_DIR_NAME / f"{prompt_id}.json"


def _load_record(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid live-run record JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Live-run record is not an object: {path}")
    return payload


def _raw_path(output_dir: Path, prompt_id: str, attempt_index: int) -> Path:
    return (
        output_dir
        / RAW_DIR_NAME
        / f"{prompt_id}.attempt-{attempt_index:03d}.json"
    )


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _portable_prompt_source(prompt_path: Path, release_dir: Path) -> tuple[str, str]:
    resolved_prompt = prompt_path.resolve()
    resolved_release = release_dir.resolve()
    try:
        return resolved_prompt.relative_to(resolved_release).as_posix(), "release"
    except ValueError:
        return resolved_prompt.name, "external_filename"


def _response_from_success(
    request: Mapping[str, Any],
    payload: Mapping[str, Any],
    *,
    provider: str,
    raw_path: Path,
    raw_sha256: str,
    output_dir: Path,
    completed_at: datetime,
    attempt_count: int,
) -> dict[str, Any]:
    choice = _first_choice(payload)
    text = _generated_text(payload)
    resolved_model = str(payload.get("model") or request["requested_model"])
    return {
        "schema_version": "1.0.0",
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": provider,
        "model": request["requested_model"],
        "requested_model": request["requested_model"],
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request["request_sha256"],
        "model_input_sha256": request["model_input_sha256"],
        "prompt_record_sha256": request["prompt_record_sha256"],
        "generated_text": text,
        "generated_code": text,
        "response_sha256": _sha256_text(text),
        "finish_reason": str(choice.get("finish_reason") or ""),
        "provider_request_id": str(payload.get("id") or ""),
        "resolved_model": resolved_model,
        "usage": payload.get("usage") if isinstance(payload.get("usage"), dict) else {},
        "completed_at": completed_at.isoformat(),
        "raw_response_path": _relative(raw_path, output_dir),
        "raw_response_sha256": raw_sha256,
        "attempt_count": attempt_count,
        "transport_affected": attempt_count > 1,
        "error": None,
    }


def _response_from_error(
    request: Mapping[str, Any],
    *,
    provider: str,
    error: ProviderTransportError,
    raw_path: Path | None,
    raw_sha256: str | None,
    output_dir: Path,
    completed_at: datetime,
    attempt_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": provider,
        "model": request["requested_model"],
        "requested_model": request["requested_model"],
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request["request_sha256"],
        "model_input_sha256": request["model_input_sha256"],
        "prompt_record_sha256": request["prompt_record_sha256"],
        "generated_text": None,
        "generated_code": "",
        "response_sha256": _sha256_text(""),
        "finish_reason": "error",
        "provider_request_id": "",
        "resolved_model": None,
        "usage": {},
        "completed_at": completed_at.isoformat(),
        "raw_response_path": (
            _relative(raw_path, output_dir) if raw_path is not None else None
        ),
        "raw_response_sha256": raw_sha256,
        "attempt_count": attempt_count,
        "transport_affected": attempt_count > 1,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "status_code": error.status_code,
            "retryable": error.retryable,
        },
    }


def _rebuild_indexes(
    output_dir: Path,
    selected_prompt_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    responses: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for prompt_id in selected_prompt_ids:
        record = _load_record(_record_path(output_dir, prompt_id))
        if record is None:
            continue
        response = record.get("response")
        if isinstance(response, dict):
            responses.append(response)
        record_attempts = record.get("attempts")
        if isinstance(record_attempts, list):
            attempts.extend(
                attempt for attempt in record_attempts if isinstance(attempt, dict)
            )
    _atomic_write_jsonl(output_dir / RESPONSES_NAME, responses)
    _atomic_write_jsonl(output_dir / ATTEMPTS_NAME, attempts)
    return responses, attempts


def _summary_result(
    *,
    output_dir: Path,
    run_id: str,
    provider: str,
    model: str,
    route: str,
    selected_prompt_ids: list[str],
    attempted_this_invocation: int,
    skipped_this_invocation: int,
) -> LiveRunResult:
    responses, _ = _rebuild_indexes(output_dir, selected_prompt_ids)
    success = sum(
        1 for row in responses if str(row.get("finish_reason") or "") != "error"
    )
    errors = sum(
        1 for row in responses if str(row.get("finish_reason") or "") == "error"
    )
    pending = len(selected_prompt_ids) - len(responses)
    result = LiveRunResult(
        run_id=run_id,
        provider=provider,
        model=model,
        route=route,
        selected_prompts=len(selected_prompt_ids),
        successful_prompts=success,
        error_prompts=errors,
        pending_prompts=pending,
        attempted_this_invocation=attempted_this_invocation,
        skipped_this_invocation=skipped_this_invocation,
        output_dir=str(output_dir),
        response_file=str(output_dir / RESPONSES_NAME),
        attempt_file=str(output_dir / ATTEMPTS_NAME),
        run_manifest=str(output_dir / RUN_MANIFEST_NAME),
    )
    _atomic_write_json(
        output_dir / RUN_SUMMARY_NAME,
        result.to_dict(portable_paths=True),
    )
    return result


def _manifest_contract(
    *,
    config: LiveRunConfig,
    run_id: str,
    provider: str,
    route: str,
    prompt_path: Path,
    requests: list[dict[str, Any]],
    credential_source: str,
) -> dict[str, Any]:
    prompt_ids = [str(row["prompt_id"]) for row in requests]
    prompt_source, prompt_source_scope = _portable_prompt_source(
        prompt_path,
        config.release_dir,
    )
    request_set_sha256 = _sha256_bytes(
        b"".join(_canonical_bytes(row) + b"\n" for row in requests)
    )
    generation_config = {
        "max_output_tokens": config.max_output_tokens,
        "max_output_field": config.max_output_field,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "seed": config.seed,
        "extra_body": config.extra_body,
    }
    return {
        **version_record(run_type="live_replication"),
        "run_id": run_id,
        "provider": provider,
        "route": route,
        "requested_model": config.model,
        "created_at": _utc_now().isoformat(),
        "prompt_source": prompt_source,
        "prompt_source_scope": prompt_source_scope,
        "prompt_source_sha256": sha256_file(prompt_path),
        "prompt_count": len(prompt_ids),
        "prompt_ids_sha256": _sha256_bytes(
            ("\n".join(prompt_ids) + "\n").encode("utf-8")
        ),
        "request_set_sha256": request_set_sha256,
        "generation_config": generation_config,
        "credential_source": credential_source,
        "credential_value_recorded": False,
        "target_metadata_exported": False,
        "third_party_prompt_export_acknowledged": True,
        "retry_policy": {
            "max_retries": config.max_retries,
            "backoff_seconds": config.retry_backoff_seconds,
            "sdk_hidden_retries": "not applicable; standard-library transport",
        },
    }


def plan_live_model_run(config: LiveRunConfig) -> dict[str, Any]:
    """Return a credential-free plan without contacting a provider."""

    _validate_config(config, require_acknowledgement=False)
    release_dir = config.release_dir.resolve()
    manifest = verify_manifest(release_dir)
    if not manifest.valid:
        raise ValueError("Release manifest verification failed")
    prompt_path, prompts = _load_prompts(config)
    route, preset = _resolve_route(config)
    provider = (
        preset.name if preset is not None else _normalize_provider(config.provider)
    )
    return {
        **version_record(run_type="live_replication"),
        "provider": provider,
        "requested_model": config.model,
        "route": route,
        "prompt_source": str(prompt_path),
        "selected_prompts": len(prompts),
        "prompt_ids": [str(row["prompt_id"]) for row in prompts],
        "output_dir": str(config.output_dir.resolve()),
        "target_metadata_exported": False,
        "requires_prompt_export_acknowledgement": True,
        "requires_authentication": not (
            config.no_auth or (preset is not None and not preset.authenticated)
        ),
        "contacts_provider": False,
    }


def _prepare_output(
    config: LiveRunConfig,
    *,
    provider: str,
    route: str,
    prompt_path: Path,
    prompts: list[dict[str, Any]],
    credential_source: str,
) -> tuple[Path, str, list[dict[str, Any]], dict[str, Any]]:
    output_dir = config.output_dir.resolve()
    manifest_path = output_dir / RUN_MANIFEST_NAME
    if output_dir.exists() and any(output_dir.iterdir()) and not config.resume:
        raise ValueError(
            f"Output directory is not empty; use --resume or choose another path: "
            f"{output_dir}"
        )
    if config.resume:
        if not manifest_path.is_file():
            raise ValueError(f"Cannot resume without {RUN_MANIFEST_NAME}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        run_id = str(manifest.get("run_id") or "")
        if not run_id:
            raise ValueError("Existing run manifest lacks run_id")
        expected = {
            "provider": provider,
            "route": route,
            "requested_model": config.model,
            "prompt_source_sha256": sha256_file(prompt_path),
        }
        mismatches = [
            f"{key}: expected {value!r}, observed {manifest.get(key)!r}"
            for key, value in expected.items()
            if manifest.get(key) != value
        ]
        if config.run_id is not None and config.run_id != run_id:
            mismatches.append(
                f"run_id: expected {config.run_id!r}, observed {run_id!r}"
            )
        if mismatches:
            raise ValueError(
                "Resume configuration does not match the existing run: "
                + "; ".join(mismatches)
            )
        requests = _read_jsonl(output_dir / REQUESTS_NAME)
        selected_ids = [str(row["prompt_id"]) for row in requests]
        requested_ids = [str(row["prompt_id"]) for row in prompts]
        if selected_ids != requested_ids:
            raise ValueError(
                "Resume prompt selection differs from the frozen request set"
            )
        return output_dir, run_id, requests, manifest

    run_id = config.run_id or (
        f"live-{_slug(provider)}-{_slug(config.model)}-{_timestamp_id()}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    requests = [
        _request_record(
            prompt,
            config,
            run_id=run_id,
            route=route,
        )
        for prompt in prompts
    ]
    manifest = _manifest_contract(
        config=config,
        run_id=run_id,
        provider=provider,
        route=route,
        prompt_path=prompt_path,
        requests=requests,
        credential_source=credential_source,
    )
    _atomic_write_jsonl(output_dir / REQUESTS_NAME, requests)
    _atomic_write_json(manifest_path, manifest)
    return output_dir, run_id, requests, manifest


def _interrupted_attempt(
    active: Mapping[str, Any],
    *,
    completed_at: datetime,
) -> dict[str, Any]:
    payload = dict(active)
    payload.update(
        {
            "completed_at": completed_at.isoformat(),
            "status": "uncertain_interrupted",
            "error_type": "InterruptedAttempt",
            "error_message": (
                "A previous process stopped after marking the request in flight; "
                "provider completion state is unknown."
            ),
            "transport_affected": True,
        }
    )
    payload.pop("active", None)
    return payload


def run_live_model(
    config: LiveRunConfig,
    *,
    transport: Transport | None = None,
    sleep: Callable[[float], None] = time.sleep,
    progress: Progress | None = None,
) -> LiveRunResult:
    """Generate a traceable response panel through one compatible endpoint."""

    _validate_config(config, require_acknowledgement=True)

    release_dir = config.release_dir.resolve()
    verification = verify_manifest(release_dir)
    if not verification.valid:
        raise ValueError("Release manifest verification failed")
    prompt_path, prompts = _load_prompts(config)
    route, preset = _resolve_route(config)
    provider = (
        preset.name if preset is not None else _normalize_provider(config.provider)
    )
    api_key, credential_source = _resolve_api_key(config, preset)
    output_dir, run_id, requests, _ = _prepare_output(
        config,
        provider=provider,
        route=route,
        prompt_path=prompt_path,
        prompts=prompts,
        credential_source=credential_source,
    )
    headers = _headers(api_key, preset)
    post = transport or _http_transport
    selected_prompt_ids = [str(request["prompt_id"]) for request in requests]
    attempted_this_invocation = 0
    skipped_this_invocation = 0
    if progress is not None:
        progress(
            {
                "event": "run_started",
                "run_id": run_id,
                "provider": provider,
                "model": config.model,
                "selected_prompts": len(selected_prompt_ids),
            }
        )

    for selected_index, request in enumerate(requests, start=1):
        prompt_id = str(request["prompt_id"])
        path = _record_path(output_dir, prompt_id)
        record = _load_record(path) or {
            "prompt_id": prompt_id,
            "request_sha256": request["request_sha256"],
            "status": "pending",
            "attempts": [],
            "active_attempt": None,
            "response": None,
        }
        if record.get("request_sha256") != request["request_sha256"]:
            raise ValueError(f"Request hash changed for {prompt_id}")
        attempts = list(record.get("attempts") or [])
        active = record.get("active_attempt")
        if isinstance(active, dict):
            if not config.retry_uncertain:
                raise ValueError(
                    f"{prompt_id} has an uncertain in-flight attempt; resume with "
                    "--retry-uncertain only after accepting a possible additional draw"
                )
            attempts.append(_interrupted_attempt(active, completed_at=_utc_now()))
            record["attempts"] = attempts
            record["active_attempt"] = None
            record["status"] = "pending"
            _atomic_write_json(path, record)

        response = record.get("response")
        response_is_error = (
            isinstance(response, dict)
            and str(response.get("finish_reason") or "") == "error"
        )
        if isinstance(response, dict) and not (
            response_is_error and config.retry_errors
        ):
            skipped_this_invocation += 1
            continue
        if config.max_new > 0 and attempted_this_invocation >= config.max_new:
            break

        if response_is_error and config.retry_errors:
            record["response"] = None
            record["status"] = "pending"

        if progress is not None:
            progress(
                {
                    "event": "prompt_started",
                    "index": selected_index,
                    "total": len(selected_prompt_ids),
                    "prompt_id": prompt_id,
                }
            )
        final_error: ProviderTransportError | None = None
        for retry_index in range(config.max_retries + 1):
            attempt_index = len(attempts) + 1
            started_at = _utc_now()
            attempt_id = f"{run_id}:{prompt_id}:{attempt_index}"
            active_attempt = {
                "attempt_id": attempt_id,
                "run_id": run_id,
                "prompt_id": prompt_id,
                "provider": provider,
                "route": route,
                "requested_model": config.model,
                "resolved_model": None,
                "request_sha256": request["request_sha256"],
                "response_text": None,
                "raw_response_path": None,
                "raw_response_sha256": None,
                "provider_request_id": None,
                "finish_reason": None,
                "status": "in_flight",
                "attempt_index": attempt_index,
                "started_at": started_at.isoformat(),
                "completed_at": None,
                "input_tokens": None,
                "output_tokens": None,
                "error_type": None,
                "error_message": None,
                "transport_affected": attempt_index > 1,
            }
            record["active_attempt"] = active_attempt
            record["status"] = "in_flight"
            _atomic_write_json(path, record)
            try:
                raw_body = post(
                    route,
                    headers,
                    _canonical_bytes(request["request_body"]),
                    config.timeout_seconds,
                )
                payload = _parse_response(raw_body)
                completed_at = _utc_now()
                raw_path = _raw_path(output_dir, prompt_id, attempt_index)
                _atomic_write_bytes(raw_path, raw_body)
                raw_sha256 = sha256_file(raw_path)
                text = _generated_text(payload)
                input_tokens, output_tokens = _token_usage(payload)
                choice = _first_choice(payload)
                attempt = ProviderAttempt(
                    attempt_id=attempt_id,
                    run_id=run_id,
                    prompt_id=prompt_id,
                    provider=provider,
                    route=route,
                    requested_model=config.model,
                    resolved_model=str(payload.get("model") or config.model),
                    request_sha256=str(request["request_sha256"]),
                    response_text=text,
                    raw_response_path=_relative(raw_path, output_dir),
                    raw_response_sha256=raw_sha256,
                    provider_request_id=str(payload.get("id") or "") or None,
                    finish_reason=str(choice.get("finish_reason") or "") or None,
                    status="success",
                    attempt_index=attempt_index,
                    started_at=started_at,
                    completed_at=completed_at,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    transport_affected=attempt_index > 1,
                ).to_dict()
                attempts.append(attempt)
                response = _response_from_success(
                    request,
                    payload,
                    provider=provider,
                    raw_path=raw_path,
                    raw_sha256=raw_sha256,
                    output_dir=output_dir,
                    completed_at=completed_at,
                    attempt_count=len(attempts),
                )
                record.update(
                    {
                        "attempts": attempts,
                        "active_attempt": None,
                        "response": response,
                        "status": "complete",
                    }
                )
                _atomic_write_json(path, record)
                final_error = None
                if progress is not None:
                    progress(
                        {
                            "event": "prompt_finished",
                            "index": selected_index,
                            "total": len(selected_prompt_ids),
                            "prompt_id": prompt_id,
                            "status": "success",
                            "finish_reason": response["finish_reason"],
                            "attempt_count": len(attempts),
                        }
                    )
                break
            except ProviderTransportError as exc:
                completed_at = _utc_now()
                raw_path: Path | None = None
                raw_sha256: str | None = None
                if exc.raw_body:
                    raw_path = _raw_path(output_dir, prompt_id, attempt_index)
                    _atomic_write_bytes(raw_path, exc.raw_body)
                    raw_sha256 = sha256_file(raw_path)
                attempt = ProviderAttempt(
                    attempt_id=attempt_id,
                    run_id=run_id,
                    prompt_id=prompt_id,
                    provider=provider,
                    route=route,
                    requested_model=config.model,
                    resolved_model=None,
                    request_sha256=str(request["request_sha256"]),
                    response_text=None,
                    raw_response_path=(
                        _relative(raw_path, output_dir)
                        if raw_path is not None
                        else None
                    ),
                    raw_response_sha256=raw_sha256,
                    provider_request_id=None,
                    finish_reason=None,
                    status="error",
                    attempt_index=attempt_index,
                    started_at=started_at,
                    completed_at=completed_at,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    transport_affected=True,
                ).to_dict()
                attempts.append(attempt)
                record.update(
                    {
                        "attempts": attempts,
                        "active_attempt": None,
                        "status": "pending",
                    }
                )
                _atomic_write_json(path, record)
                final_error = exc
                if exc.retryable and retry_index < config.max_retries:
                    delay = config.retry_backoff_seconds * (2**retry_index)
                    if progress is not None:
                        progress(
                            {
                                "event": "prompt_retry",
                                "index": selected_index,
                                "total": len(selected_prompt_ids),
                                "prompt_id": prompt_id,
                                "attempt_count": len(attempts),
                                "delay_seconds": delay,
                                "error": str(exc),
                            }
                        )
                    if delay > 0:
                        sleep(delay)
                    continue
                response = _response_from_error(
                    request,
                    provider=provider,
                    error=exc,
                    raw_path=raw_path,
                    raw_sha256=raw_sha256,
                    output_dir=output_dir,
                    completed_at=completed_at,
                    attempt_count=len(attempts),
                )
                record.update(
                    {
                        "response": response,
                        "status": "complete",
                    }
                )
                _atomic_write_json(path, record)
                if progress is not None:
                    progress(
                        {
                            "event": "prompt_finished",
                            "index": selected_index,
                            "total": len(selected_prompt_ids),
                            "prompt_id": prompt_id,
                            "status": "error",
                            "attempt_count": len(attempts),
                            "error": str(exc),
                        }
                    )
                break

        attempted_this_invocation += 1
        _rebuild_indexes(output_dir, selected_prompt_ids)
        if config.sleep_seconds > 0 and final_error is None:
            sleep(config.sleep_seconds)

    result = _summary_result(
        output_dir=output_dir,
        run_id=run_id,
        provider=provider,
        model=config.model,
        route=route,
        selected_prompt_ids=selected_prompt_ids,
        attempted_this_invocation=attempted_this_invocation,
        skipped_this_invocation=skipped_this_invocation,
    )
    if progress is not None:
        progress({"event": "run_finished", **result.to_dict()})
    return result
