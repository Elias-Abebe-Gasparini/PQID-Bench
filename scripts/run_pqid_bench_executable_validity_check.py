"""Run executable-validity and small-circuit consistency checks for PQID-Bench.

This script executes the clean source-code seed snippets, extracts a produced
Qiskit `QuantumCircuit`, compares observed structural metadata with the stored
metadata, exports OpenQASM 3 when possible, and runs a small-circuit statevector
viability check for eligible circuits.
"""

from __future__ import annotations

import argparse
import builtins
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


EVALUATOR_VERSION = "pqid-bench-evaluator-1.1.0-safe-builtins"
STRUCTURAL_PREDICATE_VERSION = "pqid-bench-reference-signature-1.0.0-count-map"


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
# The research checkout nests this script below PQID/submissions, while the
# public release places it directly below the release root.
PQID_DIR = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else SUBMISSION_DIR
DEFAULT_INPUT = (
    PQID_DIR / "data" / "processed" / "seed_drafts_quality_aware_source_code_v1.jsonl"
)
DEFAULT_OUTPUT_DIR = SUBMISSION_DIR / "artifacts"

CLEAN_ROLE_TO_LABEL = {
    "gold_generation": "strict_n8",
    "broad_generation": "extended_n8",
}


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def import_qiskit() -> dict:
    try:
        import qiskit
        import qiskit.qasm3 as qasm3
        from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
        from qiskit.circuit import Parameter, ParameterVector
        from qiskit.quantum_info import Statevector
    except Exception as exc:  # pragma: no cover - environment-dependent path
        return {"available": False, "error": repr(exc)}

    return {
        "available": True,
        "qiskit": qiskit,
        "qasm3": qasm3,
        "QuantumCircuit": QuantumCircuit,
        "QuantumRegister": QuantumRegister,
        "ClassicalRegister": ClassicalRegister,
        "Parameter": Parameter,
        "ParameterVector": ParameterVector,
        "Statevector": Statevector,
        "version": getattr(qiskit, "__version__", "<unknown>"),
    }


def clean_rows(path: Path) -> list[dict]:
    rows = []
    for index, raw in enumerate(iter_jsonl(path)):
        metadata = raw.get("metadata", {})
        role = metadata.get("seed_role")
        if role not in CLEAN_ROLE_TO_LABEL:
            continue
        code = raw.get("output") or ""
        if not code.strip():
            continue
        rows.append(
            {
                "row_id": metadata.get("content_hash") or f"clean_{index:04d}",
                "label": CLEAN_ROLE_TO_LABEL[role],
                "input": raw.get("input") or "",
                "code": code,
                "metadata": metadata,
            }
        )
    return rows


def safe_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
    if level != 0:
        raise ImportError("relative imports are disabled in the benchmark executor")
    root = str(name).split(".", maxsplit=1)[0]
    if root not in {"math", "numpy", "qiskit"}:
        raise ImportError(f"import of {name!r} is disabled in the benchmark executor")
    return builtins.__import__(name, globals, locals, fromlist, level)


def quiet_print(*args, **kwargs) -> None:
    """Preserve normal Python executability without emitting model output."""

    return None


def safe_builtins() -> dict:
    return {
        "__import__": safe_import,
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "complex": complex,
        "dict": dict,
        "enumerate": enumerate,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "max": max,
        "min": min,
        "pow": pow,
        "print": quiet_print,
        "range": range,
        "reversed": reversed,
        "round": round,
        "set": set,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
    }


def execution_namespace(metadata: dict, qiskit_env: dict) -> dict:
    QuantumCircuit = qiskit_env["QuantumCircuit"]
    QuantumRegister = qiskit_env["QuantumRegister"]
    ClassicalRegister = qiskit_env["ClassicalRegister"]
    Parameter = qiskit_env["Parameter"]
    ParameterVector = qiskit_env["ParameterVector"]

    nq = int(metadata.get("num_qubits") or 4)
    nc = int(metadata.get("num_clbits") or max(nq, 1))
    nq = max(nq, 1)
    nc = max(nc, 1)

    qreg = QuantumRegister(nq, "q")
    creg = ClassicalRegister(nc, "c")
    namespace = {
        "__builtins__": safe_builtins(),
        "np": np,
        "numpy": np,
        "math": math,
        "pi": math.pi,
        "QuantumCircuit": QuantumCircuit,
        "QuantumRegister": QuantumRegister,
        "ClassicalRegister": ClassicalRegister,
        "Parameter": Parameter,
        "ParameterVector": ParameterVector,
        "qr": qreg,
        "q": qreg,
        "cr": creg,
        "c": creg,
        "theta": Parameter("theta"),
        "phi": Parameter("phi"),
        "lam": Parameter("lambda"),
        "gamma": Parameter("gamma"),
        "beta": Parameter("beta"),
    }
    return namespace


