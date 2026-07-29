"""Run PQID-Bench text-generation requests through HF Inference Providers.

This adapter is for provider-hosted checkpoints that support text generation
but are not exposed as chat-completion models. It preserves the exported
rendered prompt and writes the same response-log schema as the other external
model runners.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from run_pqid_bench_openai_compatible_chat import (
    append_jsonl,
    existing_prompt_ids,
    format_display_path,
    iter_jsonl,
    load_provider_key,
    object_to_dict,
    reset_output,
    response_row_from_error,
    response_row_from_success,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--raw-output-file", type=Path)
    parser.add_argument("--inference-provider", default="featherless-ai")
    parser.add_argument(
        "--chat-template",
        choices=("raw", "qiskit-mistral"),
        default="raw",
        help="Optional local chat-template rendering before text generation.",
    )
    parser.add_argument("--api-key-file", default="")
    parser.add_argument("--check-credentials", action="store_true")
    parser.add_argument("--only-prompt-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-new", type=int, default=0)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--request-timeout-seconds", type=float, default=300.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    return parser.parse_args()


def routed_model_id(request: dict[str, Any], inference_provider: str) -> str:
    model_id = str(request.get("api_model_id") or request.get("model") or "")
    suffix = f":{inference_provider}"
    return model_id[: -len(suffix)] if model_id.endswith(suffix) else model_id


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            str(block.get("text") or "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(parts)
    raise ValueError(f"Unsupported message content type: {type(content).__name__}")


def render_qiskit_mistral_prompt(request: dict[str, Any]) -> str:
    """Apply the checkpoint's official Mistral system/instruction framing.

    The official ``chat_template.jinja`` wraps the first system message in
    ``[SYSTEM_PROMPT]`` and each user message in ``[INST]``. PQID-Bench's
    frozen requests contain exactly one system message followed by one user
    message, so no default checkpoint system prompt is injected here.
    """

    messages = request.get("model_input", {}).get("messages") or []
    roles = tuple(str(message.get("role") or "") for message in messages)
    if roles != ("system", "user"):
        raise ValueError(
            "Qiskit Mistral rendering expects one system and one user message; "
            f"received roles {roles}."
        )
    system_text = message_text(messages[0])
    user_text = message_text(messages[1])
    return (
        f"<s>[SYSTEM_PROMPT]{system_text}[/SYSTEM_PROMPT]"
        f"[INST]{user_text}[/INST]"
    )


def request_prompt(request: dict[str, Any], chat_template: str) -> str:
    if chat_template == "qiskit-mistral":
        return render_qiskit_mistral_prompt(request)
    body = request.get("request_body") or {}
    return str(body.get("prompt") or "")


def normalized_response(
    result: Any,
    *,
    model_id: str,
    inference_provider: str,
) -> dict[str, Any]:
    native = object_to_dict(result)
    generated = str(native.get("generated_text") or "")
    details = native.get("details") or {}
    prefill = details.get("prefill") or []
    tokens = details.get("tokens") or []
    generated_tokens = int(details.get("generated_tokens") or len(tokens))
    finish_reason = str(details.get("finish_reason") or "")
    return {
        "object": "text_generation",
        "model": model_id,
        "provider": inference_provider,
        "choices": [
            {
                "index": 0,
                "text": generated,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": len(prefill),
            "completion_tokens": generated_tokens,
            "total_tokens": len(prefill) + generated_tokens,
        },
        "native_response": native,
    }


def is_retryable_error(error: Exception) -> bool:
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    return status_code not in {400, 401, 402, 403, 404, 422}


def main() -> None:
    args = parse_args()
    rows = iter_jsonl(args.request_file)
    if not rows:
        raise SystemExit(f"ERROR: request file has no rows: {format_display_path(args.request_file)}")

    api_key = load_provider_key("huggingface_router", "", args.api_key_file)
    if args.check_credentials:
        print("huggingface_router credentials available: yes")
        return

    try:
        from huggingface_hub import InferenceClient
    except ImportError as exc:
        raise SystemExit("ERROR: install a current huggingface_hub package before running this script.") from exc

    runnable_rows = [
        row for row in rows if row.get("request_family") == "openai_compatible_completion"
    ]
    if len(runnable_rows) != len(rows):
        print(f"Skipping {len(rows) - len(runnable_rows)} non-text-generation request rows.")
    if args.only_prompt_id:
        requested = set(args.only_prompt_id)
        available = {str(row.get("prompt_id") or "") for row in runnable_rows}
        missing = sorted(requested - available)
        if missing:
            raise SystemExit(f"ERROR: requested prompt IDs are absent from the request file: {missing}")
        runnable_rows = [
            row for row in runnable_rows if str(row.get("prompt_id") or "") in requested
        ]
    if args.limit > 0:
        runnable_rows = runnable_rows[: args.limit]

    slug = args.request_file.stem.removesuffix("_requests")
    response_file = args.response_file or args.request_file.parent.parent / "responses" / f"{slug}_responses.jsonl"
    raw_output_file = args.raw_output_file or args.request_file.parent.parent / "raw_outputs" / f"{slug}_raw.jsonl"
    if args.overwrite:
        reset_output(response_file)
        reset_output(raw_output_file)

    completed = existing_prompt_ids(response_file, retry_errors=args.retry_errors) if args.resume else set()
    client = InferenceClient(
        provider=args.inference_provider,
        api_key=api_key,
        timeout=args.request_timeout_seconds,
    )
    base_url = f"huggingface-inference-provider:{args.inference_provider}"
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
        attempted_count += 1

        body = request.get("request_body") or {}
        prompt = request_prompt(request, args.chat_template)
        call_prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        model_id = routed_model_id(request, args.inference_provider)
        max_new_tokens = int(body.get("max_tokens") or 2048)
        created_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()

        for attempt in range(args.max_retries + 1):
            try:
                result = client.text_generation(
                    prompt,
                    model=model_id,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    details=True,
                    return_full_text=False,
                )
                raw = normalized_response(
                    result,
                    model_id=model_id,
                    inference_provider=args.inference_provider,
                )
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": request["row_id"],
                    "provider": "huggingface_router",
                    "inference_provider": args.inference_provider,
                    "request_sha256": request.get("request_sha256", ""),
                    "call_prompt_sha256": call_prompt_sha256,
                    "chat_template": args.chat_template,
                    "created_at_utc": created_at_utc,
                    "raw_response": raw,
                }
                response_row = response_row_from_success(
                    request=request,
                    provider="huggingface_router",
                    base_url=base_url,
                    raw=raw,
                    created_at_utc=created_at_utc,
                )
                response_row["call_prompt_sha256"] = call_prompt_sha256
                response_row["chat_template"] = args.chat_template
                success_count += 1
                break
            except Exception as exc:
                if attempt < args.max_retries and is_retryable_error(exc):
                    time.sleep(max(1.0, 2.0**attempt))
                    continue
                raw_row = {
                    "prompt_id": prompt_id,
                    "row_id": request["row_id"],
                    "provider": "huggingface_router",
                    "inference_provider": args.inference_provider,
                    "request_sha256": request.get("request_sha256", ""),
                    "call_prompt_sha256": call_prompt_sha256,
                    "chat_template": args.chat_template,
                    "created_at_utc": created_at_utc,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                response_row = response_row_from_error(
                    request=request,
                    provider="huggingface_router",
                    base_url=base_url,
                    error=exc,
                    created_at_utc=created_at_utc,
                )
                response_row["call_prompt_sha256"] = call_prompt_sha256
                response_row["chat_template"] = args.chat_template
                error_count += 1

        append_jsonl(raw_output_file, raw_row)
        append_jsonl(response_file, response_row)
        print(f"{index}/{len(runnable_rows)} {prompt_id} {response_row['finish_reason']}")
        if response_row["finish_reason"] == "error" and args.stop_on_error:
            raise SystemExit(
                f"ERROR: {prompt_id}: {raw_row.get('error_type')}: {raw_row.get('error_message')}"
            )
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print(f"response file: {format_display_path(response_file)}")
    print(f"raw output file: {format_display_path(raw_output_file)}")
    print(f"successes: {success_count}; errors: {error_count}; skipped: {skipped_count}")


if __name__ == "__main__":
    main()
