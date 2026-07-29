"""Merge disjoint PQID-Bench response logs against a frozen request order."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


HASH_FIELDS = ["request_sha256", "model_input_sha256", "prompt_record_sha256"]


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def merge(
    request_path: Path,
    input_paths: list[Path],
    output_path: Path,
    manifest_path: Path,
) -> None:
    requests = iter_jsonl(request_path)
    request_by_prompt = {str(row["prompt_id"]): row for row in requests}
    if len(request_by_prompt) != len(requests):
        raise ValueError("Frozen request file contains duplicate prompt IDs")

    responses: dict[str, dict[str, Any]] = {}
    input_entries = []
    for input_path in input_paths:
        rows = iter_jsonl(input_path)
        for response in rows:
            prompt_id = str(response.get("prompt_id") or "")
            request = request_by_prompt.get(prompt_id)
            if request is None:
                raise ValueError(f"Unknown response prompt ID {prompt_id} in {input_path}")
            if prompt_id in responses:
                raise ValueError(f"Response prompt ID occurs in multiple inputs: {prompt_id}")
            if str(response.get("row_id") or "") != str(request.get("row_id") or ""):
                raise ValueError(f"Row ID mismatch for {prompt_id}")
            for field in HASH_FIELDS:
                if str(response.get(field) or "") != str(request.get(field) or ""):
                    raise ValueError(f"{field} mismatch for {prompt_id}")
            responses[prompt_id] = response
        input_entries.append(
            {"path": str(input_path), "rows": len(rows), "sha256": sha256_file(input_path)}
        )

    missing = [str(row["prompt_id"]) for row in requests if str(row["prompt_id"]) not in responses]
    if missing:
        raise ValueError(f"Merged response set is incomplete: {missing[:10]}")
    merged = [responses[str(request["prompt_id"])] for request in requests]
    write_jsonl(output_path, merged)
    manifest = {
        "schema_version": "pqid-bench-response-merge-v1",
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "request_file": str(request_path),
        "request_rows": len(requests),
        "request_sha256": sha256_file(request_path),
        "input_response_files": input_entries,
        "output_response_file": str(output_path),
        "output_rows": len(merged),
        "output_sha256": sha256_file(output_path),
        "merge_policy": "disjoint prompt IDs ordered by frozen request manifest",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Merged rows: {len(merged)}")
    print(f"Output: {output_path}")
    print(f"Manifest: {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--input-response-file", type=Path, action="append", required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--manifest-file", type=Path, required=True)
    args = parser.parse_args()
    merge(args.request_file, args.input_response_file, args.output_file, args.manifest_file)


if __name__ == "__main__":
    main()
