"""Summarize available PQID-Bench external model evaluation reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
EVALUATIONS_DIR = ARTIFACTS_DIR / "external_model_batches" / "evaluations"
RESPONSES_DIR = ARTIFACTS_DIR / "external_model_batches" / "responses"
REPORT_STEM = "pqid_bench_external_model_results_summary"

MODEL_ROWS = [
    {
        "slug": "openai_gpt-5_6-sol",
        "provider": "OpenAI",
        "planned_model": "gpt-5.6-sol",
        "role": "newer OpenAI frontier coding/reasoning comparison",
    },
    {
        "slug": "openai_gpt-5_5",
        "provider": "OpenAI",
        "planned_model": "gpt-5.5",
        "role": "frontier coding/reasoning",
    },
    {
        "slug": "openai_gpt-5_4-mini",
        "provider": "OpenAI",
        "planned_model": "gpt-5.4-mini",
        "role": "cost/latency frontier comparison",
    },
    {
        "slug": "anthropic_claude-fable-5",
        "provider": "Anthropic",
        "planned_model": "claude-fable-5",
        "role": "newer Anthropic frontier coding/reasoning comparison",
    },
    {
        "slug": "anthropic_claude-sonnet-4-6",
        "provider": "Anthropic",
        "planned_model": "claude-sonnet-4-6",
        "role": "independent frontier coding family",
    },
    {
        "slug": "anthropic_claude-opus-4-8",
        "provider": "Anthropic",
        "planned_model": "claude-opus-4-8",
        "role": "higher-capability Anthropic frontier comparison",
    },
    {
        "slug": "google_gemini-2_5-pro",
        "provider": "Google",
        "planned_model": "gemini-2.5-pro",
        "role": "independent frontier coding family",
    },
    {
        "slug": "google_gemini-3_1-pro-preview",
        "provider": "Google",
        "planned_model": "gemini-3.1-pro-preview",
        "role": "newer Google frontier coding/reasoning comparison",
    },
    {
        "slug": "deepseek_deepseek-v4-pro",
        "provider": "DeepSeek",
        "planned_model": "deepseek-v4-pro",
        "role": "official DeepSeek frontier coding/reasoning row",
    },
    {
        "slug": "deepseek_deepseek-v4-flash",
        "provider": "DeepSeek",
        "planned_model": "deepseek-v4-flash",
        "role": "official DeepSeek fast/cost frontier comparison",
    },
    {
        "slug": "groq_llama-3_3-70b-versatile",
        "provider": "Groq",
        "planned_model": "llama-3.3-70b-versatile",
        "role": "free/low-cost open-weight Llama API bridge",
    },
    {
        "slug": "groq_qwen_qwen3-32b",
        "provider": "Groq",
        "planned_model": "qwen/qwen3-32b",
        "role": "free/low-cost open-weight reasoning/code API bridge",
    },
    {
        "slug": "groq_openai_gpt-oss-120b",
        "provider": "Groq",
        "planned_model": "openai/gpt-oss-120b",
        "role": "free/low-cost open-weight OpenAI-family API bridge",
    },
    {
        "slug": "groq_openai_gpt-oss-20b",
        "provider": "Groq",
        "planned_model": "openai/gpt-oss-20b",
        "role": "size-control against GPT-OSS 120B",
    },
    {
        "slug": "groq_llama-3_1-8b-instant",
        "provider": "Groq",
        "planned_model": "llama-3.1-8b-instant",
        "role": "fast small open-weight API bridge",
    },
    {
        "slug": "groq_meta-llama_llama-4-scout-17b-16e-instruct",
        "provider": "Groq",
        "planned_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "role": "optional newer Llama-family contrast",
    },
    {
        "slug": "github_models_mistral-ai_codestral-2501",
        "provider": "GitHub Models",
        "planned_model": "mistral-ai/codestral-2501",
        "role": "code-specialized Mistral-family baseline",
    },
    {
        "slug": "huggingface_router_qwen_qwen3-coder-next_novita",
        "provider": "Hugging Face / Novita",
        "planned_model": "qwen/qwen3-coder-next",
        "role": "current open-weight code-specialized comparison",
    },
    {
        "slug": "github_models_meta_llama-4-maverick-17b-128e-instruct-fp8",
        "provider": "GitHub Models",
        "planned_model": "meta/llama-4-maverick-17b-128e-instruct-fp8",
        "role": "Meta mixture-of-experts flagship comparison",
    },
    {
        "slug": "github_models_deepseek_deepseek-v3-0324",
        "provider": "GitHub Models",
        "planned_model": "deepseek/deepseek-v3-0324",
        "role": "DeepSeek-family coding/reasoning baseline",
    },
    {
        "slug": "apifreellm_apifreellm",
        "provider": "ApiFreeLLM",
        "planned_model": "apifreellm",
        "role": "exploratory free-router baseline; not a named-model row",
    },
]

LOWER_BOUND = {
    "name": "word_tfidf_train_instruction_copy",
    "execution_success": 0.90,
    "structural_all_match": 17 / 70,
    "gate_types_match": 18 / 70,
    "gate_count_match": 26 / 70,
    "num_qubits_match": 40 / 70,
    "qasm3_export_success": 0.90,
}


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def response_snapshot(slug: str, responses_dir: Path) -> tuple[str, dict[str, int]]:
    response_path = responses_dir / f"{slug}_responses.jsonl"
    if not response_path.exists():
        return "", {}
    rows = load_jsonl(response_path)
    latest_by_prompt = {}
    for row in rows:
        prompt_id = str(row.get("prompt_id") or "")
        if prompt_id:
            latest_by_prompt[prompt_id] = row
    latest_rows = list(latest_by_prompt.values()) or rows
    models = sorted({str(row.get("model") or "") for row in latest_rows if row.get("model")})
    finish_counts: dict[str, int] = {}
    for row in latest_rows:
        key = str(row.get("finish_reason") or "<missing>")
        finish_counts[key] = finish_counts.get(key, 0) + 1
    return ", ".join(models), finish_counts


def summarize_model(
    row: dict[str, str],
    evaluations_dir: Path,
    responses_dir: Path,
    expected_rows: int,
) -> dict[str, Any] | None:
    report_path = evaluations_dir / row["slug"] / "pqid_bench_external_model_generation_harness_report.json"
    if not report_path.exists():
        return None
    payload = load_json(report_path)
    summary = payload["summary"]
    if summary["rows"] != expected_rows:
        return None
    rates = summary["rates"]
    resolved_model, finish_counts = response_snapshot(row["slug"], responses_dir)
    return {
        **row,
        "resolved_model": resolved_model,
        "rows": summary["rows"],
        "execution_success": summary["execution_success"],
        "execution_success_rate": rates["execution_success"],
        "structural_all_match": summary["structural_all_match"],
        "structural_all_match_rate": rates["structural_all_match"],
        "gate_types_match": summary["gate_types_match"],
        "gate_types_match_rate": rates["gate_types_match"],
        "gate_count_match": summary["gate_count_match"],
        "gate_count_match_rate": rates["gate_count_match"],
        "num_qubits_match": summary["num_qubits_match"],
        "num_qubits_match_rate": rates["num_qubits_match"],
        "num_clbits_match": summary["num_clbits_match"],
        "num_clbits_match_rate": rates["num_clbits_match"],
        "qasm3_export_success": summary["qasm3_export_success"],
        "qasm3_export_success_rate": rates["qasm3_export_success"],
        "execution_errors": summary["execution_errors"],
        "structural_mismatch_checks": summary["structural_mismatch_checks"],
        "finish_counts": finish_counts,
        "report_path": (
            report_path.relative_to(SUBMISSION_DIR).as_posix()
            if report_path.is_relative_to(SUBMISSION_DIR)
            else report_path.as_posix()
        ),
    }


def load_lower_bound(path: Path | None) -> dict[str, Any]:
    if path is None:
        return dict(LOWER_BOUND)
    payload = load_json(path)
    for result in payload.get("results") or []:
        if result.get("name") != "word_tfidf_train_instruction_copy":
            continue
        rates = result["summary"]["rates"]
        return {
            "name": result["name"],
            "execution_success": rates["execution_success"],
            "structural_all_match": rates["structural_all_match"],
            "gate_types_match": rates["gate_types_match"],
            "gate_count_match": rates["gate_count_match"],
            "num_qubits_match": rates["num_qubits_match"],
            "qasm3_export_success": rates["qasm3_export_success"],
        }
    raise ValueError(f"TF-IDF instruction-copy result not found in {path}")


def write_outputs(
    rows: list[dict[str, Any]],
    output_dir: Path,
    expected_rows: int,
    lower_bound: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{REPORT_STEM}.md"
    json_path = output_dir / f"{REPORT_STEM}.json"
    lines = [
        "# PQID-Bench External Model Results Summary",
        "",
        f"- prompt split: `{expected_rows}` held-out source-file-group test prompts",
        "- response source: traceable provider batch/API logs",
        "- evaluator: strict standalone execution with safe `math` / `numpy` / `qiskit` imports",
        f"- inclusion rule: completed `{expected_rows} / {expected_rows}` response rows only; partial rows are tracked separately",
        "",
        "## Retrieval-Copy Lower Bound",
        "",
        "| baseline | execution | structural | gate types | gate count | qubits | QASM3 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {lower_bound['name']} | {pct(lower_bound['execution_success'])} | "
            f"{pct(lower_bound['structural_all_match'])} | "
            f"{pct(lower_bound['gate_types_match'])} | "
            f"{pct(lower_bound['gate_count_match'])} | "
            f"{pct(lower_bound['num_qubits_match'])} | "
            f"{pct(lower_bound['qasm3_export_success'])} |"
        ),
        "",
        "## External Model Results",
        "",
        "| provider | requested model | resolved model | rows | execution | structural | gate types | gate count | qubits | clbits | QASM3 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['provider']} | `{row['planned_model']}` | `{row['resolved_model']}` | "
            f"{row['rows']} | {pct(row['execution_success_rate'])} | "
            f"{pct(row['structural_all_match_rate'])} | "
            f"{pct(row['gate_types_match_rate'])} | "
            f"{pct(row['gate_count_match_rate'])} | "
            f"{pct(row['num_qubits_match_rate'])} | "
            f"{pct(row['num_clbits_match_rate'])} | "
            f"{pct(row['qasm3_export_success_rate'])} |"
        )
    lines.extend(["", "## Failure Notes", ""])
    for row in rows:
        lines.append(
            f"- `{row['planned_model']}` execution errors: "
            f"`{json.dumps(row['execution_errors'], sort_keys=True)}`; "
            f"structural mismatches: `{json.dumps(row['structural_mismatch_checks'], sort_keys=True)}`; "
            f"finish reasons: `{json.dumps(row['finish_counts'], sort_keys=True)}`."
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "expected_rows": expected_rows,
                "lower_bound": lower_bound,
                "rows": rows,
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {md_path.as_posix()}")
    print(f"Wrote {json_path.as_posix()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluations-dir", type=Path, default=EVALUATIONS_DIR)
    parser.add_argument("--responses-dir", type=Path, default=RESPONSES_DIR)
    parser.add_argument("--output-dir", type=Path, default=ARTIFACTS_DIR)
    parser.add_argument("--expected-rows", type=int, default=70)
    parser.add_argument("--lower-bound-report", type=Path, default=None)
    args = parser.parse_args()
    rows = [
        summary
        for row in MODEL_ROWS
        if (
            summary := summarize_model(
                row,
                evaluations_dir=args.evaluations_dir,
                responses_dir=args.responses_dir,
                expected_rows=args.expected_rows,
            )
        )
    ]
    if not rows:
        raise SystemExit("No external model evaluation reports found.")
    write_outputs(
        rows,
        output_dir=args.output_dir,
        expected_rows=args.expected_rows,
        lower_bound=load_lower_bound(args.lower_bound_report),
    )


if __name__ == "__main__":
    main()