def collect_circuits(namespace: dict, qiskit_env: dict) -> list[tuple[str, object]]:
    QuantumCircuit = qiskit_env["QuantumCircuit"]
    circuits = []
    for name, value in namespace.items():
        if isinstance(value, QuantumCircuit):
            circuits.append((name, value))
    return circuits


def choose_circuit(circuits: list[tuple[str, object]], metadata: dict) -> tuple[str, object] | tuple[None, None]:
    if not circuits:
        return None, None
    expected_qubits = metadata.get("num_qubits")
    expected_clbits = metadata.get("num_clbits")
    expected_gate_count = metadata.get("gate_count")

    def score(item: tuple[str, object]) -> tuple[float, str]:
        name, circuit = item
        score_value = 0.0
        if expected_qubits is not None:
            score_value += 100.0 * abs(circuit.num_qubits - float(expected_qubits))
        if expected_clbits is not None:
            score_value += 50.0 * abs(circuit.num_clbits - float(expected_clbits))
        if expected_gate_count is not None:
            score_value += abs(metadata_gate_count(observed_gate_counts(circuit)) - float(expected_gate_count))
        return score_value, name

    return sorted(circuits, key=score)[0]


def normalize_gate_counts(gate_counts: object) -> Counter:
    if not isinstance(gate_counts, dict):
        return Counter()
    return Counter({str(gate).lower(): int(count or 0) for gate, count in gate_counts.items()})


def observed_gate_counts(circuit: object) -> Counter:
    return Counter({str(gate).lower(): int(count) for gate, count in circuit.count_ops().items()})


def metadata_gate_count(gate_counts: Counter) -> int:
    """Match PQID's scalar gate_count convention: barriers are typed but not counted."""
    return sum(count for gate, count in gate_counts.items() if gate != "barrier")


def structural_result(circuit: object, metadata: dict) -> dict:
    """Compare the complete operation-count map, not only its vocabulary support."""

    expected_gates = normalize_gate_counts(metadata.get("gate_types"))
    observed_gates = observed_gate_counts(circuit)
    expected_gate_count = metadata.get("gate_count")
    observed_gate_count = metadata_gate_count(observed_gates)

    checks = {
        "num_qubits_match": metadata.get("num_qubits") == circuit.num_qubits,
        "num_clbits_match": metadata.get("num_clbits") == circuit.num_clbits,
        "gate_count_match": expected_gate_count == observed_gate_count,
        "gate_types_match": expected_gates == observed_gates,
    }
    checks["all_match"] = all(checks.values())
    return {
        "checks": checks,
        "expected": {
            "num_qubits": metadata.get("num_qubits"),
            "num_clbits": metadata.get("num_clbits"),
            "gate_count": expected_gate_count,
            "gate_types": dict(expected_gates),
        },
        "observed": {
            "num_qubits": circuit.num_qubits,
            "num_clbits": circuit.num_clbits,
            "gate_count": observed_gate_count,
            "raw_operation_count": sum(observed_gates.values()),
            "gate_types": dict(observed_gates),
        },
    }


def qasm_export_result(circuit: object, qiskit_env: dict) -> dict:
    try:
        qasm = qiskit_env["qasm3"].dumps(circuit)
    except Exception as exc:
        return {"success": False, "error_type": type(exc).__name__, "length": 0}
    return {"success": True, "error_type": None, "length": len(qasm)}


def simulation_circuit(circuit: object, qiskit_env: dict) -> tuple[object | None, str | None]:
    if circuit.num_qubits > 4:
        return None, "too_many_qubits"
    if circuit.parameters:
        return None, "unbound_parameters"

    QuantumCircuit = qiskit_env["QuantumCircuit"]
    sim = QuantumCircuit(circuit.num_qubits)
    skip_names = {"barrier"}
    reject_names = {"measure", "reset", "if_else", "for_loop", "while_loop", "switch_case", "delay"}

    for instruction in circuit.data:
        operation = instruction.operation
        name = operation.name.lower()
        if name in skip_names:
            continue
        if name in reject_names or instruction.clbits:
            return None, f"non_unitary_or_classical:{name}"
        qubits = [circuit.find_bit(qubit).index for qubit in instruction.qubits]
        try:
            sim.append(operation, qubits)
        except Exception as exc:
            return None, f"append_failed:{type(exc).__name__}"
    return sim, None


