"""Interactive, deterministic visual reports for PQID-Bench results."""

from __future__ import annotations

import csv
import html
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metrics import reproduce_release

MODEL_AUDIT_PATH = Path(
    "artifacts/analysis_154/pqid_bench_operational_assembly_layer_audit.json"
)
ORDERED_AUDIT_PATH = Path(
    "artifacts/analysis_154/pqid_bench_ordered_operand_validation.json"
)
REPEATABILITY_PATH = Path(
    "artifacts/stochastic_repeatability_21x72/consolidated/analysis/"
    "pqid_bench_stochastic_repeatability_model_summary.csv"
)
PROVIDER_LABELS = {
    "anthropic": "Anthropic",
    "deepseek": "DeepSeek",
    "github_models": "GitHub Models",
    "google": "Google",
    "groq": "Groq",
    "huggingface_router": "Hugging Face",
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
}


@dataclass(frozen=True, slots=True)
class DashboardData:
    """Validated data used by the static interactive explorer."""

    summary: dict[str, Any]
    models: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "models": list(self.models),
        }


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON document: {path}") from exc
    if not isinstance(payload, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return payload


def _resolve_recorded_path(release_dir: Path, recorded_path: str) -> Path:
    normalized = recorded_path.replace("\\", "/")
    marker = "artifacts/"
    if marker not in normalized:
        raise ValueError(f"Recorded audit path lacks {marker!r}: {recorded_path}")
    candidate = release_dir / normalized[normalized.index(marker) :]
    if not candidate.is_file():
        raise FileNotFoundError(f"Audit source report not found: {candidate}")
    return candidate


def _report_metrics(report: dict[str, Any]) -> dict[str, Any]:
    records = report.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("Model evaluator report has no records")

    counts = Counter(
        {
            "execution": 0,
            "assembly": 0,
            "signature": 0,
            "qubits": 0,
            "clbits": 0,
            "gate_count": 0,
            "gate_types": 0,
        }
    )
    model = ""
    provider = ""
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("Model evaluator report contains a non-object record")
        model = str(record.get("model") or model)
        provider = str(record.get("provider") or provider)
        execution = record.get("execution")
        if not isinstance(execution, dict):
            raise TypeError("Evaluator record lacks its execution object")
        is_execution = bool(
            execution.get("execution_success") and execution.get("circuit_found")
        )
        qasm = execution.get("qasm3_export") or {}
        checks = record.get("structural_checks") or {}
        counts["execution"] += int(is_execution)
        counts["assembly"] += int(is_execution and bool(qasm.get("success")))
        counts["signature"] += int(bool(checks.get("all_match")))
        counts["qubits"] += int(bool(checks.get("num_qubits_match")))
        counts["clbits"] += int(bool(checks.get("num_clbits_match")))
        counts["gate_count"] += int(bool(checks.get("gate_count_match")))
        counts["gate_types"] += int(bool(checks.get("gate_types_match")))

    if not model:
        raise ValueError("Model evaluator report does not identify its model")
    denominator = len(records)
    return {
        "reported_model": model,
        "provider": PROVIDER_LABELS.get(provider, provider or "Unknown"),
        "prompts": denominator,
        **{f"{name}_count": value for name, value in counts.items()},
        **{f"{name}_rate": value / denominator for name, value in counts.items()},
    }


def load_dashboard_data(release_dir: Path) -> DashboardData:
    """Load and cross-check the frozen 21-model visualization inputs."""

    release_dir = release_dir.resolve()
    summary = reproduce_release(release_dir).to_dict()
    assembly_audit = _load_json(release_dir / MODEL_AUDIT_PATH)
    ordered_audit = _load_json(release_dir / ORDERED_AUDIT_PATH)

    ordered_by_model = {
        str(row["model"]): row for row in ordered_audit.get("by_model", [])
    }
    repeatability_by_model: dict[str, dict[str, str]] = {}
    repeatability_path = release_dir / REPEATABILITY_PATH
    with repeatability_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            repeatability_by_model[str(row["model"])] = row

    source_reports = assembly_audit.get("source_reports")
    if not isinstance(source_reports, list):
        raise TypeError("Operational-assembly audit lacks source_reports")

    models: list[dict[str, Any]] = []
    for source in source_reports:
        report_path = _resolve_recorded_path(release_dir, str(source["path"]))
        metrics = _report_metrics(_load_json(report_path))
        model = str(source["model"])
        metrics["model"] = model
        ordered = ordered_by_model.get(model)
        repeatability = repeatability_by_model.get(model)
        if ordered is None or repeatability is None:
            raise ValueError(f"Incomplete visualization inputs for model {model!r}")
        denominator = int(metrics["prompts"])
        metrics.update(
            {
                "label": str(ordered["model_label"]),
                "ordered_count": int(ordered["ordered_wire_tape_matches"]),
                "ordered_rate": int(ordered["ordered_wire_tape_matches"])
                / denominator,
                "parameter_count": int(ordered["parameter_aware_tape_matches"]),
                "parameter_rate": int(ordered["parameter_aware_tape_matches"])
                / denominator,
                "repeatability_mean_signature_rate": float(
                    repeatability["mean_signature_rate"]
                ),
                "repeatability_signature_range_pp": float(
                    repeatability["signature_range_pp"]
                ),
                "repeatability_signature_ac1": float(
                    repeatability["signature_gwet_ac1"]
                ),
            }
        )
        models.append(metrics)

    if len(models) != int(summary["models"]):
        raise ValueError(
            f"Expected {summary['models']} model rows; observed {len(models)}"
        )
    for key, metric in (
        ("execution_count", "execution_count"),
        ("assembly_count", "assembly_count"),
        ("signature_count", "signature_count"),
    ):
        observed = sum(int(row[metric]) for row in models)
        if observed != int(summary[key]):
            raise ValueError(
                f"Dashboard aggregate mismatch for {key}: "
                f"expected {summary[key]}, observed {observed}"
            )

    models.sort(
        key=lambda row: (
            -float(row["signature_rate"]),
            -float(row["execution_rate"]),
            str(row["label"]).lower(),
        )
    )
    return DashboardData(summary=summary, models=tuple(models))


def _plotly_modules() -> tuple[Any, Any]:
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
    except ImportError as exc:
        raise RuntimeError(
            "Interactive visualization requires Plotly. Install "
            "'pqid-bench[visualization]' or 'plotly>=6,<7'."
        ) from exc
    return go, pio


def _base_layout(*, height: int) -> dict[str, Any]:
    return {
        "height": height,
        "margin": {"l": 86, "r": 26, "t": 58, "b": 58},
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#ffffff",
        "font": {
            "family": "Arial, Helvetica, sans-serif",
            "size": 13,
            "color": "#171717",
        },
        "hoverlabel": {
            "font": {"family": "Arial, Helvetica, sans-serif", "size": 13},
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "left",
            "x": 0,
        },
    }


def _figures(data: DashboardData) -> list[tuple[str, str, Any]]:
    go, _ = _plotly_modules()
    summary = data.summary
    models = list(reversed(data.models))

    ladder_labels = [
        "Execution E",
        "Assembly A",
        "Signature M<sup>sig</sup>",
        "Ordered M<sup>ord</sup>",
        "Parameter M<sup>par</sup>",
    ]
    ladder_rates = [
        float(summary["execution_rate"]),
        float(summary["assembly_rate"]),
        float(summary["signature_rate"]),
        int(summary["ordered_count"]) / int(summary["cells"]),
        int(summary["parameter_count"]) / int(summary["cells"]),
    ]
    ladder = go.Figure(
        go.Bar(
            x=ladder_labels,
            y=ladder_rates,
            marker={
                "color": ["#13756d", "#2f6690", "#d1495b", "#7a5195", "#4d7c0f"],
                "line": {"color": "#111111", "width": 1.2},
            },
            text=[f"{100 * value:.2f}%" for value in ladder_rates],
            textposition="outside",
            hovertemplate="%{x}: %{y:.2%}<extra></extra>",
        )
    )
    ladder.update_layout(
        **_base_layout(height=410),
        title="Operational admissibility and structural recovery",
        showlegend=False,
        yaxis={
            "title": "Pooled rate",
            "range": [0, 1.04],
            "tickformat": ".0%",
            "gridcolor": "#dddddd",
        },
        xaxis={"title": None},
    )

    model_labels = [str(row["label"]) for row in models]
    profile = go.Figure()
    for key, name, color, symbol in (
        ("execution_rate", "Execution", "#13756d", "circle"),
        ("assembly_rate", "Assembly", "#2f6690", "diamond"),
        ("signature_rate", "Signature", "#d1495b", "square"),
    ):
        profile.add_trace(
            go.Scatter(
                x=[float(row[key]) for row in models],
                y=model_labels,
                mode="markers",
                name=name,
                marker={
                    "color": color,
                    "size": 10,
                    "symbol": symbol,
                    "line": {"color": "#111111", "width": 0.8},
                },
                customdata=[
                    [row["provider"], row["model"]] for row in models
                ],
                hovertemplate=(
                    "<b>%{y}</b><br>%{fullData.name}: %{x:.2%}"
                    "<br>Provider: %{customdata[0]}"
                    "<br>Route: %{customdata[1]}<extra></extra>"
                ),
            )
        )
    profile.update_layout(
        **_base_layout(height=700),
        title="Model-level operational and signature outcomes",
        xaxis={
            "title": "Rate on 154 prompts",
            "range": [0, 1.02],
            "tickformat": ".0%",
            "gridcolor": "#dddddd",
        },
        yaxis={"title": None, "automargin": True},
    )

    heatmap_metrics = [
        ("execution_rate", "E"),
        ("assembly_rate", "A"),
        ("qubits_rate", "Qubits"),
        ("clbits_rate", "Clbits"),
        ("gate_count_rate", "Op. count"),
        ("gate_types_rate", "Count map"),
        ("signature_rate", "M<sup>sig</sup>"),
        ("ordered_rate", "M<sup>ord</sup>"),
        ("parameter_rate", "M<sup>par</sup>"),
    ]
    heatmap = go.Figure(
        go.Heatmap(
            z=[
                [float(row[key]) for key, _ in heatmap_metrics]
                for row in models
            ],
            x=[label for _, label in heatmap_metrics],
            y=model_labels,
            zmin=0,
            zmax=1,
            colorscale=[
                [0.0, "#7f1d1d"],
                [0.35, "#d97706"],
                [0.6, "#f3d34a"],
                [0.8, "#65a30d"],
                [1.0, "#0f766e"],
            ],
            colorbar={"title": "Rate", "tickformat": ".0%"},
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2%}<extra></extra>",
        )
    )
    heatmap.update_layout(
        **_base_layout(height=700),
        title="Component and nested-structure recovery matrix",
        xaxis={"title": None, "side": "top"},
        yaxis={"title": None, "automargin": True},
    )

    repeatability = go.Figure()
    repeatability.add_trace(
        go.Scatter(
            x=[
                float(row["repeatability_mean_signature_rate"])
                for row in models
            ],
            y=model_labels,
            error_x={
                "type": "data",
                "array": [
                    float(row["repeatability_signature_range_pp"]) / 200
                    for row in models
                ],
                "symmetric": True,
                "color": "#111111",
                "thickness": 1.2,
                "width": 4,
            },
            mode="markers",
            marker={
                "color": [
                    float(row["repeatability_signature_ac1"]) for row in models
                ],
                "colorscale": [
                    [0.0, "#d1495b"],
                    [0.5, "#f3d34a"],
                    [1.0, "#13756d"],
                ],
                "cmin": 0,
                "cmax": 1,
                "size": 11,
                "line": {"color": "#111111", "width": 0.8},
                "colorbar": {"title": "Gwet AC1"},
            },
            customdata=[
                [
                    row["repeatability_signature_range_pp"],
                    row["repeatability_signature_ac1"],
                ]
                for row in models
            ],
            hovertemplate=(
                "<b>%{y}</b><br>Three-run mean: %{x:.2%}"
                "<br>Observed range: %{customdata[0]:.2f} pp"
                "<br>Gwet AC1: %{customdata[1]:.3f}<extra></extra>"
            ),
        )
    )
    repeatability.update_layout(
        **_base_layout(height=700),
        title="Three-run signature repeatability",
        showlegend=False,
        xaxis={
            "title": "Mean signature rate; bars show half of the observed range",
            "range": [0, 0.72],
            "tickformat": ".0%",
            "gridcolor": "#dddddd",
        },
        yaxis={"title": None, "automargin": True},
    )

    providers: dict[str, list[dict[str, Any]]] = {}
    for row in data.models:
        providers.setdefault(str(row["provider"]), []).append(row)
    provider_rows = []
    for provider, rows in providers.items():
        provider_rows.append(
            {
                "provider": provider,
                "models": len(rows),
                "execution": sum(float(row["execution_rate"]) for row in rows)
                / len(rows),
                "signature": sum(float(row["signature_rate"]) for row in rows)
                / len(rows),
            }
        )
    provider_rows.sort(key=lambda row: (-row["signature"], row["provider"]))
    provider = go.Figure()
    for key, label, color in (
        ("execution", "Execution", "#13756d"),
        ("signature", "Signature", "#d1495b"),
    ):
        provider.add_trace(
            go.Bar(
                x=[row["provider"] for row in provider_rows],
                y=[row[key] for row in provider_rows],
                name=label,
                marker={"color": color, "line": {"color": "#111111", "width": 0.8}},
                customdata=[[row["models"]] for row in provider_rows],
                hovertemplate=(
                    "%{x}<br>%{fullData.name}: %{y:.2%}"
                    "<br>Routes: %{customdata[0]}<extra></extra>"
                ),
            )
        )
    provider.update_layout(
        **_base_layout(height=480),
        title="Provider-route aggregates",
        barmode="group",
        yaxis={
            "title": "Unweighted mean across model routes",
            "range": [0, 1.03],
            "tickformat": ".0%",
            "gridcolor": "#dddddd",
        },
        xaxis={"title": None, "tickangle": -30},
    )

    return [
        (
            "ladder",
            "Measurement ladder",
            ladder,
        ),
        (
            "models",
            "Model profiles",
            profile,
        ),
        (
            "heatmap",
            "Recovery matrix",
            heatmap,
        ),
        (
            "repeatability",
            "Repeatability",
            repeatability,
        ),
        (
            "providers",
            "Provider aggregates",
            provider,
        ),
    ]


