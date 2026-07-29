"""Audit the safe-built-in evaluator correction on the frozen 21-model matrix."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import run_pqid_bench_executable_validity_check as validity
import run_pqid_bench_external_model_generation_harness as harness
import run_pqid_bench_generation_copy_baseline as copy_baseline
from analyze_pqid_bench_inferential import DEFAULT_EVAL_DIRS, REPORT_NAME, read_jsonl
from pqid_bench_model_registry import MODEL_LABELS, MODEL_ORDER, model_from_report_dir


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
SPLIT_MANIFEST_PATH = ROOT / "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
CORRECTION_DIR = ROOT / "artifacts/analysis_154/evaluator_builtin_correction"
JSON_OUT = CORRECTION_DIR / "evaluator_builtin_correction_report.json"
MD_OUT = CORRECTION_DIR / "evaluator_builtin_correction_report.md"
CELL_OUT = CORRECTION_DIR / "evaluator_builtin_correction_cell_audit.jsonl"
TSV_OUT = ROOT / "tables_copy_ready/table_s31_evaluator_version_impact.tsv"

LEGACY_EVALUATOR_VERSION = "pqid-bench-evaluator-1.0.0-restricted-builtins"
CANONICAL_EVALUATOR_VERSION = validity.EVALUATOR_VERSION
STRUCTURAL_PREDICATE_VERSION = validity.STRUCTURAL_PREDICATE_VERSION


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f} pp"


def load_reports() -> list[tuple[str, Path, dict[str, Any]]]:
    reports: list[tuple[str, Path, dict[str, Any]]] = []
    seen: set[str] = set()
    for eval_dir in DEFAULT_EVAL_DIRS:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            if model not in MODEL_ORDER:
                continue
            if model in seen:
                raise ValueError(f"Duplicate canonical report for {model}")
            reports.append(
                (model, report_path, json.loads(report_path.read_text(encoding="utf-8")))
            )
            seen.add(model)
    missing = [model for model in MODEL_ORDER if model not in seen]
    if missing:
        raise ValueError(f"Missing canonical reports: {missing}")
    reports.sort(key=lambda item: MODEL_ORDER.index(item[0]))
    return reports


def stamp_canonical_report_versions(
    reports: list[tuple[str, Path, dict[str, Any]]],
) -> int:
    """Attach evaluator provenance to the frozen canonical report files."""

    stamped = 0
    for _, report_path, report in reports:
        report["evaluator_version"] = CANONICAL_EVALUATOR_VERSION
        report["structural_predicate_version"] = STRUCTURAL_PREDICATE_VERSION
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        markdown_path = report_path.with_suffix(".md")
        markdown = markdown_path.read_text(encoding="utf-8")
        markdown = markdown.replace(
            "| structural match |", "| reference-signature match |"
        ).replace(
            "| gate types match |", "| gate-type count-map match |"
        ).replace(
            "| target-context recovery structural match |",
            "| target-context recovery reference-signature match |",
        )
        if "- evaluator version:" not in markdown:
            lines = markdown.splitlines()
            version_lines = [
                "",
                f"- evaluator version: `{CANONICAL_EVALUATOR_VERSION}`",
                f"- structural predicate: `{STRUCTURAL_PREDICATE_VERSION}`",
            ]
            lines[1:1] = version_lines
            markdown = "\n".join(lines) + "\n"
        markdown_path.write_text(markdown, encoding="utf-8")
        stamped += 1
    return stamped


def evaluate_code(
    code: str,
    target_metadata: dict[str, Any],
    qiskit_env: dict[str, Any],
    *,
    legacy: bool,
) -> dict[str, Any]:
    if not code.strip():
        return {
            "executable_circuit": False,
            "signature_match": False,
            "error_type": "EmptyGeneration",
            "selected_circuit_name": None,
        }
    namespace = validity.execution_namespace({}, qiskit_env)
    if legacy:
        builtins_map = dict(namespace["__builtins__"])
        builtins_map.pop("print", None)
        builtins_map.pop("reversed", None)
        namespace["__builtins__"] = builtins_map
    try:
        exec(code, namespace, namespace)
    except Exception as exc:
        return {
            "executable_circuit": False,
            "signature_match": False,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "selected_circuit_name": None,
        }
    circuits = validity.collect_circuits(namespace, qiskit_env)
    circuit_name, circuit = validity.choose_circuit(circuits, {})
    if circuit is None:
        return {
            "executable_circuit": False,
            "signature_match": False,
            "error_type": "NoCircuitFound",
            "selected_circuit_name": None,
        }
    checks = validity.structural_result(circuit, target_metadata)["checks"]
    return {
        "executable_circuit": True,
        "signature_match": bool(checks["all_match"]),
        "error_type": None,
        "selected_circuit_name": str(circuit_name),
    }


def summarize_cells(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    cells = len(rows)
    execution = sum(bool(row[f"{prefix}_executable_circuit"]) for row in rows)
    signature = sum(bool(row[f"{prefix}_signature_match"]) for row in rows)
    gap = execution - signature
    return {
        "cells": cells,
        "execution_count": execution,
        "execution_rate": execution / cells,
        "signature_count": signature,
        "signature_rate": signature / cells,
        "execution_structure_gap_count": gap,
        "execution_structure_gap_rate": gap / cells,
        "signature_wrong_given_execution": gap / execution if execution else 0.0,
    }


def transitions(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    before_key = f"legacy_{field}"
    after_key = f"canonical_{field}"
    gained = sum(not row[before_key] and row[after_key] for row in rows)
    lost = sum(row[before_key] and not row[after_key] for row in rows)
    return {"changed": gained + lost, "gained": gained, "lost": lost}


def run() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prompts = read_jsonl(PROMPT_PATH)
    prompts_by_id = {str(prompt["prompt_id"]): prompt for prompt in prompts}
    reports = load_reports()
    versioned_report_count = stamp_canonical_report_versions(reports)
    qiskit_env = copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit unavailable: {qiskit_env.get('error')}")

    cell_rows: list[dict[str, Any]] = []
    response_hashes: list[dict[str, Any]] = []
    canonical_disagreements: list[dict[str, Any]] = []
    for model, report_path, report in reports:
        response_path = Path(str(report["expected_response_path"]))
        responses = harness.load_response_map(response_path)
        report_records = {
            str(record["prompt_id"]): record for record in report.get("records") or []
        }
        response_hashes.append(
            {
                "model": model,
                "path": response_path.as_posix(),
                "bytes": response_path.stat().st_size,
                "sha256": file_sha256(response_path),
            }
        )
        for prompt_id, prompt in prompts_by_id.items():
            response = responses.get(prompt_id) or responses.get(str(prompt["row_id"]))
            if response is None:
                raise ValueError(f"Missing frozen response for {model}: {prompt_id}")
            code = harness.generated_code(response)
            legacy = evaluate_code(
                code, prompt["target_metadata"], qiskit_env, legacy=True
            )
            canonical = evaluate_code(
                code, prompt["target_metadata"], qiskit_env, legacy=False
            )
            record = report_records[prompt_id]
            execution = record.get("execution") or {}
            reported_execution = bool(
                execution.get("execution_success") and execution.get("circuit_found")
            )
            reported_signature = bool(
                (record.get("structural_checks") or {}).get("all_match")
            )
            if (
                reported_execution != canonical["executable_circuit"]
                or reported_signature != canonical["signature_match"]
            ):
                canonical_disagreements.append(
                    {
                        "model": model,
                        "prompt_id": prompt_id,
                        "reported_execution": reported_execution,
                        "replayed_execution": canonical["executable_circuit"],
                        "reported_signature": reported_signature,
                        "replayed_signature": canonical["signature_match"],
                    }
                )
            cell_rows.append(
                {
                    "model": model,
                    "model_label": MODEL_LABELS[model],
                    "prompt_id": prompt_id,
                    "row_id": str(prompt["row_id"]),
                    "legacy_executable_circuit": legacy["executable_circuit"],
                    "canonical_executable_circuit": canonical["executable_circuit"],
                    "legacy_signature_match": legacy["signature_match"],
                    "canonical_signature_match": canonical["signature_match"],
                    "legacy_error_type": legacy.get("error_type"),
                    "canonical_error_type": canonical.get("error_type"),
                }
            )
        print(f"Audited {MODEL_LABELS[model]}")

    if canonical_disagreements:
        raise ValueError(
            f"Canonical replay disagrees with {len(canonical_disagreements)} report cells"
        )

    per_model: list[dict[str, Any]] = []
    for model in MODEL_ORDER:
        model_rows = [row for row in cell_rows if row["model"] == model]
        per_model.append(
            {
                "model": model,
                "model_label": MODEL_LABELS[model],
                "legacy": summarize_cells(model_rows, "legacy"),
                "canonical": summarize_cells(model_rows, "canonical"),
                "execution_transition": transitions(
                    model_rows, "executable_circuit"
                ),
                "signature_transition": transitions(model_rows, "signature_match"),
            }
        )

    response_manifest_material = "\n".join(
        f"{row['model']}\t{row['sha256']}\t{row['bytes']}" for row in response_hashes
    ).encode("utf-8")
    prompt_text_objects = [
        {"prompt_id": row["prompt_id"], "instruction": row["instruction"]}
        for row in prompts
    ]
    target_objects = [
        {
            "prompt_id": row["prompt_id"],
            "row_id": row["row_id"],
            "target_metadata": row["target_metadata"],
        }
        for row in prompts
    ]
    predicate_source = "\n".join(
        [
            inspect.getsource(validity.normalize_gate_counts),
            inspect.getsource(validity.observed_gate_counts),
            inspect.getsource(validity.metadata_gate_count),
            inspect.getsource(validity.structural_result),
        ]
    )
    legacy_summary = summarize_cells(cell_rows, "legacy")
    canonical_summary = summarize_cells(cell_rows, "canonical")
    payload = {
        "schema_version": "pqid-bench-evaluator-correction-audit-v2",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "versions": {
            "legacy_evaluator": LEGACY_EVALUATOR_VERSION,
            "canonical_evaluator": CANONICAL_EVALUATOR_VERSION,
            "structural_predicate": STRUCTURAL_PREDICATE_VERSION,
        },
        "policy_difference": {
            "legacy_missing_builtins": ["print", "reversed"],
            "canonical_additions": ["print", "reversed"],
            "print_behavior": "silent no-op preserving the normal None return value",
        },
        "frozen_input_hashes": {
            "prompt_file": {
                "path": PROMPT_PATH.as_posix(),
                "sha256": file_sha256(PROMPT_PATH),
            },
            "prompt_text_objects_sha256": canonical_json_sha256(prompt_text_objects),
            "target_metadata_objects_sha256": canonical_json_sha256(target_objects),
            "split_manifest": {
                "path": SPLIT_MANIFEST_PATH.as_posix(),
                "sha256": file_sha256(SPLIT_MANIFEST_PATH),
            },
            "response_log_manifest_sha256": sha256_bytes(response_manifest_material),
            "response_logs": response_hashes,
            "structural_predicate_source_sha256": sha256_bytes(
                predicate_source.encode("utf-8")
            ),
        },
        "invariants": [
            "Both policies evaluate the same 154 prompt objects and target metadata.",
            "Both policies evaluate the same 3,234 frozen model responses without regeneration.",
            "Prompt IDs, row IDs, split assignments, request/response artifacts, and their stored hashes are unchanged.",
            "The reference-signature predicate and target count maps are identical under both policies.",
            "Only admissibility of the ordinary Python built-ins print and reversed differs.",
        ],
        "legacy": legacy_summary,
        "canonical": canonical_summary,
        "execution_transition": transitions(cell_rows, "executable_circuit"),
        "signature_transition": transitions(cell_rows, "signature_match"),
        "canonical_report_replay_disagreements": len(canonical_disagreements),
        "canonical_reports_versioned": versioned_report_count,
        "per_model": per_model,
        "cell_audit_path": CELL_OUT.as_posix(),
    }
    return payload, cell_rows


def write_tsv(payload: dict[str, Any]) -> None:
    TSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "cells",
        "execution_before",
        "execution_after",
        "execution_status_changed",
        "signature_before",
        "signature_after",
        "signature_status_changed",
    ]
    rows = []
    for item in payload["per_model"]:
        rows.append(
            {
                "model": item["model_label"],
                "cells": item["canonical"]["cells"],
                "execution_before": item["legacy"]["execution_count"],
                "execution_after": item["canonical"]["execution_count"],
                "execution_status_changed": item["execution_transition"]["changed"],
                "signature_before": item["legacy"]["signature_count"],
                "signature_after": item["canonical"]["signature_count"],
                "signature_status_changed": item["signature_transition"]["changed"],
            }
        )
    rows.append(
        {
            "model": "All 21 models",
            "cells": payload["canonical"]["cells"],
            "execution_before": payload["legacy"]["execution_count"],
            "execution_after": payload["canonical"]["execution_count"],
            "execution_status_changed": payload["execution_transition"]["changed"],
            "signature_before": payload["legacy"]["signature_count"],
            "signature_after": payload["canonical"]["signature_count"],
            "signature_status_changed": payload["signature_transition"]["changed"],
        }
    )
    with TSV_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, Any], cell_rows: list[dict[str, Any]]) -> None:
    legacy = payload["legacy"]
    canonical = payload["canonical"]
    execution_transition = payload["execution_transition"]
    signature_transition = payload["signature_transition"]
    lines = [
        "# PQID-Bench Evaluator Version And Safe-Built-In Correction",
        "",
        f"- superseded evaluator: `{payload['versions']['legacy_evaluator']}`",
        f"- canonical evaluator: `{payload['versions']['canonical_evaluator']}`",
        f"- unchanged structural predicate: `{payload['versions']['structural_predicate']}`",
        f"- canonical model reports carrying both version labels: `{payload['canonical_reports_versioned']}`",
        "",
        "The audit counterfactually evaluates every frozen response under both policies. The only difference is that the canonical restricted namespace admits `print` and `reversed`; `print` is a silent no-op with the ordinary `None` return value. No provider call is repeated.",
        "",
        "## Aggregate Impact",
        "",
        "| metric | restricted built-ins | canonical safe built-ins | status changes |",
        "| --- | ---: | ---: | ---: |",
        f"| executable circuit | {legacy['execution_count']}/{legacy['cells']} ({pct(legacy['execution_rate'])}) | {canonical['execution_count']}/{canonical['cells']} ({pct(canonical['execution_rate'])}) | {execution_transition['changed']} ({execution_transition['gained']} gained, {execution_transition['lost']} lost) |",
        f"| reference-signature match | {legacy['signature_count']}/{legacy['cells']} ({pct(legacy['signature_rate'])}) | {canonical['signature_count']}/{canonical['cells']} ({pct(canonical['signature_rate'])}) | {signature_transition['changed']} ({signature_transition['gained']} gained, {signature_transition['lost']} lost) |",
        f"| execution-structure gap | {legacy['execution_structure_gap_count']}/{legacy['cells']} ({pct(legacy['execution_structure_gap_rate'])}) | {canonical['execution_structure_gap_count']}/{canonical['cells']} ({pct(canonical['execution_structure_gap_rate'])}) | {pp(canonical['execution_structure_gap_rate'] - legacy['execution_structure_gap_rate'])} |",
        "",
        "## Per-Model Impact",
        "",
        "| model | execution before -> after | execution cells changed | signature before -> after | signature cells changed |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["per_model"]:
        lines.append(
            f"| {item['model_label']} | {item['legacy']['execution_count']} -> {item['canonical']['execution_count']} | {item['execution_transition']['changed']} | {item['legacy']['signature_count']} -> {item['canonical']['signature_count']} | {item['signature_transition']['changed']} |"
        )
    hashes = payload["frozen_input_hashes"]
    lines.extend(
        [
            "",
            "## Frozen-Input Invariants",
            "",
            f"- prompt JSONL SHA-256: `{hashes['prompt_file']['sha256']}`",
            f"- normalized prompt-text SHA-256: `{hashes['prompt_text_objects_sha256']}`",
            f"- normalized target-metadata SHA-256: `{hashes['target_metadata_objects_sha256']}`",
            f"- response-log manifest SHA-256: `{hashes['response_log_manifest_sha256']}`",
            f"- structural-predicate source SHA-256: `{hashes['structural_predicate_source_sha256']}`",
            "- canonical replay disagreements with the published report matrix: `0`",
            "",
            "These hashes are evaluated once and shared by both policy branches. The correction changes evaluator admissibility only; prompts, responses, targets, split assignments, request/response artifacts, and the reference-signature predicate are unchanged.",
            "",
        ]
    )
    CORRECTION_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    with CELL_OUT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in cell_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    write_tsv(payload)
    print(f"Wrote {JSON_OUT.as_posix()}")
    print(f"Wrote {MD_OUT.as_posix()}")
    print(f"Wrote {CELL_OUT.as_posix()}")
    print(f"Wrote {TSV_OUT.as_posix()}")


if __name__ == "__main__":
    result, audited_cells = run()
    write_report(result, audited_cells)
