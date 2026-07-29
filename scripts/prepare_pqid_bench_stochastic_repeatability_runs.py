"""Prepare traceable run-1 subsets and frozen run-2/run-3 API requests."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
SOURCE_ROOT = ARTIFACTS_DIR / "external_model_batches_154"
DEFAULT_PANEL_PATH = (
    ARTIFACTS_DIR
    / "stochastic_repeatability_21x36"
    / "panel"
    / "pqid_bench_stochastic_repeatability_prompts_36.jsonl"
)
DEFAULT_OUTPUT_DIR = ARTIFACTS_DIR / "stochastic_repeatability_21x36"
SCHEMA_VERSION = "pqid-bench-stochastic-repeatability-requests-v1"


@dataclass(frozen=True)
class ModelSpec:
    model: str
    slug: str
    request_source: str
    response_source: str


def base_request(slug: str) -> str:
    return f"requests/{slug}_requests.jsonl"


def base_response(slug: str) -> str:
    return f"responses/{slug}_responses.jsonl"


MODEL_SPECS = [
    ModelSpec("gpt-5.6-sol", "openai_gpt-5_6-sol", base_request("openai_gpt-5_6-sol"), base_response("openai_gpt-5_6-sol")),
    ModelSpec("gpt-5.5", "openai_gpt-5_5", base_request("openai_gpt-5_5"), base_response("openai_gpt-5_5")),
    ModelSpec("gpt-5.4-mini", "openai_gpt-5_4-mini", base_request("openai_gpt-5_4-mini"), base_response("openai_gpt-5_4-mini")),
    ModelSpec("claude-fable-5", "anthropic_claude-fable-5", base_request("anthropic_claude-fable-5"), base_response("anthropic_claude-fable-5")),
    ModelSpec("claude-sonnet-4-6", "anthropic_claude-sonnet-4-6", base_request("anthropic_claude-sonnet-4-6"), base_response("anthropic_claude-sonnet-4-6")),
    ModelSpec("claude-opus-4-8", "anthropic_claude-opus-4-8", base_request("anthropic_claude-opus-4-8"), base_response("anthropic_claude-opus-4-8")),
    ModelSpec("gemini-2.5-pro", "google_gemini-2_5-pro", base_request("google_gemini-2_5-pro"), base_response("google_gemini-2_5-pro")),
    ModelSpec("gemini-3.1-pro-preview", "google_gemini-3_1-pro-preview", base_request("google_gemini-3_1-pro-preview"), base_response("google_gemini-3_1-pro-preview")),
    ModelSpec("deepseek-v4-pro", "deepseek_deepseek-v4-pro", base_request("deepseek_deepseek-v4-pro"), base_response("deepseek_deepseek-v4-pro")),
    ModelSpec("deepseek-v4-flash", "deepseek_deepseek-v4-flash", base_request("deepseek_deepseek-v4-flash"), base_response("deepseek_deepseek-v4-flash")),
    ModelSpec("mistral-ai/codestral-2501", "github_models_mistral-ai_codestral-2501", base_request("github_models_mistral-ai_codestral-2501"), base_response("github_models_mistral-ai_codestral-2501")),
    ModelSpec("qwen/qwen3-coder-next", "huggingface_router_qwen_qwen3-coder-next_novita", base_request("huggingface_router_qwen_qwen3-coder-next_novita"), base_response("huggingface_router_qwen_qwen3-coder-next_novita")),
    ModelSpec("meta/llama-4-maverick-17b-128e-instruct-fp8", "github_models_meta_llama-4-maverick-17b-128e-instruct-fp8", base_request("github_models_meta_llama-4-maverick-17b-128e-instruct-fp8"), base_response("github_models_meta_llama-4-maverick-17b-128e-instruct-fp8")),
    ModelSpec("llama-3.3-70b-versatile", "groq_llama-3_3-70b-versatile", base_request("groq_llama-3_3-70b-versatile"), base_response("groq_llama-3_3-70b-versatile")),
    ModelSpec("openai/gpt-oss-120b", "groq_openai_gpt-oss-120b", base_request("groq_openai_gpt-oss-120b"), base_response("groq_openai_gpt-oss-120b")),
    ModelSpec("openai/gpt-oss-20b", "groq_openai_gpt-oss-20b", base_request("groq_openai_gpt-oss-20b"), base_response("groq_openai_gpt-oss-20b")),
    ModelSpec(
        "mistralai/mistral-small-3.2-24b-instruct",
        "openrouter_mistralai_mistral-small-3_2-24b-instruct",
        "mistral_parent_control/requests/openrouter_mistralai_mistral-small-3_2-24b-instruct_requests.jsonl",
        "mistral_parent_control/responses/openrouter_mistralai_mistral-small-3_2-24b-instruct_responses.jsonl",
    ),
    ModelSpec(
        "qiskit/mistral-small-3.2-24b-qiskit",
        "huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai",
        "qiskit_mistral/requests/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_requests.jsonl",
        "qiskit_mistral/responses/huggingface_router_qiskit_mistral-small-3_2-24b-qiskit_featherless-ai_responses.jsonl",
    ),
    ModelSpec("qwen/qwen3-32b", "groq_qwen_qwen3-32b", base_request("groq_qwen_qwen3-32b"), base_response("groq_qwen_qwen3-32b")),
    ModelSpec("meta-llama/llama-4-scout-17b-16e-instruct", "groq_meta-llama_llama-4-scout-17b-16e-instruct", base_request("groq_meta-llama_llama-4-scout-17b-16e-instruct"), base_response("groq_meta-llama_llama-4-scout-17b-16e-instruct")),
    ModelSpec("llama-3.1-8b-instant", "groq_llama-3_1-8b-instant", base_request("groq_llama-3_1-8b-instant"), base_response("groq_llama-3_1-8b-instant")),
]


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(SUBMISSION_DIR.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def response_template_row(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": request["schema_version"],
        "record_type": "external_model_response",
        "run_id": request["run_id"],
        "provider": request["provider"],
        "model": request["model"],
        "api_model_id": request["api_model_id"],
        "model_label": request["model_label"],
        "prompt_id": request["prompt_id"],
        "row_id": request["row_id"],
        "request_sha256": request["request_sha256"],
        "model_input_sha256": request["model_input_sha256"],
        "prompt_record_sha256": request["prompt_record_sha256"],
        "generation_config": request["generation_config"],
        "created_at_utc": "",
        "request_id": "",
        "system_fingerprint": "",
        "model_snapshot": "",
        "finish_reason": "",
        "usage": {},
        "provider_metadata": {},
        "generated_code": "",
        "raw_response": "",
    }


def filter_requests(
    rows: list[dict[str, Any]], prompt_ids: list[str], *, run_number: int
) -> list[dict[str, Any]]:
    by_prompt = {str(row["prompt_id"]): row for row in rows}
    missing = [prompt_id for prompt_id in prompt_ids if prompt_id not in by_prompt]
    if missing:
        raise ValueError(f"Request file is missing panel prompts: {missing}")
    filtered: list[dict[str, Any]] = []
    for prompt_id in prompt_ids:
        row = dict(by_prompt[prompt_id])
        if run_number > 1:
            row["run_id"] = f"pqid_bench_stochastic_repeatability_run_{run_number}"
            row["exported_at_utc"] = datetime.now(UTC).replace(microsecond=0).isoformat()
        filtered.append(row)
    return filtered


def canonical_responses(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    # Recovery logs retain superseded records. The harness uses the last row for
    # each prompt ID, so mirror that deterministic canonicalization here.
    by_prompt: dict[str, dict[str, Any]] = {}
    for row in rows:
        prompt_id = str(row.get("prompt_id") or "")
        if prompt_id:
            by_prompt[prompt_id] = row
    return by_prompt


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# PQID-Bench Stochastic Repeatability Request Manifest",
        "",
        f"- schema: `{manifest['schema_version']}`",
        f"- panel prompts: `{manifest['prompt_count']}`",
        f"- model endpoints: `{manifest['model_count']}`",
        f"- observed baseline cells: `{manifest['prompt_count'] * manifest['model_count']}`",
        f"- newly authorized calls: `{manifest['new_api_call_count']}`",
        "- successful completed responses are never retried or selected by outcome",
        "- run 2 and run 3 preserve each model's original provider payload byte-for-byte apart from trace fields outside the provider request body",
        "",
        "## Models",
        "",
        "| model | provider | family | payload | run-1 response |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in manifest["models"]:
        lines.append(
            f"| `{row['model']}` | `{row['provider']}` | `{row['request_family']}` | "
            f"`{row['source_request_sha256']}` | `{row['source_response_sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Run Directories",
            "",
            "| run | status | request files | response files |",
            "| ---: | --- | ---: | ---: |",
        ]
    )
    for row in manifest["runs"]:
        lines.append(
            f"| {row['run_number']} | {row['status']} | {row['request_file_count']} | {row['response_file_count']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare(panel_path: Path, output_dir: Path) -> None:
    panel_rows = iter_jsonl(panel_path)
    prompt_ids = [str(row["prompt_id"]) for row in panel_rows]
    if len(prompt_ids) != 36 or len(set(prompt_ids)) != 36:
        raise ValueError("Expected a 36-prompt unique panel")

    run_entries: list[dict[str, Any]] = []
    model_entries: list[dict[str, Any]] = []
    run_file_counts = {1: {"request": 0, "response": 0}, 2: {"request": 0, "response": 0}, 3: {"request": 0, "response": 0}}

    for spec in MODEL_SPECS:
        source_request_path = SOURCE_ROOT / spec.request_source
        source_response_path = SOURCE_ROOT / spec.response_source
        source_requests = iter_jsonl(source_request_path)
        source_responses = canonical_responses(iter_jsonl(source_response_path))
        if len({str(row["prompt_id"]) for row in source_requests}) != 154:
            raise ValueError(f"{source_request_path} does not cover 154 unique prompts")
        missing_responses = [prompt_id for prompt_id in prompt_ids if prompt_id not in source_responses]
        if missing_responses:
            raise ValueError(f"{source_response_path} is missing panel prompts: {missing_responses}")

        run1_requests = filter_requests(source_requests, prompt_ids, run_number=1)
        run1_responses = [source_responses[prompt_id] for prompt_id in prompt_ids]
        for request, response in zip(run1_requests, run1_responses, strict=True):
            if request.get("request_sha256") != response.get("request_sha256"):
                raise ValueError(
                    f"Run-1 request hash mismatch for {spec.model} {request['prompt_id']}"
                )

        for run_number in (1, 2, 3):
            run_dir = output_dir / f"run_{run_number}"
            requests = (
                run1_requests
                if run_number == 1
                else filter_requests(source_requests, prompt_ids, run_number=run_number)
            )
            request_path = run_dir / "requests" / f"{spec.slug}_requests.jsonl"
            template_path = run_dir / "responses" / f"{spec.slug}_responses_template.jsonl"
            write_jsonl(request_path, requests)
            write_jsonl(template_path, [response_template_row(row) for row in requests])
            run_file_counts[run_number]["request"] += 1
            if run_number == 1:
                response_path = run_dir / "responses" / f"{spec.slug}_responses.jsonl"
                write_jsonl(response_path, run1_responses)
                run_file_counts[run_number]["response"] += 1

        first_request = run1_requests[0]
        model_entries.append(
            {
                "model": spec.model,
                "slug": spec.slug,
                "provider": first_request["provider"],
                "request_family": first_request["request_family"],
                "generation_config": first_request["generation_config"],
                "source_request_file": display_path(source_request_path),
                "source_request_sha256": sha256_file(source_request_path),
                "source_response_file": display_path(source_response_path),
                "source_response_sha256": sha256_file(source_response_path),
                "provider_request_body_sha256s": {
                    str(row["prompt_id"]): hashlib.sha256(
                        json.dumps(
                            row["request_body"],
                            ensure_ascii=True,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest()
                    for row in run1_requests
                },
            }
        )

    for run_number in (1, 2, 3):
        run_entries.append(
            {
                "run_number": run_number,
                "status": "observed canonical baseline" if run_number == 1 else "prepared for API execution",
                "request_file_count": run_file_counts[run_number]["request"],
                "response_file_count": run_file_counts[run_number]["response"],
                "directory": display_path(output_dir / f"run_{run_number}"),
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "panel_file": display_path(panel_path),
        "panel_sha256": sha256_file(panel_path),
        "prompt_count": len(prompt_ids),
        "model_count": len(MODEL_SPECS),
        "run_count": 3,
        "new_api_call_count": len(prompt_ids) * len(MODEL_SPECS) * 2,
        "selection_policy": "run 1 is canonical; completed run-2/run-3 responses are never retried or replaced by outcome",
        "models": model_entries,
        "runs": run_entries,
    }
    manifest_path = output_dir / "pqid_bench_stochastic_repeatability_request_manifest.json"
    report_path = output_dir / "pqid_bench_stochastic_repeatability_request_manifest.md"
    write_json(manifest_path, manifest)
    write_markdown(report_path, manifest)
    print(f"Wrote {display_path(manifest_path)}")
    print(f"Wrote {display_path(report_path)}")
    print(f"Prepared {len(MODEL_SPECS)} models x 36 prompts for run 2 and run 3")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel-path", type=Path, default=DEFAULT_PANEL_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    prepare(args.panel_path, args.output_dir)


if __name__ == "__main__":
    main()
