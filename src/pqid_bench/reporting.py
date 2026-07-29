"""Deterministic human-readable and tidy renderers for benchmark reports."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .metrics import BenchmarkSummary


REPORT_FORMATS = ("json", "text", "markdown", "csv")

_VERSION_FIELDS = (
    "package_version",
    "benchmark_release",
    "evaluator_version",
    "predicate_version",
    "schema_version",
    "artifact_manifest_version",
)


@dataclass(frozen=True, slots=True)
class _MetricRow:
    section: str
    metric_key: str
    metric: str
    count: int | None
    denominator: int | None
    rate: float | None
    available: bool = True


def _payload(
    summary: BenchmarkSummary | Mapping[str, Any],
    *,
    run_type: str,
) -> dict[str, Any]:
    if isinstance(summary, Mapping):
        return dict(summary)
    return summary.to_dict(run_type=run_type)


def _ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or not denominator:
        return None
    return numerator / denominator


def _summary_metric_rows(payload: Mapping[str, Any]) -> list[_MetricRow]:
    cells = int(payload["cells"])
    execution = int(payload["execution_count"])
    assembly = _optional_int(payload.get("assembly_count"))
    ordered = payload.get("ordered_count")
    parameter = payload.get("parameter_count")
    rows = [
        _MetricRow("scope", "models", "Models", int(payload["models"]), None, None),
        _MetricRow("scope", "prompts", "Prompts", int(payload["prompts"]), None, None),
        _MetricRow("scope", "cells", "Model-prompt cells", cells, None, None),
        _MetricRow(
            "primary",
            "execution",
            "Execution",
            execution,
            cells,
            float(payload["execution_rate"]),
        ),
        _MetricRow(
            "primary",
            "assembly_admissibility",
            "Quantum-assembly admissibility",
            assembly,
            cells if assembly is not None else None,
            _optional_float(payload.get("assembly_rate")),
            available=assembly is not None,
        ),
        _MetricRow(
            "primary",
            "reference_signature",
            "Reference-signature match",
            int(payload["signature_count"]),
            cells,
            float(payload["signature_rate"]),
        ),
        _MetricRow(
            "primary",
            "ordered_structure",
            "Ordered operation-and-operand tape",
            int(ordered) if ordered is not None else None,
            cells if ordered is not None else None,
            _ratio(int(ordered), cells) if ordered is not None else None,
            available=ordered is not None,
        ),
        _MetricRow(
            "primary",
            "parameter_aware_structure",
            "Parameter-aware ordered tape",
            int(parameter) if parameter is not None else None,
            cells if parameter is not None else None,
            _ratio(int(parameter), cells) if parameter is not None else None,
            available=parameter is not None,
        ),
        _MetricRow(
            "diagnostic",
            "es_gap",
            "ES-Gap",
            int(payload["es_gap_count"]),
            cells,
            float(payload["es_gap_rate"]),
        ),
        _MetricRow(
            "diagnostic",
            "execution_to_assembly_attrition",
            "Execution-to-assembly attrition",
            _optional_int(payload.get("execution_to_assembly_attrition_count")),
            cells if assembly is not None else None,
            _optional_float(
                payload.get("execution_to_assembly_attrition_rate")
            ),
            available=assembly is not None,
        ),
        _MetricRow(
            "diagnostic",
            "as_gap",
            "Assembly-Structure Gap (AS-Gap)",
            _optional_int(payload.get("as_gap_count")),
            cells if assembly is not None else None,
            _optional_float(payload.get("as_gap_rate")),
            available=assembly is not None,
        ),
        _MetricRow(
            "diagnostic",
            "assembly_without_signature",
            "Assembly admissible without signature match",
            _optional_int(payload.get("assembly_without_signature_count")),
            cells if assembly is not None else None,
            _ratio(
                _optional_int(payload.get("assembly_without_signature_count")),
                cells,
            )
            if assembly is not None
            else None,
            available=assembly is not None,
        ),
        _MetricRow(
            "diagnostic",
            "signature_without_assembly",
            "Signature match without assembly admissibility",
            _optional_int(payload.get("signature_without_assembly_count")),
            cells if assembly is not None else None,
            _ratio(
                _optional_int(payload.get("signature_without_assembly_count")),
                cells,
            )
            if assembly is not None
            else None,
            available=assembly is not None,
        ),
        _MetricRow(
            "diagnostic",
            "as_gap_share_of_es_gap",
            "AS-Gap share of ES-Gap",
            _optional_int(payload.get("as_gap_count")),
            int(payload["es_gap_count"]) if assembly is not None else None,
            _optional_float(payload.get("as_gap_share_of_es_gap")),
            available=assembly is not None,
        ),
        _MetricRow(
            "diagnostic",
            "ersd",
            "Executable signature disagreement (ERSD)",
            int(payload["es_gap_count"]),
            execution,
            _optional_float(
                payload.get("executable_signature_disagreement_rate")
            ),
            available=payload.get("executable_signature_disagreement_rate")
            is not None,
        ),
    ]

    identifiable_cells = payload.get("identifiable_cells")
    if identifiable_cells is None:
        return rows

    id_cells = int(identifiable_cells)
    id_execution = _optional_int(payload.get("identifiable_execution_count"))
    id_signature = _optional_int(payload.get("identifiable_signature_count"))
    id_disagreement = _optional_int(payload.get("identifiable_disagreement_count"))
    rows.extend(
        [
            _MetricRow(
                "identifiable",
                "identifiable_cells",
                "Identifiable model-prompt cells",
                id_cells,
                None,
                None,
            ),
            _MetricRow(
                "identifiable",
                "identifiable_execution",
                "Execution",
                id_execution,
                id_cells,
                _ratio(id_execution, id_cells),
                available=id_execution is not None,
            ),
            _MetricRow(
                "identifiable",
                "identifiable_reference_signature",
                "Reference-signature match",
                id_signature,
                id_cells,
                _ratio(id_signature, id_cells),
                available=id_signature is not None,
            ),
            _MetricRow(
                "identifiable",
                "structural_hallucination",
                "Structural hallucination",
                id_disagreement,
                id_execution,
                _optional_float(payload.get("structural_hallucination_rate")),
                available=(
                    id_disagreement is not None
                    and id_execution is not None
                    and payload.get("structural_hallucination_rate") is not None
                ),
            ),
        ]
    )
    return rows


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _count(value: int | None, *, available: bool = True) -> str:
    if not available or value is None:
        return "N/A"
    return f"{value:,}"


def _rate(value: float | None, *, available: bool = True) -> str:
    if not available or value is None:
        return "N/A"
    return f"{100 * value:.2f}%"


def _delta(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{100 * value:+.2f} pp"


def _decimal(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def _ascii_table(
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    right_aligned: set[int] | None = None,
) -> str:
    right_aligned = right_aligned or set()
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    def render_row(row: tuple[str, ...]) -> str:
        cells = []
        for index, value in enumerate(row):
            if index in right_aligned:
                cells.append(value.rjust(widths[index]))
            else:
                cells.append(value.ljust(widths[index]))
        return "  ".join(cells).rstrip()

    separator = tuple("-" * width for width in widths)
    return "\n".join(
        [render_row(headers), render_row(separator), *(render_row(row) for row in rows)]
    )


def _contract_lines(payload: Mapping[str, Any]) -> list[str]:
    labels = {
        "package_version": "Package",
        "benchmark_release": "Benchmark",
        "evaluator_version": "Evaluator",
        "predicate_version": "Predicate",
        "schema_version": "Schema",
        "artifact_manifest_version": "Artifact manifest",
    }
    lines = []
    if payload.get("run_type"):
        lines.append(f"Run type: {payload['run_type']}")
    for field in _VERSION_FIELDS:
        if payload.get(field) is not None:
            lines.append(f"{labels[field]}: {payload[field]}")
    if payload.get("source"):
        lines.append(f"Source: {payload['source']}")
    return lines


def _summary_text(payload: Mapping[str, Any]) -> str:
    rows = _summary_metric_rows(payload)
    scope = [
        (row.metric, _count(row.count, available=row.available))
        for row in rows
        if row.section == "scope"
    ]
    primary = [
        (
            row.metric,
            _count(row.count, available=row.available),
            _count(row.denominator, available=row.available),
            _rate(row.rate, available=row.available),
        )
        for row in rows
        if row.section == "primary"
    ]
    diagnostics = [
        (
            row.metric,
            _count(row.count, available=row.available),
            _count(row.denominator, available=row.available),
            _rate(row.rate, available=row.available),
        )
        for row in rows
        if row.section == "diagnostic"
    ]
    identifiable = [
        (
            row.metric,
            _count(row.count, available=row.available),
            (
                _count(row.denominator, available=row.available)
                if row.denominator is not None
                else ""
            ),
            _rate(row.rate, available=row.available) if row.rate is not None else "",
        )
        for row in rows
        if row.section == "identifiable"
    ]

    parts = [
        "PQID-Bench Evaluation Summary",
        "=============================",
        *_contract_lines(payload),
        "",
        "Scope",
        "-----",
        _ascii_table(("Metric", "Value"), scope, right_aligned={1}),
        "",
        "Primary endpoints",
        "-----------------",
        _ascii_table(
            ("Endpoint", "Count", "Denominator", "Rate"),
            primary,
            right_aligned={1, 2, 3},
        ),
        "",
        "Diagnostics",
        "-----------",
        _ascii_table(
            ("Metric", "Count", "Denominator", "Rate"),
            diagnostics,
            right_aligned={1, 2, 3},
        ),
    ]
    if identifiable:
        parts.extend(
            [
                "",
                "Identifiable subset",
                "-------------------",
                _ascii_table(
                    ("Metric", "Count", "Denominator", "Rate"),
                    identifiable,
                    right_aligned={1, 2, 3},
                ),
            ]
        )
    else:
        parts.extend(
            [
                "",
                "Identifiable subset: not supplied; structural-hallucination "
                "metrics are unavailable.",
            ]
        )

    if "canonical_parity" in payload:
        parts.extend(
            [
                "",
                "Canonical parity: "
                + ("PASS" if payload["canonical_parity"] else "FAIL"),
            ]
        )
    errors = payload.get("errors") or []
    if errors:
        parts.append("Errors:")
        parts.extend(f"- {error}" for error in errors)
    parts.extend(
        [
            "",
            "Rates use the displayed denominator. Unavailable layers are not "
            "treated as zero.",
        ]
    )
    return "\n".join(parts)


def _markdown_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _summary_markdown(payload: Mapping[str, Any]) -> str:
    rows = _summary_metric_rows(payload)
    parts = ["# PQID-Bench Evaluation Summary", ""]
    parts.extend(
        f"- **{line.split(':', 1)[0]}:**{line.split(':', 1)[1]}"
        for line in _contract_lines(payload)
    )
    parts.extend(
        [
            "",
            "## Scope",
            "",
            _markdown_table(
                ("Metric", "Value"),
                [
                    (row.metric, _count(row.count, available=row.available))
                    for row in rows
                    if row.section == "scope"
                ],
            ),
            "",
            "## Primary endpoints",
            "",
            _markdown_table(
                ("Endpoint", "Count", "Denominator", "Rate"),
                [
                    (
                        row.metric,
                        _count(row.count, available=row.available),
                        _count(row.denominator, available=row.available),
                        _rate(row.rate, available=row.available),
                    )
                    for row in rows
                    if row.section == "primary"
                ],
            ),
            "",
            "## Diagnostics",
            "",
            _markdown_table(
                ("Metric", "Count", "Denominator", "Rate"),
                [
                    (
                        row.metric,
                        _count(row.count, available=row.available),
                        _count(row.denominator, available=row.available),
                        _rate(row.rate, available=row.available),
                    )
                    for row in rows
                    if row.section == "diagnostic"
                ],
            ),
        ]
    )
    identifiable = [row for row in rows if row.section == "identifiable"]
    if identifiable:
        parts.extend(
            [
                "",
                "## Identifiable subset",
                "",
                _markdown_table(
                    ("Metric", "Count", "Denominator", "Rate"),
                    [
                        (
                            row.metric,
                            _count(row.count, available=row.available),
                            (
                                _count(row.denominator, available=row.available)
                                if row.denominator is not None
                                else ""
                            ),
                            (
                                _rate(row.rate, available=row.available)
                                if row.rate is not None
                                else ""
                            ),
                        )
                        for row in identifiable
                    ],
                ),
            ]
        )
    else:
        parts.extend(
            [
                "",
                "> Identifiable-subset data were not supplied, so "
                "structural-hallucination metrics are unavailable.",
            ]
        )
    if "canonical_parity" in payload:
        status = "PASS" if payload["canonical_parity"] else "FAIL"
        parts.extend(["", f"**Canonical parity:** {status}"])
    errors = payload.get("errors") or []
    if errors:
        parts.extend(["", "## Errors", ""])
        parts.extend(f"- {error}" for error in errors)
    parts.extend(
        [
            "",
            "_Rates use the displayed denominator. Unavailable layers are not "
            "treated as zero._",
        ]
    )
    return "\n".join(parts)


def summary_rows(
    summary: BenchmarkSummary | Mapping[str, Any],
    *,
    run_type: str = "canonical_reproduction",
) -> list[dict[str, Any]]:
    """Return a tidy, stable row representation of one benchmark summary."""

    payload = _payload(summary, run_type=run_type)
    base = {
        "report_type": "summary",
        "run_type": payload.get("run_type", ""),
        **{field: payload.get(field, "") for field in _VERSION_FIELDS},
        "source": payload.get("source", ""),
        "canonical_parity": payload.get("canonical_parity", ""),
    }
    return [
        {
            **base,
            "section": row.section,
            "metric_key": row.metric_key,
            "metric": row.metric,
            "available": row.available,
            "count": row.count,
            "denominator": row.denominator,
            "rate": row.rate,
            "rate_percent": 100 * row.rate if row.rate is not None else None,
        }
        for row in _summary_metric_rows(payload)
    ]


def _summary_csv(payload: Mapping[str, Any]) -> str:
    rows = summary_rows(payload)
    fieldnames = tuple(rows[0])
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                **row,
                "available": str(bool(row["available"])).lower(),
                "rate": _decimal(row["rate"]),
                "rate_percent": _decimal(row["rate_percent"]),
                "canonical_parity": (
                    str(row["canonical_parity"]).lower()
                    if isinstance(row["canonical_parity"], bool)
                    else row["canonical_parity"]
                ),
            }
        )
    return buffer.getvalue().rstrip("\n")


def _comparison_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidate_payload = payload["candidate"]
    frozen_payload = payload["frozen"]
    candidate_rows = {
        row.metric_key: row for row in _summary_metric_rows(candidate_payload)
    }
    frozen_rows = {
        row.metric_key: row for row in _summary_metric_rows(frozen_payload)
    }
    keys = list(candidate_rows)
    keys.extend(key for key in frozen_rows if key not in candidate_rows)
    base = {
        "report_type": "comparison",
        "run_type": payload.get("run_type", ""),
        **{field: payload.get(field, "") for field in _VERSION_FIELDS},
        "comparison_label": payload.get("comparison_label", ""),
        "candidate_source": payload.get("candidate_source", ""),
    }
    rows = []
    for key in keys:
        candidate = candidate_rows.get(key)
        frozen = frozen_rows.get(key)
        candidate_rate = candidate.rate if candidate and candidate.available else None
        frozen_rate = frozen.rate if frozen and frozen.available else None
        delta_rate = (
            candidate_rate - frozen_rate
            if candidate_rate is not None and frozen_rate is not None
            else None
        )
        template = candidate or frozen
        assert template is not None
        rows.append(
            {
                **base,
                "section": template.section,
                "metric_key": key,
                "metric": template.metric,
                "candidate_available": bool(candidate and candidate.available),
                "candidate_count": candidate.count if candidate else None,
                "candidate_denominator": candidate.denominator if candidate else None,
                "candidate_rate": candidate_rate,
                "frozen_available": bool(frozen and frozen.available),
                "frozen_count": frozen.count if frozen else None,
                "frozen_denominator": frozen.denominator if frozen else None,
                "frozen_rate": frozen_rate,
                "delta_rate": delta_rate,
                "delta_percentage_points": (
                    100 * delta_rate if delta_rate is not None else None
                ),
            }
        )
    return rows


def _count_rate(row: Mapping[str, Any], prefix: str) -> str:
    if not row[f"{prefix}_available"]:
        return "N/A"
    count = row[f"{prefix}_count"]
    denominator = row[f"{prefix}_denominator"]
    rate = row[f"{prefix}_rate"]
    if denominator is None:
        return _count(count)
    return f"{_count(count)}/{_count(denominator)} ({_rate(rate)})"


def _comparison_text(payload: Mapping[str, Any]) -> str:
    rows = _comparison_rows(payload)
    scope = payload["comparison_scope"]
    scope_rows = [
        ("Mode", str(scope["mode"])),
        ("Prompts", f"{int(scope['prompt_count']):,}"),
        ("Candidate models", f"{int(scope['candidate_models']):,}"),
        ("Candidate cells", f"{int(scope['candidate_cells']):,}"),
        ("Frozen models", f"{int(scope['frozen_models']):,}"),
        ("Frozen cells", f"{int(scope['frozen_cells']):,}"),
    ]
    metric_rows = [
        (
            row["metric"],
            _count_rate(row, "candidate"),
            _count_rate(row, "frozen"),
            _delta(row["delta_rate"]) if row["candidate_rate"] is not None else "N/A",
        )
        for row in rows
        if row["section"] != "scope"
    ]
    return "\n".join(
        [
            "PQID-Bench Candidate Comparison",
            "===============================",
            f"Comparison: {payload.get('comparison_label', '')}",
            *_contract_lines(payload),
            f"Candidate source: {payload.get('candidate_source', '')}",
            "",
            "Aligned scope",
            "-------------",
            _ascii_table(("Metric", "Value"), scope_rows, right_aligned={1}),
            "",
            "Outcomes",
            "--------",
            _ascii_table(
                ("Metric", "Candidate", "Frozen", "Delta"),
                metric_rows,
                right_aligned={1, 2, 3},
            ),
            "",
            "Deltas are candidate minus frozen in percentage points. Counts and "
            "rates use the displayed aligned denominators.",
        ]
    )


def _comparison_markdown(payload: Mapping[str, Any]) -> str:
    rows = _comparison_rows(payload)
    scope = payload["comparison_scope"]
    parts = [
        "# PQID-Bench Candidate Comparison",
        "",
        f"- **Comparison:** {payload.get('comparison_label', '')}",
    ]
    parts.extend(
        f"- **{line.split(':', 1)[0]}:**{line.split(':', 1)[1]}"
        for line in _contract_lines(payload)
    )
    parts.extend(
        [
            f"- **Candidate source:** {payload.get('candidate_source', '')}",
            "",
            "## Aligned scope",
            "",
            _markdown_table(
                ("Metric", "Value"),
                [
                    ("Mode", str(scope["mode"])),
                    ("Prompts", f"{int(scope['prompt_count']):,}"),
                    ("Candidate models", f"{int(scope['candidate_models']):,}"),
                    ("Candidate cells", f"{int(scope['candidate_cells']):,}"),
                    ("Frozen models", f"{int(scope['frozen_models']):,}"),
                    ("Frozen cells", f"{int(scope['frozen_cells']):,}"),
                ],
            ),
            "",
            "## Outcomes",
            "",
            _markdown_table(
                ("Metric", "Candidate", "Frozen", "Delta"),
                [
                    (
                        row["metric"],
                        _count_rate(row, "candidate"),
                        _count_rate(row, "frozen"),
                        (
                            _delta(row["delta_rate"])
                            if row["candidate_rate"] is not None
                            else "N/A"
                        ),
                    )
                    for row in rows
                    if row["section"] != "scope"
                ],
            ),
            "",
            "_Deltas are candidate minus frozen in percentage points. Counts and "
            "rates use the displayed aligned denominators._",
        ]
    )
    return "\n".join(parts)


def _comparison_csv(payload: Mapping[str, Any]) -> str:
    rows = _comparison_rows(payload)
    fieldnames = tuple(rows[0])
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                **row,
                "candidate_available": str(row["candidate_available"]).lower(),
                "frozen_available": str(row["frozen_available"]).lower(),
                "candidate_rate": _decimal(row["candidate_rate"]),
                "frozen_rate": _decimal(row["frozen_rate"]),
                "delta_rate": _decimal(row["delta_rate"]),
                "delta_percentage_points": _decimal(
                    row["delta_percentage_points"]
                ),
            }
        )
    return buffer.getvalue().rstrip("\n")


def render_summary(
    summary: BenchmarkSummary | Mapping[str, Any],
    *,
    output_format: str = "text",
    run_type: str = "canonical_reproduction",
) -> str:
    """Render a benchmark summary as JSON, text, Markdown, or tidy CSV."""

    payload = _payload(summary, run_type=run_type)
    _validate_format(output_format)
    if output_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    if output_format == "text":
        return _summary_text(payload)
    if output_format == "markdown":
        return _summary_markdown(payload)
    return _summary_csv(payload)


def render_comparison(
    payload: Mapping[str, Any],
    *,
    output_format: str = "text",
) -> str:
    """Render an aligned candidate-versus-frozen comparison."""

    _validate_format(output_format)
    if output_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    if output_format == "text":
        return _comparison_text(payload)
    if output_format == "markdown":
        return _comparison_markdown(payload)
    return _comparison_csv(payload)


def render_report(
    payload: Mapping[str, Any],
    *,
    output_format: str,
    report_type: str,
) -> str:
    """Dispatch one CLI payload to its deterministic renderer."""

    if report_type == "summary":
        return render_summary(payload, output_format=output_format)
    if report_type == "comparison":
        return render_comparison(payload, output_format=output_format)
    raise ValueError(f"Unsupported report type: {report_type!r}")


def _validate_format(output_format: str) -> None:
    if output_format not in REPORT_FORMATS:
        choices = ", ".join(REPORT_FORMATS)
        raise ValueError(
            f"Unsupported report format {output_format!r}; choose one of: {choices}"
        )
