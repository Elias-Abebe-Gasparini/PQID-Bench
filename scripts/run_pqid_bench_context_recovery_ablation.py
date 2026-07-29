"""Run a conservative context-recovery ablation for executable-validity misses.

The strict executable-validity check intentionally executes each source-code
snippet in isolation. This ablation targets only the strict-run `NameError`
tail and supplies simple notebook-local context that is recoverable from
metadata or common Qiskit naming conventions.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import run_pqid_bench_executable_validity_check as validity


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = validity.DEFAULT_INPUT
DEFAULT_OUTPUT_DIR = SUBMISSION_DIR / "artifacts"

REPORT_NAME = "pqid_bench_context_recovery_ablation_report"

MISSING_NAME_RE = re.compile(r"name '([^']+)' is not defined")


def missing_name(error_message: str | None) -> str | None:
    if not error_message:
        return None
    match = MISSING_NAME_RE.search(error_message)
    return match.group(1) if match else None


def int_meta(metadata: dict, key: str, default: int) -> int:
    try:
        return int(metadata.get(key) or default)
    except (TypeError, ValueError):
        return default


def infer_problem_size(metadata: dict, code: str, *, symbol: str) -> int:
    nq = max(int_meta(metadata, "num_qubits", 1), 1)
    nc = max(int_meta(metadata, "num_clbits", 0), 0)
    compact = re.sub(r"\s+", "", code)

    if f"{symbol}*2" in compact or f"2*{symbol}" in compact:
        return max(nq // 2, 1)
    if f"{symbol}+1" in compact or f"1+{symbol}" in compact:
        if nc:
            return nc
        return max(nq - 1, 1)
    if nc and nc <= nq:
        return nc
    return nq


def register(namespace: dict, qiskit_env: dict, name: str, size: int, *, kind: str) -> None:
    size = max(int(size), 1)
    if kind == "quantum":
        namespace[name] = qiskit_env["QuantumRegister"](size, name)
    elif kind == "classical":
        namespace[name] = qiskit_env["ClassicalRegister"](size, name)
    else:  # pragma: no cover - defensive programming
        raise ValueError(f"Unknown register kind: {kind}")


def add_gate_classes(namespace: dict) -> list[str]:
    recovered = []
    try:
        from qiskit.circuit.library import HGate, SGate, TGate, XGate
    except Exception:
        return recovered
    for name, value in {"HGate": HGate, "SGate": SGate, "TGate": TGate, "XGate": XGate}.items():
        namespace[name] = value
        recovered.append(name)
    return recovered


def build_recovery_namespace(row: dict, qiskit_env: dict, target_symbol: str | None) -> tuple[dict, list[str], dict]:
    metadata = row["metadata"]
    code = row["code"]
    nq = max(int_meta(metadata, "num_qubits", 1), 1)
    nc = max(int_meta(metadata, "num_clbits", 0), 0)
    Parameter = qiskit_env["Parameter"]

    recovered: dict = {
        "sqrt": math.sqrt,
        "num_qubits": nq,
        "nqubits": nq,
        "n": infer_problem_size(metadata, code, symbol="n"),
        "n_qubits": infer_problem_size(metadata, code, symbol="n_qubits"),
        "angle": Parameter("angle"),
        "a": Parameter("a"),
        "b": Parameter("b"),
        "t": Parameter("t"),
    }
    reasons = {
        "sqrt": "math.sqrt",
        "num_qubits": "metadata.num_qubits",
        "nqubits": "metadata.num_qubits",
        "n": "metadata-derived problem size",
        "n_qubits": "metadata-derived problem size",
        "angle": "symbolic Parameter",
        "a": "symbolic Parameter",
        "b": "symbolic Parameter",
        "t": "symbolic Parameter",
    }

    register(recovered, qiskit_env, "qreg", nq, kind="quantum")
    register(recovered, qiskit_env, "qreg2", nq, kind="quantum")
    register(recovered, qiskit_env, "q3", 3 if nq >= 3 else nq, kind="quantum")
    register(recovered, qiskit_env, "i_q", nq, kind="quantum")
    register(recovered, qiskit_env, "qb", nq, kind="quantum")
    register(recovered, qiskit_env, "creg", nc or nq, kind="classical")
    register(recovered, qiskit_env, "creg2", nc or nq, kind="classical")
    register(recovered, qiskit_env, "c3", 3 if (nc or nq) >= 3 else (nc or nq), kind="classical")
    register(recovered, qiskit_env, "i_c", nc or nq, kind="classical")
    reasons.update(
        {
            "qreg": "metadata-sized QuantumRegister",
            "qreg2": "metadata-sized QuantumRegister",
            "q3": "three-qubit QuantumRegister alias",
            "i_q": "metadata-sized QuantumRegister alias",
            "qb": "metadata-sized QuantumRegister alias",
            "creg": "metadata-sized ClassicalRegister",
            "creg2": "metadata-sized ClassicalRegister",
            "c3": "three-bit ClassicalRegister alias",
            "i_c": "metadata-sized ClassicalRegister alias",
        }
    )

    if "QuantumCircuit(q, anc, c)" in code and nq > 1:
        register(recovered, qiskit_env, "q", nq - 1, kind="quantum")
        register(recovered, qiskit_env, "anc", 1, kind="quantum")
        reasons["q"] = "data register recovered from q + anc constructor"
        reasons["anc"] = "single-qubit ancilla register"
    else:
        register(recovered, qiskit_env, "anc", 1, kind="quantum")
        reasons["anc"] = "single-qubit ancilla register"

    if "crz" in code or "crx" in code:
        first = max(nc // 2, 1)
        second = max(nc - first, 1)
        register(recovered, qiskit_env, "crz", first, kind="classical")
        register(recovered, qiskit_env, "crx", second, kind="classical")
        reasons["crz"] = "split classical register"
        reasons["crx"] = "split classical register"

    if target_symbol == "circ":
        QuantumCircuit = qiskit_env["QuantumCircuit"]
        recovered["circ"] = QuantumCircuit(nq)
        reasons["circ"] = "empty metadata-sized quantum circuit placeholder"

    for name in add_gate_classes(recovered):
        reasons[name] = "standard Qiskit gate class"

    names = sorted(recovered)
    return recovered, names, reasons


def evaluate_with_recovery(row: dict, qiskit_env: dict, baseline: dict) -> dict:
    metadata = row["metadata"]
    namespace = validity.execution_namespace(metadata, qiskit_env)
    baseline_missing = missing_name(baseline.get("execution_error_message"))
    recovered, recovered_symbols, reasons = build_recovery_namespace(row, qiskit_env, baseline_missing)
    namespace.update(recovered)

    try:
        exec(row["code"], namespace, namespace)
    except Exception as exc:
        return {
            "row_id": row["row_id"],
            "label": row["label"],
            "file_path": metadata.get("file_path"),
            "baseline_error_type": baseline.get("execution_error_type"),
            "baseline_error_message": baseline.get("execution_error_message"),
            "baseline_missing_symbol": baseline_missing,
            "recovered_symbols": recovered_symbols,
            "recovery_reasons": reasons,
            "recovery_execution_success": False,
            "recovery_error_type": type(exc).__name__,
            "recovery_error_message": str(exc),
            "circuit_found": False,
        }

    circuits = validity.collect_circuits(namespace, qiskit_env)
    circuit_name, circuit = validity.choose_circuit(circuits, metadata)
    if circuit is None:
        return {
            "row_id": row["row_id"],
            "label": row["label"],
            "file_path": metadata.get("file_path"),
            "baseline_error_type": baseline.get("execution_error_type"),
            "baseline_error_message": baseline.get("execution_error_message"),
            "baseline_missing_symbol": baseline_missing,
            "recovered_symbols": recovered_symbols,
            "recovery_reasons": reasons,
            "recovery_execution_success": True,
            "recovery_error_type": None,
            "recovery_error_message": None,
            "circuit_found": False,
            "circuit_count": 0,
        }

    structural = validity.structural_result(circuit, metadata)
    qasm = validity.qasm_export_result(circuit, qiskit_env)
    simulation = validity.simulation_result(circuit, qiskit_env)
    return {
        "row_id": row["row_id"],
        "label": row["label"],
        "file_path": metadata.get("file_path"),
        "baseline_error_type": baseline.get("execution_error_type"),
        "baseline_error_message": baseline.get("execution_error_message"),
        "baseline_missing_symbol": baseline_missing,
        "recovered_symbols": recovered_symbols,
        "recovery_reasons": reasons,
        "recovery_execution_success": True,
        "recovery_error_type": None,
        "recovery_error_message": None,
        "circuit_found": True,
        "circuit_count": len(circuits),
        "selected_circuit_name": circuit_name,
        "structural": structural,
        "qasm3_export": qasm,
        "simulation": simulation,
    }


def rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def summarize(baseline_results: list[dict], recovery_results: list[dict], total_rows: int) -> dict:
    target_rows = len(recovery_results)
    baseline_success = sum(1 for row in baseline_results if row.get("execution_success"))
    baseline_name_errors = sum(
        1 for row in baseline_results if row.get("execution_error_type") == "NameError"
    )
    recovered_success = sum(1 for row in recovery_results if row.get("recovery_execution_success"))
    recovered_circuits = sum(1 for row in recovery_results if row.get("circuit_found"))
    recovered_structural = sum(
        1 for row in recovery_results if row.get("structural", {}).get("checks", {}).get("all_match")
    )
    recovered_qasm = sum(1 for row in recovery_results if row.get("qasm3_export", {}).get("success"))
    recovered_sim_eligible = sum(
        1 for row in recovery_results if row.get("simulation", {}).get("eligible")
    )
    recovered_sim_success = sum(
        1 for row in recovery_results if row.get("simulation", {}).get("success")
    )

    by_symbol = {}
    for symbol in sorted(set(row.get("baseline_missing_symbol") for row in recovery_results)):
        subset = [row for row in recovery_results if row.get("baseline_missing_symbol") == symbol]
        by_symbol[str(symbol)] = {
            "target_rows": len(subset),
            "execution_recovered": sum(1 for row in subset if row.get("recovery_execution_success")),
            "circuit_found": sum(1 for row in subset if row.get("circuit_found")),
            "structural_match": sum(
                1 for row in subset if row.get("structural", {}).get("checks", {}).get("all_match")
            ),
            "qasm3_export_success": sum(
                1 for row in subset if row.get("qasm3_export", {}).get("success")
            ),
        }

    recovery_errors = Counter(
        row.get("recovery_error_type")
        for row in recovery_results
        if not row.get("recovery_execution_success")
    )
    structural_mismatches = Counter(
        check
        for row in recovery_results
        if row.get("circuit_found")
        and not row.get("structural", {}).get("checks", {}).get("all_match")
        for check, passed in row.get("structural", {}).get("checks", {}).items()
        if check != "all_match" and not passed
    )
    qasm_errors = Counter(
        row.get("qasm3_export", {}).get("error_type")
        for row in recovery_results
        if row.get("circuit_found") and not row.get("qasm3_export", {}).get("success")
    )
    symbol_usage = Counter(
        symbol for row in recovery_results for symbol in row.get("recovered_symbols", [])
    )

    return {
        "total_clean_rows": total_rows,
        "strict_execution_success": baseline_success,
        "strict_execution_rate": rate(baseline_success, total_rows),
        "strict_name_error_failures": baseline_name_errors,
        "target_rows": target_rows,
        "recovered_execution_success": recovered_success,
        "recovered_circuit_found": recovered_circuits,
        "recovered_structural_match": recovered_structural,
        "recovered_qasm3_export_success": recovered_qasm,
        "recovered_simulation_eligible": recovered_sim_eligible,
        "recovered_simulation_success": recovered_sim_success,
        "recovered_execution_rate_on_targets": rate(recovered_success, target_rows),
        "recovered_structural_rate_on_targets": rate(recovered_structural, target_rows),
        "overall_execution_success_after_recovery": baseline_success + recovered_success,
        "overall_execution_rate_after_recovery": rate(baseline_success + recovered_success, total_rows),
        "by_missing_symbol": by_symbol,
        "residual_recovery_errors": dict(recovery_errors),
        "structural_mismatch_checks": dict(structural_mismatches),
        "qasm3_export_errors": dict(qasm_errors),
        "recovered_symbol_usage": dict(symbol_usage),
    }


def example_rows(results: list[dict], *, recovered: bool, limit: int = 8) -> list[dict]:
    examples = []
    for row in results:
        if recovered and not row.get("recovery_execution_success"):
            continue
        if not recovered and row.get("recovery_execution_success"):
            continue
        item = {
            "row_id": row["row_id"],
            "label": row["label"],
            "file_path": row.get("file_path"),
            "baseline_missing_symbol": row.get("baseline_missing_symbol"),
        }
        if recovered:
            item.update(
                {
                    "structural_match": row.get("structural", {}).get("checks", {}).get("all_match"),
                    "qasm3_export": row.get("qasm3_export", {}).get("success"),
                    "simulation_eligible": row.get("simulation", {}).get("eligible"),
                }
            )
        else:
            item.update(
                {
                    "residual_error": row.get("recovery_error_type"),
                    "message": row.get("recovery_error_message"),
                }
            )
        examples.append(item)
        if len(examples) >= limit:
            break
    return examples


def example_quality_issues(results: list[dict], limit: int = 6) -> list[dict]:
    examples = []
    for row in results:
        structural_ok = row.get("structural", {}).get("checks", {}).get("all_match")
        qasm_ok = row.get("qasm3_export", {}).get("success")
        if not row.get("circuit_found") or (structural_ok is not False and qasm_ok is not False):
            continue
        examples.append(
            {
                "row_id": row["row_id"],
                "label": row["label"],
                "file_path": row.get("file_path"),
                "baseline_missing_symbol": row.get("baseline_missing_symbol"),
                "structural_checks": row.get("structural", {}).get("checks"),
                "qasm3_export": qasm_ok,
                "qasm3_error": row.get("qasm3_export", {}).get("error_type"),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def write_outputs(output_dir: Path, input_path: Path, qiskit_env: dict, rows: list[dict], recovery_results: list[dict], summary: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{REPORT_NAME}.md"
    json_path = output_dir / f"{REPORT_NAME}.json"

    lines = [
        "# PQID-Bench Context-Recovery Ablation Report",
        "",
        f"- input file: `{validity.display_path(input_path)}`",
        f"- clean source-code rows: `{len(rows):,}`",
        f"- Qiskit available: `{qiskit_env.get('available')}`",
        f"- Qiskit version: `{qiskit_env.get('version', '<unavailable>')}`",
        "",
        "## Headline Recovery",
        "",
        "| check | rows | rate |",
        "| --- | ---: | ---: |",
        f"| strict isolated execution succeeds | {summary['strict_execution_success']:,} | {pct(summary['strict_execution_rate'])} |",
        f"| strict `NameError` target rows | {summary['target_rows']:,} | {pct(rate(summary['target_rows'], summary['total_clean_rows']))} |",
        f"| target rows execute after recovery | {summary['recovered_execution_success']:,} | {pct(summary['recovered_execution_rate_on_targets'])} |",
        f"| target rows produce `QuantumCircuit` after recovery | {summary['recovered_circuit_found']:,} | {pct(rate(summary['recovered_circuit_found'], summary['target_rows']))} |",
        f"| target rows structurally match after recovery | {summary['recovered_structural_match']:,} | {pct(summary['recovered_structural_rate_on_targets'])} |",
        f"| target rows export OpenQASM 3 after recovery | {summary['recovered_qasm3_export_success']:,} | {pct(rate(summary['recovered_qasm3_export_success'], summary['target_rows']))} |",
        f"| target rows pass small-circuit simulation after recovery | {summary['recovered_simulation_success']:,} | {pct(rate(summary['recovered_simulation_success'], summary['target_rows']))} |",
        f"| overall execution after strict + recovery | {summary['overall_execution_success_after_recovery']:,} | {pct(summary['overall_execution_rate_after_recovery'])} |",
        "",
        "Recovery is applied only to rows that failed strict isolated execution with `NameError`. The ablation supplies metadata-sized registers, common notebook aliases, symbolic angle parameters, and standard Qiskit gate classes.",
        "",
        "## Recovery By Missing Symbol",
        "",
        "| missing symbol | target rows | execution recovered | structural match | QASM3 export |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for symbol, item in sorted(
        summary["by_missing_symbol"].items(),
        key=lambda pair: (-pair[1]["target_rows"], pair[0]),
    ):
        lines.append(
            f"| `{symbol}` | {item['target_rows']:,} | {item['execution_recovered']:,} | "
            f"{item['structural_match']:,} | {item['qasm3_export_success']:,} |"
        )

    lines.extend(["", "## Residual Recovery Errors", ""])
    if summary["residual_recovery_errors"]:
        lines.extend(["| error type | rows |", "| --- | ---: |"])
        for error, count in sorted(summary["residual_recovery_errors"].items(), key=lambda pair: (-pair[1], str(pair[0]))):
            lines.append(f"| `{error}` | {count:,} |")
    else:
        lines.append("No residual execution errors among targeted rows.")

    lines.extend(["", "## Residual Structural / Export Issues", ""])
    if summary["structural_mismatch_checks"]:
        lines.extend(["| structural failed check | rows |", "| --- | ---: |"])
        for check, count in sorted(summary["structural_mismatch_checks"].items(), key=lambda pair: (-pair[1], str(pair[0]))):
            lines.append(f"| `{check}` | {count:,} |")
    else:
        lines.append("No structural mismatches among recovered target rows.")
    lines.append("")
    if summary["qasm3_export_errors"]:
        lines.extend(["| QASM3 export error | rows |", "| --- | ---: |"])
        for error, count in sorted(summary["qasm3_export_errors"].items(), key=lambda pair: (-pair[1], str(pair[0]))):
            lines.append(f"| `{error}` | {count:,} |")
    else:
        lines.append("No QASM3 export errors among recovered target rows.")

    quality_issues = example_quality_issues(recovery_results)
    lines.extend(["", "## Representative Residual Structural / Export Issues", ""])
    if quality_issues:
        for index, row in enumerate(quality_issues, start=1):
            lines.append(f"### Quality Issue {index}")
            lines.append("")
            for key, value in row.items():
                lines.append(f"- {key}: `{value}`")
            lines.append("")
    else:
        lines.append("No residual structural or export issues.")

    lines.extend(["", "## Representative Recovered Rows", ""])
    for index, row in enumerate(example_rows(recovery_results, recovered=True), start=1):
        lines.append(f"### Recovered {index}")
        lines.append("")
        for key, value in row.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")

    residual = example_rows(recovery_results, recovered=False)
    lines.extend(["", "## Representative Residual Failures", ""])
    if residual:
        for index, row in enumerate(residual, start=1):
            lines.append(f"### Residual {index}")
            lines.append("")
            for key, value in row.items():
                lines.append(f"- {key}: `{value}`")
            lines.append("")
    else:
        lines.append("No residual failures.")

    payload = {
        "input_file": validity.display_path(input_path),
        "qiskit_available": qiskit_env.get("available"),
        "qiskit_version": qiskit_env.get("version"),
        "row_count": len(rows),
        "summary": summary,
        "recovered_examples": example_rows(recovery_results, recovered=True),
        "quality_issue_examples": quality_issues,
        "residual_examples": residual,
    }
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {validity.display_path(report_path)}")
    print(f"Wrote {validity.display_path(json_path)}")


def run(input_path: Path, output_dir: Path) -> None:
    qiskit_env = validity.import_qiskit()
    rows = validity.clean_rows(input_path)
    if len(rows) != 734:
        raise ValueError(f"Expected 734 clean source-code rows, found {len(rows)}")
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is not available: {qiskit_env.get('error')}")

    baseline_results = [validity.evaluate_row(row, qiskit_env) for row in rows]
    baseline_by_id = {row["row_id"]: row for row in baseline_results}
    targets = [
        row
        for row in rows
        if baseline_by_id[row["row_id"]].get("execution_error_type") == "NameError"
    ]
    recovery_results = [
        evaluate_with_recovery(row, qiskit_env, baseline_by_id[row["row_id"]])
        for row in targets
    ]
    summary = summarize(baseline_results, recovery_results, len(rows))
    write_outputs(output_dir, input_path, qiskit_env, rows, recovery_results, summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.input, args.output_dir)


if __name__ == "__main__":
    main()
