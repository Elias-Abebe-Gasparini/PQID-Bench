"""Materialize OpenAI Batch outputs into PQID-Bench response logs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
DEFAULT_REQUEST_FILE = ARTIFACTS_DIR / "external_model_batches" / "requests" / "openai_gpt-5_5_requests.jsonl"
DEFAULT_BATCH_OUTPUT_FILE = (
    ARTIFACTS_DIR / "external_model_batches" / "openai_batch" / "raw_outputs" / "openai_gpt-5_5_batch_output.jsonl"
)
DEFAULT_BATCH_ERROR_FILE = (
    ARTIFACTS_DIR / "external_model_batches" / "openai_batch" / "raw_outputs" / "openai_gpt-5_5_batch_errors.jsonl"
)
DEFAULT_OUTPUT_FILE = ARTIFACTS_DIR / "external_model_batches" / "responses" / "openai_gpt-5_5_responses.jsonl"
SCHEMA_VERSION = "pqid-bench-external-model-batch-v1"


def iter_jsonl(path: Path, *, missing_ok: bool = False) -> list[dict[str, Any]]:
    if missing_ok and not path.exists():
        return []
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def strip_code_fences(text: object) -> str:
    rendered = str(text or "").strip()
    fenced = re.search(r"```(?:python|py)?\s*(.*?)```", rendered, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return rendered


def extract_response_text(body: dict[str, Any]) -> str:
    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in body.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"}:
                text = (
                    content.get("text")
                    or content.get("output_text")
                    or content.get("value")
                    or ""
                )
                if text:
                    chunks.append(str(text))
    return "".join(chunks).strip()


def unix_to_iso(value: Any) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC).replace(microsecond=0).isoformat()
    if isinstance(value, str) and value.strip():
        return value
    return ""


def canonical_custom_id(value: Any) -> str:
    text = str(value or "")
    if "::" in text:
        return text.split("::")[-1]
    return text


def batch_line_by_prompt(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped = {}
    for row in rows:
        prompt_id = canonical_custom_id(row.get("custom_id"))
        if prompt_id:
            mapped[prompt_id] = row
    return mapped


def error_by_prompt(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped = {}
    for row in rows:
        prompt_id = canonical_custom_id(row.get("custom_id"))
        if prompt_id:
            mapped[prompt_id] = row
    return mapped


def finish_reason(body: dict[str, Any], error: dict[str, Any] | None) -> str:
    if error:
        return "error"
    status = str(body.get("status") or "").strip()
    incomplete = body.get("incomplete_details") or {}
    if status == "incomplete" and incomplete.get("reason"):
        return f"incomplete:{incomplete['reason']}"
    if status:
        return status
    for item in body.get("output", []) or []:
        item_status = item.get("status")
        if item_status:
            return str(item_status)
    return ""


def response_row_from_batch(
    request: dict[str, Any],
    batch_line: dict[str, Any] | None,
    batch_error: dict[str, Any] | None,
) -> dict[str, Any]:
    response = (batch_line or {}).get("response") or {}
    body = response.get("body") or {}
    status_code = response.get("status_code")
    # A stale batch error file from an earlier retry can share custom IDs with a
    # later successful run. Only consult the external error map when there is no
    # successful output row for this prompt.
    if batch_line is not None and status_code == 200:
        error = body.get("error")
    else:
        error = (batch_line or {}).get("error") or batch_error or body.get("error")
    text = extract_response_text(body) if body else ""
    provider_metadata = {
        "batch_custom_id": (batch_line or batch_error or {}).get("custom_id"),
        "status_code": status_code,
        "batch_error": error or {},
        "response_status": body.get("status"),
        "incomplete_details": body.get("incomplete_details") or {},
    }
    if batch_line is None:
        provider_metadata["missing_batch_output"] = True
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": request["provider"],
        "model": body.get("model") or request["model"],
        "api_model_id": request["api_model_id"],
        "model_label": request["model_label"],
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request["request_sha256"],
        "model_input_sha256": request["model_input_sha256"],
        "prompt_record_sha256": request["prompt_record_sha256"],
        "generation_config": request["generation_config"],
        "created_at_utc": unix_to_iso(body.get("created_at")),
        "request_id": response.get("request_id") or body.get("id") or "",
        "system_fingerprint": body.get("system_fingerprint") or "",
        "model_snapshot": body.get("model") or "",
        "finish_reason": finish_reason(body, error if isinstance(error, dict) else None),
        "usage": body.get("usage") or {},
        "provider_metadata": provider_metadata,
        "generated_code": strip_code_fences(text),
        "raw_response": json.dumps(body, ensure_ascii=True, sort_keys=True) if body else "",
    }


def write_report(
    *,
    report_path: Path,
    request_file: Path,
    batch_output_file: Path,
    batch_error_file: Path,
    output_file: Path,
    rows: list[dict[str, Any]],
) -> None:
    finish_counts = Counter(row.get("finish_reason") or "<missing>" for row in rows)
    empty_count = sum(1 for row in rows if not str(row.get("generated_code") or "").strip())
    lines = [
        "# PQID-Bench OpenAI Batch Materialization Report",
        "",
        f"- request file: `{display_path(request_file)}`",
        f"- batch output file: `{display_path(batch_output_file)}`",
        f"- batch error file: `{display_path(batch_error_file)}`",
        f"- response log: `{display_path(output_file)}`",
        f"- rows: `{len(rows)}`",
        f"- empty generated code rows: `{empty_count}`",
        "",
        "## Finish Reasons",
        "",
        "| finish reason | rows |",
        "| --- | ---: |",
    ]
    for key, value in finish_counts.most_common():
        lines.append(f"| `{key}` | {value} |")
    write_text(report_path, "\n".join(lines) + "\n")


def materialize(
    request_file: Path,
    batch_output_file: Path,
    batch_error_file: Path,
    output_file: Path,
    report_file: Path,
) -> None:
    requests = iter_jsonl(request_file)
    output_rows = iter_jsonl(batch_output_file)
    error_rows = iter_jsonl(batch_error_file, missing_ok=True)
    outputs = batch_line_by_prompt(output_rows)
    errors = error_by_prompt(error_rows)

    materialized = []
    for request in requests:
        prompt_id = request["prompt_id"]
        materialized.append(
            response_row_from_batch(
                request=request,
                batch_line=outputs.get(prompt_id),
                batch_error=errors.get(prompt_id),
            )
        )
    write_jsonl(output_file, materialized)
    write_report(
        report_path=report_file,
        request_file=request_file,
        batch_output_file=batch_output_file,
        batch_error_file=batch_error_file,
        output_file=output_file,
        rows=materialized,
    )
    print(f"Wrote {display_path(output_file)}")
    print(f"Wrote {display_path(report_file)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-file", type=Path, default=DEFAULT_REQUEST_FILE)
    parser.add_argument("--batch-output-file", type=Path, default=DEFAULT_BATCH_OUTPUT_FILE)
    parser.add_argument("--batch-error-file", type=Path, default=DEFAULT_BATCH_ERROR_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--report-file", type=Path, default=None)
    args = parser.parse_args()
    report_file = args.report_file or args.output_file.with_name(args.output_file.stem + "_materialization_report.md")
    materialize(
        request_file=args.request_file,
        batch_output_file=args.batch_output_file,
        batch_error_file=args.batch_error_file,
        output_file=args.output_file,
        report_file=report_file,
    )


if __name__ == "__main__":
    main()
