"""Container boundary for executing archived generated programs."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metrics import summarize_evaluation_records
from .reporting import render_summary
from .version import version_record

IMAGE = "pqid-bench-evaluator:1.0.0"
EVALUATOR_OUTPUTS = (
    "pqid_bench_external_model_generation_harness_report.json",
    "pqid_bench_external_model_generation_harness_report.md",
)
CANONICAL_EVALUATIONS = "pqid_bench_canonical_evaluations.jsonl"
SUMMARY_OUTPUTS = {
    "json": "pqid_bench_candidate_summary.json",
    "text": "pqid_bench_candidate_summary.txt",
    "markdown": "pqid_bench_candidate_summary.md",
    "csv": "pqid_bench_candidate_summary.csv",
}
EXPECTED_OUTPUTS = (
    *EVALUATOR_OUTPUTS,
    CANONICAL_EVALUATIONS,
    *SUMMARY_OUTPUTS.values(),
)


@dataclass(frozen=True, slots=True)
class ReplayPlan:
    build_command: tuple[str, ...] | None
    run_command: tuple[str, ...]
    release_dir: Path
    response_file: Path
    output_dir: Path


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def canonicalize_harness_report(report_path: Path) -> list[dict[str, Any]]:
    """Flatten one evaluator report into the stable evaluation-cell contract."""

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid evaluator report JSON: {report_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Evaluator report must be a JSON object")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Evaluator report contains no evaluation records")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, record_value in enumerate(records, start=1):
        if not isinstance(record_value, dict):
            raise ValueError(f"Evaluator record {index} is not an object")
        record = record_value
        model = str(record.get("model") or "")
        prompt_id = str(record.get("prompt_id") or "")
        if not model or not prompt_id:
            raise ValueError(f"Evaluator record {index} lacks model or prompt_id")
        key = (model, prompt_id)
        if key in seen:
            raise ValueError(
                f"Duplicate model-prompt key in evaluator report: {key!r}"
            )
        seen.add(key)

        execution = _mapping(record.get("execution"))
        structural = _mapping(record.get("structural_checks"))
        qasm3 = _mapping(execution.get("qasm3_export"))
        executable = bool(
            execution.get("execution_success") and execution.get("circuit_found")
        )
        assembly = bool(qasm3.get("success"))
        signature = bool(structural.get("all_match"))
        if assembly and not executable:
            raise ValueError(
                f"Evaluator record {index} violates assembly => execution"
            )
        if signature and not executable:
            raise ValueError(
                f"Evaluator record {index} violates signature => execution"
            )

        rows.append(
            {
                **version_record(run_type="supplied_evaluation"),
                "record_type": "canonical_evaluation",
                "model": model,
                "provider": str(record.get("provider") or ""),
                "prompt_id": prompt_id,
                "row_id": str(record.get("row_id") or ""),
                "report_executable": executable,
                "report_assembly_admissible": assembly,
                "report_signature_match": signature,
                "gate_types_match": bool(structural.get("gate_types_match")),
                "gate_count_match": bool(structural.get("gate_count_match")),
                "num_qubits_match": bool(structural.get("num_qubits_match")),
                "num_clbits_match": bool(structural.get("num_clbits_match")),
                "selected_circuit_name": str(
                    execution.get("selected_circuit_name") or ""
                ),
                "execution_error_type": execution.get("execution_error_type"),
            }
        )
    return rows


def write_replay_derivatives(output_dir: Path) -> None:
    """Write canonical cells and R-friendly summaries from evaluator output."""

    report_path = output_dir / EVALUATOR_OUTPUTS[0]
    rows = canonicalize_harness_report(report_path)
    evaluations = output_dir / CANONICAL_EVALUATIONS
    evaluations.write_text(
        "".join(
            json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    summary = summarize_evaluation_records(rows)
    for output_format, filename in SUMMARY_OUTPUTS.items():
        rendered = render_summary(
            summary,
            output_format=output_format,
            run_type="supplied_evaluation",
        )
        (output_dir / filename).write_text(rendered + "\n", encoding="utf-8")


def docker_available() -> bool:
    executable = shutil.which("docker")
    if executable is None:
        return False
    try:
        result = subprocess.run(
            [executable, "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def replay_plan(
    *,
    release_dir: Path,
    response_file: Path,
    output_dir: Path,
    build_image: bool,
) -> ReplayPlan:
    release_dir = release_dir.resolve()
    response_file = response_file.resolve()
    output_dir = output_dir.resolve()
    dockerfile = release_dir / "docker" / "evaluator" / "Dockerfile"
    if not dockerfile.is_file():
        raise FileNotFoundError(dockerfile)
    if not response_file.is_file():
        raise FileNotFoundError(response_file)
    output_dir.mkdir(parents=True, exist_ok=True)

    build = (
        (
            "docker",
            "build",
            "--tag",
            IMAGE,
            "--file",
            str(dockerfile),
            str(release_dir),
        )
        if build_image
        else None
    )
    try:
        release_response = response_file.relative_to(release_dir)
    except ValueError:
        response_mount = (
            "--volume",
            f"{response_file.parent}:/responses:ro",
        )
        container_response = f"/responses/{response_file.name}"
    else:
        response_mount = ()
        container_response = f"/release/{release_response.as_posix()}"

    run = (
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "128",
        "--memory",
        "2g",
        "--cpus",
        "2",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=256m",
        "--env",
        "HOME=/tmp",
        "--volume",
        f"{release_dir}:/release:ro",
        *response_mount,
        "--volume",
        f"{output_dir}:/output:rw",
        IMAGE,
        "--input",
        "/release/data/pqid_bench_evaluator_source_734.jsonl",
        "--output-dir",
        "/output",
        "--prompt-path",
        (
            "/release/artifacts/test_split_154/"
            "pqid_bench_external_generation_prompts_154.jsonl"
        ),
        "--template-path",
        (
            "/release/artifacts/test_split_154/"
            "pqid_bench_external_generation_response_template_154.jsonl"
        ),
        "--response-path",
        container_response,
        "--split-manifest",
        "/release/artifacts/test_split_154/pqid_bench_split_154_manifest.json",
        "--use-existing-prompts",
    )
    return ReplayPlan(
        build_command=build,
        run_command=run,
        release_dir=release_dir,
        response_file=response_file,
        output_dir=output_dir,
    )


def execute_replay(plan: ReplayPlan, *, timeout_seconds: int) -> None:
    if not docker_available():
        raise RuntimeError(
            "Docker Engine is unavailable; executable replay was not attempted"
        )
    if plan.build_command is not None:
        subprocess.run(plan.build_command, check=True, timeout=timeout_seconds)

    with tempfile.TemporaryDirectory(prefix="pqid-bench-replay-") as directory:
        staging_root = Path(directory)
        staged_output = staging_root / "output"
        staged_output.mkdir()
        replacements = {
            f"{plan.output_dir}:/output:rw": f"{staged_output}:/output:rw",
        }

        try:
            plan.response_file.relative_to(plan.release_dir)
        except ValueError:
            staged_responses = staging_root / "responses"
            staged_responses.mkdir()
            staged_response = staged_responses / plan.response_file.name
            shutil.copy2(plan.response_file, staged_response)
            replacements[f"{plan.response_file.parent}:/responses:ro"] = (
                f"{staged_responses}:/responses:ro"
            )

        staged_command = tuple(
            replacements.get(part, part) for part in plan.run_command
        )
        subprocess.run(staged_command, check=True, timeout=timeout_seconds)

        for name in EVALUATOR_OUTPUTS:
            source = staged_output / name
            if source.is_symlink() or not source.is_file():
                raise RuntimeError(f"Replay did not produce a regular {name} file")
        write_replay_derivatives(staged_output)

        for name in EXPECTED_OUTPUTS:
            source = staged_output / name
            if source.is_symlink() or not source.is_file():
                raise RuntimeError(f"Replay did not produce a regular {name} file")
            shutil.copy2(source, plan.output_dir / name)
