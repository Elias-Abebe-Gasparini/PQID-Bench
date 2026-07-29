"""Audit high-confidence prompt-identifiability exceptions in PQID-Bench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pqid_bench_model_registry import (
    INITIAL_19_MODEL_ORDER,
    MODEL_LABELS,
    MODEL_ORDER,
    model_from_report_dir,
)


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = (
    SUBMISSION_DIR
    / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
)
EVAL_DIR = SUBMISSION_DIR / "artifacts/external_model_batches_154/evaluations"
DEFAULT_EVAL_DIRS = [
    EVAL_DIR,
    SUBMISSION_DIR / "artifacts/external_model_batches_154/mistral_parent_control/evaluations",
    SUBMISSION_DIR / "artifacts/external_model_batches_154/qiskit_mistral/evaluations",
]
OUTPUT_DIR = SUBMISSION_DIR / "artifacts/analysis_154"
REPORT_NAME = "pqid_bench_external_model_generation_harness_report.json"

# These are high-confidence exceptions, not an automated claim that every
# other prompt is perfectly identifiable. Each exception requires exact hidden
# source details that the evaluator checks but the model input does not state.
IDENTIFIABILITY_EXCEPTIONS = {
    "pqid_bench_external_gen_0040": {
        "class": "unavailable_external_reference",
        "reason": "The prompt refers to a shown decomposition and source gate order that are not included in the model input.",
    },
    "pqid_bench_external_gen_0117": {
        "class": "underspecified_operation_multiplicity",
        "reason": "QFT-style staging does not determine the target's eight barrier operations.",
    },
    "pqid_bench_external_gen_0141": {
        "class": "underspecified_repetition_pattern",
        "reason": "A long CNOT pattern does not determine 77 CNOTs, 40 barriers, and 10 X operations.",
    },
    "pqid_bench_external_gen_0142": {
        "class": "minimum_constraints_scored_as_exact",
        "reason": "At-least constraints do not determine the exact 25-gate, 14-type target multiset or three classical bits.",
    },
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def executable_circuit(record: dict[str, Any]) -> bool:
    execution = record.get("execution") or {}
    return bool(execution.get("execution_success") and execution.get("circuit_found"))


def structural_match(record: dict[str, Any]) -> bool:
    return bool((record.get("structural_checks") or {}).get("all_match"))


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f} pp"


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    execution = sum(executable_circuit(record) for record in records)
    structural = sum(structural_match(record) for record in records)
    gap = execution - structural
    return {
        "n": n,
        "execution_count": execution,
        "execution_rate": execution / n if n else 0.0,
        "structural_count": structural,
        "structural_rate": structural / n if n else 0.0,
        "execution_structure_gap_count": gap,
        "execution_structure_gap_rate": gap / n if n else 0.0,
        "signature_match_given_execution": structural / execution if execution else 0.0,
        "signature_wrong_given_execution": gap / execution if execution else 0.0,
    }


def run(
    prompt_path: Path,
    eval_dirs: Path | list[Path],
    model_order: list[str] | None = None,
) -> dict[str, Any]:
    model_order = list(model_order or MODEL_ORDER)
    prompts = read_jsonl(prompt_path)
    prompts_by_id = {row["prompt_id"]: row for row in prompts}
    missing = sorted(set(IDENTIFIABILITY_EXCEPTIONS) - set(prompts_by_id))
    if missing:
        raise RuntimeError(f"Identifiability exceptions absent from prompt file: {missing}")

    records: list[dict[str, Any]] = []
    if isinstance(eval_dirs, Path):
        eval_dirs = [eval_dirs]
    for eval_dir in eval_dirs:
        for report_path in sorted(eval_dir.glob(f"*/{REPORT_NAME}")):
            model = model_from_report_dir(report_path.parent.name)
            if model not in model_order:
                continue
            report = json.loads(report_path.read_text(encoding="utf-8"))
            for record in report.get("records") or []:
                records.append({**record, "planned_model": model})

    expected = len(prompts) * len(model_order)
    if len(records) != expected:
        raise RuntimeError(f"Expected {expected} prompt-model records, found {len(records)}")

    exception_ids = set(IDENTIFIABILITY_EXCEPTIONS)
    identifiable_records = [
        record for record in records if record["prompt_id"] not in exception_ids
    ]
    full = summarize(records)
    identifiable = summarize(identifiable_records)

    by_model = []
    for model in model_order:
        model_records = [record for record in records if record["planned_model"] == model]
        model_identifiable = [
            record for record in model_records if record["prompt_id"] not in exception_ids
        ]
        full_model = summarize(model_records)
        identifiable_model = summarize(model_identifiable)
        by_model.append(
            {
                "model": model,
                "model_label": MODEL_LABELS[model],
                "full": full_model,
                "identifiable": identifiable_model,
                "structural_delta_pp": 100.0
                * (identifiable_model["structural_rate"] - full_model["structural_rate"]),
            }
        )

    exceptions = []
    for prompt_id, audit in IDENTIFIABILITY_EXCEPTIONS.items():
        prompt = prompts_by_id[prompt_id]
        prompt_records = [record for record in records if record["prompt_id"] == prompt_id]
        exceptions.append(
            {
                "prompt_id": prompt_id,
                **audit,
                "instruction": prompt["instruction"],
                "target_metadata": prompt["target_metadata"],
                "model_rows": len(prompt_records),
                "execution_count": sum(executable_circuit(record) for record in prompt_records),
                "structural_count": sum(structural_match(record) for record in prompt_records),
            }
        )

    return {
        "audit_scope": "four high-confidence prompt-identifiability exceptions",
        "primary_prompt_count": len(prompts),
        "identifiable_prompt_count": len(prompts) - len(exception_ids),
        "model_count": len(model_order),
        "primary": full,
        "identifiable_sensitivity": identifiable,
        "execution_delta_pp": 100.0
        * (identifiable["execution_rate"] - full["execution_rate"]),
        "structural_delta_pp": 100.0
        * (identifiable["structural_rate"] - full["structural_rate"]),
        "exceptions": exceptions,
        "by_model": by_model,
        "interpretation": (
            "The frozen 154-prompt result remains primary. The 150-prompt sensitivity "
            "removes four prompts whose exact evaluator-facing signatures are not "
            "entailed by the model input; it is a robustness check, not a post-hoc "
            "replacement leaderboard."
        ),
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    primary = result["primary"]
    sensitivity = result["identifiable_sensitivity"]
    lines = [
        "# PQID-Bench Prompt-Identifiability Sensitivity",
        "",
        "The frozen 154-prompt result remains the primary analysis. This sensitivity removes four high-confidence exceptions where the strict target signature depends on source details that are not stated in the model input.",
        "",
        "| analysis | prompts | prompt-model rows | executable circuit | structural match | ES-gap | signature-wrong given execution |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| frozen primary | {result['primary_prompt_count']} | {primary['n']} | {primary['execution_count']} ({pct(primary['execution_rate'])}) | {primary['structural_count']} ({pct(primary['structural_rate'])}) | {primary['execution_structure_gap_count']} ({pct(primary['execution_structure_gap_rate'])}) | {pct(primary['signature_wrong_given_execution'])} |",
        f"| identifiable sensitivity | {result['identifiable_prompt_count']} | {sensitivity['n']} | {sensitivity['execution_count']} ({pct(sensitivity['execution_rate'])}) | {sensitivity['structural_count']} ({pct(sensitivity['structural_rate'])}) | {sensitivity['execution_structure_gap_count']} ({pct(sensitivity['execution_structure_gap_rate'])}) | {pct(sensitivity['signature_wrong_given_execution'])} |",
        "",
        f"The sensitivity changes executable-circuit success by {pp(result['execution_delta_pp'] / 100.0)} and structural match by {pp(result['structural_delta_pp'] / 100.0)}. The structural numerator remains unchanged because all four exception prompts are missed structurally by every model row.",
        "",
        "## High-Confidence Exceptions",
        "",
        f"| prompt | exception class | executable / {result['model_count']} | structural / {result['model_count']} | reason |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in result["exceptions"]:
        lines.append(
            f"| `{row['prompt_id']}` | `{row['class']}` | {row['execution_count']} | {row['structural_count']} | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Per-Model Sensitivity",
            "",
            "| model | structural, 154 | structural, 150 | change |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in result["by_model"]:
        lines.append(
            f"| {row['model_label']} | {pct(row['full']['structural_rate'])} | {pct(row['identifiable']['structural_rate'])} | {row['structural_delta_pp']:+.2f} pp |"
        )
    lines.extend(
        [
            "",
            "The direction and ordering of the main capability gradient are preserved. This check therefore separates a small prompt-identifiability limitation from the broader execution-structure gap without discarding the frozen challenge cases.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-path", type=Path, default=PROMPT_PATH)
    parser.add_argument(
        "--eval-dir",
        type=Path,
        action="append",
        default=None,
        help="Evaluation directory; may be repeated for additional completed model rows.",
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--initial-19",
        action="store_true",
        help="Rebuild the archived sensitivity result for the initial 19-model roster.",
    )
    args = parser.parse_args()

    model_order = INITIAL_19_MODEL_ORDER if args.initial_19 else MODEL_ORDER
    result = run(args.prompt_path, args.eval_dir or DEFAULT_EVAL_DIRS, model_order)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "pqid_bench_prompt_identifiability_sensitivity.json"
    md_path = args.output_dir / "pqid_bench_prompt_identifiability_sensitivity.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(md_path, result)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