def _metric_html(summary: dict[str, Any]) -> str:
    metrics = (
        ("Models", f"{int(summary['models']):,}"),
        ("Prompts", f"{int(summary['prompts']):,}"),
        ("Execution", f"{100 * float(summary['execution_rate']):.2f}%"),
        ("Assembly", f"{100 * float(summary['assembly_rate']):.2f}%"),
        ("Signature", f"{100 * float(summary['signature_rate']):.2f}%"),
        ("ES-Gap", f"{100 * float(summary['es_gap_rate']):.2f} pp"),
    )
    return "\n".join(
        (
            '<div class="metric">'
            f'<span class="metric-label">{html.escape(label)}</span>'
            f'<strong>{html.escape(value)}</strong>'
            "</div>"
        )
        for label, value in metrics
    )


def _table_html(models: tuple[dict[str, Any], ...]) -> str:
    rows = []
    for row in models:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['label']))}</td>"
            f"<td>{html.escape(str(row['provider']))}</td>"
            f"<td>{100 * float(row['execution_rate']):.2f}%</td>"
            f"<td>{100 * float(row['assembly_rate']):.2f}%</td>"
            f"<td>{100 * float(row['signature_rate']):.2f}%</td>"
            f"<td>{100 * float(row['ordered_rate']):.2f}%</td>"
            f"<td>{100 * float(row['parameter_rate']):.2f}%</td>"
            f"<td>{float(row['repeatability_signature_ac1']):.3f}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_dashboard(
    release_dir: Path,
    output_path: Path,
    *,
    plotlyjs: str = "embed",
) -> DashboardData:
    """Write a standalone interactive report and return its validated data."""

    if plotlyjs not in {"embed", "cdn"}:
        raise ValueError("plotlyjs must be 'embed' or 'cdn'")
    data = load_dashboard_data(release_dir)
    _, pio = _plotly_modules()
    fragments = []
    navigation = []
    include_plotlyjs: bool | str = True if plotlyjs == "embed" else "cdn"
    for index, (slug, label, figure) in enumerate(_figures(data)):
        navigation.append(f'<a href="#{slug}">{html.escape(label)}</a>')
        figure_html = pio.to_html(
            figure,
            full_html=False,
            include_plotlyjs=include_plotlyjs if index == 0 else False,
            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": False,
                "toImageButtonOptions": {
                    "format": "svg",
                    "filename": f"pqid-bench-{slug}",
                },
            },
            div_id=f"pqid-bench-{slug}",
        )
        fragments.append(
            f'<section id="{slug}" class="figure-section">'
            f"<h2>{html.escape(label)}</h2>"
            '<p class="scroll-note">Scroll horizontally to inspect the '
            "complete chart.</p>"
            f'<div class="plot-wrap plot-{slug}">{figure_html}</div>'
            "</section>"
        )

    summary = data.summary
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Interactive PQID-Bench v1.0.0 result explorer">
  <title>PQID-Bench Interactive Explorer</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #171717;
      --muted: #5d6670;
      --line: #c9ced3;
      --surface: #f4f6f7;
      --teal: #13756d;
      --red: #b83245;
    }}
    * {{ box-sizing: border-box; }}
    html {{ max-width: 100%; overflow-x: hidden; scroll-behavior: smooth; }}
    body {{
      margin: 0;
      width: 100vw;
      max-width: 100%;
      overflow-x: hidden;
      color: var(--ink);
      background: #fff;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    header {{
      border-bottom: 3px solid var(--ink);
      padding: 2rem max(1.2rem, calc((100vw - 1180px) / 2));
    }}
    header p {{
      width: 100%;
      max-width: 860px;
      overflow-wrap: anywhere;
      color: var(--muted);
      margin-bottom: 0;
    }}
    h1 {{ margin: 0; font-size: clamp(1.9rem, 4vw, 3rem); letter-spacing: 0; }}
    h2 {{ font-size: 1.35rem; letter-spacing: 0; margin: 0 0 .8rem; }}
    nav {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      gap: .35rem;
      overflow-x: auto;
      padding: .65rem max(1.2rem, calc((100vw - 1180px) / 2));
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, .97);
    }}
    nav a {{
      color: var(--ink);
      font-size: .9rem;
      font-weight: 700;
      padding: .4rem .55rem;
      text-decoration: none;
      white-space: nowrap;
    }}
    nav a:hover, nav a:focus {{ color: var(--teal); text-decoration: underline; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 1.4rem 1.2rem 3rem; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      border: 1px solid var(--line);
      margin-bottom: 1.6rem;
    }}
    .metric {{ min-width: 0; padding: .8rem; border-right: 1px solid var(--line); }}
    .metric:last-child {{ border-right: 0; }}
    .metric-label {{ display: block; color: var(--muted); font-size: .78rem; }}
    .metric strong {{ display: block; font-size: 1.2rem; margin-top: .15rem; }}
    .figure-section {{ padding: 1.5rem 0; border-top: 1px solid var(--line); }}
    .plot-wrap {{
      max-width: 100%;
      overflow-x: auto;
      overscroll-behavior-inline: contain;
      -webkit-overflow-scrolling: touch;
    }}
    .plotly-graph-div {{ width: 100% !important; }}
    .scroll-note {{
      display: none;
      color: var(--muted);
      font-size: .82rem;
      margin: -.25rem 0 .45rem;
    }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); }}
    table {{ border-collapse: collapse; min-width: 820px; width: 100%; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: .55rem .65rem; }}
    th {{ text-align: left; background: var(--surface); }}
    td:nth-child(n+3) {{ text-align: right; font-variant-numeric: tabular-nums; }}
    footer {{
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: .86rem;
      padding: 1rem max(1.2rem, calc((100vw - 1180px) / 2));
    }}
    @media (max-width: 760px) {{
      header, nav, main, footer {{ width: 100vw; max-width: 100vw; }}
      header p {{ width: 20rem; max-width: calc(100vw - 3rem); }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .metric {{ border-bottom: 1px solid var(--line); }}
      .metric:nth-child(2n) {{ border-right: 0; }}
      header {{ padding-top: 1.3rem; }}
      .scroll-note {{ display: block; }}
      .plot-wrap .plotly-graph-div {{ min-width: 840px; }}
      .plot-ladder .plotly-graph-div {{ min-width: 700px; }}
      .plot-providers .plotly-graph-div {{ min-width: 760px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>PQID-Bench Interactive Explorer</h1>
    <p>
      Frozen v{html.escape(str(summary['benchmark_release']))} evidence,
      rendered from archived evaluation records. Hover, zoom, isolate traces,
      and download SVG views without contacting a model provider.
    </p>
  </header>
  <nav aria-label="Explorer sections">
    {''.join(navigation)}
    <a href="#data-table">Data table</a>
  </nav>
  <main>
    <section class="metrics" aria-label="Headline metrics">
      {_metric_html(summary)}
    </section>
    {''.join(fragments)}
    <section id="data-table" class="figure-section">
      <h2>Model-level data</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th><th>Provider route</th><th>Execution</th>
              <th>Assembly</th><th>Signature</th><th>Ordered</th>
              <th>Parameter</th><th>Signature AC1</th>
            </tr>
          </thead>
          <tbody>{_table_html(data.models)}</tbody>
        </table>
      </div>
    </section>
  </main>
  <footer>
    PQID-Bench package {html.escape(str(summary['package_version']))};
    evaluator {html.escape(str(summary['evaluator_version']))};
    predicate {html.escape(str(summary['predicate_version']))}.
    Interactive views are descriptive interfaces over the frozen artifacts.
  </footer>
</body>
</html>
"""
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")
    return data


def ecosystem_flow_svg() -> str:
    """Return the package-ecosystem workflow as an accessible SVG."""

    stages = (
        ("PQID source", "734 clean rows", "#dbeafe"),
        ("Frozen split", "514 / 66 / 154", "#dcfce7"),
        ("Model routes", "21 completed", "#fef3c7"),
        ("Docker replay", "E / A / M", "#fee2e2"),
        ("Reports", "JSON / text / CSV", "#ede9fe"),
        ("Explorer", "Plotly / Pages", "#ccfbf1"),
    )
    boxes = []
    arrows = []
    for index, (title, subtitle, fill) in enumerate(stages):
        x = 25 + index * 195
        boxes.append(
            f'<rect x="{x}" y="58" width="165" height="92" rx="6" '
            f'fill="{fill}" stroke="#111111" stroke-width="2"/>'
            f'<text x="{x + 82.5}" y="94" text-anchor="middle" '
            f'font-size="18" font-weight="700">{html.escape(title)}</text>'
            f'<text x="{x + 82.5}" y="123" text-anchor="middle" '
            f'font-size="14">{html.escape(subtitle)}</text>'
        )
        if index < len(stages) - 1:
            arrows.append(
                f'<line x1="{x + 165}" y1="104" x2="{x + 190}" y2="104" '
                'stroke="#111111" stroke-width="2" marker-end="url(#arrow)"/>'
            )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="210" '
        'viewBox="0 0 1200 210" role="img" '
        'aria-labelledby="title description">'
        '<title id="title">PQID-Bench reproducibility workflow</title>'
        '<desc id="description">Six stages connect the PQID source to the '
        'interactive evidence explorer.</desc>'
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" '
        'refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" '
        'fill="#111111"/></marker></defs>'
        '<rect width="1200" height="210" fill="#ffffff"/>'
        '<text x="25" y="30" font-family="Arial, Helvetica, sans-serif" '
        'font-size="18" font-weight="700">From governed data to inspectable '
        'evidence</text>'
        f'<g font-family="Arial, Helvetica, sans-serif" fill="#171717">'
        f'{"".join(arrows)}{"".join(boxes)}</g></svg>'
    )


def measurement_ladder_svg(summary: dict[str, Any]) -> str:
    """Return a compact static fallback for the five-layer result ladder."""

    cells = int(summary["cells"])
    stages = (
        ("E", "Execution", int(summary["execution_count"]), "#dbeafe"),
        ("A", "Assembly", int(summary["assembly_count"]), "#ccfbf1"),
        (
            "M sig",
            "Signature",
            int(summary["signature_count"]),
            "#fee2e2",
        ),
        ("M ord", "Ordered", int(summary["ordered_count"]), "#ede9fe"),
        (
            "M par",
            "Parameter",
            int(summary["parameter_count"]),
            "#dcfce7",
        ),
    )
    boxes = []
    arrows = []
    for index, (symbol, label, count, fill) in enumerate(stages):
        x = 28 + index * 232
        boxes.append(
            f'<rect x="{x}" y="50" width="192" height="120" rx="6" '
            f'fill="{fill}" stroke="#111111" stroke-width="2"/>'
            f'<text x="{x + 96}" y="84" text-anchor="middle" font-size="25" '
            f'font-weight="700">{symbol}</text>'
            f'<text x="{x + 96}" y="111" text-anchor="middle" '
            f'font-size="15">{html.escape(label)}</text>'
            f'<text x="{x + 96}" y="145" text-anchor="middle" font-size="22" '
            f'font-weight="700">{100 * count / cells:.2f}%</text>'
        )
        if index < len(stages) - 1:
            arrows.append(
                f'<line x1="{x + 192}" y1="110" x2="{x + 225}" y2="110" '
                'stroke="#111111" stroke-width="2" marker-end="url(#arrow)"/>'
            )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="215" '
        'viewBox="0 0 1200 215" role="img" '
        'aria-labelledby="title description">'
        '<title id="title">PQID-Bench operational and structural ladder</title>'
        '<desc id="description">Rates decrease from executable programs through '
        'assembly admissibility to increasingly strict structural recovery.</desc>'
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" '
        'refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" '
        'fill="#111111"/></marker></defs>'
        '<rect width="1200" height="215" fill="#ffffff"/>'
        f'<g font-family="Arial, Helvetica, sans-serif" fill="#171717">'
        f'{"".join(arrows)}{"".join(boxes)}</g></svg>'
    )


def benchmark_split_svg(
    *,
    train: int = 514,
    validation: int = 66,
    test: int = 154,
) -> str:
    """Return an accessible pie chart for the frozen benchmark split."""

    segments = (
        ("Train", train, "#7cc5e8"),
        ("Validation", validation, "#f2c86b"),
        ("Test", test, "#80c58a"),
    )
    total = sum(count for _, count, _ in segments)
    if total <= 0 or any(count < 0 for _, count, _ in segments):
        raise ValueError("Split counts must be nonnegative with a positive total")

    center_x = 300
    center_y = 215
    radius = 145
    angle = -math.pi / 2
    slices = []
    legend = []
    for index, (label, count, fill) in enumerate(segments):
        next_angle = angle + (2 * math.pi * count / total)
        x1 = center_x + radius * math.cos(angle)
        y1 = center_y + radius * math.sin(angle)
        x2 = center_x + radius * math.cos(next_angle)
        y2 = center_y + radius * math.sin(next_angle)
        large_arc = 1 if next_angle - angle > math.pi else 0
        slices.append(
            f'<path d="M {center_x} {center_y} L {x1:.3f} {y1:.3f} '
            f'A {radius} {radius} 0 {large_arc} 1 {x2:.3f} {y2:.3f} Z" '
            f'fill="{fill}" stroke="#ffffff" stroke-width="3"/>'
        )
        legend_y = 132 + index * 78
        percentage = 100 * count / total
        legend.append(
            f'<rect x="620" y="{legend_y - 19}" width="28" height="28" rx="3" '
            f'fill="{fill}" stroke="#111111" stroke-width="1.5"/>'
            f'<text x="668" y="{legend_y}" font-size="20" font-weight="700">'
            f'{html.escape(label)}</text>'
            f'<text x="668" y="{legend_y + 25}" font-size="16">'
            f'{count:,} prompts ({percentage:.1f}%)</text>'
        )
        angle = next_angle

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" '
        'viewBox="0 0 1200 420" role="img" '
        'aria-labelledby="title description">'
        '<title id="title">PQID-Bench frozen split composition</title>'
        f'<desc id="description">The {total}-prompt clean generation population '
        f'contains {train} training, {validation} validation, and {test} test '
        'prompts.</desc>'
        '<rect width="1200" height="420" fill="#ffffff"/>'
        '<g font-family="Arial, Helvetica, sans-serif" fill="#171717">'
        '<text x="25" y="34" font-size="20" font-weight="700">Frozen benchmark '
        'composition</text>'
        f'{"".join(slices)}'
        f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="none" '
        'stroke="#111111" stroke-width="2"/>'
        f'{"".join(legend)}'
        f'<text x="620" y="370" font-size="17" font-weight="700">N = {total:,}'
        '</text>'
        '<text x="620" y="394" font-size="15">Deterministic, signature-aware '
        'partition</text>'
        '</g></svg>'
    )


def endpoint_rates_svg(summary: dict[str, Any]) -> str:
    """Return an accessible horizontal bar chart for the five endpoints."""

    cells = int(summary["cells"])
    if cells <= 0:
        raise ValueError("The endpoint denominator must be positive")
    endpoints = (
        ("Python execution (E)", int(summary["execution_count"]), "#7cc5e8"),
        ("Assembly admissibility (A)", int(summary["assembly_count"]), "#63c7bb"),
        ("Signature recovery (M sig)", int(summary["signature_count"]), "#ef9a9a"),
        ("Ordered recovery (M ord)", int(summary["ordered_count"]), "#b9a5e3"),
        ("Parameter recovery (M par)", int(summary["parameter_count"]), "#80c58a"),
    )
    plot_x = 310
    plot_width = 800
    plot_top = 82
    row_gap = 61
    bar_height = 34

    grid = []
    for tick in (0, 25, 50, 75, 100):
        x = plot_x + plot_width * tick / 100
        grid.append(
            f'<line x1="{x:.1f}" y1="58" x2="{x:.1f}" y2="370" '
            'stroke="#d1d5db" stroke-width="1"/>'
            f'<text x="{x:.1f}" y="397" text-anchor="middle" '
            f'font-size="14">{tick}</text>'
        )

    bars = []
    for index, (label, count, fill) in enumerate(endpoints):
        rate = 100 * count / cells
        y = plot_top + index * row_gap
        width = plot_width * rate / 100
        bars.append(
            f'<text x="{plot_x - 18}" y="{y + 24}" text-anchor="end" '
            f'font-size="17">{html.escape(label)}</text>'
            f'<rect x="{plot_x}" y="{y}" width="{width:.2f}" '
            f'height="{bar_height}" rx="3" fill="{fill}" '
            'stroke="#111111" stroke-width="1.5"/>'
            f'<text x="{plot_x + width + 12:.2f}" y="{y + 24}" '
            f'font-size="17" font-weight="700">{rate:.2f}%</text>'
        )

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="425" '
        'viewBox="0 0 1200 425" role="img" '
        'aria-labelledby="title description">'
        '<title id="title">PQID-Bench endpoint rates</title>'
        '<desc id="description">Operational admissibility remains above '
        'ninety-one percent, while increasingly strict structural recovery '
        'ranges from approximately forty-eight to fifty-three percent.</desc>'
        '<rect width="1200" height="425" fill="#ffffff"/>'
        '<g font-family="Arial, Helvetica, sans-serif" fill="#171717">'
        '<text x="25" y="30" font-size="20" font-weight="700">Operational '
        'admissibility versus structural recovery</text>'
        f'{"".join(grid)}{"".join(bars)}'
        '<text x="710" y="420" text-anchor="middle" font-size="14">'
        'Rate across 3,234 frozen model-prompt cells (%)</text>'
        '</g></svg>'
    )


def write_site_assets(
    release_dir: Path,
    output_dir: Path,
    *,
    plotlyjs: str = "cdn",
) -> DashboardData:
    """Generate the Pages-only explorer and its static fallback diagrams."""

    output_dir = output_dir.resolve()
    data = build_dashboard(
        release_dir,
        output_dir / "overview.html",
        plotlyjs=plotlyjs,
    )
    assets = output_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "ecosystem-flow.svg").write_text(
        ecosystem_flow_svg(),
        encoding="utf-8",
    )
    (assets / "measurement-ladder.svg").write_text(
        measurement_ladder_svg(data.summary),
        encoding="utf-8",
    )
    split_root = Path(release_dir).resolve() / "data" / "splits"
    split_counts = {
        name: sum(
            1
            for line in (split_root / f"{name}.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
        for name in ("train", "validation", "test")
    }
    (assets / "benchmark-split.svg").write_text(
        benchmark_split_svg(**split_counts),
        encoding="utf-8",
    )
    (assets / "endpoint-rates.svg").write_text(
        endpoint_rates_svg(data.summary),
        encoding="utf-8",
    )
    (output_dir / "dashboard-data.json").write_text(
        json.dumps(data.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return data
