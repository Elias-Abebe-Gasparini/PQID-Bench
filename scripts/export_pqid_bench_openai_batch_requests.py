"""Export OpenAI Batch API JSONL requests for PQID-Bench model evaluation.

The generic external-model request files under `artifacts/external_model_batches`
are provider-neutral traceability records. This script converts only the OpenAI
records into the concrete Batch API JSONL shape:

    {"custom_id": ..., "method": "POST", "url": "/v1/responses", "body": ...}

No API calls are made here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
GENERIC_REQUEST_DIR = ARTIFACTS_DIR / "external_model_batches" / "requests"
DEFAULT_OUTPUT_DIR = ARTIFACTS_DIR / "external_model_batches" / "openai_batch"
SCHEMA_VERSION = "pqid-bench-openai-batch-v1"


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def slug_from_request_path(path: Path) -> str:
    name = path.name
    suffix = "_requests.jsonl"
    return name[: -len(suffix)] if name.endswith(suffix) else path.stem


def openai_request_files(generic_request_dir: Path) -> list[Path]:
    return sorted(generic_request_dir.glob("openai_*_requests.jsonl"))


def convert_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for row in rows:
        if row.get("provider") != "openai":
            raise ValueError(f"Expected provider=openai, found {row.get('provider')}")
        body = row.get("request_body") or {}
        serialized_body = json.dumps(body, ensure_ascii=True)
        if "target_metadata" in serialized_body:
            raise ValueError(f"target_metadata leaked into request body for {row.get('prompt_id')}")
        converted.append(
            {
                "custom_id": row["prompt_id"],
                "method": "POST",
                "url": "/v1/responses",
                "body": body,
            }
        )
    return converted


def command_lines(slug: str) -> dict[str, str]:
    batch_request = f"artifacts/external_model_batches/openai_batch/requests/{slug}_batch_requests.jsonl"
    state_file = f"artifacts/external_model_batches/openai_batch/state/{slug}_batch_state.json"
    raw_output = f"artifacts/external_model_batches/openai_batch/raw_outputs/{slug}_batch_output.jsonl"
    raw_errors = f"artifacts/external_model_batches/openai_batch/raw_outputs/{slug}_batch_errors.jsonl"
    generic_request = f"artifacts/external_model_batches/requests/{slug}_requests.jsonl"
    response_log = f"artifacts/external_model_batches/responses/{slug}_responses.jsonl"
    evaluation_dir = f"artifacts/external_model_batches/evaluations/{slug}"
    return {
        "create_or_inspect_batch": (
            "python scripts/run_pqid_bench_openai_batch_job.py "
            f"--request-file {batch_request} "
            f"--state-file {state_file} "
            "--endpoint /v1/responses "
            "--completion-window 24h"
        ),
        "wait_and_download": (
            "python scripts/run_pqid_bench_openai_batch_job.py "
            f"--batch-id <BATCH_ID_FROM_STATE> "
            f"--state-file {state_file} "
            "--wait "
            f"--download-output-file {raw_output} "
            f"--download-error-file {raw_errors}"
        ),
        "materialize_response_log": (
            "python scripts/materialize_pqid_bench_openai_batch_responses.py "
            f"--request-file {generic_request} "
            f"--batch-output-file {raw_output} "
            f"--batch-error-file {raw_errors} "
            f"--output-file {response_log}"
        ),
        "score_response_log": (
            "python scripts/run_pqid_bench_external_model_generation_harness.py "
            "--prompt-path artifacts/pqid_bench_external_generation_prompts.jsonl "
            "--template-path artifacts/pqid_bench_external_generation_response_template.jsonl "
            f"--response-path {response_log} "
            f"--output-dir {evaluation_dir}"
        ),
    }


def write_manifest_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench OpenAI Batch Request Manifest",
        "",
        f"- exported at UTC: `{manifest['exported_at_utc']}`",
        f"- OpenAI request files: `{manifest['model_count']}`",
        "- API endpoint: `/v1/responses`",
        "- this file records batch inputs only; it is not a model result",
        "",
        "## Files",
        "",
        "| model | batch request file | rows | SHA-256 |",
        "| --- | --- | ---: | --- |",
    ]
    for entry in manifest["files"]:
        lines.append(
            f"| `{entry['model']}` | `{entry['batch_request_file']}` | "
            f"{entry['rows']} | `{entry['batch_request_sha256']}` |"
        )
    lines.extend(["", "## Commands", ""])
    for entry in manifest["files"]:
        lines.append(f"### {entry['model']}")
        lines.append("")
        for label, command in entry["commands"].items():
            lines.append(f"- {label}: `{command}`")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def export_openai_batches(generic_request_dir: Path, output_dir: Path) -> None:
    request_files = openai_request_files(generic_request_dir)
    if not request_files:
        raise FileNotFoundError(f"No OpenAI request files found in {generic_request_dir}")

    exported_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    batch_request_dir = output_dir / "requests"
    manifest_files = []

    for request_file in request_files:
        slug = slug_from_request_path(request_file)
        rows = iter_jsonl(request_file)
        converted = convert_rows(rows)
        batch_request_file = batch_request_dir / f"{slug}_batch_requests.jsonl"
        write_jsonl(batch_request_file, converted)
        first_model = rows[0].get("api_model_id") or rows[0].get("model") if rows else slug
        manifest_files.append(
            {
                "schema_version": SCHEMA_VERSION,
                "model": first_model,
                "slug": slug,
                "rows": len(converted),
                "generic_request_file": display_path(request_file),
                "generic_request_sha256": sha256_file(request_file),
                "batch_request_file": display_path(batch_request_file),
                "batch_request_sha256": sha256_file(batch_request_file),
                "commands": command_lines(slug),
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "exported_at_utc": exported_at_utc,
        "model_count": len(manifest_files),
        "files": manifest_files,
    }
    manifest_json = output_dir / "openai_batch_request_manifest.json"
    manifest_md = output_dir / "openai_batch_request_manifest.md"
    write_json(manifest_json, manifest)
    write_manifest_md(manifest_md, manifest)
    print(f"Wrote {display_path(manifest_md)}")
    print(f"Wrote {len(manifest_files)} OpenAI Batch request files under {display_path(batch_request_dir)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generic-request-dir", type=Path, default=GENERIC_REQUEST_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    export_openai_batches(generic_request_dir=args.generic_request_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