def simulation_result(circuit: object, qiskit_env: dict) -> dict:
    sim, reason = simulation_circuit(circuit, qiskit_env)
    if sim is None:
        return {"eligible": False, "success": False, "skip_reason": reason, "norm": None}
    try:
        state = qiskit_env["Statevector"].from_instruction(sim)
        norm = float(sum(abs(value) ** 2 for value in state.data))
    except Exception as exc:
        return {
            "eligible": True,
            "success": False,
            "skip_reason": None,
            "error_type": type(exc).__name__,
            "norm": None,
        }
    return {
        "eligible": True,
        "success": abs(norm - 1.0) < 1e-9,
        "skip_reason": None,
        "error_type": None,
        "norm": norm,
    }


def evaluate_row(row: dict, qiskit_env: dict) -> dict:
    metadata = row["metadata"]
    namespace = execution_namespace(metadata, qiskit_env)
    try:
        exec(row["code"], namespace, namespace)
    except Exception as exc:
        return {
            "row_id": row["row_id"],
            "label": row["label"],
            "file_path": metadata.get("file_path"),
            "execution_success": False,
            "execution_error_type": type(exc).__name__,
            "execution_error_message": str(exc),
            "circuit_found": False,
        }

    circuits = collect_circuits(namespace, qiskit_env)
    circuit_name, circuit = choose_circuit(circuits, metadata)
    if circuit is None:
        return {
            "row_id": row["row_id"],
            "label": row["label"],
            "file_path": metadata.get("file_path"),
            "execution_success": True,
            "execution_error_type": None,
            "circuit_found": False,
            "circuit_count": 0,
        }

    structural = structural_result(circuit, metadata)
    qasm = qasm_export_result(circuit, qiskit_env)
    simulation = simulation_result(circuit, qiskit_env)
    return {
        "row_id": row["row_id"],
        "label": row["label"],
        "file_path": metadata.get("file_path"),
        "execution_success": True,
        "execution_error_type": None,
        "circuit_found": True,
        "circuit_count": len(circuits),
        "selected_circuit_name": circuit_name,
        "structural": structural,
        "qasm3_export": qasm,
        "stored_qasm3_export_successful": metadata.get("openqasm3_export_successful"),
        "simulation": simulation,
    }


def summarize(results: list[dict]) -> dict:
    total = len(results)
    labels = sorted(set(result["label"] for result in results))

    def rate(count: int, denom: int = total) -> float:
        return count / denom if denom else 0.0

    summary = {
        "rows": total,
        "execution_success": sum(1 for result in results if result.get("execution_success")),
        "circuit_found": sum(1 for result in results if result.get("circuit_found")),
        "structural_all_match": sum(
            1
            for result in results
            if result.get("structural", {}).get("checks", {}).get("all_match")
        ),
        "qasm3_export_success": sum(
            1 for result in results if result.get("qasm3_export", {}).get("success")
        ),
        "simulation_eligible": sum(
            1 for result in results if result.get("simulation", {}).get("eligible")
        ),
        "simulation_success": sum(
            1 for result in results if result.get("simulation", {}).get("success")
        ),
    }
    summary["rates"] = {
        "execution_success": rate(summary["execution_success"]),
        "circuit_found": rate(summary["circuit_found"]),
        "structural_all_match": rate(summary["structural_all_match"]),
        "qasm3_export_success": rate(summary["qasm3_export_success"]),
        "simulation_success_among_all": rate(summary["simulation_success"]),
        "simulation_success_among_eligible": summary["simulation_success"]
        / summary["simulation_eligible"]
        if summary["simulation_eligible"]
        else 0.0,
    }

    by_label = {}
    for label in labels:
        subset = [result for result in results if result["label"] == label]
        denom = len(subset)
        by_label[label] = {
            "rows": denom,
            "execution_success": sum(1 for result in subset if result.get("execution_success")),
            "circuit_found": sum(1 for result in subset if result.get("circuit_found")),
            "structural_all_match": sum(
                1
                for result in subset
                if result.get("structural", {}).get("checks", {}).get("all_match")
            ),
            "qasm3_export_success": sum(
                1 for result in subset if result.get("qasm3_export", {}).get("success")
            ),
            "simulation_eligible": sum(
                1 for result in subset if result.get("simulation", {}).get("eligible")
            ),
            "simulation_success": sum(
                1 for result in subset if result.get("simulation", {}).get("success")
            ),
        }
        by_label[label]["rates"] = {
            key: by_label[label][key] / denom if denom else 0.0
            for key in [
                "execution_success",
                "circuit_found",
                "structural_all_match",
                "qasm3_export_success",
            ]
        }
        by_label[label]["rates"]["simulation_success_among_eligible"] = (
            by_label[label]["simulation_success"] / by_label[label]["simulation_eligible"]
            if by_label[label]["simulation_eligible"]
            else 0.0
        )
    summary["by_label"] = by_label

    summary["execution_errors"] = dict(
        Counter(
            result.get("execution_error_type")
            for result in results
            if not result.get("execution_success")
        )
    )
    summary["simulation_skips"] = dict(
        Counter(
            result.get("simulation", {}).get("skip_reason")
            for result in results
            if result.get("circuit_found")
            and not result.get("simulation", {}).get("eligible")
        )
    )
    summary["qasm3_export_errors"] = dict(
        Counter(
            result.get("qasm3_export", {}).get("error_type")
            for result in results
            if result.get("circuit_found")
            and not result.get("qasm3_export", {}).get("success")
        )
    )
    summary["structural_mismatch_checks"] = dict(
        Counter(
            check
            for result in results
            if result.get("circuit_found")
            and not result.get("structural", {}).get("checks", {}).get("all_match")
            for check, passed in result.get("structural", {}).get("checks", {}).items()
            if check != "all_match" and not passed
        )
    )
    return summary


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def example_failures(results: list[dict], limit: int = 8) -> list[dict]:
    examples = []
    for result in results:
        if not result.get("execution_success") or not result.get("circuit_found"):
            examples.append(
                {
                    "row_id": result["row_id"],
                    "label": result["label"],
                    "file_path": result.get("file_path"),
                    "issue": result.get("execution_error_type") or "no_circuit_found",
                    "message": result.get("execution_error_message"),
                }
            )
        elif not result.get("structural", {}).get("checks", {}).get("all_match"):
            examples.append(
                {
                    "row_id": result["row_id"],
                    "label": result["label"],
                    "file_path": result.get("file_path"),
                    "issue": "structural_metadata_mismatch",
                    "checks": result.get("structural", {}).get("checks"),
                    "expected": result.get("structural", {}).get("expected"),
                    "observed": result.get("structural", {}).get("observed"),
                }
            )
        if len(examples) >= limit:
            break
    return examples


