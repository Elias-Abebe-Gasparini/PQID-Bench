"""Canonicalize an append-only response log after interrupted resume overlap.

The original response file is preserved verbatim in an audit directory.  For
each requested prompt, the canonical log keeps the earliest non-error response;
an error is retained only when no successful response exists.  All superseded
rows remain available in a separate JSONL audit file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


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


def is_error(row: dict[str, Any]) -> bool:
    return str(row.get("finish_reason") or "").lower() == "error"


def canonicalize(request_path: Path, response_path: Path, audit_dir: Path) -> None:
    requests = iter_jsonl(request_path)
    responses = iter_jsonl(response_path)
    slug = response_path.name.removesuffix("_responses.jsonl")
    request_by_prompt = {str(row["prompt_id"]): row for row in requests}
    if len(request_by_prompt) != len(requests):
        raise ValueError("Request file contains duplicate prompt IDs")

    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, response in enumerate(responses):
        prompt_id = str(response.get("prompt_id") or "")
        request = request_by_prompt.get(prompt_id)
        if request is None:
            raise ValueError(f"Response prompt is absent from request file: {prompt_id}")
        if str(response.get("row_id") or "") != str(request.get("row_id") or ""):
            raise ValueError(f"Row ID mismatch for {prompt_id}")
        if str(response.get("request_sha256") or "") != str(request.get("request_sha256") or ""):
            raise ValueError(f"Request hash mismatch for {prompt_id}")
        grouped[prompt_id].append((index, response))

    missing = [prompt_id for prompt_id in request_by_prompt if prompt_id not in grouped]
    if missing:
        raise ValueError(f"Cannot canonicalize an incomplete log; missing prompts: {missing[:5]}")

    selected_by_prompt: dict[str, tuple[int, dict[str, Any]]] = {}
    superseded: list[dict[str, Any]] = []
    for prompt_id, candidates in grouped.items():
        successful = [item for item in candidates if not is_error(item[1])]
        pool = successful or candidates
        selected = min(
            pool,
            key=lambda item: (
                str(item[1].get("created_at_utc") or ""),
                item[0],
            ),
        )
        selected_by_prompt[prompt_id] = selected
        for item in candidates:
            if item[0] != selected[0]:
                superseded.append(
                    {
                        "superseded_reason": "duplicate successful call" if not is_error(item[1]) else "retryable API error",
                        "original_file_index": item[0],
                        "response": item[1],
                    }
                )

    canonical = [selected_by_prompt[str(request["prompt_id"])][1] for request in requests]
    if len(canonical) != len(requests):
        raise RuntimeError("Canonical response count differs from request count")

    audit_dir.mkdir(parents=True, exist_ok=True)
    original_path = audit_dir / f"{slug}_responses_precanonical.jsonl"
    superseded_path = audit_dir / f"{slug}_superseded_rows.jsonl"
    manifest_path = audit_dir / f"{slug}_canonicalization_manifest.json"
    if original_path.exists() or superseded_path.exists() or manifest_path.exists():
        raise FileExistsError(f"Canonicalization audit already exists for {slug}")

    write_jsonl(original_path, responses)
    write_jsonl(superseded_path, superseded)
    original_sha = sha256_file(response_path)
    write_jsonl(response_path, canonical)
    manifest = {
        "schema_version": "pqid-bench-response-canonicalization-v1",
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "selection_policy": "earliest non-error response by created_at_utc, then append order",
        "request_file": str(request_path),
        "response_file": str(response_path),
        "original_response_file": str(original_path),
        "superseded_response_file": str(superseded_path),
        "request_rows": len(requests),
        "original_response_rows": len(responses),
        "canonical_response_rows": len(canonical),
        "superseded_rows": len(superseded),
        "original_response_sha256": original_sha,
        "canonical_response_sha256": sha256_file(response_path),
        "original_audit_sha256": sha256_file(original_path),
        "superseded_audit_sha256": sha256_file(superseded_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Canonical rows: {len(canonical)}")
    print(f"Superseded rows preserved: {len(superseded)}")
    print(f"Manifest: {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--response-file", type=Path, required=True)
    parser.add_argument("--audit-dir", type=Path, required=True)
    args = parser.parse_args()
    canonicalize(args.request_file, args.response_file, args.audit_dir)


if __name__ == "__main__":
    main()
