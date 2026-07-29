"""Build diagnostic figure panels for PQID-Bench complexity and failures."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from acm_figure_style import ACM_SERIF_FONT_STACK


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
ARTIFACTS_DIR = ROOT / "artifacts"
FIGURES_DIR = ROOT / "figures"

COMPLEXITY_JSON = ARTIFACTS_DIR / "analysis_154/pqid_bench_complexity_difficulty_analysis.json"
FAILURE_JSON = ARTIFACTS_DIR / "analysis_154/pqid_bench_item_failure_matrix_analysis.json"

COMPLEXITY_SVG = FIGURES_DIR / "complexity_difficulty_panel.svg"
COMPLEXITY_CAPTION = FIGURES_DIR / "complexity_difficulty_panel_caption.md"
FAILURE_SVG = FIGURES_DIR / "failure_taxonomy_panel.svg"
FAILURE_CAPTION = FIGURES_DIR / "failure_taxonomy_panel_caption.md"


TEXT = "#1f2933"
MUTED = "#64748b"
GRID = "#edf2f7"
AXIS = "#516174"
PANEL_BG = "#ffffff"
TEAL = "#1f766d"
GOLD = "#b7791f"
RUST = "#b45309"
BLUE = "#315a9f"
PLUM = "#7c3f72"
LIGHT_TEAL = "#d9f0eb"
LIGHT_GOLD = "#f7e7c4"
LIGHT_BLUE = "#dbe7fb"
LIGHT_RUST = "#f4d5c4"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.1f} pp"


def tag(name: str, attrs: dict[str, object] | None = None, content: str | None = None) -> str:
    attrs = attrs or {}
    attr_text = "".join(f' {key}="{escape(str(value))}"' for key, value in attrs.items())
    if content is None:
        return f"<{name}{attr_text}/>"
    return f"<{name}{attr_text}>{content}</{name}>"


def text(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 16,
    weight: int = 400,
    fill: str = TEXT,
    anchor: str = "start",
) -> str:
    return tag(
        "text",
        {
            "x": round(x, 2),
            "y": round(y, 2),
            "font-size": size,
            "font-weight": weight,
            "fill": fill,
            "text-anchor": anchor,
            "font-family": ACM_SERIF_FONT_STACK,
        },
        escape(value),
    )


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str = "none",
    rx: int = 0,
    stroke_width: float = 1,
) -> str:
    return tag(
        "rect",
        {
            "x": round(x, 2),
            "y": round(y, 2),
            "width": round(width, 2),
            "height": round(height, 2),
            "rx": rx,
            "fill": fill,
            "stroke": stroke,
            "stroke-width": stroke_width,
        },
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = GRID, width: float = 1) -> str:
    return tag(
        "line",
        {
            "x1": round(x1, 2),
            "y1": round(y1, 2),
            "x2": round(x2, 2),
            "y2": round(y2, 2),
            "stroke": stroke,
            "stroke-width": width,
        },
    )


def panel_title(x: float, y: float, label: str, title: str) -> list[str]:
    return [
        text(x, y, label, size=16, weight=800, fill=BLUE),
        text(x + 30, y, title, size=21, weight=800),
    ]


def bar_label(value: float) -> str:
    return f"{value * 100.0:.0f}%"


def display_family_label(value: str) -> str:
    mapping = {
        "arithmetic_toffoli": "Arithmetic / Toffoli",
        "bell_or_superdense": "Bell / Superdense",
        "deep_mixed_rotation": "Deep Mixed Rotation",
        "deutsch_jozsa": "Deutsch-Jozsa",
        "error_correction": "Error Correction",
        "generic_or_low_level": "Generic / Low Level",
        "oracle_logic": "Oracle Logic",
        "pauli_measurement": "Pauli Measurement",
        "teleportation": "Teleportation",
    }
    if value in mapping:
        return mapping[value]
    cleaned = value.replace("_or_", " / ").replace("_", " ")
    return " ".join(cleaned.split()).title()


def write_complexity_panel(data: dict) -> None:
    width = 1120
    height = 620
    margin = 34
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "PQID-Bench complexity-conditioned difficulty panel"),
        tag(
            "desc",
            {"id": "desc"},
            "Panel summarizing how reference-signature match changes with gate diversity, feature presence, and complexity descriptors.",
        ),
        rect(0, 0, width, height, fill=PANEL_BG),
    ]

    # Panel A: gate diversity execution vs structural bars.
    x0, y0 = 40, 48
    lines.extend(panel_title(x0, y0, "A", "Gate-type diversity"))
    chart_x, chart_y = x0, y0 + 34
    chart_w, row_h = 440, 46
    diversity_rows = data["by_gate_diversity"]
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        tx = chart_x + 128 + tick * 250
        lines.append(line(tx, chart_y - 6, tx, chart_y + len(diversity_rows) * row_h + 4, stroke=GRID))
        lines.append(text(tx, chart_y - 12, f"{int(tick * 100)}", size=12, fill=MUTED, anchor="middle"))
    for idx, row in enumerate(diversity_rows):
        y = chart_y + idx * row_h
        lines.append(text(chart_x, y + 22, row["group"], size=15, weight=600))
        execution = row["execution_success"]
        structural = row["structural_all_match"]
        bx = chart_x + 128
        lines.append(rect(bx, y + 4, 250 * execution, 15, fill=LIGHT_TEAL, rx=3))
        lines.append(rect(bx, y + 25, 250 * structural, 15, fill=TEAL, rx=3))
        lines.append(text(bx + 250 * execution + 7, y + 17, bar_label(execution), size=12, fill=MUTED))
        lines.append(text(bx + 250 * structural + 7, y + 38, bar_label(structural), size=12, fill=TEXT))
    lines.append(rect(chart_x + 128, chart_y + len(diversity_rows) * row_h + 22, 12, 12, fill=LIGHT_TEAL))
    lines.append(text(chart_x + 146, chart_y + len(diversity_rows) * row_h + 32, "execution", size=12, fill=MUTED))
    lines.append(rect(chart_x + 228, chart_y + len(diversity_rows) * row_h + 22, 12, 12, fill=TEAL))
    lines.append(text(chart_x + 246, chart_y + len(diversity_rows) * row_h + 32, "reference-signature match", size=12, fill=MUTED))

    # Panel B: feature contrasts.
    x1, y1 = 590, 48
    lines.extend(panel_title(x1, y1, "B", "Feature-presence signature contrast"))
    features = [
        ("has_barrier", "barrier"),
        ("has_controlled_or_entangling", "controlled/entangling"),
        ("has_rotation", "rotation"),
        ("has_measure", "measurement"),
    ]
    feature_rows = data["by_boolean_feature"]
    row_lookup: dict[tuple[str, str], dict] = {
        (row["feature"], row["group"]): row for row in feature_rows
    }
    base_x, base_y = x1, y1 + 38
    axis_x = base_x + 250
    scale = 260
    lines.append(line(axis_x, base_y - 12, axis_x, base_y + 178, stroke="#9aa8b6", width=1.35))
    lines.append(text(axis_x, base_y - 18, "0 pp", size=12, fill=MUTED, anchor="middle"))
    lines.append(text(axis_x - 130, base_y - 18, "-50", size=12, fill=MUTED, anchor="middle"))
    lines.append(text(axis_x + 130, base_y - 18, "+50", size=12, fill=MUTED, anchor="middle"))
    for idx, (feature, label) in enumerate(features):
        no = row_lookup[(feature, "False")]["structural_all_match"]
        yes = row_lookup[(feature, "True")]["structural_all_match"]
        delta = yes - no
        y = base_y + idx * 44
        dx = delta * scale
        color = RUST if delta < 0 else TEAL
        lines.append(text(base_x, y + 5, label, size=15, weight=600))
        lines.append(line(axis_x, y, axis_x + dx, y, stroke=color, width=7))
        lines.append(tag("circle", {"cx": round(axis_x + dx, 2), "cy": y, "r": 5, "fill": color}))
        lines.append(text(axis_x + dx + (10 if delta >= 0 else -10), y + 4, pp(delta), size=12, fill=color, anchor="start" if delta >= 0 else "end"))

    # Panel C: correlations.
    x2, y2 = 40, 330
    lines.extend(panel_title(x2, y2, "C", "Correlation with per-prompt signature rate"))
    corr_rows = data["feature_correlations_with_prompt_structural_rate"]
    corr_labels = {
        "num_qubits": "qubits",
        "num_clbits": "classical bits",
        "gate_count": "gate count",
        "gate_type_count": "gate types",
        "gate_entropy": "gate entropy",
    }
    corr_x = x2 + 260
    corr_y = y2 + 46
    corr_scale = 180
    lines.append(line(corr_x, corr_y - 22, corr_x, corr_y + 200, stroke="#9aa8b6", width=1.35))
    lines.append(text(corr_x - corr_scale, corr_y - 28, "-1", size=12, fill=MUTED, anchor="middle"))
    lines.append(text(corr_x, corr_y - 28, "0", size=12, fill=MUTED, anchor="middle"))
    lines.append(text(corr_x + corr_scale, corr_y - 28, "+1", size=12, fill=MUTED, anchor="middle"))
    for idx, (key, value) in enumerate(corr_rows.items()):
        y = corr_y + idx * 34
        color = PLUM if value < 0 else TEAL
        end_x = corr_x + value * corr_scale
        lines.append(text(x2, y + 5, corr_labels.get(key, key), size=15, weight=600))
        lines.append(line(corr_x, y, end_x, y, stroke=color, width=6.5))
        lines.append(tag("circle", {"cx": round(end_x, 2), "cy": y, "r": 5, "fill": color}))
        lines.append(text(end_x + (10 if value >= 0 else -10), y + 4, f"{value:.3f}", size=12, fill=color, anchor="start" if value >= 0 else "end"))

    # Panel D: hardest examples summary.
    x3, y3 = 590, 330
    lines.extend(panel_title(x3, y3, "D", "Hardest item families"))
    hard = data["hardest_prompts"][:6]
    for idx, row in enumerate(hard):
        y = y3 + 42 + idx * 34
        family = row["families"][0] if row["families"] else "generic"
        label = f"{row['prompt_id'][-4:]}  {display_family_label(family)}"
        detail = f"q={row['num_qubits']}, c={row['num_clbits']}, gates={row['gate_count']}, types={row['gate_type_count']}, match={pct(row['structural_rate'])}"
        lines.append(rect(x3, y - 18, 485, 29, fill="#fbfdff", stroke="#dce5ee", rx=4))
        lines.append(text(x3 + 12, y + 2, label, size=13, weight=600))
        lines.append(text(x3 + 225, y + 2, detail, size=12, fill=MUTED))

    lines.append("</svg>")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    COMPLEXITY_SVG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_failure_label(label: str) -> str:
    mapping = {
        "structural_match": "signature match",
        "gate_types_mismatch": "gate-type mismatch",
        "num_clbits_mismatch": "classical-bit mismatch",
        "num_qubits_mismatch": "qubit-count mismatch",
        "gate_count_mismatch": "gate-count mismatch",
        "qasm3_export_failure": "QASM3 export failure",
        "no_circuit_found": "no circuit found",
        "empty_generation": "empty generation",
    }
    if label.startswith("execution_failure:"):
        return "execution: " + label.split(":", 1)[1]
    return mapping.get(label, label)


def write_failure_panel(data: dict) -> None:
    width = 1120
    height = 620
    margin = 34
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "PQID-Bench failure taxonomy panel"),
        tag(
            "desc",
            {"id": "desc"},
            "Panel summarizing execution-structure gap, primary failures, component mismatches, and item difficulty buckets.",
        ),
        rect(0, 0, width, height, fill=PANEL_BG),
    ]

    # Panel A: conditional fidelity.
    x0, y0 = 40, 48
    lines.extend(panel_title(x0, y0, "A", "Execution-structure gap"))
    overall = data["overall"]
    metrics = [
        ("execution", overall["execution_success"], TEAL),
        ("QASM3", overall["qasm3_success"], BLUE),
        ("signature", overall["structural_all_match"], GOLD),
        ("M | E", overall["structural_given_execution"], RUST),
        ("wrong | E", overall["runnable_wrong_given_execution"], PLUM),
    ]
    bar_x = x0 + 128
    bar_y = y0 + 36
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        tx = bar_x + tick * 270
        lines.append(line(tx, bar_y - 10, tx, bar_y + len(metrics) * 42, stroke=GRID))
        lines.append(text(tx, bar_y - 16, f"{int(tick * 100)}", size=12, fill=MUTED, anchor="middle"))
    for idx, (label, value, color) in enumerate(metrics):
        y = bar_y + idx * 42
        lines.append(text(x0, y + 18, label, size=15, weight=600))
        lines.append(rect(bar_x, y + 3, 270 * value, 18, fill=color, rx=4))
        lines.append(text(bar_x + 270 * value + 8, y + 18, bar_label(value), size=12, fill=TEXT))

    # Panel B: primary outcomes.
    x1, y1 = 590, 48
    lines.extend(panel_title(x1, y1, "B", "Primary outcome / failure"))
    total = data["evaluation_count"]
    primary = list(data["primary_failure_counts"].items())[:6]
    max_count = max(count for _, count in primary)
    bx = x1 + 178
    by = y1 + 38
    for idx, (label, count) in enumerate(primary):
        y = by + idx * 38
        share = count / total
        color = TEAL if label == "structural_match" else RUST if "execution" in label else GOLD
        lines.append(text(x1, y + 14, normalize_failure_label(label), size=13, weight=600))
        lines.append(rect(bx, y, 250 * count / max_count, 18, fill=color, rx=4))
        lines.append(text(bx + 250 * count / max_count + 8, y + 14, f"{count} ({bar_label(share)})", size=12, fill=TEXT))

    # Panel C: component mismatches.
    x2, y2 = 40, 330
    lines.extend(panel_title(x2, y2, "C", "Component mismatches among nonmatches"))
    all_counts = data["component_mismatch_counts_among_all_nonmatches"]
    executed_counts = data["component_mismatch_counts_among_executed_nonmatches"]
    components = [
        ("gate_types_match", "gate types"),
        ("num_clbits_match", "classical bits"),
        ("gate_count_match", "gate count"),
        ("num_qubits_match", "qubits"),
    ]
    max_component = max(all_counts.values())
    cx = x2 + 130
    cy = y2 + 42
    for idx, (key, label) in enumerate(components):
        y = cy + idx * 48
        all_count = all_counts.get(key, 0)
        exec_count = executed_counts.get(key, 0)
        lines.append(text(x2, y + 17, label, size=15, weight=600))
        lines.append(rect(cx, y, 310 * all_count / max_component, 15, fill=LIGHT_GOLD, rx=3))
        lines.append(rect(cx, y + 20, 310 * exec_count / max_component, 15, fill=GOLD, rx=3))
        lines.append(text(cx + 316, y + 12, str(all_count), size=12, fill=MUTED))
        lines.append(text(cx + 316, y + 32, str(exec_count), size=12, fill=TEXT))
    lines.append(rect(cx, cy + len(components) * 48 + 12, 12, 12, fill=LIGHT_GOLD))
    lines.append(text(cx + 18, cy + len(components) * 48 + 22, "all nonmatches", size=12, fill=MUTED))
    lines.append(rect(cx + 128, cy + len(components) * 48 + 12, 12, 12, fill=GOLD))
    lines.append(text(cx + 146, cy + len(components) * 48 + 22, "executed nonmatches", size=12, fill=MUTED))

    # Panel D: item difficulty buckets.
    x3, y3 = 590, 330
    lines.extend(panel_title(x3, y3, "D", "Held-out prompt difficulty buckets"))
    buckets = [
        ("universal_hard", "solved by 0 models", RUST),
        ("mixed_disagreement", "mixed disagreement", BLUE),
        ("universal_easy", "solved by all models", TEAL),
        ("frontier_only", "frontier-only solves", PLUM),
        ("non_frontier_only", "non-frontier-only solves", GOLD),
    ]
    counts = data["item_bucket_counts"]
    max_bucket = max(counts.values())
    dx = x3 + 176
    dy = y3 + 42
    for idx, (key, label, color) in enumerate(buckets):
        y = dy + idx * 42
        count = counts.get(key, 0)
        lines.append(text(x3, y + 15, label, size=15, weight=600))
        lines.append(rect(dx, y, 260 * count / max_bucket if max_bucket else 0, 18, fill=color, rx=4))
        lines.append(text(dx + 260 * count / max_bucket + 8 if max_bucket else dx + 8, y + 15, str(count), size=12, fill=TEXT))
    mixed_count = counts.get("mixed_disagreement", 0)
    prompt_count = data.get("prompt_count", 70)
    lines.append(text(x3, dy + len(buckets) * 42 + 18, f"{mixed_count}/{prompt_count} prompts in mixed disagreement.", size=13, fill=MUTED))

    lines.append("</svg>")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    FAILURE_SVG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_captions(complexity: dict, failure: dict) -> None:
    diversity = {row["group"]: row for row in complexity["by_gate_diversity"]}
    low = diversity["1-2 gate types"]["structural_all_match"]
    high = diversity["5+ gate types"]["structural_all_match"]
    barrier_rows = {
        row["group"]: row
        for row in complexity["by_boolean_feature"]
        if row["feature"] == "has_barrier"
    }
    barrier_delta = barrier_rows["True"]["structural_all_match"] - barrier_rows["False"]["structural_all_match"]
    corr = complexity["feature_correlations_with_prompt_structural_rate"]
    evaluation_count = failure["evaluation_count"]
    prompt_count = failure["prompt_count"]
    model_count = failure["model_count"]
    mixed_count = failure["item_bucket_counts"]["mixed_disagreement"]
    COMPLEXITY_CAPTION.write_text(
        "\n".join(
            [
                "# Complexity-Difficulty Panel Caption",
                "",
                "**Supplemental Figure S2. Complexity-conditioned external-generation difficulty.** The panel summarizes `{}` prompt-model evaluations over `{}` held-out prompts and `{}` completed model rows. Gate-type diversity is the strongest difficulty signal: targets with `1-2` gate types have reference-signature match `{}` while targets with `5+` gate types fall to `{}`. Barriers produce a `{}` signature-match contrast, and the strongest negative correlations with per-prompt reference-signature rate are gate entropy (`r={:.3f}`) and gate-type count (`r={:.3f}`).".format(
                    evaluation_count,
                    prompt_count,
                    model_count,
                    pct(low),
                    pct(high),
                    pp(barrier_delta),
                    corr["gate_entropy"],
                    corr["gate_type_count"],
                ),
                "",
                "Source artifact: `artifacts/analysis_154/pqid_bench_complexity_difficulty_analysis.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    overall = failure["overall"]
    primary = failure["primary_failure_counts"]
    FAILURE_CAPTION.write_text(
        "\n".join(
            [
                "# Failure-Taxonomy Panel Caption",
                "",
                "**Supporting failure-taxonomy panel.** Across `{}` prompt-model evaluations, execution succeeds in `{}` but reference-signature match succeeds in only `{}`. Conditional on execution, signature match is `{}`, leaving `{}` of executable outputs runnable but signature-wrong. The largest nonmatch class is gate-type mismatch (`{}` primary cases; `{}` component failures among all nonmatches), and `{} / {}` held-out prompts fall in the mixed-disagreement region where some models succeed and others fail.".format(
                    evaluation_count,
                    pct(overall["execution_success"]),
                    pct(overall["structural_all_match"]),
                    pct(overall["structural_given_execution"]),
                    pct(overall["runnable_wrong_given_execution"]),
                    primary.get("gate_types_mismatch", 0),
                    failure["component_mismatch_counts_among_all_nonmatches"].get("gate_types_match", 0),
                    mixed_count,
                    prompt_count,
                ),
                "",
                "Source artifact: `artifacts/analysis_154/pqid_bench_item_failure_matrix_analysis.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    complexity = load_json(COMPLEXITY_JSON)
    failure = load_json(FAILURE_JSON)
    write_complexity_panel(complexity)
    write_failure_panel(failure)
    write_captions(complexity, failure)
    print(f"Wrote {COMPLEXITY_SVG}")
    print(f"Wrote {COMPLEXITY_CAPTION}")
    print(f"Wrote {FAILURE_SVG}")
    print(f"Wrote {FAILURE_CAPTION}")


if __name__ == "__main__":
    main()
