"""Trace retrieval-copy hits missed by all external model rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import analyze_pqid_bench_item_failure_matrix as item_failure
import build_pqid_bench_result_panels as panels
import run_pqid_bench_generation_copy_baseline as copy_baseline
from pqid_bench_model_registry import EXPANDED_MODEL_ORDER, MODEL_ORDER


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
PROMPT_JSONL = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
SPLIT_MANIFEST = ROOT / "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
MATRIX_CSV = ROOT / "artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv"
EVAL_DIR = ROOT / "artifacts/external_model_batches_154/evaluations"
DEFAULT_EVAL_DIRS = [
    EVAL_DIR,
    ROOT / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    ROOT / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
JSON_OUT = ROOT / "artifacts/analysis_154/pqid_bench_retrieval_copy_complementarity_cases.json"
MD_OUT = ROOT / "artifacts/analysis_154/pqid_bench_retrieval_copy_complementarity_cases.md"


def read_prompts(path: Path) -> dict[str, dict[str, Any]]:
    prompts: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        prompts[str(record["prompt_id"])] = record
    return prompts


def compact_gates(gates: dict[str, int]) -> str:
    return ", ".join(f"{gate}:{count}" for gate, count in sorted(gates.items()))


def target_summary(metadata: dict[str, Any]) -> str:
    return (
        f"{metadata['num_qubits']}q/{metadata['num_clbits']}c; "
        f"{metadata['gate_count']} gates; {compact_gates(metadata['gate_types'])}"
    )


def count_external_failures(
    prompt_id: str,
    eval_rows: list[dict[str, Any]],
    model_order: list[str],
) -> dict[str, Any]:
    rows = [
        row
        for row in eval_rows
        if row["prompt_id"] == prompt_id and row["model"] in model_order
    ]
    primary = Counter(row["primary_failure"] for row in rows)
    return {
        "model_rows": len(rows),
        "execution_success": sum(row["execution"]["execution_success"] for row in rows),
        "qasm3_success": sum(row["execution"]["qasm3_success"] for row in rows),
        "num_qubits_match": sum(row["checks"]["num_qubits_match"] for row in rows),
        "num_clbits_match": sum(row["checks"]["num_clbits_match"] for row in rows),
        "gate_count_match": sum(row["checks"]["gate_count_match"] for row in rows),
        "gate_types_match": sum(row["checks"]["gate_types_match"] for row in rows),
        "all_match": sum(row["checks"]["all_match"] for row in rows),
        "primary_failure_counts": dict(primary),
    }


def run(
    *,
    matrix_csv: Path = MATRIX_CSV,
    eval_dirs: Path | list[Path] = EVAL_DIR,
    model_order: list[str] | None = None,
) -> dict[str, Any]:
    if model_order is None:
        model_order = list(MODEL_ORDER)
    prompts = read_prompts(PROMPT_JSONL)
    matrix_rows = panels.read_matrix(matrix_csv)
    matrix_by_prompt = {row["prompt_id"]: row for row in matrix_rows}
    prompt_by_row_id = panels.read_prompt_row_ids(PROMPT_JSONL)
    eval_rows = item_failure.load_evaluations(eval_dirs)

    source_rows = copy_baseline.clean_rows(copy_baseline.DEFAULT_INPUT)
    splits = copy_baseline.split_rows(source_rows, split_manifest_path=SPLIT_MANIFEST)
    qiskit_env = copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is unavailable: {qiskit_env.get('error')}")

    _, records_by_name = copy_baseline.run_generators(
        train_rows=splits["train"],
        test_rows=splits["test"],
        qiskit_env=qiskit_env,
    )

    cases_by_prompt: dict[str, dict[str, Any]] = {}
    baseline_prompt_hits = []
    for baseline in panels.BASELINE_ORDER:
        for record in records_by_name[baseline]:
            if not record.get("structural_checks", {}).get("all_match"):
                continue
            prompt_id = prompt_by_row_id.get(str(record["row_id"]))
            if prompt_id is None:
                continue
            matrix_row = matrix_by_prompt[prompt_id]
            external_successes = sum(
                int(matrix_row.get(model, "0") or 0) for model in model_order
            )
            if external_successes != 0:
                continue

            prompt = prompts[prompt_id]
            case = cases_by_prompt.setdefault(
                prompt_id,
                {
                    "prompt_id": prompt_id,
                    "row_id": record["row_id"],
                    "label": record["label"],
                    "instruction": prompt["instruction"],
                    "families": matrix_row.get("families", ""),
                    "difficulty": float(matrix_row.get("difficulty", 1.0)),
                    "target_file": record["target_file"],
                    "target_metadata": record["target_metadata"],
                    "target_summary": target_summary(record["target_metadata"]),
                    "external_failure_summary": count_external_failures(
                        prompt_id, eval_rows, model_order
                    ),
                    "successful_copy_baselines": [],
                },
            )
            hit = {
                "baseline": baseline,
                "baseline_label": panels.MODEL_LABELS[baseline],
                "score": record["score"],
                "copied_row_id": record["predicted_row_id"],
                "copied_file": record["predicted_file"],
                "copied_label": record["predicted_label"],
                "same_label": record["same_label"],
                "same_group": record["same_group"],
                "predicted_metadata": record["predicted_metadata"],
            }
            case["successful_copy_baselines"].append(hit)
            baseline_prompt_hits.append({**hit, "prompt_id": prompt_id, "row_id": record["row_id"]})

    unique_cases = sorted(cases_by_prompt.values(), key=lambda row: row["prompt_id"])
    aggregate_external_rows = [
        row
        for case in unique_cases
        for row in eval_rows
        if row["prompt_id"] == case["prompt_id"] and row["model"] in model_order
    ]
    aggregate = {
        "unique_prompt_count": len(unique_cases),
        "baseline_prompt_hit_count": len(baseline_prompt_hits),
        "baseline_hit_counts": dict(Counter(hit["baseline_label"] for hit in baseline_prompt_hits)),
        "external_model_attempts": len(aggregate_external_rows),
        "external_execution_success": sum(
            row["execution"]["execution_success"] for row in aggregate_external_rows
        ),
        "external_qasm3_success": sum(row["execution"]["qasm3_success"] for row in aggregate_external_rows),
        "external_gate_types_match": sum(
            row["checks"]["gate_types_match"] for row in aggregate_external_rows
        ),
        "external_structural_match": sum(row["checks"]["all_match"] for row in aggregate_external_rows),
        "external_primary_failure_counts": dict(
            Counter(row["primary_failure"] for row in aggregate_external_rows)
        ),
    }

    return {
        "summary": aggregate,
        "cases": unique_cases,
        "baseline_prompt_hits": baseline_prompt_hits,
    }


def write_markdown(payload: dict[str, Any], path: Path = MD_OUT) -> None:
    summary = payload["summary"]
    lines = [
        "# PQID-Bench Retrieval-Copy Complementarity Cases",
        "",
        "This report lists held-out generation prompts solved by at least one retrieval-copy baseline and by none of the "
        f"{summary['external_model_attempts'] // summary['unique_prompt_count']} completed named external model rows.",
        "",
        "## Summary",
        "",
        f"- unique prompt targets: `{summary['unique_prompt_count']}`",
        f"- baseline-prompt hits: `{summary['baseline_prompt_hit_count']}`",
        f"- external model attempts on these targets: `{summary['external_model_attempts']}`",
        f"- external execution success: `{summary['external_execution_success']}/{summary['external_model_attempts']}`",
        f"- external QASM3 export success: `{summary['external_qasm3_success']}/{summary['external_model_attempts']}`",
        f"- external gate-type count-map matches: `{summary['external_gate_types_match']}/{summary['external_model_attempts']}`",
        f"- external all-structure matches: `{summary['external_structural_match']}/{summary['external_model_attempts']}`",
        f"- baseline hit counts: `{summary['baseline_hit_counts']}`",
        f"- external primary failures: `{summary['external_primary_failure_counts']}`",
        "",
        "## Prompt-Level Cases",
        "",
        "| prompt | slice | family | target summary | successful copy baselines | copied source files | external failure summary | instruction |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:
        baselines = ", ".join(hit["baseline_label"] for hit in case["successful_copy_baselines"])
        copied = "<br>".join(
            f"{hit['baseline_label']}: `{hit['copied_file']}`"
            for hit in case["successful_copy_baselines"]
        )
        failure = case["external_failure_summary"]
        failure_text = (
            f"exec {failure['execution_success']}/{failure['model_rows']}; "
            f"QASM3 {failure['qasm3_success']}/{failure['model_rows']}; "
            f"gate vocab {failure['gate_types_match']}/{failure['model_rows']}; "
            f"all-structure {failure['all_match']}/{failure['model_rows']}"
        )
        instruction = " ".join(str(case["instruction"]).split())
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{case['prompt_id']}`",
                    f"`{case['label']}`",
                    case["families"],
                    case["target_summary"],
                    baselines,
                    copied,
                    failure_text,
                    instruction,
                ]
            )
            + " |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-csv", type=Path, default=MATRIX_CSV)
    parser.add_argument("--eval-dir", type=Path, action="append", default=None)
    parser.add_argument("--expanded-roster", action="store_true")
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    args = parser.parse_args()

    model_order = list(EXPANDED_MODEL_ORDER if args.expanded_roster else MODEL_ORDER)
    payload = run(
        matrix_csv=args.matrix_csv,
        eval_dirs=args.eval_dir or DEFAULT_EVAL_DIRS,
        model_order=model_order,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(payload, args.md_out)
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")


if __name__ == "__main__":
    main()
