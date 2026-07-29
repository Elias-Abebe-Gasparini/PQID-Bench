"""Prepare and evaluate external-model generation runs for PQID-Bench.

This harness exports the held-out generation prompts from the same source-file
group split used by `run_pqid_bench_generation_copy_baseline.py`. If a response
JSONL is supplied, it evaluates generated code with the same executable and
structural checks used by the retrieval-copy lower bound. The headline path
uses strict standalone execution; target-metadata context is reported only as a
recovery diagnostic.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import run_pqid_bench_generation_copy_baseline as copy_baseline
import run_pqid_bench_executable_validity_check as validity
import run_pqid_bench_retrieval_baseline as retrieval


DEFAULT_INPUT = retrieval.DEFAULT_INPUT
DEFAULT_OUTPUT_DIR = retrieval.DEFAULT_OUTPUT_DIR
DEFAULT_PROMPT_PATH = DEFAULT_OUTPUT_DIR / "pqid_bench_external_generation_prompts.jsonl"
DEFAULT_TEMPLATE_PATH = DEFAULT_OUTPUT_DIR / "pqid_bench_external_generation_response_template.jsonl"
DEFAULT_RESPONSE_PATH = DEFAULT_OUTPUT_DIR / "pqid_bench_external_generation_responses.jsonl"
REPORT_STEM = "pqid_bench_external_model_generation_harness_report"


SYSTEM_PROMPT = (
    "You are generating Qiskit Python code for a benchmark. Return only Python "
    "code, with no Markdown fences and no prose. The evaluation environment has "
    "QuantumCircuit, QuantumRegister, ClassicalRegister, Parameter, "
    "ParameterVector, numpy as np, and math/pi available. Define at least one "
    "QuantumCircuit object that implements the requested circuit."
)


def iter_jsonl(path: Path) -> list[dict]:
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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def prompt_text(instruction: str) -> str:
    return "\n".join(
        [
            SYSTEM_PROMPT,
            "",
            "Instruction:",
            instruction.strip(),
            "",
            "Return only executable Python code.",
        ]
    )


def prompt_record(row: dict, index: int) -> dict:
    prompt_id = f"pqid_bench_external_gen_{index:04d}"
    prompt = prompt_text(row["query"])
    return {
        "prompt_id": prompt_id,
        "row_id": row["row_id"],
        "label": row["label"],
        "split": "test",
        "instruction": row["query"],
        "prompt": prompt,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": row["query"]},
        ],
        "target_metadata": {
            "num_qubits": row["metadata"].get("num_qubits"),
            "num_clbits": row["metadata"].get("num_clbits"),
            "gate_count": row["metadata"].get("gate_count"),
            "gate_types": row["metadata"].get("gate_types"),
        },
    }


def response_template(prompt: dict) -> dict:
    return {
        "prompt_id": prompt["prompt_id"],
        "row_id": prompt["row_id"],
        "provider": "",
        "model": "",
        "generated_code": "",
        "raw_response": "",
        "finish_reason": "",
    }


def strip_code_fences(text: object) -> str:
    rendered = str(text or "").strip()
    fenced = re.search(r"```(?:python|py)?\s*(.*?)```", rendered, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return rendered


def generated_code(response: dict) -> str:
    # `raw_response` is provenance, not a code channel. Falling back to it
    # turns empty refusals or thinking-only responses into provider JSON (often
    # the literal token `null`) and misclassifies them as execution NameErrors.
    for field in ["generated_code", "code", "completion", "text"]:
        value = response.get(field)
        if value:
            return strip_code_fences(value)
    return ""


def load_response_map(path: Path) -> dict[str, dict]:
    responses = iter_jsonl(path)
    mapped = {}
    for response in responses:
        key = response.get("prompt_id") or response.get("row_id")
        if not key:
            raise ValueError(f"Response missing prompt_id/row_id: {response}")
        mapped[str(key)] = response
    return mapped


def empty_generation_result() -> dict:
    """Represent an empty provider completion as a failed generation attempt."""
    return {
        "execution_success": False,
        "circuit_found": False,
        "execution_error_type": "EmptyGeneration",
        "execution_error_message": "The provider response contained no generated code.",
        "qasm3_export": {
            "success": False,
            "error_type": "EmptyGeneration",
            "length": 0,
        },
        "simulation": {
            "eligible": False,
            "success": False,
            "skip_reason": "empty_generation",
            "norm": None,
        },
    }


def evaluate_responses(
    test_rows: list[dict],
    prompt_rows: list[dict],
    response_path: Path,
) -> tuple[list[dict], list[str]]:
    response_map = load_response_map(response_path)
    qiskit_env = copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is unavailable: {qiskit_env.get('error')}")

    rows_by_id = {row["row_id"]: row for row in test_rows}
    missing = []
    records = []
    for prompt in prompt_rows:
        response = response_map.get(prompt["prompt_id"]) or response_map.get(prompt["row_id"])
        if response is None:
            missing.append(prompt["prompt_id"])
            continue
        target_row = rows_by_id[prompt["row_id"]]
        code = generated_code(response)
        is_empty = not bool(code.strip())
        if is_empty:
            strict_execution = empty_generation_result()
            target_context_execution = empty_generation_result()
        else:
            strict_execution = copy_baseline.execute_generated_code(
                target_row=target_row,
                generated_code=code,
                context_metadata={},
                qiskit_env=qiskit_env,
            )
            target_context_execution = copy_baseline.execute_generated_code(
                target_row=target_row,
                generated_code=code,
                context_metadata=target_row["metadata"],
                qiskit_env=qiskit_env,
            )
        checks = strict_execution.get("structural", {}).get("checks", {})
        target_context_checks = target_context_execution.get("structural", {}).get("checks", {})
        records.append(
            {
                "prompt_id": prompt["prompt_id"],
                "row_id": target_row["row_id"],
                "label": target_row["label"],
                "provider": response.get("provider"),
                "model": response.get("model"),
                "finish_reason": response.get("finish_reason"),
                "generated_code_length": len(code),
                "empty_generation": is_empty,
                "execution_mode": "strict_standalone",
                "execution": strict_execution,
                "structural_checks": checks,
                "target_context_recovery_execution": target_context_execution,
                "target_context_recovery_structural_checks": target_context_checks,
                "target_metadata": prompt["target_metadata"],
            }
        )
    return records, missing


def summarize_external_records(records: list[dict]) -> dict:
    total = len(records)

    def rate(count: int) -> float:
        return count / total if total else 0.0

    summary = {
        "rows": total,
        "empty_generation": sum(1 for record in records if record["empty_generation"]),
        "python_execution_success": sum(
            1 for record in records if record["execution"].get("execution_success")
        ),
        "execution_success": sum(
            1
            for record in records
            if record["execution"].get("execution_success")
            and record["execution"].get("circuit_found")
        ),
        "circuit_found": sum(1 for record in records if record["execution"].get("circuit_found")),
        "structural_all_match": sum(
            1 for record in records if record.get("structural_checks", {}).get("all_match")
        ),
        "num_qubits_match": sum(
            1 for record in records if record.get("structural_checks", {}).get("num_qubits_match")
        ),
        "num_clbits_match": sum(
            1 for record in records if record.get("structural_checks", {}).get("num_clbits_match")
        ),
        "gate_count_match": sum(
            1 for record in records if record.get("structural_checks", {}).get("gate_count_match")
        ),
        "gate_types_match": sum(
            1 for record in records if record.get("structural_checks", {}).get("gate_types_match")
        ),
        "qasm3_export_success": sum(
            1 for record in records if record["execution"].get("qasm3_export", {}).get("success")
        ),
        "target_context_python_execution_success": sum(
            1
            for record in records
            if record["target_context_recovery_execution"].get("execution_success")
        ),
        "target_context_execution_success": sum(
            1
            for record in records
            if record["target_context_recovery_execution"].get("execution_success")
            and record["target_context_recovery_execution"].get("circuit_found")
        ),
        "target_context_structural_all_match": sum(
            1
            for record in records
            if record.get("target_context_recovery_structural_checks", {}).get("all_match")
        ),
    }
    summary["rates"] = {
        key: rate(value)
        for key, value in summary.items()
        if key not in {"rows", "rates"} and isinstance(value, int)
    }
    summary["execution_errors"] = dict(
        Counter(
            (
                record["execution"].get("execution_error_type") or "ExecutionFailure"
                if not record["execution"].get("execution_success")
                else "NoCircuitReturned"
            )
            for record in records
            if not (
                record["execution"].get("execution_success")
                and record["execution"].get("circuit_found")
            )
        )
    )
    summary["structural_mismatch_checks"] = dict(
        Counter(
            check
            for record in records
            if record["execution"].get("circuit_found")
            and not record.get("structural_checks", {}).get("all_match")
            for check, passed in record.get("structural_checks", {}).items()
            if check != "all_match" and not passed
        )
    )
    return summary


def split_summary(splits: dict[str, list[dict]]) -> dict:
    summary = {}
    for split, rows in splits.items():
        labels = Counter(row["label"] for row in rows)
        summary[split] = {
            "rows": len(rows),
            "groups": len({row["_group_id"] for row in rows}),
            "labels": {label: labels[label] for label in retrieval.LABEL_ORDER},
        }
    return summary


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_report(
    output_dir: Path,
    input_path: Path,
    prompt_path: Path,
    template_path: Path,
    response_path: Path,
    rows: list[dict],
    splits: dict[str, list[dict]],
    prompt_rows: list[dict],
    evaluated_records: list[dict] | None,
    missing_responses: list[str],
    split_manifest_path: Path | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{REPORT_STEM}.md"
    json_path = output_dir / f"{REPORT_STEM}.json"
    label_counts = Counter(row["label"] for row in rows)
    split_stats = split_summary(splits)
    summary = summarize_external_records(evaluated_records or []) if evaluated_records is not None else None

    split_policy = (
        f"frozen split manifest `{retrieval.display_path(split_manifest_path)}`"
        if split_manifest_path is not None
        else "same deterministic source-file-group split used by the retrieval-copy generation baseline"
    )
    lines = [
        "# PQID-Bench External Model Generation Harness Report",
        "",
        f"- evaluator version: `{validity.EVALUATOR_VERSION}`",
        f"- structural predicate version: `{validity.STRUCTURAL_PREDICATE_VERSION}`",
        f"- input file: `{retrieval.display_path(input_path)}`",
        f"- clean source-code rows: `{len(rows):,}`",
        f"- split policy: {split_policy}",
        f"- exported prompts: `{retrieval.display_path(prompt_path)}`",
        f"- response template: `{retrieval.display_path(template_path)}`",
        f"- expected response path: `{retrieval.display_path(response_path)}`",
        "",
        "## Clean Pool",
        "",
        "| slice | rows |",
        "| --- | ---: |",
    ]
    for label in retrieval.LABEL_ORDER:
        lines.append(f"| `{label}` | {label_counts[label]:,} |")

    lines.extend(
        [
            "",
            "## Held-Out Prompt Split",
            "",
            "| split | rows | groups | strict_n8 | extended_n8 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for split in ["train", "validation", "test"]:
        stats = split_stats[split]
        labels = stats["labels"]
        lines.append(
            f"| `{split}` | {stats['rows']:,} | {stats['groups']:,} | "
            f"{labels['strict_n8']:,} | {labels['extended_n8']:,} |"
        )

    lines.extend(
        [
            "",
            "## Response Schema",
            "",
            "Fill `generated_code` for each prompt in the response template. Optional fields `provider`, `model`, `raw_response`, and `finish_reason` are preserved in the evaluation JSON.",
            "",
            "Use only the `prompt` or `messages` fields as model input. `target_metadata` is included for transparent scoring and should not be passed to the model.",
            "",
            "Required matching key: `prompt_id` or `row_id`.",
        ]
    )

    lines.extend(
        [
            "",
            "## Evaluation Status",
            "",
            f"- evaluator version: `{validity.EVALUATOR_VERSION}`",
            f"- structural predicate: `{validity.STRUCTURAL_PREDICATE_VERSION}`",
        ]
    )
    if summary is None:
        lines.extend(
            [
                "No response JSONL was supplied. The external generation stage is ready for a live model run, and this report records the exact held-out prompts and import schema.",
            ]
        )
    else:
        rates = summary["rates"]
        lines.extend(
            [
                f"- evaluated responses: `{summary['rows']:,}`",
                f"- missing prompts: `{len(missing_responses):,}`",
                "",
                "| metric | count | rate |",
                "| --- | ---: | ---: |",
                f"| empty generation | {summary['empty_generation']:,} | {pct(rates['empty_generation'])} |",
                f"| Python execution success | {summary['python_execution_success']:,} | {pct(rates['python_execution_success'])} |",
                f"| executable circuit returned, E | {summary['execution_success']:,} | {pct(rates['execution_success'])} |",
                f"| reference-signature match | {summary['structural_all_match']:,} | {pct(rates['structural_all_match'])} |",
                f"| gate-type count-map match | {summary['gate_types_match']:,} | {pct(rates['gate_types_match'])} |",
                f"| gate count match | {summary['gate_count_match']:,} | {pct(rates['gate_count_match'])} |",
                f"| qubit count match | {summary['num_qubits_match']:,} | {pct(rates['num_qubits_match'])} |",
                f"| QASM3 export success | {summary['qasm3_export_success']:,} | {pct(rates['qasm3_export_success'])} |",
                f"| target-context recovery execution success | {summary['target_context_execution_success']:,} | {pct(rates['target_context_execution_success'])} |",
                f"| target-context recovery reference-signature match | {summary['target_context_structural_all_match']:,} | {pct(rates['target_context_structural_all_match'])} |",
            ]
        )

    payload = {
        "evaluator_version": validity.EVALUATOR_VERSION,
        "structural_predicate_version": validity.STRUCTURAL_PREDICATE_VERSION,
        "input_file": retrieval.display_path(input_path),
        "row_count": len(rows),
        "label_counts": dict(label_counts),
        "split_policy": split_policy,
        "split_manifest": retrieval.display_path(split_manifest_path) if split_manifest_path else None,
        "split_summary": split_stats,
        "prompt_count": len(prompt_rows),
        "prompt_path": retrieval.display_path(prompt_path),
        "response_template_path": retrieval.display_path(template_path),
        "expected_response_path": retrieval.display_path(response_path),
        "response_supplied": evaluated_records is not None,
        "missing_response_count": len(missing_responses),
        "missing_responses": missing_responses[:20],
        "summary": summary,
        "records": evaluated_records or [],
    }

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {retrieval.display_path(prompt_path)}")
    print(f"Wrote {retrieval.display_path(template_path)}")
    print(f"Wrote {retrieval.display_path(report_path)}")
    print(f"Wrote {retrieval.display_path(json_path)}")


def run(
    input_path: Path,
    output_dir: Path,
    prompt_path: Path,
    template_path: Path,
    response_path: Path,
    split_manifest_path: Path | None = None,
    use_existing_prompts: bool = False,
) -> None:
    rows = copy_baseline.clean_rows(input_path)
    if len(rows) != 734:
        raise ValueError(f"Expected 734 clean source-code rows, found {len(rows)}")
    splits = copy_baseline.split_rows(rows, split_manifest_path=split_manifest_path)
    frozen_test_rows = splits["test"]
    if use_existing_prompts:
        if not prompt_path.exists():
            raise FileNotFoundError(f"Existing prompt file not found: {prompt_path}")
        prompt_rows = iter_jsonl(prompt_path)
        if not prompt_rows:
            raise ValueError(f"Existing prompt file has no rows: {prompt_path}")
        frozen_by_row_id = {str(row["row_id"]): row for row in frozen_test_rows}
        prompt_ids = [str(prompt.get("prompt_id") or "") for prompt in prompt_rows]
        if any(not prompt_id for prompt_id in prompt_ids) or len(set(prompt_ids)) != len(prompt_ids):
            raise ValueError("Existing prompt file must contain unique nonempty prompt IDs")
        missing_row_ids = [
            str(prompt.get("row_id") or "")
            for prompt in prompt_rows
            if str(prompt.get("row_id") or "") not in frozen_by_row_id
        ]
        if missing_row_ids:
            raise ValueError(
                "Existing prompts are not members of the frozen test split: "
                f"{missing_row_ids[:10]}"
            )
        test_rows = [frozen_by_row_id[str(prompt["row_id"])] for prompt in prompt_rows]
        if not template_path.exists():
            raise FileNotFoundError(f"Existing response template not found: {template_path}")
    else:
        test_rows = frozen_test_rows
        prompt_rows = [prompt_record(row, index) for index, row in enumerate(test_rows, start=1)]
        template_rows = [response_template(prompt) for prompt in prompt_rows]
        write_jsonl(prompt_path, prompt_rows)
        write_jsonl(template_path, template_rows)

    evaluated_records: list[dict] | None = None
    missing_responses: list[str] = []
    if response_path.exists():
        evaluated_records, missing_responses = evaluate_responses(
            test_rows=test_rows,
            prompt_rows=prompt_rows,
            response_path=response_path,
        )

    write_report(
        output_dir=output_dir,
        input_path=input_path,
        prompt_path=prompt_path,
        template_path=template_path,
        response_path=response_path,
        rows=rows,
        splits=splits,
        prompt_rows=prompt_rows,
        evaluated_records=evaluated_records,
        missing_responses=missing_responses,
        split_manifest_path=split_manifest_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--prompt-path", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--template-path", type=Path, default=DEFAULT_TEMPLATE_PATH)
    parser.add_argument("--response-path", type=Path, default=DEFAULT_RESPONSE_PATH)
    parser.add_argument("--split-manifest", type=Path, default=None)
    parser.add_argument(
        "--use-existing-prompts",
        action="store_true",
        help=(
            "Evaluate the supplied prompt subset without regenerating the frozen split "
            "or overwriting its response template."
        ),
    )
    args = parser.parse_args()

    run(
        input_path=args.input,
        output_dir=args.output_dir,
        prompt_path=args.prompt_path,
        template_path=args.template_path,
        response_path=args.response_path,
        split_manifest_path=args.split_manifest,
        use_existing_prompts=args.use_existing_prompts,
    )


if __name__ == "__main__":
    main()