def example_qasm_failures(results: list[dict], limit: int = 4) -> list[dict]:
    examples = []
    for result in results:
        if result.get("circuit_found") and not result.get("qasm3_export", {}).get("success"):
            examples.append(
                {
                    "row_id": result["row_id"],
                    "label": result["label"],
                    "file_path": result.get("file_path"),
                    "error": result.get("qasm3_export", {}).get("error_type"),
                }
            )
        if len(examples) >= limit:
            break
    return examples


def write_outputs(
    output_dir: Path,
    input_path: Path,
    qiskit_env: dict,
    rows: list[dict],
    results: list[dict],
    summary: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "pqid_bench_executable_validity_report.md"
    json_path = output_dir / "pqid_bench_executable_validity_report.json"
    label_counts = Counter(row["label"] for row in rows)

    lines = [
        "# PQID-Bench Executable Validity And Small-Circuit Consistency Report",
        "",
        f"- input file: `{display_path(input_path)}`",
        f"- clean source-code rows: `{len(rows):,}`",
        f"- Qiskit available: `{qiskit_env.get('available')}`",
        f"- Qiskit version: `{qiskit_env.get('version', '<unavailable>')}`",
        "",
        "## Clean Execution Pool",
        "",
        "| slice | rows |",
        "| --- | ---: |",
    ]
    for label in ["strict_n8", "extended_n8"]:
        lines.append(f"| `{label}` | {label_counts[label]:,} |")

    lines.extend(
        [
            "",
            "## Headline Checks",
            "",
            "| check | rows | rate |",
            "| --- | ---: | ---: |",
            f"| snippet executed without exception | {summary['execution_success']:,} | {pct(summary['rates']['execution_success'])} |",
            f"| `QuantumCircuit` object found | {summary['circuit_found']:,} | {pct(summary['rates']['circuit_found'])} |",
            f"| structure matches stored metadata | {summary['structural_all_match']:,} | {pct(summary['rates']['structural_all_match'])} |",
            f"| OpenQASM 3 export succeeds | {summary['qasm3_export_success']:,} | {pct(summary['rates']['qasm3_export_success'])} |",
            f"| small-circuit simulation eligible | {summary['simulation_eligible']:,} | {pct(summary['simulation_eligible'] / summary['rows'])} |",
            f"| small-circuit simulation succeeds among eligible | {summary['simulation_success']:,} | {pct(summary['rates']['simulation_success_among_eligible'])} |",
            "",
            "Note: scalar `gate_count` follows the stored PQID convention, where barriers are retained in `gate_types` but excluded from the scalar count.",
        ]
    )

    lines.extend(
        [
            "",
            "## Slice Breakdown",
            "",
            "| slice | rows | execution success | circuit found | structural match | QASM3 export | simulation eligible | simulation success / eligible |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in ["strict_n8", "extended_n8"]:
        item = summary["by_label"][label]
        sim_rate = (
            item["simulation_success"] / item["simulation_eligible"]
            if item["simulation_eligible"]
            else 0.0
        )
        lines.append(
            f"| `{label}` | {item['rows']:,} | {pct(item['rates']['execution_success'])} | "
            f"{pct(item['rates']['circuit_found'])} | {pct(item['rates']['structural_all_match'])} | "
            f"{pct(item['rates']['qasm3_export_success'])} | {item['simulation_eligible']:,} | "
            f"{item['simulation_success']:,} / {item['simulation_eligible']:,} ({pct(sim_rate)}) |"
        )

    lines.extend(
        [
            "",
            "## Execution Errors",
            "",
        ]
    )
    if summary["execution_errors"]:
        lines.extend(["| error type | rows |", "| --- | ---: |"])
        for error, count in sorted(summary["execution_errors"].items(), key=lambda item: (-item[1], str(item[0]))):
            lines.append(f"| `{error}` | {count:,} |")
    else:
        lines.append("No execution errors.")

    lines.extend(
        [
            "",
            "## Structural Mismatch Checks",
            "",
        ]
    )
    if summary["structural_mismatch_checks"]:
        lines.extend(["| failed check | rows |", "| --- | ---: |"])
        for check, count in sorted(
            summary["structural_mismatch_checks"].items(),
            key=lambda item: (-item[1], str(item[0])),
        ):
            lines.append(f"| `{check}` | {count:,} |")
    else:
        lines.append("No structural mismatches among extracted circuits.")

    lines.extend(
        [
            "",
            "## QASM3 Export Errors",
            "",
        ]
    )
    if summary["qasm3_export_errors"]:
        lines.extend(["| error type | rows |", "| --- | ---: |"])
        for error, count in sorted(
            summary["qasm3_export_errors"].items(),
            key=lambda item: (-item[1], str(item[0])),
        ):
            lines.append(f"| `{error}` | {count:,} |")
    else:
        lines.append("No QASM3 export errors among extracted circuits.")

    lines.extend(
        [
            "",
            "## Small-Circuit Simulation Skip Reasons",
            "",
        ]
    )
    if summary["simulation_skips"]:
        lines.extend(["| reason | rows |", "| --- | ---: |"])
        for reason, count in sorted(summary["simulation_skips"].items(), key=lambda item: (-item[1], str(item[0]))):
            lines.append(f"| `{reason}` | {count:,} |")
    else:
        lines.append("No simulation skips among extracted circuits.")

    failures = example_failures(results)
    lines.extend(
        [
            "",
            "## Representative Execution / Metadata Issues",
            "",
        ]
    )
    if failures:
        for index, failure in enumerate(failures, start=1):
            lines.append(f"### Issue {index}")
            lines.append("")
            for key, value in failure.items():
                lines.append(f"- {key}: `{value}`")
            lines.append("")
    else:
        lines.append("No execution, circuit-extraction, or structural metadata issues found.")

    qasm_failures = example_qasm_failures(results)
    lines.extend(
        [
            "",
            "## Representative QASM3 Export Issues",
            "",
        ]
    )
    if qasm_failures:
        for index, failure in enumerate(qasm_failures, start=1):
            lines.append(f"### QASM Issue {index}")
            lines.append("")
            for key, value in failure.items():
                lines.append(f"- {key}: `{value}`")
            lines.append("")
    else:
        lines.append("No QASM3 export issues found.")

    payload = {
        "input_file": display_path(input_path),
        "qiskit_available": qiskit_env.get("available"),
        "qiskit_version": qiskit_env.get("version"),
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "summary": summary,
        "issues": failures,
    }
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {display_path(report_path)}")
    print(f"Wrote {display_path(json_path)}")


def run(input_path: Path, output_dir: Path) -> None:
    qiskit_env = import_qiskit()
    rows = clean_rows(input_path)
    if len(rows) != 734:
        raise ValueError(f"Expected 734 clean source-code rows, found {len(rows)}")
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is not available: {qiskit_env.get('error')}")

    results = [evaluate_row(row, qiskit_env) for row in rows]
    summary = summarize(results)
    write_outputs(output_dir, input_path, qiskit_env, rows, results, summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    run(args.input, args.output_dir)


if __name__ == "__main__":
    main()
