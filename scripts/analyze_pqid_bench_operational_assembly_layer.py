"""Audit the operational assembly-admissibility layer on the frozen panel.

The canonical external-generation endpoint E records successful generated-code
execution with a selected QuantumCircuit. The intermediate endpoint A records
that the selected circuit also serializes to OpenQASM 3 under the frozen
evaluator. This script verifies the reported counts and pointwise nesting used
by the manuscript's operational-to-structural validation ladder.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pqid_bench_model_registry import (
    MODEL_LABELS,
    PRIMARY_MODEL_ORDER,
    model_from_report_dir,
)


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIRS = [
    ROOT / "artifacts/external_model_batches_154/evaluations",
    ROOT / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    ROOT / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
JSON_OUT = ANALYSIS_DIR / "pqid_bench_operational_assembly_layer_audit.json"
MD_OUT = ANALYSIS_DIR / "pqid_bench_operational_assembly_layer_audit.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pct(count: int, denominator: int) -> str:
    return f"{100.0 * count / denominator:.2f}%"


def pp(numerator: int, denominator: int) -> str:
    return f"{100.0 * numerator / denominator:.2f} pp"


def load_cells() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cells: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    seen_models: set[str] = set()

    for evaluation_dir in EVALUATION_DIRS:
        for report_path in sorted(evaluation_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            if model in seen_models:
                raise RuntimeError(f"Duplicate model report: {model}")
            seen_models.add(model)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            records = report.get("records", [])
            if len(records) != 154:
                raise RuntimeError(
                    f"{model} has {len(records)} records rather than 154"
                )

            summary = report.get("summary", {})
            record_e = 0
            record_a = 0
            record_m = 0
            for record in records:
                execution = record.get("execution") or {}
                checks = record.get("structural_checks") or {}
                python_success = bool(execution.get("execution_success"))
                circuit_found = bool(execution.get("circuit_found"))
                e_value = python_success and circuit_found
                qasm_success = bool(
                    (execution.get("qasm3_export") or {}).get("success")
                )
                a_value = e_value and qasm_success
                m_value = bool(checks.get("all_match"))

                record_e += int(e_value)
                record_a += int(a_value)
                record_m += int(m_value)
                cells.append(
                    {
                        "model": model,
                        "model_label": MODEL_LABELS.get(model, model),
                        "provider": record.get("provider"),
                        "prompt_id": record["prompt_id"],
                        "python_execution_success": python_success,
                        "E": e_value,
                        "A": a_value,
                        "M_sig": m_value,
                        "qasm3_export_error_type": (
                            execution.get("qasm3_export") or {}
                        ).get("error_type"),
                    }
                )

            expected = {
                "E": int(summary.get("circuit_found", -1)),
                "A": int(summary.get("qasm3_export_success", -1)),
                "M_sig": int(summary.get("structural_all_match", -1)),
            }
            observed = {"E": record_e, "A": record_a, "M_sig": record_m}
            if observed != expected:
                raise RuntimeError(
                    f"Record/summary mismatch for {model}: "
                    f"observed={observed}, expected={expected}"
                )

            sources.append(
                {
                    "model": model,
                    "path": report_path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(report_path),
                    "records": len(records),
                }
            )

    expected_models = set(PRIMARY_MODEL_ORDER)
    if seen_models != expected_models:
        missing = sorted(expected_models - seen_models)
        extra = sorted(seen_models - expected_models)
        raise RuntimeError(f"Model roster mismatch; missing={missing}, extra={extra}")

    keys = {(cell["model"], cell["prompt_id"]) for cell in cells}
    if len(keys) != len(cells):
        raise RuntimeError("Duplicate model-prompt cells found")
    if len(cells) != 21 * 154:
        raise RuntimeError(f"Expected 3,234 cells, found {len(cells)}")
    return cells, sources


def summarize(cells: list[dict[str, Any]], sources: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(cells)
    python_count = sum(int(cell["python_execution_success"]) for cell in cells)
    e_count = sum(int(cell["E"]) for cell in cells)
    a_count = sum(int(cell["A"]) for cell in cells)
    m_count = sum(int(cell["M_sig"]) for cell in cells)

    e_without_a = [cell for cell in cells if cell["E"] and not cell["A"]]
    a_without_m = [cell for cell in cells if cell["A"] and not cell["M_sig"]]
    violations = {
        "A_not_E": [
            cell for cell in cells if cell["A"] and not cell["E"]
        ],
        "M_sig_not_A": [
            cell for cell in cells if cell["M_sig"] and not cell["A"]
        ],
        "M_sig_not_E": [
            cell for cell in cells if cell["M_sig"] and not cell["E"]
        ],
    }
    if any(violations.values()):
        raise RuntimeError(
            "Pointwise nesting failed: "
            + ", ".join(f"{key}={len(value)}" for key, value in violations.items())
        )

    es_gap_count = e_count - m_count
    assembly_gap_count = a_count - m_count
    result = {
        "schema_version": "pqid-bench-operational-assembly-audit-v1.1",
        "panel": {
            "models": len(PRIMARY_MODEL_ORDER),
            "prompts": 154,
            "cells": n,
        },
        "definitions": {
            "python_execution_success": (
                "The extracted generated Python program completes under the "
                "frozen evaluator namespace."
            ),
            "E": (
                "Executable-circuit materialization: generated Python completes "
                "and the evaluator selects a QuantumCircuit."
            ),
            "A": (
                "Quantum-assembly admissibility: E=1 and the selected circuit "
                "serializes successfully to OpenQASM 3 under the frozen evaluator."
            ),
            "M_sig": (
                "Frozen reference-signature recovery: qubit count, classical-bit "
                "count, and complete operation-type count map agree."
            ),
            "AS_gap": (
                "Assembly-Structure Gap: the pooled A minus M_sig contrast. "
                "On this frozen panel it equals the A=1, M_sig=0 cell rate "
                "because M_sig_not_A=0."
            ),
            "scope_caveat": (
                "A verifies OpenQASM 3 serialization, not execution of the emitted "
                "assembly on a simulator or quantum backend."
            ),
        },
        "counts": {
            "python_execution_success": python_count,
            "E": e_count,
            "A": a_count,
            "M_sig": m_count,
            "python_success_without_E": python_count - e_count,
            "E_without_A": len(e_without_a),
            "A_without_M_sig": len(a_without_m),
            "M_sig_without_A": len(violations["M_sig_not_A"]),
            "E_without_M_sig": es_gap_count,
        },
        "rates": {
            "python_execution_success": python_count / n,
            "E": e_count / n,
            "A": a_count / n,
            "M_sig": m_count / n,
        },
        "gaps": {
            "E_minus_A_count": e_count - a_count,
            "E_minus_A_rate": (e_count - a_count) / n,
            "ES_signature_count": es_gap_count,
            "ES_signature_rate": es_gap_count / n,
            "AS_signature_count": assembly_gap_count,
            "AS_signature_rate": assembly_gap_count / n,
            "AS_share_of_ES_signature_gap": (
                assembly_gap_count / es_gap_count if es_gap_count else None
            ),
            # Backward-compatible machine keys retained for the v1 audit reader.
            "assembly_to_signature_count": assembly_gap_count,
            "assembly_to_signature_rate": assembly_gap_count / n,
            "assembly_share_of_ES_signature_gap": (
                assembly_gap_count / es_gap_count if es_gap_count else None
            ),
        },
        "nesting": {
            "validated_chain": "M_sig <= A <= E",
            "A_not_E": 0,
            "M_sig_not_A": 0,
            "M_sig_not_E": 0,
        },
        "E_without_A_cells": e_without_a,
        "source_reports": sources,
    }
    return result


def write_markdown(result: dict[str, Any]) -> None:
    panel = result["panel"]
    counts = result["counts"]
    gaps = result["gaps"]
    lines = [
        "# PQID-Bench Operational Assembly-Layer Audit",
        "",
        (
            f"Frozen panel: `{panel['models']} x {panel['prompts']} = "
            f"{panel['cells']:,}` model-prompt cells."
        ),
        "",
        "## Endpoint Definitions",
        "",
        "- `E`: executable-circuit materialization; generated Python completes and "
        "the evaluator selects a `QuantumCircuit`.",
        "- `A`: quantum-assembly admissibility; `E=1` and the selected circuit "
        "serializes successfully to OpenQASM 3 under the frozen evaluator.",
        "- `M_sig`: recovery of the frozen qubit count, classical-bit count, and "
        "complete operation-type count map.",
        "- Scope: `A` does not mean that the emitted OpenQASM 3 program was executed "
        "on a simulator or hardware backend.",
        "",
        "## Frozen-Panel Results",
        "",
        "| endpoint or contrast | count | rate |",
        "| --- | ---: | ---: |",
        (
            f"| Python program completes | {counts['python_execution_success']:,} | "
            f"{pct(counts['python_execution_success'], panel['cells'])} |"
        ),
        (
            f"| executable-circuit materialization, `E` | {counts['E']:,} | "
            f"{pct(counts['E'], panel['cells'])} |"
        ),
        (
            f"| quantum-assembly admissibility, `A` | {counts['A']:,} | "
            f"{pct(counts['A'], panel['cells'])} |"
        ),
        (
            f"| reference-signature recovery, `M_sig` | {counts['M_sig']:,} | "
            f"{pct(counts['M_sig'], panel['cells'])} |"
        ),
        (
            f"| `E=1, A=0` | {counts['E_without_A']:,} | "
            f"{pp(gaps['E_minus_A_count'], panel['cells'])} |"
        ),
        (
            f"| `A=1, M_sig=0` | {counts['A_without_M_sig']:,} | "
            f"{pp(gaps['assembly_to_signature_count'], panel['cells'])} |"
        ),
        (
            f"| `E=1, M_sig=0` | {counts['E_without_M_sig']:,} | "
            f"{pp(gaps['ES_signature_count'], panel['cells'])} |"
        ),
        "",
        (
            "The pointwise chain `M_sig <= A <= E` has zero violations. "
            f"The Assembly-Structure Gap (AS-Gap) retains "
            f"`{100 * gaps['assembly_share_of_ES_signature_gap']:.2f}%` of the "
            "signature-level ES-Gap."
        ),
        "",
        "## Six Executable Circuits Without Assembly Admissibility",
        "",
        "| model | prompt | provider | export error |",
        "| --- | --- | --- | --- |",
    ]
    for cell in result["E_without_A_cells"]:
        lines.append(
            f"| {cell['model_label']} | `{cell['prompt_id']}` | "
            f"`{cell['provider']}` | `{cell['qasm3_export_error_type']}` |"
        )
    lines.extend(
        [
            "",
            "The audit reads the canonical evaluator reports only. It does not "
            "change prompts, outputs, targets, evaluator policy, or structural "
            "predicates.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    cells, sources = load_cells()
    result = summarize(cells, sources)
    JSON_OUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(result)
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")


if __name__ == "__main__":
    main()
