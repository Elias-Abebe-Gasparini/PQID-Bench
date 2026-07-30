"""Command-line interface for collection, reproduction, and isolated replay."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .live import (
    PROVIDER_PRESETS,
    LiveRunConfig,
    plan_live_model_run,
    run_live_model,
)
from .manifest import verify_manifest
from .metrics import (
    iter_jsonl,
    prepare_comparison,
    reproduce_release,
    summarize_evaluation_records,
    validate_canonical_summary,
    validate_repeatability,
)
from .replay import docker_available, execute_replay, replay_plan
from .reporting import REPORT_FORMATS, render_report
from .version import (
    BENCHMARK_RELEASE,
    EVALUATOR_VERSION,
    PACKAGE_VERSION,
    PREDICATE_VERSION,
    SCHEMA_VERSION,
    version_record,
)
from .visualization import build_dashboard


def _json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _release_dir(value: str) -> Path:
    path = Path(value).resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Release directory not found: {path}")
    return path


def _write_optional(
    payload: dict[str, Any],
    output: Path | None,
    *,
    output_format: str,
    report_type: str,
) -> None:
    rendered = render_report(
        payload,
        output_format=output_format,
        report_type=report_type,
    )
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def _load_candidate_run_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid candidate run manifest JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Candidate run manifest must be a JSON object")

    required = (
        "package_version",
        "benchmark_release",
        "evaluator_version",
        "predicate_version",
        "schema_version",
        "artifact_manifest_version",
        "run_type",
    )
    missing = [name for name in required if not payload.get(name)]
    if missing:
        raise ValueError(
            "Candidate run manifest lacks required fields: " + ", ".join(missing)
        )
    allowed_run_types = {
        "canonical_reproduction",
        "archived_replay",
        "supplied_evaluation",
        "live_replication",
    }
    if payload["run_type"] not in allowed_run_types:
        raise ValueError(
            f"Candidate run manifest has unsupported run_type "
            f"{payload['run_type']!r}"
        )
    expected = {
        "benchmark_release": BENCHMARK_RELEASE,
        "evaluator_version": EVALUATOR_VERSION,
        "predicate_version": PREDICATE_VERSION,
        "schema_version": SCHEMA_VERSION,
    }
    mismatches = [
        f"{name}: expected {value!r}, observed {payload.get(name)!r}"
        for name, value in expected.items()
        if payload.get(name) != value
    ]
    if mismatches:
        raise ValueError(
            "Candidate run manifest is incompatible with the frozen comparison "
            "contract: " + "; ".join(mismatches)
        )
    return payload


def _load_json_object(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON object file: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _live_config(args: argparse.Namespace) -> LiveRunConfig:
    return LiveRunConfig(
        release_dir=args.release_dir,
        output_dir=args.output_dir,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        api_key_file=args.api_key_file,
        no_auth=args.no_auth,
        prompt_path=args.prompt_path,
        prompt_ids=tuple(args.prompt_ids),
        limit=args.limit,
        max_new=args.max_new,
        max_output_tokens=args.max_output_tokens,
        max_output_field=args.max_output_field,
        temperature=args.temperature,
        top_p=args.top_p,
        seed=args.seed,
        extra_body=_load_json_object(args.extra_body_json),
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        retry_backoff_seconds=args.retry_backoff_seconds,
        sleep_seconds=args.sleep_seconds,
        run_id=args.run_id,
        resume=args.resume,
        retry_errors=args.retry_errors,
        retry_uncertain=args.retry_uncertain,
        acknowledge_prompt_export=args.acknowledge_third_party_prompt_export,
        allow_insecure_http=args.allow_insecure_http,
    )


def _print_live_progress(event: Mapping[str, Any]) -> None:
    event_type = event.get("event")
    if event_type == "run_started":
        print(
            f"Starting {event['selected_prompts']}-prompt live run for "
            f"{event['provider']} / {event['model']}.",
            file=sys.stderr,
            flush=True,
        )
    elif event_type == "prompt_started":
        print(
            f"{event['index']}/{event['total']} {event['prompt_id']} calling provider",
            file=sys.stderr,
            flush=True,
        )
    elif event_type == "prompt_retry":
        print(
            f"{event['index']}/{event['total']} {event['prompt_id']} retry "
            f"{event['attempt_count']} after {event['error']}",
            file=sys.stderr,
            flush=True,
        )
    elif event_type == "prompt_finished":
        detail = event.get("finish_reason") or event.get("error") or ""
        print(
            f"{event['index']}/{event['total']} {event['prompt_id']} "
            f"{event['status']} {detail}".rstrip(),
            file=sys.stderr,
            flush=True,
        )


def command_run_model(args: argparse.Namespace) -> int:
    config = _live_config(args)
    if args.dry_run:
        _json(plan_live_model_run(config))
        return 0
    if not args.acknowledge_third_party_prompt_export:
        print(
            "Refusing live generation without "
            "--acknowledge-third-party-prompt-export.",
            file=sys.stderr,
        )
        return 2
    result = run_live_model(
        config,
        progress=None if args.quiet else _print_live_progress,
    )
    _json(result.to_dict())
    return 1 if result.error_prompts else 0


def command_doctor(_: argparse.Namespace) -> int:
    packages: dict[str, str | None] = {}
    for name in ("qiskit", "qiskit-aer", "jsonschema", "plotly"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    _json(
        {
            **version_record(run_type="canonical_reproduction"),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "docker_cli": shutil.which("docker"),
            "docker_daemon_available": docker_available(),
            "optional_packages": packages,
        }
    )
    return 0


def command_verify(args: argparse.Namespace) -> int:
    manifest = verify_manifest(args.release_dir)
    payload: dict[str, Any] = {
        **version_record(run_type="canonical_reproduction"),
        "manifest": manifest.to_dict(),
    }
    problems: list[str] = []
    if not manifest.valid:
        problems.append("artifact manifest verification failed")
    if args.full:
        summary = reproduce_release(args.release_dir)
        parity = list(validate_canonical_summary(summary))
        repeatability = list(validate_repeatability(args.release_dir))
        payload["summary"] = summary.to_dict()
        payload["release_parity_errors"] = parity
        payload["repeatability_parity_errors"] = repeatability
        problems.extend(parity)
        problems.extend(repeatability)
    payload["valid"] = not problems
    payload["errors"] = problems
    _json(payload)
    return 0 if not problems else 1


def command_reproduce(args: argparse.Namespace) -> int:
    summary = reproduce_release(args.release_dir)
    errors = list(validate_canonical_summary(summary))
    payload = {**summary.to_dict(), "canonical_parity": not errors, "errors": errors}
    _write_optional(
        payload,
        args.output,
        output_format=args.output_format,
        report_type="summary",
    )
    return 0 if not errors else 1


def command_evaluate(args: argparse.Namespace) -> int:
    summary = summarize_evaluation_records(iter_jsonl(args.evaluations))
    payload = {
        **summary.to_dict(run_type="supplied_evaluation"),
        "source": str(args.evaluations.resolve()),
    }
    _write_optional(
        payload,
        args.output,
        output_format=args.output_format,
        report_type="summary",
    )
    return 0


def command_compare(args: argparse.Namespace) -> int:
    candidate_manifest = _load_candidate_run_manifest(args.candidate_run_manifest)
    candidate, frozen, scope = prepare_comparison(
        args.release_dir,
        iter_jsonl(args.evaluations),
        allow_partial=args.allow_partial,
    )
    fields = (
        "execution_rate",
        "signature_rate",
        "es_gap_rate",
        "executable_signature_disagreement_rate",
        "structural_hallucination_rate",
    )
    deltas = {
        field: (
            getattr(candidate, field) - getattr(frozen, field)
            if getattr(candidate, field) is not None
            and getattr(frozen, field) is not None
            else None
        )
        for field in fields
    }
    payload = {
        **version_record(run_type="supplied_evaluation"),
        "comparison_scope": scope.to_dict(),
        "comparison_label": (
            "matched-subset comparison"
            if scope.mode == "matched_subset"
            else "frozen 154-prompt comparison"
        ),
        "candidate_source": str(args.evaluations.resolve()),
        "candidate_run_manifest_source": str(
            args.candidate_run_manifest.resolve()
        ),
        "candidate_run_manifest": candidate_manifest,
        "candidate": candidate.to_dict(run_type="supplied_evaluation"),
        "frozen": frozen.to_dict(),
        "candidate_minus_frozen": deltas,
    }
    _write_optional(
        payload,
        args.output,
        output_format=args.output_format,
        report_type="comparison",
    )
    return 0


def command_dashboard(args: argparse.Namespace) -> int:
    data = build_dashboard(
        args.release_dir,
        args.output,
        plotlyjs=args.plotlyjs,
    )
    _json(
        {
            **version_record(run_type="canonical_reproduction"),
            "output": str(args.output.resolve()),
            "plotlyjs": args.plotlyjs,
            "models": len(data.models),
            "prompts": int(data.summary["prompts"]),
            "cells": int(data.summary["cells"]),
        }
    )
    return 0


def command_replay(args: argparse.Namespace) -> int:
    if not args.acknowledge_code_execution:
        print(
            "Refusing executable replay without --acknowledge-code-execution. "
            "Generated Python is run only in the hardened Docker worker.",
            file=sys.stderr,
        )
        return 2
    manifest = verify_manifest(args.release_dir)
    if not manifest.valid:
        print(
            "Refusing executable replay because release-manifest verification failed.",
            file=sys.stderr,
        )
        return 1
    plan = replay_plan(
        release_dir=args.release_dir,
        response_file=args.responses,
        output_dir=args.output_dir,
        build_image=args.build_image,
    )
    if args.dry_run:
        _json(
            {
                **version_record(run_type="archived_replay"),
                "build_command": plan.build_command,
                "run_command": plan.run_command,
                "executed": False,
            }
        )
        return 0
    execute_replay(plan, timeout_seconds=args.timeout_seconds)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pqid-bench")
    root.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PACKAGE_VERSION}",
    )
    sub = root.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Report package and optional-runtime status")
    doctor.set_defaults(func=command_doctor)

    verify = sub.add_parser(
        "verify",
        help="Verify the release manifest and optional parity",
    )
    verify.add_argument("release_dir", type=_release_dir)
    verify.add_argument("--full", action="store_true")
    verify.set_defaults(func=command_verify)

    reproduce = sub.add_parser(
        "reproduce",
        help="Safely recompute published metrics from archived evaluation records",
    )
    reproduce.add_argument("--release-dir", required=True, type=_release_dir)
    reproduce.add_argument("--output", type=Path)
    reproduce.add_argument(
        "--format",
        choices=REPORT_FORMATS,
        default="json",
        dest="output_format",
        help="Report format (default: json)",
    )
    reproduce.set_defaults(func=command_reproduce)

    evaluate = sub.add_parser(
        "evaluate",
        help="Summarize canonical evaluation records without executing generated code",
    )
    evaluate.add_argument("--evaluations", required=True, type=Path)
    evaluate.add_argument("--output", type=Path)
    evaluate.add_argument(
        "--format",
        choices=REPORT_FORMATS,
        default="json",
        dest="output_format",
        help="Report format (default: json)",
    )
    evaluate.set_defaults(func=command_evaluate)

    compare = sub.add_parser(
        "compare",
        help="Compare supplied canonical evaluations with the frozen benchmark",
    )
    compare.add_argument("--evaluations", required=True, type=Path)
    compare.add_argument("--release-dir", required=True, type=_release_dir)
    compare.add_argument("--candidate-run-manifest", required=True, type=Path)
    compare.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "Allow a common strict subset of frozen prompt IDs and compare it "
            "with the same frozen matched subset"
        ),
    )
    compare.add_argument("--output", type=Path)
    compare.add_argument(
        "--format",
        choices=REPORT_FORMATS,
        default="json",
        dest="output_format",
        help="Report format (default: json)",
    )
    compare.set_defaults(func=command_compare)

    dashboard = sub.add_parser(
        "dashboard",
        help="Build a standalone interactive Plotly report from frozen results",
    )
    dashboard.add_argument("--release-dir", required=True, type=_release_dir)
    dashboard.add_argument("--output", required=True, type=Path)
    dashboard.add_argument(
        "--plotlyjs",
        choices=("embed", "cdn"),
        default="embed",
        help=(
            "Embed Plotly.js for an offline report or load it from the CDN "
            "(default: embed)"
        ),
    )
    dashboard.set_defaults(func=command_dashboard)

    run_model = sub.add_parser(
        "run-model",
        help="Collect model responses from an OpenAI-compatible endpoint",
    )
    run_model.add_argument("--release-dir", required=True, type=_release_dir)
    run_model.add_argument("--output-dir", required=True, type=Path)
    run_model.add_argument(
        "--provider",
        required=True,
        help=(
            "Provider preset or custom label. Presets: "
            + ", ".join(sorted(PROVIDER_PRESETS))
        ),
    )
    run_model.add_argument("--model", required=True)
    run_model.add_argument(
        "--base-url",
        help="Override the preset or define a custom OpenAI-compatible base URL",
    )
    run_model.add_argument("--api-key-env")
    run_model.add_argument("--api-key-file", type=Path)
    run_model.add_argument(
        "--no-auth",
        action="store_true",
        help="Use an endpoint that requires no Authorization header",
    )
    run_model.add_argument(
        "--prompt-path",
        type=Path,
        help="Override the frozen 154-prompt JSONL",
    )
    run_model.add_argument(
        "--prompt-id",
        action="append",
        default=[],
        dest="prompt_ids",
        help="Select one prompt ID; repeat for multiple prompts",
    )
    run_model.add_argument("--limit", type=int, default=0)
    run_model.add_argument(
        "--max-new",
        type=int,
        default=0,
        help="Maximum newly attempted prompts in this invocation; 0 means all",
    )
    run_model.add_argument("--max-output-tokens", type=int, default=2048)
    run_model.add_argument(
        "--max-output-field",
        choices=("max_tokens", "max_completion_tokens"),
        default="max_tokens",
    )
    run_model.add_argument("--temperature", type=float, default=0.0)
    run_model.add_argument(
        "--omit-temperature",
        action="store_const",
        const=None,
        dest="temperature",
    )
    run_model.add_argument("--top-p", type=float, default=1.0)
    run_model.add_argument(
        "--omit-top-p",
        action="store_const",
        const=None,
        dest="top_p",
    )
    run_model.add_argument("--seed", type=int)
    run_model.add_argument(
        "--extra-body-json",
        type=Path,
        help="JSON object merged into every request; credential-like keys are rejected",
    )
    run_model.add_argument("--timeout-seconds", type=float, default=120.0)
    run_model.add_argument("--max-retries", type=int, default=2)
    run_model.add_argument("--retry-backoff-seconds", type=float, default=1.0)
    run_model.add_argument("--sleep-seconds", type=float, default=0.0)
    run_model.add_argument("--run-id")
    run_model.add_argument("--resume", action="store_true")
    run_model.add_argument(
        "--retry-errors",
        action="store_true",
        help="With --resume, retry prompts whose canonical response is an error",
    )
    run_model.add_argument(
        "--retry-uncertain",
        action="store_true",
        help=(
            "Retry a request marked in flight by an interrupted process, "
            "accepting a possible additional stochastic draw"
        ),
    )
    run_model.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help="Allow plain HTTP for a non-loopback custom endpoint",
    )
    run_model.add_argument(
        "--acknowledge-third-party-prompt-export",
        action="store_true",
        help="Acknowledge provider retention, policy, and billing risks",
    )
    run_model.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print a credential-free plan without contacting a provider",
    )
    run_model.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-prompt progress on stderr",
    )
    run_model.set_defaults(func=command_run_model)

    replay = sub.add_parser(
        "replay",
        help="Evaluate supplied generated programs in the isolated Docker worker",
    )
    replay.add_argument("--release-dir", required=True, type=_release_dir)
    replay.add_argument("--responses", required=True, type=Path)
    replay.add_argument("--output-dir", required=True, type=Path)
    replay.add_argument("--build-image", action="store_true")
    replay.add_argument("--dry-run", action="store_true")
    replay.add_argument("--timeout-seconds", type=int, default=3600)
    replay.add_argument("--acknowledge-code-execution", action="store_true")
    replay.set_defaults(func=command_replay)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, TypeError, ValueError, RuntimeError) as exc:
        print(f"pqid-bench: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
