"""Create a cryptographically sealed preregistration bundle for the 72-prompt audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from build_pqid_bench_stochastic_repeatability_panel import (
    BIN_ORDER,
    COHORT_ORDER,
    cohort,
    gate_type_bin,
    has_barrier,
    iter_jsonl,
    prompt_number,
    reference_signature,
    stable_json,
)
from build_pqid_bench_stochastic_repeatability_extension import (
    EXPECTED_BASE_PANEL_SHA256,
    SCHEMA_VERSION as SELECTION_SCHEMA_VERSION,
    SELECTION_SEED,
    SELECTION_SEED_DERIVATION,
    choose_cross_stratum_quotas,
    representative_rows,
    seeded_rank,
)


SUBMISSION_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SUBMISSION_DIR.parents[2]
AUDIT_36_ROOT = SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x36"
AUDIT_72_ROOT = SUBMISSION_DIR / "artifacts" / "stochastic_repeatability_21x72"
PANEL_ROOT = AUDIT_72_ROOT / "panel"
RUNS_ROOT = AUDIT_72_ROOT / "augmentation_runs"
PANEL_MANIFEST_PATH = (
    PANEL_ROOT / "pqid_bench_stochastic_repeatability_augmentation_manifest.json"
)
REQUEST_MANIFEST_PATH = (
    RUNS_ROOT / "pqid_bench_stochastic_repeatability_request_manifest.json"
)
EXPECTED_AUGMENTATION_PANEL_SHA256 = (
    "9f36bdfabbfe53d0b719e95961d84cf50bb38c21a8dbbaf01d047416dfe241b0"
)
EXPECTED_COMBINED_PANEL_SHA256 = (
    "3e242bf2d8db9e4deda76a1a62c06484949ff245e8aa6284c64948e51c4049ed"
)
EXPECTED_REQUEST_MANIFEST_SHA256 = (
    "911ae8e60ff994795a8220407bac90b0d35c0d8126cfed3da1d8c142fbdef9ea"
)
BUNDLE_SCHEMA_VERSION = "pqid-bench-repeatability-preregistration-bundle-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def resolve_submission_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = (SUBMISSION_DIR / path, WORKSPACE_ROOT / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve frozen artifact path: {value}")


def copy_into(source: Path, bundle_root: Path, relative_target: Path) -> Path:
    target = bundle_root / relative_target
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def build_eligible_pool(
    panel_manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    prompt_path = resolve_submission_path(str(panel_manifest["source_prompt_file"]))
    identifiability_path = resolve_submission_path(
        str(panel_manifest["identifiability_audit_file"])
    )
    base_panel_path = resolve_submission_path(str(panel_manifest["base_panel_file"]))

    if sha256_file(prompt_path) != str(panel_manifest["source_prompt_sha256"]):
        raise AssertionError("Source prompt file changed after panel selection")
    if sha256_file(identifiability_path) != str(
        panel_manifest["identifiability_audit_sha256"]
    ):
        raise AssertionError("Identifiability audit changed after panel selection")
    if sha256_file(base_panel_path) != EXPECTED_BASE_PANEL_SHA256:
        raise AssertionError("Original 36-prompt panel changed")

    prompts = iter_jsonl(prompt_path)
    base_rows = iter_jsonl(base_panel_path)
    identifiability = json.loads(identifiability_path.read_text(encoding="utf-8"))
    excluded_ids = {
        str(row["prompt_id"]) for row in identifiability.get("exceptions", [])
    }
    base_signatures = {stable_json(reference_signature(row)) for row in base_rows}
    representatives, signature_members = representative_rows(
        prompts,
        excluded_ids,
        base_signatures,
    )

    rows: list[dict[str, Any]] = []
    for prompt in sorted(
        representatives,
        key=lambda row: (
            BIN_ORDER[gate_type_bin(row)],
            COHORT_ORDER[cohort(row)],
            prompt_number(str(row["prompt_id"])),
        ),
    ):
        signature = reference_signature(prompt)
        signature_key = stable_json(signature)
        rows.append(
            {
                "representative_prompt_id": str(prompt["prompt_id"]),
                "collapsed_signature_members": signature_members[signature_key],
                "cohort": cohort(prompt),
                "gate_type_bin": gate_type_bin(prompt),
                "has_barrier": has_barrier(prompt),
                "reference_signature": signature,
                "reference_signature_sha256": sha256_text(signature_key),
                "selection_rank_sha256": seeded_rank(
                    "panel", str(prompt["prompt_id"])
                ),
                "source_prompt_record": prompt,
            }
        )

    if len(rows) != int(panel_manifest["eligible_remaining_unique_signature_count"]):
        raise AssertionError("Eligible-pool size does not match the frozen manifest")

    capacities: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        capacities[(row["gate_type_bin"], row["cohort"])].append(row)
    quotas = choose_cross_stratum_quotas(capacities)
    capacity_summary = {
        f"{gate_bin}|{cohort_name}": len(capacities[(gate_bin, cohort_name)])
        for gate_bin in BIN_ORDER
        for cohort_name in COHORT_ORDER
    }
    quota_summary = {
        f"{gate_bin}|{cohort_name}": quotas[(gate_bin, cohort_name)]
        for gate_bin in BIN_ORDER
        for cohort_name in COHORT_ORDER
    }
    if capacity_summary["5+|pilot"] != 5:
        raise AssertionError("The recorded 6/6 infeasibility condition no longer holds")
    return rows, {**capacity_summary, **{f"selected:{k}": v for k, v in quota_summary.items()}}


def inspect_live_outputs() -> dict[str, Any]:
    result: dict[str, Any] = {
        "criterion": (
            "Live output means a non-template response, raw provider output, "
            "evaluation artifact, process log, or OpenAI Batch state/output/error file."
        ),
        "runs": {},
    }
    all_live_files: list[str] = []
    for run_number in (2, 3):
        run_root = RUNS_ROOT / f"run_{run_number}"
        live_files: list[str] = []
        for path in sorted(item for item in run_root.rglob("*") if item.is_file()):
            relative = path.relative_to(run_root)
            parts = {part.lower() for part in relative.parts}
            name = path.name.lower()
            is_live = False
            if "responses" in parts:
                is_live = name.endswith("_responses.jsonl") and not name.endswith(
                    "_responses_template.jsonl"
                )
            if "raw_outputs" in parts or "evaluations" in parts or "logs" in parts:
                is_live = True
            if "openai_batch" in parts and "requests" not in parts:
                is_live = is_live or any(
                    token in name
                    for token in ("state", "output", "error", "result", "response")
                )
            if is_live:
                live_files.append(relative.as_posix())
        result["runs"][f"run_{run_number}"] = {
            "live_output_file_count": len(live_files),
            "live_output_files": live_files,
        }
        all_live_files.extend(f"run_{run_number}/{path}" for path in live_files)
    result["all_live_output_file_count"] = len(all_live_files)
    result["all_live_output_files"] = all_live_files
    result["pretransmission_empty"] = not all_live_files
    if all_live_files:
        raise AssertionError(
            "Cannot freeze a pre-transmission bundle after live outputs exist: "
            + ", ".join(all_live_files)
        )
    return result


def run_invariance_tests() -> str:
    test_path = SUBMISSION_DIR / "scripts" / "test_pqid_bench_stochastic_repeatability.py"
    command = [sys.executable, "-m", "unittest", "-v", str(test_path)]
    completed = subprocess.run(
        command,
        cwd=WORKSPACE_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    transcript = (
        f"Command: {' '.join(command)}\n"
        f"Working directory: {WORKSPACE_ROOT}\n"
        f"Exit code: {completed.returncode}\n\n"
        "--- STDOUT ---\n"
        f"{completed.stdout}\n"
        "--- STDERR ---\n"
        f"{completed.stderr}"
    )
    if completed.returncode != 0:
        raise AssertionError("Invariant tests failed; preregistration bundle not created")
    if "Ran 6 tests" not in transcript or "OK" not in transcript:
        raise AssertionError("Invariant-test transcript did not confirm all six tests")
    return transcript


def evaluator_contract() -> dict[str, Any]:
    reports = sorted(
        (AUDIT_36_ROOT / "run_1" / "evaluations").glob(
            "*/pqid_bench_external_model_generation_harness_report.json"
        )
    )
    if len(reports) != 21:
        raise AssertionError(f"Expected 21 canonical evaluator reports, found {len(reports)}")
    versions: set[str] = set()
    predicates: set[str] = set()
    for path in reports:
        report = json.loads(path.read_text(encoding="utf-8"))
        versions.add(str(report.get("evaluator_version") or ""))
        predicates.add(str(report.get("structural_predicate_version") or ""))
    if len(versions) != 1 or len(predicates) != 1:
        raise AssertionError("Canonical reports do not share one evaluator contract")
    harness = SUBMISSION_DIR / "scripts" / "run_pqid_bench_external_model_generation_harness.py"
    return {
        "evaluator_versions": sorted(versions),
        "structural_predicate_versions": sorted(predicates),
        "canonical_report_count": len(reports),
        "evaluator_harness_file": harness.relative_to(WORKSPACE_ROOT).as_posix(),
        "evaluator_harness_sha256": sha256_file(harness),
        "frozen_predicate": "M = Q AND K AND T (Q, K, and T are execution-gated)",
        "gate_type_component": "complete gate-type count-map equality",
        "scalar_gate_count_role": "redundant diagnostic under count-map equality",
    }


def route_contract(request_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in request_manifest["models"]:
        body_hashes = dict(model["provider_request_body_sha256s"])
        rows.append(
            {
                "slug": model["slug"],
                "provider": model["provider"],
                "model": model["model"],
                "request_family": model["request_family"],
                "generation_config": model["generation_config"],
                "source_request_file": model["source_request_file"],
                "source_request_sha256": model["source_request_sha256"],
                "source_response_file": model["source_response_file"],
                "source_response_sha256": model["source_response_sha256"],
                "provider_request_body_count": len(body_hashes),
                "provider_request_body_map_sha256": sha256_text(
                    stable_json(body_hashes)
                ),
            }
        )
    if len(rows) != 21 or any(row["provider_request_body_count"] != 36 for row in rows):
        raise AssertionError("Request-route contract is not 21 models by 36 prompts")
    return rows


def copy_frozen_inputs(bundle_root: Path) -> None:
    copies: list[tuple[Path, Path]] = [
        (
            AUDIT_72_ROOT / "PRESPECIFIED_AUGMENTATION_PROTOCOL.md",
            Path("protocol/PRESPECIFIED_AUGMENTATION_PROTOCOL.md"),
        ),
        (
            AUDIT_36_ROOT / "PRESPECIFIED_PROTOCOL.md",
            Path("protocol/INHERITED_PRESPECIFIED_PROTOCOL.md"),
        ),
        (
            AUDIT_36_ROOT / "PROTOCOL_AMENDMENTS.md",
            Path("protocol/INHERITED_PROTOCOL_AMENDMENTS.md"),
        ),
        (
            PANEL_ROOT / "pqid_bench_stochastic_repeatability_augmentation_manifest.json",
            Path("panel/augmentation_manifest.json"),
        ),
        (
            PANEL_ROOT / "pqid_bench_stochastic_repeatability_augmentation_manifest.md",
            Path("panel/augmentation_manifest.md"),
        ),
        (
            PANEL_ROOT / "pqid_bench_stochastic_repeatability_augmentation_prompts_36.jsonl",
            Path("panel/augmentation_prompts_36.jsonl"),
        ),
        (
            PANEL_ROOT / "pqid_bench_stochastic_repeatability_prompts_72.jsonl",
            Path("panel/combined_prompts_72.jsonl"),
        ),
        (
            REQUEST_MANIFEST_PATH,
            Path("requests/request_manifest.json"),
        ),
        (
            REQUEST_MANIFEST_PATH.with_suffix(".md"),
            Path("requests/request_manifest.md"),
        ),
        (
            AUDIT_72_ROOT / "RUN_STOCHASTIC_REPEATABILITY_AUGMENTATION.ps1",
            Path("code/RUN_STOCHASTIC_REPEATABILITY_AUGMENTATION.ps1"),
        ),
        (
            AUDIT_36_ROOT / "RUN_STOCHASTIC_REPEATABILITY.ps1",
            Path("code/RUN_STOCHASTIC_REPEATABILITY.ps1"),
        ),
    ]
    script_names = (
        "build_pqid_bench_stochastic_repeatability_panel.py",
        "build_pqid_bench_stochastic_repeatability_extension.py",
        "prepare_pqid_bench_stochastic_repeatability_runs.py",
        "analyze_pqid_bench_stochastic_repeatability.py",
        "consolidate_pqid_bench_stochastic_repeatability_72.py",
        "test_pqid_bench_stochastic_repeatability.py",
        "run_pqid_bench_external_model_generation_harness.py",
        Path(__file__).name,
    )
    for name in script_names:
        copies.append(
            (
                SUBMISSION_DIR / "scripts" / name,
                Path("code") / name,
            )
        )
    for source, relative in copies:
        copy_into(source, bundle_root, relative)

    for run_number in (2, 3):
        run_root = RUNS_ROOT / f"run_{run_number}"
        for source in sorted((run_root / "requests").glob("*.jsonl")):
            copy_into(
                source,
                bundle_root,
                Path(f"requests/run_{run_number}/generic") / source.name,
            )
        for source in sorted((run_root / "openai_batch" / "requests").glob("*")):
            if source.is_file():
                copy_into(
                    source,
                    bundle_root,
                    Path(f"requests/run_{run_number}/openai_batch") / source.name,
                )


def build_hash_inventory(bundle_root: Path) -> str:
    rows: list[str] = []
    for path in sorted(item for item in bundle_root.rglob("*") if item.is_file()):
        if path.name == "SHA256SUMS.txt":
            continue
        rows.append(f"{sha256_file(path)}  {path.relative_to(bundle_root).as_posix()}")
    return "\n".join(rows) + "\n"


def write_readme(
    bundle_root: Path,
    *,
    frozen_at: str,
    eligible_count: int,
    protocol_sha256: str,
) -> None:
    text = f"""# PQID-Bench 72-Prompt Repeatability Preregistration Bundle

