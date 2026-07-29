"""Audit completeness and trace consistency of an expanded model run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_model(batch_dir: Path, request_path: Path, expected_rows: int) -> dict[str, Any]:
    slug = request_path.name.removesuffix("_requests.jsonl")
    response_path = batch_dir / "responses" / f"{slug}_responses.jsonl"
    evaluation_path = (
        batch_dir
        / "evaluations"
        / slug
        / "pqid_bench_external_model_generation_harness_report.json"
    )
    requests = iter_jsonl(request_path)
    responses = iter_jsonl(response_path)
    request_by_prompt = {str(row.get("prompt_id") or ""): row for row in requests}
    response_by_prompt: dict[str, dict[str, Any]] = {}
    duplicate_prompt_ids = []
    hash_mismatches = []
    for response in responses:
        prompt_id = str(response.get("prompt_id") or "")
        if prompt_id in response_by_prompt:
            duplicate_prompt_ids.append(prompt_id)
        response_by_prompt[prompt_id] = response
        request = request_by_prompt.get(prompt_id)
        if request is None:
            hash_mismatches.append(f"{prompt_id}:missing_request")
            continue
        for field in ["request_sha256", "model_input_sha256", "prompt_record_sha256"]:
            if str(response.get(field) or "") != str(request.get(field) or ""):
                hash_mismatches.append(f"{prompt_id}:{field}")
    missing = sorted(set(request_by_prompt) - set(response_by_prompt))
    finish_counts = Counter(
        str(row.get("finish_reason") or "<missing>") for row in response_by_prompt.values()
    )
    error_prompts = sorted(
        prompt_id
        for prompt_id, row in response_by_prompt.items()
        if str(row.get("finish_reason") or "").lower() == "error"
    )
    resolved_models = sorted(
        {
            str(row.get("model_snapshot") or row.get("model") or "")
            for row in response_by_prompt.values()
            if row.get("model_snapshot") or row.get("model")
        }
    )
    evaluation_rows = None
    metrics = None
    if evaluation_path.exists():
        evaluation = load_json(evaluation_path)
        summary = evaluation.get("summary") or {}
        evaluation_rows = summary.get("rows")
        rates = summary.get("rates") or {}
        metrics = {
            "execution_success": rates.get("execution_success"),
            "structural_all_match": rates.get("structural_all_match"),
            "gate_types_match": rates.get("gate_types_match"),
            "qasm3_export_success": rates.get("qasm3_export_success"),
        }
    complete = (
        len(requests) == expected_rows
        and len(response_by_prompt) == expected_rows
        and not duplicate_prompt_ids
        and not missing
        and not error_prompts
        and not hash_mismatches
        and evaluation_rows == expected_rows
    )
    return {
        "slug": slug,
        "provider": requests[0].get("provider") if requests else None,
        "requested_model": requests[0].get("api_model_id") if requests else None,
        "resolved_models": resolved_models,
        "request_rows": len(requests),
        "response_rows": len(responses),
        "unique_response_prompts": len(response_by_prompt),
        "evaluation_rows": evaluation_rows,
        "finish_counts": dict(finish_counts),
        "missing_prompt_count": len(missing),
        "missing_prompts": missing,
        "error_prompt_count": len(error_prompts),
        "error_prompts": error_prompts,
        "duplicate_prompt_count": len(duplicate_prompt_ids),
        "duplicate_prompts": sorted(set(duplicate_prompt_ids)),
        "hash_mismatch_count": len(hash_mismatches),
        "hash_mismatches": hash_mismatches,
        "metrics": metrics,
        "status": "complete" if complete else "pending",
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench Expanded Model Run Status",
        "",
        f"- audited at UTC: `{payload['created_at_utc']}`",
        f"- expected prompts per model: `{payload['expected_rows']}`",
        f"- complete rows: `{payload['complete_model_count']}`",
        f"- pending rows: `{payload['pending_model_count']}`",
        "",
        "| provider | requested model | status | requests | unique responses | evaluation rows | execution | structural | finish reasons |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["models"]:
        metrics = row.get("metrics") or {}
        execution = metrics.get("execution_success")
        structural = metrics.get("structural_all_match")
        lines.append(
            f"| {row.get('provider') or ''} | `{row.get('requested_model') or ''}` | {row['status']} | "
            f"{row['request_rows']} | {row['unique_response_prompts']} | {row.get('evaluation_rows') or ''} | "
            f"{100 * execution:.2f}%" if isinstance(execution, (int, float)) else ""
        )
        # Replace the partially assembled row with a complete, precedence-safe rendering.
        lines[-1] = (
            f"| {row.get('provider') or ''} | `{row.get('requested_model') or ''}` | {row['status']} | "
            f"{row['request_rows']} | {row['unique_response_prompts']} | {row.get('evaluation_rows') or ''} | "
            f"{f'{100 * execution:.2f}%' if isinstance(execution, (int, float)) else ''} | "
            f"{f'{100 * structural:.2f}%' if isinstance(structural, (int, float)) else ''} | "
            f"`{json.dumps(row['finish_counts'], sort_keys=True)}` |"
        )
    pending = [row for row in payload["models"] if row["status"] != "complete"]
    if pending:
        lines.extend(["", "## Pending Details", ""])
        for row in pending:
            lines.append(
                f"- `{row['requested_model']}`: missing `{row['missing_prompt_count']}`, "
                f"error prompts `{row['error_prompt_count']}`, hash mismatches "
                f"`{row['hash_mismatch_count']}`, evaluation rows `{row['evaluation_rows']}`."
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=154)
    args = parser.parse_args()
    request_paths = sorted((args.batch_dir / "requests").glob("*_requests.jsonl"))
    models = [audit_model(args.batch_dir, path, args.expected_rows) for path in request_paths]
    complete_count = sum(row["status"] == "complete" for row in models)
    payload = {
        "schema_version": "pqid-bench-expanded-model-run-audit-v1",
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "expected_rows": args.expected_rows,
        "model_count": len(models),
        "complete_model_count": complete_count,
        "pending_model_count": len(models) - complete_count,
        "models": models,
    }
    json_path = args.batch_dir / "pqid_bench_expanded_model_run_status.json"
    md_path = args.batch_dir / "pqid_bench_expanded_model_run_status.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(md_path, payload)
    print(f"Complete model rows: {complete_count}/{len(models)}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
