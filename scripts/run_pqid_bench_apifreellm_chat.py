"""Run PQID-Bench prompts through the ApiFreeLLM chat API.

ApiFreeLLM's free endpoint is not OpenAI-compatible. This runner consumes the
frozen PQID-Bench external-generation prompt manifest directly and writes
response JSONL rows in the schema consumed by
`run_pqid_bench_external_model_generation_harness.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
PQID_ROOT = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else SUBMISSION_DIR
PQID_SCRIPTS_DIR = PQID_ROOT / "scripts"
if str(PQID_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PQID_SCRIPTS_DIR))

from project_paths import format_display_path, get_repo_root, get_user_secret_dir, load_secret  # noqa: E402


SCHEMA_VERSION = "pqid-bench-external-model-batch-v1"
DEFAULT_PROMPT_FILE = ARTIFACTS_DIR / "pqid_bench_external_generation_prompts.jsonl"
DEFAULT_RESPONSE_DIR = ARTIFACTS_DIR / "external_model_batches" / "responses"
DEFAULT_RAW_DIR = ARTIFACTS_DIR / "external_model_batches" / "apifreellm_api" / "raw_outputs"
DEFAULT_BASE_URL = "https://apifreellm.com/api/v1/chat"
DEFAULT_RESPONSE_FILE = DEFAULT_RESPONSE_DIR / "apifreellm_apifreellm_responses.jsonl"
DEFAULT_RAW_OUTPUT_FILE = DEFAULT_RAW_DIR / "apifreellm_apifreellm_raw_outputs.jsonl"


class ApiFreeLLMHTTPError(RuntimeError):
    """HTTP error wrapper that preserves status and response body."""

    def __init__(self, status: int, reason: str, body: str) -> None:
        self.status = status
        self.reason = reason
        self.body = body
        super().__init__(f"HTTP {status} {reason}: {body[:500]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT_FILE)
    parser.add_argument(
        "--request-file",
        type=Path,
        default=None,
        help="Compatibility alias for --prompt-file.",
    )
    parser.add_argument("--response-file", type=Path, default=DEFAULT_RESPONSE_FILE)
    parser.add_argument("--raw-output-file", type=Path, default=DEFAULT_RAW_OUTPUT_FILE)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="APIFREELLM_API_KEY")
    parser.add_argument("--api-key-file", default="")
    parser.add_argument("--model", default="apifreellm")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=25.0,
        help="Delay between requests. Free tier documents one request every 20 seconds.",
    )
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--request-timeout-seconds", type=float, default=120.0)
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
        help="Load the ApiFreeLLM key and print whether it is available, without calling the API.",
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


def secret_file_candidates(explicit_path: str) -> list[Path]:
    if explicit_path:
        return [Path(explicit_path).expanduser()]
    repo_root = get_repo_root(__file__)
    secret_dir = get_user_secret_dir()
    file_names = [".apifreellm_api_key", "apifreellm_api_key.txt", "APIFREELLM_API_KEY"]
    candidates = []
    for name in file_names:
        candidates.extend([repo_root / name, PQID_ROOT / name, secret_dir / name])
    return candidates


def load_apifreellm_key(api_key_env: str, api_key_file: str) -> str:
    return load_secret(
        env_name=api_key_env,
        file_env_name=f"{api_key_env}_FILE",
        file_candidates=secret_file_candidates(api_key_file),
        named_file_candidates=["APIFREELLM_API_KEY"],
        label="ApiFreeLLM API key",
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


def call_apifreellm(
    *,
    prompt: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    body: dict[str, Any] = {"message": prompt}
    if model:
        body["model"] = model
    timeout = timeout_seconds if timeout_seconds > 0 else None
    response = requests.post(
        base_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "PQID-Bench/1.0 research reproducibility runner",
        },
        json=body,
        timeout=timeout,
    )
    if not response.ok:
        raise ApiFreeLLMHTTPError(response.status_code, response.reason, response.text)
    return response.json()


def generated_text(raw: dict[str, Any]) -> str:
    return str(raw.get("response") or "").strip()


def response_row_from_success(
    *,
    prompt_row: dict[str, Any],
    model: str,
    base_url: str,
    raw: dict[str, Any],
    created_at_utc: str,
) -> dict[str, Any]:
    resolved_model = str(raw.get("model") or model or "apifreellm")
    success = bool(raw.get("success", True))
    finish_reason = "stop" if success else "error"
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": "apifreellm_apifreellm_single_pass_free_tier",
        "provider": "apifreellm",
        "model": resolved_model,
        "api_model_id": model,
        "model_label": "ApiFreeLLM free endpoint",
        "prompt_id": prompt_row["prompt_id"],
        "row_id": prompt_row["row_id"],
        "request_sha256": "",
        "model_input_sha256": "",
        "prompt_record_sha256": "",
        "generation_config": {
            "single_pass": True,
            "temperature": None,
            "free_tier_rate_limit_seconds": 20,
        },
        "created_at_utc": created_at_utc,
        "request_id": str(raw.get("id") or ""),
        "system_fingerprint": "",
        "model_snapshot": resolved_model,
        "finish_reason": finish_reason,
        "usage": raw.get("usage") or {},
        "provider_metadata": {
            "base_url": base_url,
            "tier": raw.get("tier", ""),
            "features": raw.get("features", {}),
            "finish_reason_inferred": True,
            "model_identity_note": "ApiFreeLLM free endpoint does not document a stable underlying model ID.",
        },
        "generated_code": generated_text(raw),
        "raw_response": json.dumps(raw, ensure_ascii=True, sort_keys=True),
    }


def response_row_from_error(
    *,
    prompt_row: dict[str, Any],
    model: str,
    base_url: str,
    error: Exception,
    created_at_utc: str,
) -> dict[str, Any]:
    provider_metadata = {
        "base_url": base_url,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if isinstance(error, ApiFreeLLMHTTPError):
        provider_metadata["http_status"] = error.status
        provider_metadata["http_reason"] = error.reason
        provider_metadata["http_body"] = error.body
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": "apifreellm_apifreellm_single_pass_free_tier",
        "provider": "apifreellm",
        "model": model,
        "api_model_id": model,
        "model_label": "ApiFreeLLM free endpoint",
        "prompt_id": prompt_row["prompt_id"],
        "row_id": prompt_row["row_id"],
        "request_sha256": "",
        "model_input_sha256": "",
        "prompt_record_sha256": "",
        "generation_config": {
            "single_pass": True,
            "temperature": None,
            "free_tier_rate_limit_seconds": 20,
        },
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
    prompt_file = args.request_file or args.prompt_file
    rows = iter_jsonl(prompt_file)
    if not rows:
        raise SystemExit(f"ERROR: prompt file has no rows: {format_display_path(prompt_file)}")

    api_key = load_apifreellm_key(args.api_key_env, args.api_key_file)
    if args.check_credentials:
        print("ApiFreeLLM credentials available: yes")
        return

    if args.overwrite:
        reset_output(args.response_file)
        reset_output(args.raw_output_file)

    completed = existing_prompt_ids(args.response_file, retry_errors=args.retry_errors) if args.resume else set()
    runnable_rows = rows[: args.limit] if args.limit > 0 else rows

    success_count = 0
    error_count = 0
    skipped_count = 0

    for index, prompt_row in enumerate(runnable_rows, start=1):
        prompt_id = str(prompt_row["prompt_id"])
        if prompt_id in completed:
            skipped_count += 1
            continue

        raw_row: dict[str, Any] = {}
        response_row: dict[str, Any] = {}
        for attempt in range(args.max_retries + 1):
            created_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
            try:
                raw = call_apifreellm(
                    prompt=str(prompt_row.get("prompt") or ""),
                    model=args.model,
                    api_key=api_key,
                    base_url=args.base_url,
                    timeout_seconds=args.request_timeout_seconds,
                )
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": prompt_row["row_id"],
                    "provider": "apifreellm",
                    "created_at_utc": created_at_utc,
                    "raw_response": raw,
                }
                response_row = response_row_from_success(
                    prompt_row=prompt_row,
                    model=args.model,
                    base_url=args.base_url,
                    raw=raw,
                    created_at_utc=created_at_utc,
                )
                if response_row["finish_reason"] == "error":
                    error_count += 1
                else:
                    success_count += 1
                break
            except Exception as exc:  # provider errors vary by endpoint/load
                if attempt < args.max_retries:
                    time.sleep(max(args.sleep_seconds, 2.0**attempt))
                    continue
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": prompt_row["row_id"],
                    "provider": "apifreellm",
                    "created_at_utc": created_at_utc,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                response_row = response_row_from_error(
                    prompt_row=prompt_row,
                    model=args.model,
                    base_url=args.base_url,
                    error=exc,
                    created_at_utc=created_at_utc,
                )
                error_count += 1
                if args.stop_on_error:
                    append_jsonl(args.raw_output_file, raw_row)
                    append_jsonl(args.response_file, response_row)
                    raise

        append_jsonl(args.raw_output_file, raw_row)
        append_jsonl(args.response_file, response_row)
        print(f"{index}/{len(runnable_rows)} {prompt_id} {response_row['finish_reason']}")
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print(f"response file: {format_display_path(args.response_file)}")
    print(f"raw output file: {format_display_path(args.raw_output_file)}")
    print(f"successes: {success_count}; errors: {error_count}; skipped: {skipped_count}")


if __name__ == "__main__":
    main()