This bundle was sealed at `{frozen_at}` before any live response, raw provider
output, evaluation artifact, or process log existed for augmentation Runs 2
and 3. It cryptographically records the outcome-blind 36-prompt confirmatory
panel that extends the original 36-prompt audit to 72 prompts.

## Frozen Design

- 21 model routes;
- 36 original prompts plus 36 signature-disjoint confirmatory prompts;
- 72 unique reference signatures and no identifiability exceptions;
- 18 pilot and 18 extension prompts in the added panel;
- 12 added prompts in each gate-type bin;
- 1,512 new logical calls and 4,536 pooled run-level outputs when complete.

The added `3 x 2` allocation is `7/5`, `6/6`, and `5/7` across the `1-2`,
`3-4`, and `5+` gate-type rows. Exact `6/6` balance is infeasible because the
remaining eligible pool contains only five pilot signatures in the `5+` row.
The eligible-pool snapshot contains `{eligible_count}` remaining unique-signature
representatives and all collapsed prompt-member IDs.

## Evidential Order

1. original 36-prompt audit;
2. new 36-prompt confirmatory replication;
3. pooled 72-prompt precision analysis;
4. complete deployment and common no-recorded-disturbance estimates reported separately.

## Integrity

`SHA256SUMS.txt` hashes every file in this directory except itself. The sibling
ZIP archive has a separate `.sha256` seal. The frozen augmentation protocol
hash at bundle creation is `{protocol_sha256}`. API credentials are deliberately
excluded.
"""
    (bundle_root / "README.md").write_text(text, encoding="utf-8", newline="\n")


def freeze_bundle(output_dir: Path) -> tuple[Path, Path, str]:
    if output_dir.exists() or output_dir.with_suffix(".zip").exists():
        raise FileExistsError(f"Refusing to overwrite preregistration bundle: {output_dir}")

    panel_manifest = json.loads(PANEL_MANIFEST_PATH.read_text(encoding="utf-8"))
    request_manifest = json.loads(REQUEST_MANIFEST_PATH.read_text(encoding="utf-8"))
    if str(panel_manifest["schema_version"]) != SELECTION_SCHEMA_VERSION:
        raise AssertionError("Unexpected augmentation selection schema")
    if str(panel_manifest["selection_seed"]) != SELECTION_SEED:
        raise AssertionError("Selection seed changed")
    if str(panel_manifest["selection_seed_derivation"]) != SELECTION_SEED_DERIVATION:
        raise AssertionError("Selection-seed derivation changed")
    if str(panel_manifest["augmentation_panel_sha256"]) != EXPECTED_AUGMENTATION_PANEL_SHA256:
        raise AssertionError("Augmentation panel hash changed")
    if str(panel_manifest["combined_panel_sha256"]) != EXPECTED_COMBINED_PANEL_SHA256:
        raise AssertionError("Combined panel hash changed")
    if sha256_file(REQUEST_MANIFEST_PATH) != EXPECTED_REQUEST_MANIFEST_SHA256:
        raise AssertionError("Request manifest hash changed")

    frozen_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    empty_assertion = inspect_live_outputs()
    empty_assertion["asserted_at_utc"] = frozen_at
    eligible_rows, allocation = build_eligible_pool(panel_manifest)
    tests = run_invariance_tests()
    evaluator = evaluator_contract()
    routes = route_contract(request_manifest)

    output_dir.mkdir(parents=True)
    copy_frozen_inputs(output_dir)
    write_jsonl(output_dir / "panel" / "eligible_remaining_signature_pool.jsonl", eligible_rows)
    write_json(
        output_dir / "panel" / "allocation_feasibility.json",
        {
            "selection_seed": SELECTION_SEED,
            "selection_seed_derivation": SELECTION_SEED_DERIVATION,
            "eligible_remaining_unique_signatures": len(eligible_rows),
            "cross_stratum_counts": allocation,
            "exact_six_by_six_feasible": False,
            "binding_constraint": (
                "Only five eligible pilot-cohort signatures remain in the 5+ gate-type bin."
            ),
            "optimization_rule": (
                "Minimize maximum absolute cell deviation from six, then the sum of "
                "squared deviations, with deterministic seeded tie-breaking."
            ),
        },
    )
    write_json(output_dir / "audit" / "pretransmission_empty_assertion.json", empty_assertion)
    (output_dir / "audit" / "invariance_test_transcript.txt").parent.mkdir(
        parents=True, exist_ok=True
    )
    (output_dir / "audit" / "invariance_test_transcript.txt").write_text(
        tests, encoding="utf-8", newline="\n"
    )
    write_json(output_dir / "contract" / "evaluator_predicate_contract.json", evaluator)
    write_json(output_dir / "contract" / "route_contract.json", routes)

    protocol_path = AUDIT_72_ROOT / "PRESPECIFIED_AUGMENTATION_PROTOCOL.md"
    bundle_manifest = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "sealed_at_utc": frozen_at,
        "pretransmission_empty": True,
        "selection_is_outcome_blind": True,
        "selection_seed": SELECTION_SEED,
        "panel": {
            "original_prompt_count": 36,
            "confirmatory_prompt_count": 36,
            "pooled_prompt_count": 72,
            "unique_signature_count": 72,
            "augmentation_panel_sha256": EXPECTED_AUGMENTATION_PANEL_SHA256,
            "combined_panel_sha256": EXPECTED_COMBINED_PANEL_SHA256,
            "eligible_remaining_signature_count": len(eligible_rows),
        },
        "requests": {
            "model_count": 21,
            "prompt_count": 36,
            "new_run_count": 2,
            "new_logical_call_count": 1512,
            "pooled_run_level_output_count": 4536,
            "request_manifest_sha256": EXPECTED_REQUEST_MANIFEST_SHA256,
        },
        "protocol_sha256": sha256_file(protocol_path),
        "evaluator_contract": evaluator,
        "credential_files_included": False,
    }
    write_json(output_dir / "BUNDLE_MANIFEST.json", bundle_manifest)
    write_readme(
        output_dir,
        frozen_at=frozen_at,
        eligible_count=len(eligible_rows),
        protocol_sha256=bundle_manifest["protocol_sha256"],
    )
    sums = build_hash_inventory(output_dir)
    (output_dir / "SHA256SUMS.txt").write_text(sums, encoding="ascii", newline="\n")

    archive_base = str(output_dir)
    archive = Path(
        shutil.make_archive(
            archive_base,
            "zip",
            root_dir=output_dir.parent,
            base_dir=output_dir.name,
        )
    )
    archive_hash = sha256_file(archive)
    seal_path = Path(str(archive) + ".sha256")
    seal_path.write_text(
        f"{archive_hash}  {archive.name}\n", encoding="ascii", newline="\n"
    )
    return archive, seal_path, archive_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    archive, seal_path, archive_hash = freeze_bundle(args.output_dir.resolve())
    print(f"Wrote preregistration bundle: {args.output_dir.resolve()}")
    print(f"Wrote sealed archive: {archive}")
    print(f"Wrote archive seal: {seal_path}")
    print(f"Archive SHA-256: {archive_hash}")


if __name__ == "__main__":
    main()
