"""Run OpenAI-compatible chat API calls for PQID-Bench request JSONL files.

This runner is intended for Groq, GitHub Models, OpenRouter, local vLLM/SGLang,
or any endpoint that implements `/chat/completions`. It materializes response
JSONL rows in the same schema consumed by
`run_pqid_bench_external_model_generation_harness.py`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
PQID_ROOT = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else SUBMISSION_DIR
PQID_SCRIPTS_DIR = PQID_ROOT / "scripts"
if str(PQID_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PQID_SCRIPTS_DIR))

from project_paths import format_display_path, get_repo_root, get_user_secret_dir, load_secret  # noqa: E402


SCHEMA_VERSION = "pqid-bench-external-model-batch-v1"
DEFAULT_REQUEST_DIR = ARTIFACTS_DIR / "external_model_batches" / "requests"
DEFAULT_RESPONSE_DIR = ARTIFACTS_DIR / "external_model_batches" / "responses"
DEFAULT_RAW_DIR = ARTIFACTS_DIR / "external_model_batches" / "openai_compatible_api" / "raw_outputs"

PROVIDER_DEFAULTS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_name": "GROQ_API_KEY",
        "file_env_name": "GROQ_API_KEY_FILE",
        "secret_files": [".groq_api_key", "groq_api_key.txt"],
        "headers": {},
    },
    "github_models": {
        "base_url": "https://models.github.ai/inference",
        "env_name": "GITHUB_TOKEN",
        "file_env_name": "GITHUB_TOKEN_FILE",
        "secret_files": [".github_token", "github_token.txt"],
        "headers": {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_name": "OPENROUTER_API_KEY",
        "file_env_name": "OPENROUTER_API_KEY_FILE",
        "secret_files": [".openrouter_api_key", "openrouter_api_key.txt"],
        "headers": {},
    },
    "huggingface_router": {
        "base_url": "https://router.huggingface.co/v1",
        "env_name": "HF_TOKEN",
        "file_env_name": "HF_TOKEN_FILE",
        "secret_files": [".hf_token", "hf_token.txt", "huggingface_token.txt"],
        "headers": {},
    },
    "nvidia_nim": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "env_name": "NVIDIA_API_KEY",
        "file_env_name": "NVIDIA_API_KEY_FILE",
        "secret_files": [".nvidia_api_key", "nvidia_api_key.txt"],
        "headers": {},
    },
    "deepinfra": {
        "base_url": "https://api.deepinfra.com/v1/openai",
        "env_name": "DEEPINFRA_TOKEN",
        "file_env_name": "DEEPINFRA_TOKEN_FILE",
        "secret_files": [".deepinfra_token", "deepinfra_token.txt", "deepinfra_api_key.txt"],
        "headers": {},
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "env_name": "DEEPSEEK_API_KEY",
        "file_env_name": "DEEPSEEK_API_KEY_FILE",
        "secret_files": [".deepseek_api_key", "deepseek_api_key.txt", "DEEPSEEK_API_KEY"],
        "headers": {},
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--response-file", type=Path, default=None)
    parser.add_argument("--raw-output-file", type=Path, default=None)
    parser.add_argument("--provider", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key-env", default="")
    parser.add_argument("--api-key-file", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--only-prompt-id",
        action="append",
        default=[],
        help="Run only the named prompt ID; may be supplied repeatedly.",
    )
    parser.add_argument(
        "--max-new",
        type=int,
        default=0,
        help="Run at most this many non-skipped rows after resume filtering; 0 means no cap.",
    )
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument(
        "--request-timeout-seconds",
        type=float,
        default=0.0,
        help="Optional per-request API timeout in seconds; use 0 for SDK default.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="With --resume, rerun rows whose existing response has finish_reason=error.",
    )
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument(
        "--check-credentials",
        action="store_true",
        help="Load the provider key and print whether it is available, without calling the API.",
    )
    return parser.parse_args()


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {format_display_path(path)}: {exc}") from exc
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def slug_from_request_path(path: Path) -> str:
    name = path.name
    return name.removesuffix("_requests.jsonl").removesuffix(".jsonl")


def unique_value(rows: list[dict[str, Any]], field: str) -> str:
    values = sorted({str(row.get(field) or "") for row in rows if row.get(field)})
    if len(values) != 1:
        raise ValueError(f"Expected one `{field}` value in request file, found {values}")
    return values[0]


def provider_defaults(provider: str) -> dict[str, Any]:
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS.get(provider.replace("-", "_"), {}))


def secret_file_candidates(provider: str, explicit_path: str) -> list[Path]:
    if explicit_path:
        return [Path(explicit_path).expanduser()]
    defaults = provider_defaults(provider)
    repo_root = get_repo_root(__file__)
    secret_dir = get_user_secret_dir()
    file_names = defaults.get("secret_files") or [f"{provider}_api_key.txt"]
    candidates = []
    for name in file_names:
        candidates.extend([repo_root / name, PQID_ROOT / name, secret_dir / name])
    return candidates


def load_provider_key(provider: str, api_key_env: str, api_key_file: str) -> str:
    defaults = provider_defaults(provider)
    env_name = api_key_env or defaults.get("env_name") or f"{provider.upper()}_API_KEY"
    file_env_name = defaults.get("file_env_name") or f"{env_name}_FILE"
    try:
        return load_secret(
            env_name=env_name,
            file_env_name=file_env_name,
            file_candidates=secret_file_candidates(provider, api_key_file),
            named_file_candidates=None,
            label=f"{provider} API key",
        )
    except SystemExit:
        if provider != "huggingface_router" or api_key_env or api_key_file:
            raise
        try:
            from huggingface_hub import get_token
        except ImportError:
            raise
        token = get_token()
        if token:
            return token
        raise


def object_to_dict(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, (dict, list, str, int, float, bool)):
        return value
    return str(value)


def first_choice(raw: dict[str, Any]) -> dict[str, Any]:
    choices = raw.get("choices") or []
    return choices[0] if choices else {}


def generated_text(raw: dict[str, Any]) -> str:
    choice = first_choice(raw)
    message = choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    if content is not None:
        return str(content).strip()
    return str(choice.get("text") or "").strip()


def response_row_from_success(
    *,
    request: dict[str, Any],
    provider: str,
    base_url: str,
    raw: dict[str, Any],
    created_at_utc: str,
) -> dict[str, Any]:
    choice = first_choice(raw)
    resolved_model = str(raw.get("model") or request.get("api_model_id") or request.get("model") or "")
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": provider,
        "model": resolved_model,
        "api_model_id": request.get("api_model_id") or request.get("model"),
        "model_label": request.get("model_label", ""),
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request.get("request_sha256", ""),
        "model_input_sha256": request.get("model_input_sha256", ""),
        "prompt_record_sha256": request.get("prompt_record_sha256", ""),
        "generation_config": request.get("generation_config", {}),
        "created_at_utc": created_at_utc,
        "request_id": str(raw.get("id") or ""),
        "system_fingerprint": str(raw.get("system_fingerprint") or ""),
        "model_snapshot": resolved_model,
        "finish_reason": str(choice.get("finish_reason") or ""),
        "usage": raw.get("usage") or {},
        "provider_metadata": {
            "base_url": base_url,
            "request_provider": request.get("provider", ""),
            "response_object": raw.get("object", ""),
            "served_by": str(raw.get("provider") or raw.get("provider_name") or ""),
            "requested_provider_routing": (
                ((request.get("request_body") or {}).get("extra_body") or {}).get("provider")
                or {}
            ),
        },
        "generated_code": generated_text(raw),
        "raw_response": json.dumps(raw, ensure_ascii=True, sort_keys=True),
    }


def response_row_from_error(
    *,
    request: dict[str, Any],
    provider: str,
    base_url: str,
    error: Exception,
    created_at_utc: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": provider,
        "model": request.get("api_model_id") or request.get("model"),
        "api_model_id": request.get("api_model_id") or request.get("model"),
        "model_label": request.get("model_label", ""),
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request.get("request_sha256", ""),
        "model_input_sha256": request.get("model_input_sha256", ""),
        "prompt_record_sha256": request.get("prompt_record_sha256", ""),
        "generation_config": request.get("generation_config", {}),
        "created_at_utc": created_at_utc,
        "request_id": "",
        "system_fingerprint": "",
        "model_snapshot": "",
        "finish_reason": "error",
        "usage": {},
        "provider_metadata": {
            "base_url": base_url,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "request_provider": request.get("provider", ""),
            "requested_provider_routing": (
                ((request.get("request_body") or {}).get("extra_body") or {}).get("provider")
                or {}
            ),
        },
        "generated_code": "",
        "raw_response": "",
    }


def existing_prompt_ids(response_file: Path, retry_errors: bool = False) -> set[str]:
    if not response_file.exists():
        return set()
    completed = set()
    for row in iter_jsonl(response_file):
        prompt_id = row.get("prompt_id")
        if not prompt_id:
            continue
        if retry_errors and str(row.get("finish_reason") or "") == "error":
            continue
        completed.add(str(prompt_id))
    return completed


def reset_output(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def attach_attempt_trace(
    response_row: dict[str, Any], raw_row: dict[str, Any], attempt_trace: list[dict[str, Any]]
) -> None:
    """Attach the frozen transport-attempt audit without creating another model draw."""

    metadata = response_row.setdefault("provider_metadata", {})
    metadata["attempt_count"] = len(attempt_trace)
    metadata["initial_attempt_success"] = bool(
        attempt_trace and attempt_trace[0]["outcome"] == "success"
    )
    metadata["recovered_after_transport_error"] = bool(
        attempt_trace
        and attempt_trace[-1]["outcome"] == "success"
        and any(item["outcome"] == "error" for item in attempt_trace[:-1])
    )
    metadata["attempt_trace"] = attempt_trace
    raw_row["attempt_trace"] = attempt_trace


def main() -> None:
    args = parse_args()
    rows = iter_jsonl(args.request_file)
    if not rows:
        raise SystemExit(f"ERROR: request file has no rows: {format_display_path(args.request_file)}")

    provider = args.provider or unique_value(rows, "provider")
    defaults = provider_defaults(provider)
    base_url = args.base_url or defaults.get("base_url")
    if not base_url:
        raise SystemExit("ERROR: provide --base-url or use a known provider.")

    api_key = load_provider_key(provider, args.api_key_env, args.api_key_file)
    if args.check_credentials:
        print(f"{provider} credentials available: yes")
        return

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("ERROR: install the OpenAI Python SDK before running this script.") from exc

    slug = slug_from_request_path(args.request_file)
    response_file = args.response_file or DEFAULT_RESPONSE_DIR / f"{slug}_responses.jsonl"
    raw_output_file = args.raw_output_file or DEFAULT_RAW_DIR / f"{slug}_raw_outputs.jsonl"

    if args.overwrite:
        reset_output(response_file)
        reset_output(raw_output_file)

    completed = existing_prompt_ids(response_file, retry_errors=args.retry_errors) if args.resume else set()
    runnable_families = {"openai_compatible_chat", "openai_compatible_completion"}
    runnable_rows = [row for row in rows if row.get("request_family") in runnable_families]
    if len(runnable_rows) != len(rows):
        print(f"Skipping {len(rows) - len(runnable_rows)} incompatible request rows.")
    if args.only_prompt_id:
        requested_ids = set(args.only_prompt_id)
        available_ids = {str(row.get("prompt_id") or "") for row in runnable_rows}
        missing_ids = sorted(requested_ids - available_ids)
        if missing_ids:
            raise SystemExit(f"ERROR: requested prompt IDs are absent from the request file: {missing_ids}")
        runnable_rows = [
            row for row in runnable_rows if str(row.get("prompt_id") or "") in requested_ids
        ]
    if args.limit > 0:
        runnable_rows = runnable_rows[: args.limit]

    headers = dict(defaults.get("headers") or {})
    if provider == "openrouter":
        referer = os.environ.get("OPENROUTER_HTTP_REFERER", "").strip()
        title = os.environ.get("OPENROUTER_APP_TITLE", "").strip()
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-OpenRouter-Title"] = title

    client_kwargs: dict[str, Any] = {
        "api_key": api_key,
        "base_url": base_url,
        "default_headers": headers or None,
        # This runner owns retry policy through --max-retries. Disable the
        # SDK's hidden retry layer so timeout duration and trace counts remain
        # reproducible.
        "max_retries": 0,
    }
    if args.request_timeout_seconds > 0:
        client_kwargs["timeout"] = args.request_timeout_seconds
    client = OpenAI(**client_kwargs)
    success_count = 0
    error_count = 0
    skipped_count = 0
    attempted_count = 0

    for index, request in enumerate(runnable_rows, start=1):
        prompt_id = str(request["prompt_id"])
        if prompt_id in completed:
            skipped_count += 1
            continue
        if args.max_new > 0 and attempted_count >= args.max_new:
            break

        body = dict(request["request_body"])
        raw_row: dict[str, Any]
        response_row: dict[str, Any]
        attempt_trace: list[dict[str, Any]] = []
        for attempt in range(args.max_retries + 1):
            created_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
            try:
                if request.get("request_family") == "openai_compatible_completion":
                    completion = client.completions.create(**body)
                else:
                    completion = client.chat.completions.create(**body)
                raw = object_to_dict(completion)
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": request["row_id"],
                    "provider": provider,
                    "request_sha256": request.get("request_sha256", ""),
                    "created_at_utc": created_at_utc,
                    "raw_response": raw,
                }
                response_row = response_row_from_success(
                    request=request,
                    provider=provider,
                    base_url=base_url,
                    raw=raw,
                    created_at_utc=created_at_utc,
                )
                attempt_trace.append(
                    {
                        "attempt": attempt + 1,
                        "created_at_utc": created_at_utc,
                        "outcome": "success",
                    }
                )
                success_count += 1
                break
            except Exception as exc:  # provider SDK errors vary by endpoint
                attempt_trace.append(
                    {
                        "attempt": attempt + 1,
                        "created_at_utc": created_at_utc,
                        "outcome": "error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
                if attempt < args.max_retries:
                    time.sleep(max(1.0, 2.0**attempt))
                    continue
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": request["row_id"],
                    "provider": provider,
                    "request_sha256": request.get("request_sha256", ""),
                    "created_at_utc": created_at_utc,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                response_row = response_row_from_error(
                    request=request,
                    provider=provider,
                    base_url=base_url,
                    error=exc,
                    created_at_utc=created_at_utc,
                )
                error_count += 1
                if args.stop_on_error:
                    attach_attempt_trace(response_row, raw_row, attempt_trace)
                    append_jsonl(raw_output_file, raw_row)
                    append_jsonl(response_file, response_row)
                    print(f"{index}/{len(runnable_rows)} {prompt_id} error")
                    print(f"response file: {format_display_path(response_file)}")
                    print(f"raw output file: {format_display_path(raw_output_file)}")
                    raise SystemExit(
                        f"ERROR: {prompt_id}: {type(exc).__name__}: {exc}"
                    )

        attach_attempt_trace(response_row, raw_row, attempt_trace)
        append_jsonl(raw_output_file, raw_row)
        append_jsonl(response_file, response_row)
        attempted_count += 1
        print(f"{index}/{len(runnable_rows)} {prompt_id} {response_row['finish_reason']}")
        if args.max_new > 0 and attempted_count >= args.max_new:
            break
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print(f"response file: {format_display_path(response_file)}")
    print(f"raw output file: {format_display_path(raw_output_file)}")
    print(f"successes: {success_count}; errors: {error_count}; skipped: {skipped_count}")


if __name__ == "__main__":
    main()
