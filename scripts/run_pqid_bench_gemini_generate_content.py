"""Run PQID-Bench external generation rows through the Gemini API.

This runner consumes request rows exported with request_family
`gemini_generate_content` and writes response JSONL rows in the same schema
consumed by `run_pqid_bench_external_model_generation_harness.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
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
DEFAULT_RESPONSE_DIR = ARTIFACTS_DIR / "external_model_batches" / "responses"
DEFAULT_RAW_DIR = ARTIFACTS_DIR / "external_model_batches" / "gemini_api" / "raw_outputs"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiHTTPError(RuntimeError):
    """HTTP error wrapper that preserves status and response body."""

    def __init__(self, status: int, reason: str, body: str) -> None:
        super().__init__(f"HTTP {status} {reason}: {body}")
        self.status = status
        self.reason = reason
        self.body = body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--response-file", type=Path, default=None)
    parser.add_argument("--raw-output-file", type=Path, default=None)
    parser.add_argument("--api-key-env", default="GEMINI_API_KEY")
    parser.add_argument("--api-key-file", default="")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--max-retries", type=int, default=2)
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
        help="Load the Gemini key and print whether it is available, without calling the API.",
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


def secret_file_candidates(explicit_path: str) -> list[Path]:
    if explicit_path:
        return [Path(explicit_path).expanduser()]
    repo_root = get_repo_root(__file__)
    secret_dir = get_user_secret_dir()
    file_names = [".gemini_api_key", "gemini_api_key.txt", "GEMINI_API_KEY"]
    candidates = []
    for name in file_names:
        candidates.extend([repo_root / name, PQID_ROOT / name, secret_dir / name])
    return candidates


def load_gemini_key(api_key_env: str, api_key_file: str) -> str:
    return load_secret(
        env_name=api_key_env,
        file_env_name=f"{api_key_env}_FILE",
        file_candidates=secret_file_candidates(api_key_file),
        named_file_candidates=None,
        label="Gemini API key",
    )


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


def generation_config_for_api(config: dict[str, Any]) -> dict[str, Any]:
    mapped = {}
    if "temperature" in config:
        mapped["temperature"] = config["temperature"]
    if "top_p" in config:
        mapped["topP"] = config["top_p"]
    if "max_output_tokens" in config:
        mapped["maxOutputTokens"] = config["max_output_tokens"]
    return mapped


def request_body_for_api(request: dict[str, Any]) -> dict[str, Any]:
    body = dict(request.get("request_body") or {})
    body.pop("model", None)
    if "system_instruction" in body:
        body["systemInstruction"] = body.pop("system_instruction")
    if "generation_config" in body:
        body["generationConfig"] = generation_config_for_api(body.pop("generation_config") or {})
    return body


def text_from_response(raw: dict[str, Any]) -> str:
    candidates = raw.get("candidates") or []
    if not candidates:
        return ""
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    text_parts = []
    for part in parts:
        if isinstance(part, dict) and part.get("text") is not None:
            text_parts.append(str(part.get("text") or ""))
    return "\n".join(part for part in text_parts if part).strip()


def finish_reason_from_response(raw: dict[str, Any]) -> str:
    candidates = raw.get("candidates") or []
    if not candidates:
        return ""
    return str(candidates[0].get("finishReason") or "")


def call_gemini(request: dict[str, Any], api_key: str, base_url: str) -> dict[str, Any]:
    model = str(request.get("api_model_id") or request.get("model") or "")
    if not model:
        raise ValueError("Gemini request row is missing api_model_id/model.")
    quoted_model = urllib.parse.quote(f"models/{model}", safe="/")
    query = urllib.parse.urlencode({"key": api_key})
    url = f"{base_url.rstrip('/')}/{quoted_model}:generateContent?{query}"
    payload = json.dumps(request_body_for_api(request), ensure_ascii=True).encode("utf-8")
    http_request = urllib.request.Request(
        url=url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(http_request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GeminiHTTPError(exc.code, exc.reason, body) from exc


def response_row_from_success(
    *,
    request: dict[str, Any],
    base_url: str,
    raw: dict[str, Any],
    created_at_utc: str,
) -> dict[str, Any]:
    requested_model = str(request.get("api_model_id") or request.get("model") or "")
    resolved_model = str(raw.get("modelVersion") or requested_model)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": "google",
        "model": resolved_model,
        "api_model_id": requested_model,
        "model_label": request.get("model_label", ""),
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request.get("request_sha256", ""),
        "model_input_sha256": request.get("model_input_sha256", ""),
        "prompt_record_sha256": request.get("prompt_record_sha256", ""),
        "generation_config": request.get("generation_config", {}),
        "created_at_utc": created_at_utc,
        "request_id": str(raw.get("responseId") or ""),
        "system_fingerprint": "",
        "model_snapshot": resolved_model,
        "finish_reason": finish_reason_from_response(raw),
        "usage": raw.get("usageMetadata") or {},
        "provider_metadata": {
            "base_url": base_url,
            "request_provider": request.get("provider", ""),
            "response_model_version": str(raw.get("modelVersion") or ""),
        },
        "generated_code": text_from_response(raw),
        "raw_response": json.dumps(raw, ensure_ascii=True, sort_keys=True),
    }


def response_row_from_error(
    *,
    request: dict[str, Any],
    base_url: str,
    error: Exception,
    created_at_utc: str,
) -> dict[str, Any]:
    provider_metadata = {
        "base_url": base_url,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "request_provider": request.get("provider", ""),
    }
    if isinstance(error, GeminiHTTPError):
        provider_metadata["http_status"] = error.status
        provider_metadata["http_reason"] = error.reason
        provider_metadata["http_body"] = error.body
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": "google",
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
        "provider_metadata": provider_metadata,
        "generated_code": "",
        "raw_response": "",
    }


def main() -> None:
    args = parse_args()
    rows = iter_jsonl(args.request_file)
    if not rows:
        raise SystemExit(f"ERROR: request file has no rows: {format_display_path(args.request_file)}")

    api_key = load_gemini_key(args.api_key_env, args.api_key_file)
    if args.check_credentials:
        print("Gemini credentials available: yes")
        return

    slug = slug_from_request_path(args.request_file)
    response_file = args.response_file or DEFAULT_RESPONSE_DIR / f"{slug}_responses.jsonl"
    raw_output_file = args.raw_output_file or DEFAULT_RAW_DIR / f"{slug}_raw_outputs.jsonl"

    if args.overwrite:
        reset_output(response_file)
        reset_output(raw_output_file)

    completed = existing_prompt_ids(response_file, retry_errors=args.retry_errors) if args.resume else set()
    runnable_rows = [row for row in rows if row.get("request_family") == "gemini_generate_content"]
    if len(runnable_rows) != len(rows):
        print(f"Skipping {len(rows) - len(runnable_rows)} non-Gemini request rows.")
    if args.limit > 0:
        runnable_rows = runnable_rows[: args.limit]

    success_count = 0
    error_count = 0
    skipped_count = 0

    for index, request in enumerate(runnable_rows, start=1):
        prompt_id = str(request.get("prompt_id") or "")
        if prompt_id in completed:
            skipped_count += 1
            continue

        raw_row: dict[str, Any] = {}
        response_row: dict[str, Any] = {}
        attempt_trace: list[dict[str, Any]] = []
        for attempt in range(args.max_retries + 1):
            created_at_utc = datetime.now(UTC).isoformat(timespec="seconds")
            try:
                raw = call_gemini(request, api_key=api_key, base_url=args.base_url)
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": request["row_id"],
                    "provider": "google",
                    "request_sha256": request.get("request_sha256", ""),
                    "created_at_utc": created_at_utc,
                    "raw_response": raw,
                }
                response_row = response_row_from_success(
                    request=request,
                    base_url=args.base_url,
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
            except Exception as exc:  # provider errors vary by endpoint
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
                    "provider": "google",
                    "request_sha256": request.get("request_sha256", ""),
                    "created_at_utc": created_at_utc,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                response_row = response_row_from_error(
                    request=request,
                    base_url=args.base_url,
                    error=exc,
                    created_at_utc=created_at_utc,
                )
                error_count += 1
                if args.stop_on_error:
                    attach_attempt_trace(response_row, raw_row, attempt_trace)
                    append_jsonl(raw_output_file, raw_row)
                    append_jsonl(response_file, response_row)
                    raise

        attach_attempt_trace(response_row, raw_row, attempt_trace)
        append_jsonl(raw_output_file, raw_row)
        append_jsonl(response_file, response_row)
        print(f"{index}/{len(runnable_rows)} {prompt_id} {response_row['finish_reason']}")
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print(f"response file: {format_display_path(response_file)}")
    print(f"raw output file: {format_display_path(raw_output_file)}")
    print(f"successes: {success_count}; errors: {error_count}; skipped: {skipped_count}")


if __name__ == "__main__":
    main()
