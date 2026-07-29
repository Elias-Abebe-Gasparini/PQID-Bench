"""Safe metric reproduction from archived evaluation records."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .version import version_record


CANONICAL_COUNTS = {
    "cells": 3234,
    "models": 21,
    "prompts": 154,
    "execution": 2950,
    "assembly": 2944,
    "signature": 1703,
    "ordered": 1576,
    "parameter": 1545,
    "execution_to_assembly_attrition": 6,
    "as_gap": 1241,
    "assembly_without_signature": 1241,
    "signature_without_assembly": 0,
    "identifiable_cells": 3150,
    "identifiable_execution": 2890,
    "identifiable_signature": 1703,
    "identifiable_disagreement": 1187,
    "repeatability_cells": 4536,
    "repeatability_models": 21,
    "repeatability_prompts": 72,
    "repeatability_runs": 3,
}


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    cells: int
    models: int
    prompts: int
    execution_count: int
    signature_count: int
    ordered_count: int | None
    parameter_count: int | None
    es_gap_count: int
    execution_rate: float
    signature_rate: float
    es_gap_rate: float
    executable_signature_disagreement_rate: float | None
    identifiable_cells: int | None = None
    identifiable_execution_count: int | None = None
    identifiable_signature_count: int | None = None
    identifiable_disagreement_count: int | None = None
    structural_hallucination_rate: float | None = None
    assembly_count: int | None = None
    assembly_rate: float | None = None
    execution_to_assembly_attrition_count: int | None = None
    execution_to_assembly_attrition_rate: float | None = None
    as_gap_count: int | None = None
    as_gap_rate: float | None = None
    assembly_without_signature_count: int | None = None
    signature_without_assembly_count: int | None = None
    as_gap_share_of_es_gap: float | None = None

    def to_dict(
        self,
        *,
        run_type: str = "canonical_reproduction",
    ) -> dict[str, Any]:
        return {**version_record(run_type=run_type), **asdict(self)}

    def render(
        self,
        *,
        output_format: str = "text",
        run_type: str = "canonical_reproduction",
    ) -> str:
        """Render this summary for a person or a tabular downstream tool."""

        from .reporting import render_summary

        return render_summary(
            self,
            output_format=output_format,
            run_type=run_type,
        )

    def to_text(self, *, run_type: str = "canonical_reproduction") -> str:
        """Return the compact human-readable report."""

        return self.render(output_format="text", run_type=run_type)

    def to_markdown(self, *, run_type: str = "canonical_reproduction") -> str:
        """Return a copy-ready Markdown report."""

        return self.render(output_format="markdown", run_type=run_type)

    def to_csv(self, *, run_type: str = "canonical_reproduction") -> str:
        """Return a tidy long-form CSV report."""

        return self.render(output_format="csv", run_type=run_type)

    def to_rows(
        self,
        *,
        run_type: str = "canonical_reproduction",
    ) -> list[dict[str, Any]]:
        """Return tidy numerical rows without requiring pandas."""

        from .reporting import summary_rows

        return summary_rows(self, run_type=run_type)

    def __str__(self) -> str:
        return self.to_text()


@dataclass(frozen=True, slots=True)
class ComparisonScope:
    mode: str
    prompt_count: int
    prompt_ids_sha256: str
    prompt_ids: tuple[str, ...]
    candidate_models: int
    candidate_cells: int
    frozen_models: int
    frozen_cells: int
    identifiable_exclusions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            yield row


def _bool(row: Mapping[str, Any], names: tuple[str, ...], *, required: bool) -> bool | None:
    found: list[tuple[str, bool]] = []
    for name in names:
        if name in row:
            value = row[name]
            if isinstance(value, bool):
                found.append((name, value))
            elif value in (0, 1):
                found.append((name, bool(value)))
            else:
                raise ValueError(f"Field {name!r} must be Boolean or 0/1")
    if found:
        first_value = found[0][1]
        if any(value != first_value for _, value in found[1:]):
            details = ", ".join(f"{name}={value}" for name, value in found)
            raise ValueError(
                f"Conflicting aliases for {names[0]!r}: {details}"
            )
        return first_value
    if required:
        raise ValueError(f"Missing required field; expected one of {names}")
    return None


def summarize_evaluation_records(
    rows: Iterable[Mapping[str, Any]],
    *,
    identifiable: Mapping[str, Any] | None = None,
) -> BenchmarkSummary:
    materialized = list(rows)
    if not materialized:
        raise ValueError("No evaluation records supplied")

    models: set[str] = set()
    prompts: set[str] = set()
    execution = assembly = signature = ordered = parameter = 0
    ordered_available = parameter_available = True
    assembly_seen = 0
    ordered_seen = parameter_seen = False
    assembly_without_signature = signature_without_assembly = 0
    seen_keys: set[tuple[str, str]] = set()

    for index, row in enumerate(materialized, start=1):
        model = str(row.get("model") or "")
        prompt = str(row.get("prompt_id") or "")
        if not model or not prompt:
            raise ValueError(f"Record {index} lacks model or prompt_id")
        key = (model, prompt)
        if key in seen_keys:
            raise ValueError(
                f"Duplicate model-prompt key at record {index}: "
                f"model={model!r}, prompt_id={prompt!r}"
            )
        seen_keys.add(key)
        models.add(model)
        prompts.add(prompt)
        is_execution = bool(
            _bool(row, ("report_executable", "execution", "execution_success"), required=True)
        )
        is_assembly = _bool(
            row,
            (
                "report_assembly_admissible",
                "assembly",
                "assembly_admissible",
                "qasm3_export_success",
            ),
            required=False,
        )
        is_signature = bool(
            _bool(
                row,
                ("report_signature_match", "signature", "signature_match"),
                required=True,
            )
        )
        is_ordered = _bool(
            row,
            ("ordered_wire_tape_match", "ordered_match"),
            required=False,
        )
        is_parameter = _bool(
            row,
            ("parameter_aware_tape_match", "parameter_match"),
            required=False,
        )
        assembly_seen += int(is_assembly is not None)
        ordered_seen = ordered_seen or is_ordered is not None
        parameter_seen = parameter_seen or is_parameter is not None
        if is_assembly and not is_execution:
            raise ValueError(f"Record {index} violates assembly => execution")
        if is_signature and not is_execution:
            raise ValueError(f"Record {index} violates signature => execution")
        if is_ordered is not None and is_ordered and not is_signature:
            raise ValueError(f"Record {index} violates ordered => signature")
        if is_parameter is not None and is_parameter and not bool(is_ordered):
            raise ValueError(f"Record {index} violates parameter => ordered")
        execution += int(is_execution)
        if is_assembly is not None:
            assembly += int(is_assembly)
            assembly_without_signature += int(is_assembly and not is_signature)
            signature_without_assembly += int(is_signature and not is_assembly)
        signature += int(is_signature)
        if is_ordered is None and is_execution:
            ordered_available = False
        elif is_ordered is not None:
            ordered += int(is_ordered)
        if is_parameter is None and is_execution:
            parameter_available = False
        elif is_parameter is not None:
            parameter += int(is_parameter)

    cells = len(materialized)
    if assembly_seen not in (0, cells):
        raise ValueError(
            "Assembly admissibility must be present for every evaluation record "
            "or omitted from all records"
        )
    assembly_count = assembly if assembly_seen == cells else None
    gap = execution - signature
    execution_to_assembly_attrition = (
        execution - assembly_count if assembly_count is not None else None
    )
    as_gap = assembly_count - signature if assembly_count is not None else None
    identifiable_payload = identifiable or {}
    id_cells = identifiable_payload.get("n")
    id_execution = identifiable_payload.get("execution_count")
    id_signature = identifiable_payload.get("structural_count")
    id_disagreement = identifiable_payload.get("execution_structure_gap_count")
    return BenchmarkSummary(
        cells=cells,
        models=len(models),
        prompts=len(prompts),
        execution_count=execution,
        signature_count=signature,
        ordered_count=ordered if ordered_available and ordered_seen else None,
        parameter_count=parameter if parameter_available and parameter_seen else None,
        es_gap_count=gap,
        execution_rate=execution / cells,
        signature_rate=signature / cells,
        es_gap_rate=gap / cells,
        executable_signature_disagreement_rate=(gap / execution if execution else None),
        identifiable_cells=int(id_cells) if id_cells is not None else None,
        identifiable_execution_count=(
            int(id_execution) if id_execution is not None else None
        ),
        identifiable_signature_count=(
            int(id_signature) if id_signature is not None else None
        ),
        identifiable_disagreement_count=(
            int(id_disagreement) if id_disagreement is not None else None
        ),
        structural_hallucination_rate=(
            int(id_disagreement) / int(id_execution)
            if id_execution and id_disagreement is not None
            else None
        ),
        assembly_count=assembly_count,
        assembly_rate=(assembly_count / cells if assembly_count is not None else None),
        execution_to_assembly_attrition_count=execution_to_assembly_attrition,
        execution_to_assembly_attrition_rate=(
            execution_to_assembly_attrition / cells
            if execution_to_assembly_attrition is not None
            else None
        ),
        as_gap_count=as_gap,
        as_gap_rate=(as_gap / cells if as_gap is not None else None),
        assembly_without_signature_count=(
            assembly_without_signature if assembly_count is not None else None
        ),
        signature_without_assembly_count=(
            signature_without_assembly if assembly_count is not None else None
        ),
        as_gap_share_of_es_gap=(
            as_gap / gap
            if as_gap is not None and gap
            else None
        ),
    )


def _load_identifiable(release_dir: Path) -> Mapping[str, Any]:
    path = (
        release_dir
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_prompt_identifiability_sensitivity.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["identifiable_sensitivity"]


def _load_identifiable_exclusions(release_dir: Path) -> tuple[str, ...]:
    path = (
        release_dir
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_prompt_identifiability_sensitivity.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(sorted(str(row["prompt_id"]) for row in payload["exceptions"]))


def _with_identifiable_summary(
    rows: list[Mapping[str, Any]],
    *,
    excluded_prompt_ids: tuple[str, ...],
) -> BenchmarkSummary:
    excluded = set(excluded_prompt_ids)
    identifiable_rows = [
        row for row in rows if str(row.get("prompt_id") or "") not in excluded
    ]
    if not identifiable_rows:
        raise ValueError(
            "The comparison prompt set contains no prompts under the frozen "
            "identifiability policy"
        )
    identifiable = summarize_evaluation_records(identifiable_rows)
    payload = {
        "n": identifiable.cells,
        "execution_count": identifiable.execution_count,
        "structural_count": identifiable.signature_count,
        "execution_structure_gap_count": identifiable.es_gap_count,
    }
    return summarize_evaluation_records(rows, identifiable=payload)


def _load_frozen_evaluation_rows(release_dir: Path) -> list[dict[str, Any]]:
    path = (
        release_dir
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_ordered_operand_cell_audit.jsonl"
    )
    return list(iter_jsonl(path))


def _load_frozen_prompt_ids(release_dir: Path) -> tuple[str, ...]:
    path = (
        release_dir
        / "artifacts"
        / "test_split_154"
        / "pqid_bench_external_generation_prompts_154.jsonl"
    )
    prompt_ids: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(iter_jsonl(path), start=1):
        prompt_id = str(row.get("prompt_id") or "")
        if not prompt_id:
            raise ValueError(f"Frozen prompt record {index} lacks prompt_id")
        if prompt_id in seen:
            raise ValueError(f"Duplicate frozen prompt_id: {prompt_id}")
        seen.add(prompt_id)
        prompt_ids.append(prompt_id)
    return tuple(sorted(prompt_ids))


def prepare_comparison(
    release_dir: Path,
    candidate_rows: Iterable[Mapping[str, Any]],
    *,
    allow_partial: bool,
) -> tuple[BenchmarkSummary, BenchmarkSummary, ComparisonScope]:
    """Align a candidate evaluation with the frozen prompt denominator."""

    release_dir = release_dir.resolve()
    rows = list(candidate_rows)
    base_candidate = summarize_evaluation_records(rows)
    frozen_prompt_ids = _load_frozen_prompt_ids(release_dir)
    frozen_prompt_set = set(frozen_prompt_ids)

    prompts_by_model: dict[str, set[str]] = {}
    for row in rows:
        model = str(row["model"])
        prompts_by_model.setdefault(model, set()).add(str(row["prompt_id"]))
    model_prompt_sets = list(prompts_by_model.values())
    candidate_prompt_set = model_prompt_sets[0]
    if any(prompt_set != candidate_prompt_set for prompt_set in model_prompt_sets[1:]):
        raise ValueError(
            "Candidate models do not share one common prompt denominator"
        )

    unknown = sorted(candidate_prompt_set - frozen_prompt_set)
    missing = sorted(frozen_prompt_set - candidate_prompt_set)
    if unknown:
        raise ValueError(
            "Candidate contains prompt IDs outside the frozen test set: "
            + ", ".join(unknown)
        )
    if missing and not allow_partial:
        raise ValueError(
            "Candidate prompt denominator does not match the frozen 154-prompt "
            f"test set; missing {len(missing)} prompt IDs. Use --allow-partial "
            "only for an explicitly labelled matched-subset comparison."
        )

    selected_prompt_ids = tuple(sorted(candidate_prompt_set))
    if not selected_prompt_ids:
        raise ValueError("Candidate comparison prompt set is empty")
    frozen_rows = [
        row
        for row in _load_frozen_evaluation_rows(release_dir)
        if str(row["prompt_id"]) in candidate_prompt_set
    ]
    exclusions = _load_identifiable_exclusions(release_dir)
    candidate = _with_identifiable_summary(
        rows,
        excluded_prompt_ids=exclusions,
    )
    frozen = _with_identifiable_summary(
        frozen_rows,
        excluded_prompt_ids=exclusions,
    )
    digest = hashlib.sha256(
        ("\n".join(selected_prompt_ids) + "\n").encode("utf-8")
    ).hexdigest()
    scope = ComparisonScope(
        mode="matched_subset" if missing else "full_test_set",
        prompt_count=len(selected_prompt_ids),
        prompt_ids_sha256=digest,
        prompt_ids=selected_prompt_ids,
        candidate_models=base_candidate.models,
        candidate_cells=base_candidate.cells,
        frozen_models=frozen.models,
        frozen_cells=frozen.cells,
        identifiable_exclusions=exclusions,
    )
    return candidate, frozen, scope


def reproduce_release(release_dir: Path) -> BenchmarkSummary:
    release_dir = release_dir.resolve()
    audit_path = (
        release_dir
        / "artifacts"
        / "analysis_154"
        / "pqid_bench_ordered_operand_cell_audit.jsonl"
    )
    return summarize_evaluation_records(
        iter_jsonl(audit_path),
        identifiable=_load_identifiable(release_dir),
    )


def validate_canonical_summary(summary: BenchmarkSummary) -> tuple[str, ...]:
    observed = {
        "cells": summary.cells,
        "models": summary.models,
        "prompts": summary.prompts,
        "execution": summary.execution_count,
        "assembly": summary.assembly_count,
        "signature": summary.signature_count,
        "ordered": summary.ordered_count,
        "parameter": summary.parameter_count,
        "execution_to_assembly_attrition": (
            summary.execution_to_assembly_attrition_count
        ),
        "as_gap": summary.as_gap_count,
        "assembly_without_signature": summary.assembly_without_signature_count,
        "signature_without_assembly": summary.signature_without_assembly_count,
        "identifiable_cells": summary.identifiable_cells,
        "identifiable_execution": summary.identifiable_execution_count,
        "identifiable_signature": summary.identifiable_signature_count,
        "identifiable_disagreement": summary.identifiable_disagreement_count,
    }
    return tuple(
        f"{key}: expected {expected}, observed {observed.get(key)}"
        for key, expected in CANONICAL_COUNTS.items()
        if key in observed and observed.get(key) != expected
    )


def validate_repeatability(release_dir: Path) -> tuple[str, ...]:
    path = (
        release_dir
        / "artifacts"
        / "stochastic_repeatability_21x72"
        / "consolidated"
        / "analysis"
        / "pqid_bench_stochastic_repeatability_cell_outcomes.csv"
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    observed = {
        "repeatability_cells": len(rows),
        "repeatability_models": len({row["model"] for row in rows}),
        "repeatability_prompts": len({row["prompt_id"] for row in rows}),
        "repeatability_runs": len({row["run"] for row in rows}),
    }
    return tuple(
        f"{key}: expected {CANONICAL_COUNTS[key]}, observed {value}"
        for key, value in observed.items()
        if value != CANONICAL_COUNTS[key]
    )
