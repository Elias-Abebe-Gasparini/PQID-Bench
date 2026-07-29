"""Validate the PQID-Bench reference-signature predicate against circuit tapes.

The published predicate records qubit count, classical-bit count, scalar gate
count, and the complete gate-type count map. This audit replays the frozen source and
generated programs through the same restricted Qiskit namespace and circuit
selection rules, then adds progressively stricter diagnostics:

* operation-name order;
* ordered quantum and classical operands;
* measurement mapping;
* literal parameter tokens; and
* global phase.

Exact tape agreement is intentionally not called semantic equivalence. Commuting
operations and other equivalent rewrites may fail this strict source-recovery
check while implementing the same physical transformation.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

import run_pqid_bench_executable_validity_check as validity
import run_pqid_bench_external_model_generation_harness as harness
import run_pqid_bench_generation_copy_baseline as copy_baseline
import run_pqid_bench_context_recovery_ablation as context_recovery
from analyze_pqid_bench_complexity_difficulty import family_labels
from analyze_pqid_bench_inferential import (
    DEFAULT_EVAL_DIRS,
    IDENTIFIABILITY_EXCLUSIONS,
    REPORT_NAME,
    metadata_signature,
    percentile_interval,
    read_jsonl,
)
from pqid_bench_model_registry import MODEL_LABELS, MODEL_ORDER, model_from_report_dir


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
PROMPT_PATH = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
SPLIT_MANIFEST_PATH = ROOT / "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
JSON_OUT = ANALYSIS_DIR / "pqid_bench_ordered_operand_validation.json"
MD_OUT = ANALYSIS_DIR / "pqid_bench_ordered_operand_validation.md"
CELL_JSONL_OUT = ANALYSIS_DIR / "pqid_bench_ordered_operand_cell_audit.jsonl"
MODEL_CSV_OUT = ANALYSIS_DIR / "pqid_bench_ordered_operand_by_model.csv"
S30_TSV_OUT = ROOT / "tables_copy_ready/table_s30_ordered_operand_validation.tsv"


def pct(value: float, digits: int = 2) -> str:
    return f"{100.0 * value:.{digits}f}%"


def pp(value: float, digits: int = 2) -> str:
    return f"{100.0 * value:+.{digits}f} pp"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def cohort_map(path: Path) -> dict[str, str]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(item["prompt_id"]): str(item["cohort"])
        for item in manifest["test_prompt_order"]
    }


def materialize_circuit(
    code: str,
    *,
    context_metadata: dict[str, Any],
    selection_metadata: dict[str, Any],
    qiskit_env: dict[str, Any],
    namespace_updates: dict[str, Any] | None = None,
) -> tuple[str | None, object | None, str | None]:
    namespace = validity.execution_namespace(context_metadata, qiskit_env)
    if namespace_updates:
        namespace.update(namespace_updates)
    try:
        exec(code, namespace, namespace)
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"
    circuits = validity.collect_circuits(namespace, qiskit_env)
    name, circuit = validity.choose_circuit(circuits, selection_metadata)
    if circuit is None:
        return None, None, "NoCircuitFound"
    return str(name), circuit, None


def bit_index(circuit: object, bit: object) -> int:
    location = circuit.find_bit(bit)
    return int(location.index)


def parameter_token(value: object) -> dict[str, Any]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return {"kind": "symbolic", "value": str(value)}
    if math.isnan(numeric):
        rendered: float | str = "nan"
    elif math.isinf(numeric):
        rendered = "inf" if numeric > 0 else "-inf"
    else:
        rendered = round(numeric, 12)
    return {"kind": "numeric", "value": rendered}


def operation_tape(circuit: object) -> list[dict[str, Any]]:
    tape = []
    for item in circuit.data:
        if hasattr(item, "operation"):
            operation = item.operation
            qubits = item.qubits
            clbits = item.clbits
        else:
            operation, qubits, clbits = item
        tape.append(
            {
                "name": str(operation.name).lower(),
                "qubits": [bit_index(circuit, bit) for bit in qubits],
                "clbits": [bit_index(circuit, bit) for bit in clbits],
                "params": [parameter_token(value) for value in operation.params],
            }
        )
    return tape


def phase_token(circuit: object) -> dict[str, Any]:
    return parameter_token(circuit.global_phase)


def phase_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left["kind"] != right["kind"]:
        return False
    if left["kind"] == "symbolic":
        return left["value"] == right["value"]
    if not isinstance(left["value"], (int, float)) or not isinstance(
        right["value"], (int, float)
    ):
        return left["value"] == right["value"]
    difference = float(left["value"]) - float(right["value"])
    wrapped = (difference + math.pi) % (2.0 * math.pi) - math.pi
    return bool(math.isclose(wrapped, 0.0, abs_tol=1e-10, rel_tol=1e-10))


def name_sequence(tape: list[dict[str, Any]]) -> list[str]:
    return [item["name"] for item in tape]


def quantum_operand_sequence(tape: list[dict[str, Any]]) -> list[list[int]]:
    return [item["qubits"] for item in tape]


def classical_operand_sequence(tape: list[dict[str, Any]]) -> list[list[int]]:
    return [item["clbits"] for item in tape]


def wire_tape(tape: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": item["name"], "qubits": item["qubits"], "clbits": item["clbits"]}
        for item in tape
    ]


def parameter_sequence(tape: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    return [item["params"] for item in tape]


def measurement_map(tape: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"qubits": item["qubits"], "clbits": item["clbits"]}
        for item in tape
        if item["name"] == "measure"
    ]


def sequence_ratio(left: list[Any], right: list[Any]) -> float:
    left_tokens = [json.dumps(value, sort_keys=True, separators=(",", ":")) for value in left]
    right_tokens = [json.dumps(value, sort_keys=True, separators=(",", ":")) for value in right]
    return float(difflib.SequenceMatcher(a=left_tokens, b=right_tokens, autojunk=False).ratio())


def compare_tapes(
    reference_tape: list[dict[str, Any]],
    candidate_tape: list[dict[str, Any]],
    reference_phase: dict[str, Any],
    candidate_phase: dict[str, Any],
    reference_shape: tuple[int, int],
    candidate_shape: tuple[int, int],
) -> dict[str, Any]:
    reference_names = name_sequence(reference_tape)
    candidate_names = name_sequence(candidate_tape)
    reference_qargs = quantum_operand_sequence(reference_tape)
    candidate_qargs = quantum_operand_sequence(candidate_tape)
    reference_cargs = classical_operand_sequence(reference_tape)
    candidate_cargs = classical_operand_sequence(candidate_tape)
    reference_wire_tape = wire_tape(reference_tape)
    candidate_wire_tape = wire_tape(candidate_tape)
    reference_params = parameter_sequence(reference_tape)
    candidate_params = parameter_sequence(candidate_tape)
    gate_order_match = reference_names == candidate_names
    quantum_operands_match = reference_qargs == candidate_qargs
    classical_operands_match = reference_cargs == candidate_cargs
    operation_wire_match = reference_wire_tape == candidate_wire_tape
    circuit_shape_match = reference_shape == candidate_shape
    ordered_wire_match = circuit_shape_match and operation_wire_match
    parameter_match = reference_params == candidate_params
    global_phase_match = phase_equal(reference_phase, candidate_phase)
    parameter_aware_match = ordered_wire_match and parameter_match
    return {
        "gate_order_match": gate_order_match,
        "quantum_operand_sequence_match": quantum_operands_match,
        "classical_operand_sequence_match": classical_operands_match,
        "circuit_shape_match": circuit_shape_match,
        "operation_wire_tape_match": operation_wire_match,
        "ordered_wire_tape_match": ordered_wire_match,
        "measurement_map_match": measurement_map(reference_tape) == measurement_map(candidate_tape),
        "parameter_token_sequence_match": parameter_match,
        "parameter_aware_tape_match": parameter_aware_match,
        "global_phase_match": global_phase_match,
        "full_literal_circuit_match": parameter_aware_match and global_phase_match,
        "gate_order_similarity": sequence_ratio(reference_names, candidate_names),
        "ordered_wire_tape_similarity": sequence_ratio(reference_wire_tape, candidate_wire_tape),
    }


def load_reports(eval_dirs: list[Path]) -> list[tuple[str, Path, dict[str, Any]]]:
    reports = []
    seen_models = set()
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            if model not in MODEL_ORDER:
                continue
            if model in seen_models:
                raise ValueError(f"Duplicate canonical report for model {model}")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            reports.append((model, report_path, report))
            seen_models.add(model)
    missing = [model for model in MODEL_ORDER if model not in seen_models]
    if missing:
        raise ValueError(f"Missing canonical reports: {missing}")
    reports.sort(key=lambda item: MODEL_ORDER.index(item[0]))
    return reports


def reference_circuits(
    prompts: list[dict[str, Any]],
    split_manifest: Path,
    qiskit_env: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    source_rows = copy_baseline.clean_rows(copy_baseline.DEFAULT_INPUT)
    splits = copy_baseline.split_rows(source_rows, split_manifest_path=split_manifest)
    rows_by_id = {str(row["row_id"]): row for row in splits["test"]}
    references: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    for prompt in prompts:
        prompt_id = str(prompt["prompt_id"])
        row = rows_by_id[str(prompt["row_id"])]
        recovered, _, _ = context_recovery.build_recovery_namespace(
            row, qiskit_env, target_symbol=None
        )
        selected_name, circuit, error = materialize_circuit(
            row["code"],
            context_metadata=row["metadata"],
            selection_metadata=row["metadata"],
            qiskit_env=qiskit_env,
            namespace_updates=recovered,
        )
        if circuit is None:
            errors.append({"prompt_id": prompt_id, "error": error})
            continue
        structural = validity.structural_result(circuit, row["metadata"])
        if not structural["checks"]["all_match"]:
            errors.append(
                {
                    "prompt_id": prompt_id,
                    "error": "ReferenceCircuitDoesNotMatchFrozenSignature",
                    "structural": structural,
                }
            )
            continue
        references[prompt_id] = {
            "selected_circuit_name": selected_name,
            "tape": operation_tape(circuit),
            "global_phase": phase_token(circuit),
            "shape": (int(circuit.num_qubits), int(circuit.num_clbits)),
            "metadata": prompt["target_metadata"],
        }
    return references, errors


def audit_cells(
    prompts: list[dict[str, Any]],
    reports: list[tuple[str, Path, dict[str, Any]]],
    references: dict[str, dict[str, Any]],
    cohorts: dict[str, str],
    qiskit_env: dict[str, Any],
) -> list[dict[str, Any]]:
    prompts_by_id = {str(prompt["prompt_id"]): prompt for prompt in prompts}
    rows: list[dict[str, Any]] = []
    for model, report_path, report in reports:
        response_path = Path(str(report["expected_response_path"]))
        if not response_path.exists():
            raise FileNotFoundError(f"Response log for {model} does not exist: {response_path}")
        responses = harness.load_response_map(response_path)
        records = {str(record["prompt_id"]): record for record in report["records"]}
        for prompt_id, prompt in prompts_by_id.items():
            record = records[prompt_id]
            execution = record.get("execution") or {}
            report_executable = bool(execution.get("execution_success")) and bool(
                execution.get("circuit_found")
            )
            report_assembly_admissible = report_executable and bool(
                (execution.get("qasm3_export") or {}).get("success")
            )
            signature_match = bool((record.get("structural_checks") or {}).get("all_match"))
            base = {
                "prompt_id": prompt_id,
                "row_id": str(prompt["row_id"]),
                "cohort": cohorts[prompt_id],
                "target_signature": metadata_signature(prompt),
                "families": family_labels(str(prompt["instruction"])),
                "model": model,
                "model_label": MODEL_LABELS[model],
                "report_executable": report_executable,
                "report_assembly_admissible": report_assembly_admissible,
                "report_signature_match": signature_match,
                "report_selected_circuit_name": execution.get("selected_circuit_name"),
                "response_path": response_path.as_posix(),
                "report_path": report_path.as_posix(),
            }
            reference = references.get(prompt_id)
            if reference is None:
                rows.append(
                    {
                        **base,
                        "replay_available": False,
                        "replay_error": "ReferenceCircuitUnavailable",
                    }
                )
                continue
            if not report_executable:
                rows.append(
                    {
                        **base,
                        "replay_available": False,
                        "replay_error": None,
                    }
                )
                continue
            response = responses.get(prompt_id) or responses.get(str(prompt["row_id"]))
            if response is None:
                rows.append(
                    {
                        **base,
                        "replay_available": False,
                        "replay_error": "ResponseRecordMissing",
                    }
                )
                continue
            code = harness.generated_code(response)
            candidate_name, candidate_circuit, error = materialize_circuit(
                code,
                context_metadata={},
                selection_metadata={},
                qiskit_env=qiskit_env,
            )
            if candidate_circuit is None:
                rows.append(
                    {
                        **base,
                        "replay_available": False,
                        "replay_error": error,
                    }
                )
                continue
            candidate_structural = validity.structural_result(
                candidate_circuit, prompt["target_metadata"]
            )
            candidate_tape = operation_tape(candidate_circuit)
            comparison = compare_tapes(
                reference["tape"],
                candidate_tape,
                reference["global_phase"],
                phase_token(candidate_circuit),
                reference["shape"],
                (int(candidate_circuit.num_qubits), int(candidate_circuit.num_clbits)),
            )
            rows.append(
                {
                    **base,
                    "replay_available": True,
                    "replay_error": None,
                    "replay_selected_circuit_name": candidate_name,
                    "selected_name_consistent": candidate_name
                    == execution.get("selected_circuit_name"),
                    "replay_signature_match": bool(
                        candidate_structural["checks"]["all_match"]
                    ),
                    "signature_replay_consistent": signature_match
                    == bool(candidate_structural["checks"]["all_match"]),
                    "reference_operation_count": len(reference["tape"]),
                    "candidate_operation_count": len(candidate_tape),
                    **comparison,
                    "reference_tape": reference["tape"],
                    "candidate_tape": candidate_tape,
                    "reference_global_phase": reference["global_phase"],
                    "candidate_global_phase": phase_token(candidate_circuit),
                }
            )
        print(f"Audited {MODEL_LABELS[model]} ({len(records)} prompts)")
    return rows


def safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    executable = [row for row in rows if row["report_executable"]]
    replayed = [row for row in rows if row.get("replay_available")]
    signature_passes = [row for row in replayed if row["report_signature_match"]]
    measured_passes = [
        row
        for row in signature_passes
        if any(item["name"] == "measure" for item in row["reference_tape"])
    ]

    def agreement(field: str, denominator_rows: list[dict[str, Any]]) -> dict[str, Any]:
        count = sum(1 for row in denominator_rows if row.get(field) is True)
        return {
            "count": count,
            "denominator": len(denominator_rows),
            "rate": safe_rate(count, len(denominator_rows)),
        }

    return {
        "cells": total,
        "report_executable": len(executable),
        "replayed_executable": len(replayed),
        "replay_failures_among_report_executable": len(executable) - len(replayed),
        "report_signature_matches": sum(1 for row in rows if row["report_signature_match"]),
        "signature_matches_replayed": len(signature_passes),
        "signature_replay_disagreements": sum(
            1 for row in replayed if not row.get("signature_replay_consistent", False)
        ),
        "selected_name_disagreements": sum(
            1 for row in replayed if not row.get("selected_name_consistent", False)
        ),
        "gate_order_given_signature": agreement("gate_order_match", signature_passes),
        "quantum_operands_given_signature": agreement(
            "quantum_operand_sequence_match", signature_passes
        ),
        "classical_operands_given_signature": agreement(
            "classical_operand_sequence_match", signature_passes
        ),
        "ordered_wire_tape_given_signature": agreement(
            "ordered_wire_tape_match", signature_passes
        ),
        "measurement_map_given_signature_and_measurement": agreement(
            "measurement_map_match", measured_passes
        ),
        "parameter_tokens_given_signature": agreement(
            "parameter_token_sequence_match", signature_passes
        ),
        "parameter_aware_tape_given_signature": agreement(
            "parameter_aware_tape_match", signature_passes
        ),
        "global_phase_given_signature": agreement("global_phase_match", signature_passes),
        "full_literal_circuit_given_signature": agreement(
            "full_literal_circuit_match", signature_passes
        ),
        "ordered_wire_matches_outside_signature": sum(
            1
            for row in replayed
            if row.get("ordered_wire_tape_match") and not row["report_signature_match"]
        ),
        "mean_gate_order_similarity_given_signature": float(
            np.mean([row["gate_order_similarity"] for row in signature_passes])
        )
        if signature_passes
        else None,
        "mean_wire_tape_similarity_given_signature": float(
            np.mean([row["ordered_wire_tape_similarity"] for row in signature_passes])
        )
        if signature_passes
        else None,
    }


def crossed_cluster_interval(
    rows: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    field: str,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    prompt_ids = [str(prompt["prompt_id"]) for prompt in prompts]
    prompt_index = {prompt_id: index for index, prompt_id in enumerate(prompt_ids)}
    model_index = {model: index for index, model in enumerate(MODEL_ORDER)}
    signature_keys = [metadata_signature(prompt) for prompt in prompts]
    cluster_ids = {key: index for index, key in enumerate(sorted(set(signature_keys)))}
    prompts_by_cluster: list[list[int]] = [[] for _ in cluster_ids]
    for index, key in enumerate(signature_keys):
        prompts_by_cluster[cluster_ids[key]].append(index)

    signature_matrix = np.zeros((len(prompt_ids), len(MODEL_ORDER)), dtype=bool)
    field_matrix = np.zeros_like(signature_matrix)
    available_matrix = np.zeros_like(signature_matrix)
    for row in rows:
        p_idx = prompt_index[row["prompt_id"]]
        m_idx = model_index[row["model"]]
        signature_matrix[p_idx, m_idx] = bool(row["report_signature_match"])
        available_matrix[p_idx, m_idx] = bool(row.get("replay_available"))
        field_matrix[p_idx, m_idx] = bool(row.get(field))

    eligible = signature_matrix & available_matrix
    point_denominator = int(np.sum(eligible))
    point_numerator = int(np.sum(field_matrix & eligible))
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=float)
    for replicate in range(replicates):
        sampled_models = rng.integers(0, len(MODEL_ORDER), size=len(MODEL_ORDER))
        sampled_clusters = rng.integers(
            0, len(prompts_by_cluster), size=len(prompts_by_cluster)
        )
        sampled_prompts = np.asarray(
            [
                prompt_index_value
                for cluster in sampled_clusters
                for prompt_index_value in prompts_by_cluster[int(cluster)]
            ],
            dtype=int,
        )
        denominator = int(np.sum(eligible[np.ix_(sampled_prompts, sampled_models)]))
        numerator = int(
            np.sum((field_matrix & eligible)[np.ix_(sampled_prompts, sampled_models)])
        )
        samples[replicate] = numerator / denominator if denominator else np.nan
    samples = samples[~np.isnan(samples)]
    return {
        "field": field,
        "count": point_numerator,
        "denominator": point_denominator,
        "rate": point_numerator / point_denominator,
        "crossed_bootstrap_95": percentile_interval(samples),
        "replicates": int(len(samples)),
    }


def per_model_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for model in MODEL_ORDER:
        selected = [row for row in rows if row["model"] == model]
        summary = summarize_subset(selected)
        output.append(
            {
                "model": model,
                "model_label": MODEL_LABELS[model],
                "executable": summary["report_executable"],
                "signature_matches": summary["report_signature_matches"],
                "gate_order_matches": summary["gate_order_given_signature"]["count"],
                "ordered_wire_tape_matches": summary["ordered_wire_tape_given_signature"]["count"],
                "parameter_aware_tape_matches": summary[
                    "parameter_aware_tape_given_signature"
                ]["count"],
                "full_literal_matches": summary["full_literal_circuit_given_signature"]["count"],
                "signature_rate": summary["report_signature_matches"] / len(selected),
                "ordered_wire_given_signature_rate": summary[
                    "ordered_wire_tape_given_signature"
                ]["rate"],
                "parameter_aware_given_signature_rate": summary[
                    "parameter_aware_tape_given_signature"
                ]["rate"],
            }
        )
    return output


def write_model_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_s30_tsv(path: Path, payload: dict[str, Any]) -> None:
    crossed = {item["field"]: item for item in payload["crossed_intervals"]}
    labels = [
        ("gate_order_match", "operation-name order"),
        ("quantum_operand_sequence_match", "ordered quantum operands"),
        ("classical_operand_sequence_match", "ordered classical operands"),
        ("ordered_wire_tape_match", "circuit shape plus ordered operation/wire tape"),
        ("parameter_aware_tape_match", "ordered wire tape plus exact parameter values"),
        ("full_literal_circuit_match", "parameter-aware tape plus global phase"),
    ]
    rows = []
    for field, label in labels:
        item = crossed[field]
        rows.append(
            {
                "diagnostic": label,
                "matches": item["count"],
                "signature_pass_denominator": item["denominator"],
                "conditional_rate": item["rate"],
                "crossed_ci_low": item["crossed_bootstrap_95"][0],
                "crossed_ci_high": item["crossed_bootstrap_95"][1],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def interval_pct(interval: list[float]) -> str:
    return f"[{pct(interval[0])}, {pct(interval[1])}]"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    design = payload["design"]
    summary = payload["overall"]
    crossed = payload["crossed_intervals"]
    by_model = payload["by_model"]
    by_cohort = payload["by_cohort"]
    identifiable = payload["identifiable_150"]
    fields = {
        item["field"]: item for item in crossed
    }
    lines = [
        "# Ordered And Operand-Aware Validation Of The PQID-Bench Signature Predicate",
        "",
        "## Audit design",
        "",
        f"- evaluator version: `{design['evaluator_version']}`",
        f"- structural predicate: `{design['structural_predicate_version']}`",
        "",
        f"The audit replays `{design['cell_count']:,}` frozen prompt-model outputs and the `{design['prompt_count']}` clean reference programs through the same restricted Qiskit namespace and circuit-selection functions used by the published harness. Clean references receive the conservative metadata-derived context aliases already documented by the source-validity ablation; generated outputs retain the strict standalone namespace. The audit compares the selected circuits without changing the headline scores.",
        "",
        "The current reference-signature predicate is",
        "",
        "$$M_i(f)=Q_i(f)K_i(f)T_i(f),$$",
        "",
        "where the scored indicators compare qubit count, classical-bit count, and the complete gate-type count map. Scalar non-barrier gate-count agreement is recorded separately as G_i(f). Because exact count-map equality implies scalar gate-count equality for every frozen target and evaluated candidate, G_i(f) is retained as a diagnostic rather than an independent restriction. The stricter ordered-wire diagnostic is",
        "",
        "$$W_i(f)=\\mathbf{1}[(q_i,c_i,(o_t,\\mathbf{q}_t,\\mathbf{c}_t)_{t=1}^{L_i})=(q_i^*,c_i^*,(o_t^*,\\mathbf{q}_t^*,\\mathbf{c}_t^*)_{t=1}^{L_i^*})],$$",
        "",
        "with circuit widths $(q_i,c_i)$, operation name $o_t$, ordered quantum operands $\\mathbf{q}_t$, and ordered classical operands $\\mathbf{c}_t$ at tape position $t$. Parameter tokens and global phase are reported as still stricter diagnostics.",
        "",
        "## Replay integrity",
        "",
        f"All `{design['reference_circuits_materialized']}` reference circuits materialized and matched their frozen signatures; reference failures: `{design['reference_errors']}`. Of `{summary['report_executable']:,}` outputs marked executable by the stored reports, `{summary['replayed_executable']:,}` replayed successfully. Signature replay disagreements: `{summary['signature_replay_disagreements']}`; selected-circuit-name disagreements: `{summary['selected_name_disagreements']}`.",
        "",
        "## Conditional agreement among current signature passes",
        "",
        "| diagnostic | matches / signature passes | rate | crossed model-by-signature 95% interval |",
        "|---|---:|---:|---:|",
    ]
    display_fields = [
        ("gate_order_match", "operation-name order"),
        ("quantum_operand_sequence_match", "ordered quantum operands"),
        ("classical_operand_sequence_match", "ordered classical operands"),
        ("ordered_wire_tape_match", "ordered operation-and-wire tape"),
        ("parameter_aware_tape_match", "ordered wire tape plus exact parameter values"),
        ("full_literal_circuit_match", "parameter-aware tape plus global phase"),
    ]
    for key, label in display_fields:
        item = fields[key]
        lines.append(
            f"| {label} | {item['count']:,} / {item['denominator']:,} | {pct(item['rate'])} | {interval_pct(item['crossed_bootstrap_95'])} |"
        )
    measurement = summary["measurement_map_given_signature_and_measurement"]
    lines.extend(
        [
            "",
            f"For signature-matched targets containing measurements, the exact qubit-to-classical-bit map agrees in `{measurement['count']:,} / {measurement['denominator']:,}` cases (`{pct(measurement['rate']) if measurement['rate'] is not None else 'n/a'}`). There are `{summary['ordered_wire_matches_outside_signature']}` replayed ordered-wire matches outside the current signature-pass set; an exact ordered-wire match should imply the four coarser signature components, so any nonzero value would indicate an evaluator inconsistency.",
            "",
            "A signature pass that fails the ordered-wire test is called a *signature-only pass* here, not a semantic false positive. Exact source order is stricter than physical or algorithmic equivalence and can reject valid commuting or rewritten circuits.",
            "",
            "## Cohort sensitivity",
            "",
            "| cohort | cells | signature passes | ordered-wire / signature | parameter-aware / signature |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for cohort in ["pilot", "extension"]:
        item = by_cohort[cohort]
        wire = item["ordered_wire_tape_given_signature"]
        parameter = item["parameter_aware_tape_given_signature"]
        lines.append(
            f"| {cohort} | {item['cells']:,} | {item['report_signature_matches']:,} | {wire['count']:,}/{wire['denominator']:,} ({pct(wire['rate']) if wire['rate'] is not None else 'n/a'}) | {parameter['count']:,}/{parameter['denominator']:,} ({pct(parameter['rate']) if parameter['rate'] is not None else 'n/a'}) |"
        )
    lines.extend(
        [
            "",
            f"Excluding the four prespecified prompt-identifiability exceptions leaves `{identifiable['cells']:,}` cells and `{identifiable['report_signature_matches']:,}` signature passes. Its ordered-wire conditional agreement is `{pct(identifiable['ordered_wire_tape_given_signature']['rate'])}`.",
            "",
            "## Per-model audit",
            "",
            "| model | executable | signature | ordered-wire | ordered-wire / signature | parameter-aware / signature |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in by_model:
        lines.append(
            f"| {row['model_label']} | {row['executable']} | {row['signature_matches']} | {row['ordered_wire_tape_matches']} | {pct(row['ordered_wire_given_signature_rate']) if row['ordered_wire_given_signature_rate'] is not None else 'n/a'} | {pct(row['parameter_aware_given_signature_rate']) if row['parameter_aware_given_signature_rate'] is not None else 'n/a'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        "The ordered-wire rate quantifies how often the current signature predicate also recovers the evaluator-selected reference operation-and-operand tape. It should be used as a validation layer and a design target for PQID-Bench 2, not retroactively substituted for the published headline denominator. Parameter-token and global-phase agreement are separate stricter representation-level checks; neither proves nor disproves semantic circuit equivalence.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "python PQID/submissions/acm_tqc_benchmark/scripts/analyze_pqid_bench_ordered_operand_validation.py",
            "```",
            "",
            f"- machine-readable summary: `{JSON_OUT.as_posix()}`",
            f"- cell-level audit: `{CELL_JSONL_OUT.as_posix()}`",
            f"- per-model table: `{MODEL_CSV_OUT.as_posix()}`",
            f"- Supplemental Table S30 TSV: `{S30_TSV_OUT.as_posix()}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-path", type=Path, default=PROMPT_PATH)
    parser.add_argument("--split-manifest", type=Path, default=SPLIT_MANIFEST_PATH)
    parser.add_argument("--eval-dir", type=Path, action="append", default=None)
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument("--cell-jsonl-out", type=Path, default=CELL_JSONL_OUT)
    parser.add_argument("--model-csv-out", type=Path, default=MODEL_CSV_OUT)
    parser.add_argument("--bootstrap", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()

    prompts = read_jsonl(args.prompt_path)
    cohorts = cohort_map(args.split_manifest)
    qiskit_env = copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit unavailable: {qiskit_env.get('error')}")
    references, reference_errors = reference_circuits(
        prompts, args.split_manifest, qiskit_env
    )
    reports = load_reports(args.eval_dir or DEFAULT_EVAL_DIRS)
    rows = audit_cells(prompts, reports, references, cohorts, qiskit_env)
    overall = summarize_subset(rows)
    by_model = per_model_summary(rows)
    by_cohort = {
        cohort: summarize_subset([row for row in rows if row["cohort"] == cohort])
        for cohort in ["pilot", "extension"]
    }
    identifiable_rows = [
        row for row in rows if row["prompt_id"] not in IDENTIFIABILITY_EXCLUSIONS
    ]
    crossed_fields = [
        "gate_order_match",
        "quantum_operand_sequence_match",
        "classical_operand_sequence_match",
        "ordered_wire_tape_match",
        "parameter_aware_tape_match",
        "full_literal_circuit_match",
    ]
    crossed_intervals = [
        crossed_cluster_interval(
            rows,
            prompts,
            field,
            args.bootstrap,
            args.seed + index,
        )
        for index, field in enumerate(crossed_fields)
    ]
    payload = {
        "schema_version": "pqid-bench-ordered-operand-validation-v1",
        "design": {
            "evaluator_version": validity.EVALUATOR_VERSION,
            "structural_predicate_version": validity.STRUCTURAL_PREDICATE_VERSION,
            "prompt_count": len(prompts),
            "model_count": len(MODEL_ORDER),
            "cell_count": len(rows),
            "target_signature_count": len(
                {metadata_signature(prompt) for prompt in prompts}
            ),
            "reference_circuits_materialized": len(references),
            "reference_errors": len(reference_errors),
            "reference_error_records": reference_errors,
            "candidate_selection": (
                "strict standalone namespace and alphabetical circuit selection, "
                "matching the current harness"
            ),
            "reference_selection": (
                "target-metadata context and target-metadata circuit selection, "
                "matching clean-source validation"
            ),
            "exact_tape_is_semantic_equivalence": False,
            "bootstrap_replicates": args.bootstrap,
            "bootstrap_seed": args.seed,
        },
        "overall": overall,
        "crossed_intervals": crossed_intervals,
        "by_cohort": by_cohort,
        "identifiable_150": summarize_subset(identifiable_rows),
        "by_model": by_model,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_jsonl(args.cell_jsonl_out, rows)
    write_model_csv(args.model_csv_out, by_model)
    write_s30_tsv(S30_TSV_OUT, payload)
    write_markdown(args.md_out, payload)
    print(f"Wrote {args.json_out.as_posix()}")
    print(f"Wrote {args.md_out.as_posix()}")
    print(f"Wrote {args.cell_jsonl_out.as_posix()}")
    print(f"Wrote {args.model_csv_out.as_posix()}")
    print(f"Wrote {S30_TSV_OUT.as_posix()}")


if __name__ == "__main__":
    main()
