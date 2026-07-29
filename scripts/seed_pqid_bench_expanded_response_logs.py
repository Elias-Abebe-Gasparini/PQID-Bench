"""Import verified 70-prompt pilot responses into a versioned expanded run.

The script never imports a pilot row unless its prompt ID, row ID, request hash,
model-input hash, and prompt-record hash match the corresponding request in the
expanded request file.  Original raw provider outputs remain in place and are
referenced by hash from the import manifest.
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
DEFAULT_PILOT_DIR = ARTIFACTS_DIR / "external_model_batches"
DEFAULT_EXPANDED_DIR = ARTIFACTS_DIR / "external_model_batches_154"
SCHEMA_VERSION = "pqid-bench-expanded-response-import-v1"
HASH_FIELDS = [
    "request_sha256",
    "model_input_sha256",
    "prompt_record_sha256",
]


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


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def raw_artifacts(pilot_dir: Path, slug: str) -> list[Path]:
    candidates = list(pilot_dir.glob(f"**/{slug}_raw_outputs.jsonl"))
    candidates.extend(pilot_dir.glob(f"**/{slug}_batch_output.jsonl"))
    candidates.extend(pilot_dir.glob(f"**/{slug}_batch_errors.jsonl"))
    return sorted({path.resolve(): path for path in candidates}.values(), key=lambda path: path.as_posix())


def validate_and_order(
    requests: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    slug: str,
) -> list[dict[str, Any]]:
    request_by_prompt = {str(row["prompt_id"]): row for row in requests}
    if len(request_by_prompt) != len(requests):
        raise ValueError(f"Duplicate prompt IDs in expanded request file for {slug}")
    response_by_prompt = {}
    for response in responses:
        prompt_id = str(response.get("prompt_id") or "")
        if not prompt_id or prompt_id in response_by_prompt:
            raise ValueError(f"Missing or duplicate pilot response prompt ID for {slug}: {prompt_id}")
        request = request_by_prompt.get(prompt_id)
        if request is None:
            raise ValueError(f"Pilot response {prompt_id} is absent from expanded requests for {slug}")
        if str(response.get("row_id") or "") != str(request.get("row_id") or ""):
            raise ValueError(f"Row ID mismatch for {slug} {prompt_id}")
        for field in HASH_FIELDS:
            if str(response.get(field) or "") != str(request.get(field) or ""):
                raise ValueError(f"{field} mismatch for {slug} {prompt_id}")
        response_by_prompt[prompt_id] = response

    if len(response_by_prompt) != 70:
        raise ValueError(f"Expected 70 pilot responses for {slug}, found {len(response_by_prompt)}")
    request_order = [str(row["prompt_id"]) for row in requests]
    expected_pilot = request_order[:70]
    if set(response_by_prompt) != set(expected_pilot):
        raise ValueError(f"Pilot responses do not correspond to the first 70 prompts for {slug}")
    return [response_by_prompt[prompt_id] for prompt_id in expected_pilot]


def write_manifest_md(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench 154-Run Pilot Response Import",
        "",
        f"- imported at UTC: `{manifest['created_at_utc']}`",
        f"- imported model rows: `{manifest['model_count']}`",
        "- each imported response was matched on prompt ID, row ID, and three request hashes",
        "- original raw provider outputs remain immutable in the 70-prompt pilot directory",
        "",
        "| model slug | imported rows | pilot response SHA-256 | expanded response SHA-256 | raw trace files |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for entry in manifest["models"]:
        lines.append(
            f"| `{entry['slug']}` | {entry['imported_rows']} | `{entry['pilot_response_sha256']}` | "
            f"`{entry['expanded_response_sha256']}` | {len(entry['raw_artifacts'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def seed(pilot_dir: Path, expanded_dir: Path, overwrite: bool) -> None:
    request_dir = expanded_dir / "requests"
    response_dir = expanded_dir / "responses"
    pilot_response_dir = pilot_dir / "responses"
    request_files = sorted(request_dir.glob("*_requests.jsonl"))
    if not request_files:
        raise FileNotFoundError(f"No expanded request files in {request_dir}")

    entries = []
    for request_path in request_files:
        slug = request_path.name.removesuffix("_requests.jsonl")
        pilot_response_path = pilot_response_dir / f"{slug}_responses.jsonl"
        expanded_response_path = response_dir / f"{slug}_responses.jsonl"
        if not pilot_response_path.exists():
            raise FileNotFoundError(f"Pilot response file missing for {slug}: {pilot_response_path}")
        if expanded_response_path.exists() and expanded_response_path.stat().st_size and not overwrite:
            raise FileExistsError(
                f"Expanded response file already contains data: {expanded_response_path}; use --overwrite"
            )

        requests = iter_jsonl(request_path)
        if len(requests) != 154:
            raise ValueError(f"Expected 154 expanded requests for {slug}, found {len(requests)}")
        pilot_responses = iter_jsonl(pilot_response_path)
        imported = validate_and_order(requests, pilot_responses, slug)
        write_jsonl(expanded_response_path, imported)

        raw_files = raw_artifacts(pilot_dir, slug)
        entries.append(
            {
                "slug": slug,
                "request_file": display_path(request_path),
                "request_sha256": sha256_file(request_path),
                "pilot_response_file": display_path(pilot_response_path),
                "pilot_response_sha256": sha256_file(pilot_response_path),
                "expanded_response_file": display_path(expanded_response_path),
                "expanded_response_sha256": sha256_file(expanded_response_path),
                "imported_rows": len(imported),
                "raw_artifacts": [
                    {"path": display_path(path), "sha256": sha256_file(path)}
                    for path in raw_files
                ],
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "pilot_dir": display_path(pilot_dir),
        "expanded_dir": display_path(expanded_dir),
        "model_count": len(entries),
        "models": entries,
    }
    manifest_dir = expanded_dir / "manifests"
    manifest_json = manifest_dir / "pilot_response_import_manifest.json"
    manifest_md = manifest_dir / "pilot_response_import_manifest.md"
    manifest_json.parent.mkdir(parents=True, exist_ok=True)
    manifest_json.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_md(manifest_md, manifest)
    print(f"Wrote {display_path(manifest_md)}")
    print(f"Imported 70 verified pilot responses for {len(entries)} model rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, default=DEFAULT_PILOT_DIR)
    parser.add_argument("--expanded-dir", type=Path, default=DEFAULT_EXPANDED_DIR)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    seed(args.pilot_dir, args.expanded_dir, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
