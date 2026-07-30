"""Build the clean-vs-mutation-stress schematic for the benchmark study."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from acm_figure_style import ACM_SERIF_FONT_STACK


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_DIR = SCRIPT_PATH.parents[1]
PQID_DIR = SCRIPT_PATH.parents[3] if len(SCRIPT_PATH.parents) > 3 else SUBMISSION_DIR
ARTIFACTS_DIR = SUBMISSION_DIR / "artifacts"
FIGURES_DIR = SUBMISSION_DIR / "figures"

READINESS_JSON = PQID_DIR / "data" / "processed" / "pqid_bench_tables" / "pqid_bench_readiness_and_packaging_report.json"
MUTATION_JSON = ARTIFACTS_DIR / "pqid_bench_mutation_stress_baseline_report.json"
SVG_PATH = FIGURES_DIR / "clean_vs_mutation_stress_schematic.svg"
CAPTION_PATH = FIGURES_DIR / "clean_vs_mutation_stress_schematic_caption.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: int | float) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return f"{value:,}"


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def display_source_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PQID_DIR.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def tag(name: str, attrs: dict[str, object] | None = None, content: str | None = None) -> str:
    attrs = attrs or {}
    attr_text = "".join(f' {key}="{escape(str(value))}"' for key, value in attrs.items())
    if content is None:
        return f"<{name}{attr_text}/>"
    return f"<{name}{attr_text}>{content}</{name}>"


def text(x: int, y: int, value: str, *, size: int = 20, weight: int = 400, fill: str = "#1f2933", anchor: str = "start") -> str:
    return tag(
        "text",
        {
            "x": x,
            "y": y,
            "font-size": size,
            "font-weight": weight,
            "fill": fill,
            "text-anchor": anchor,
            "font-family": ACM_SERIF_FONT_STACK,
        },
        escape(value),
    )


def wrapped_text(x: int, y: int, value: str, *, width: int = 42, line_height: int = 22, size: int = 17, fill: str = "#4a5568") -> str:
    parts = []
    for offset, line in enumerate(textwrap.wrap(value, width=width)):
        parts.append(text(x, y + offset * line_height, line, size=size, fill=fill))
    return "\n".join(parts)


def rect(x: int, y: int, width: int, height: int, *, fill: str, stroke: str = "#d6dee6", rx: int = 8, stroke_width: int = 2) -> str:
    return tag(
        "rect",
        {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "rx": rx,
            "fill": fill,
            "stroke": stroke,
            "stroke-width": stroke_width,
        },
    )


def line(x1: int, y1: int, x2: int, y2: int, *, stroke: str = "#64748b", width: int = 3, marker: bool = True) -> str:
    attrs = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": stroke, "stroke-width": width, "fill": "none"}
    if marker:
        attrs["marker-end"] = "url(#arrow)"
    return tag("line", attrs)


def box_with_items(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    fill: str,
    stroke: str,
    eyebrow: str,
    title: str,
    value: str,
    items: list[str],
) -> str:
    parts = [rect(x, y, width, height, fill=fill, stroke=stroke)]
    parts.append(text(x + 24, y + 36, eyebrow.upper(), size=13, weight=700, fill=stroke))
    parts.append(text(x + 24, y + 72, title, size=25, weight=700, fill="#172026"))
    parts.append(text(x + 24, y + 112, value, size=36, weight=800, fill="#172026"))
    item_y = y + 146
    for item in items:
        parts.append(tag("circle", {"cx": x + 31, "cy": item_y - 6, "r": 4, "fill": stroke}))
        parts.append(wrapped_text(x + 44, item_y, item, width=42, line_height=21, size=16, fill="#334155"))
        item_y += 54
    return "\n".join(parts)


def build_svg(readiness: dict, mutation: dict) -> str:
    dist = readiness["target_distribution"]
    release = readiness["slice_by_release_bucket"]
    source_rows = readiness["source_rows"]

    strict = dist["strict_n8"]
    extended = dist["extended_n8"]
    clean = strict + extended
    stress = dist["mutation_stress_n8"]
    broad = dist["validated_broad_n8"]
    master = dist["validated_master_only"]
    diagnostic = dist["tier2_unvalidated"]

    clean_release_cleared = sum(release[label]["public_open"] for label in ("strict_n8", "extended_n8"))
    clean_internal = release["strict_n8"]["restricted_internal_only"] + release["extended_n8"]["restricted_internal_only"]
    stress_public = release["mutation_stress_n8"]["public_open"]

    test_counts = mutation["test_counts"]
    best = next(row for row in mutation["results"] if row["name"] == mutation["best_fair_baseline"])
    best_metrics = best["metrics"]

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="840" viewBox="0 0 1200 840" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "PQID-Bench clean versus mutation-stress routing schematic"),
        tag(
            "desc",
            {"id": "desc"},
            "Schematic separating clean strict and extended benchmark controls from mutation-stress rows, with counts, release status, and detection evidence.",
        ),
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/>',
        "</marker>",
        "</defs>",
        rect(0, 0, 1200, 840, fill="#ffffff", stroke="#ffffff", rx=0, stroke_width=0),
        text(60, 62, "PQID-Bench slice routing: clean controls vs mutation-stress rows", size=29, weight=800, fill="#111827"),
        wrapped_text(
            60,
            96,
            "The benchmark does not flatten all validated and stress material into one generation set; clean controls, mutation-stress rows, and diagnostic material are routed to different tasks.",
            width=110,
            line_height=24,
            size=17,
            fill="#475569",
        ),
        rect(410, 154, 380, 96, fill="#f8fafc", stroke="#94a3b8"),
        text(600, 190, "PQID source rows", size=16, weight=700, fill="#475569", anchor="middle"),
        text(600, 226, fmt(source_rows), size=34, weight=800, fill="#111827", anchor="middle"),
        line(510, 252, 270, 312),
        line(690, 252, 930, 312),
        line(600, 252, 600, 638),
        box_with_items(
            60,
            312,
            470,
            300,
            fill="#ecfdf5",
            stroke="#0f766e",
            eyebrow="clean generation controls",
            title="Strict + extended n/8",
            value=f"{fmt(clean)} rows",
            items=[
                f"strict_n8: {fmt(strict)} rows; extended_n8: {fmt(extended)} rows",
                f"repository-cleared release: {fmt(clean_release_cleared)} rows; internal-only: {fmt(clean_internal)}",
                "used for generation, retrieval, executable validity, and small-circuit checks",
            ],
        ),
        box_with_items(
            670,
            312,
            470,
            300,
            fill="#fff7ed",
            stroke="#c2410c",
            eyebrow="mutation-stress material",
            title="Stress rows stay separate",
            value=f"{fmt(stress)} rows",
            items=[
                f"public-open: {fmt(stress_public)} rows",
                "used for robustness, stress detection, and diagnostic controls",
                "not silently blended into the clean generation target set",
            ],
        ),
        rect(420, 638, 360, 94, fill="#f1f5f9", stroke="#64748b"),
        text(600, 669, "Other non-clean routes", size=18, weight=700, fill="#1f2937", anchor="middle"),
        text(600, 700, f"broader validated: {fmt(broad + master)}", size=16, fill="#334155", anchor="middle"),
        text(600, 724, f"diagnosis-oriented: {fmt(diagnostic)}", size=16, fill="#334155", anchor="middle"),
        rect(60, 638, 300, 94, fill="#f8fafc", stroke="#CBD5E1"),
        text(210, 669, "Clean-control test split", size=18, weight=700, fill="#1f2937", anchor="middle"),
        text(210, 700, f"{fmt(test_counts['clean_control'])} clean test rows", size=16, fill="#334155", anchor="middle"),
        text(210, 724, "group-safe split", size=16, fill="#334155", anchor="middle"),
        rect(840, 638, 300, 94, fill="#f8fafc", stroke="#CBD5E1"),
        text(990, 669, "Mutation-stress test split", size=18, weight=700, fill="#1f2937", anchor="middle"),
        text(990, 700, f"{fmt(test_counts['mutation_stress'])} stress test rows", size=16, fill="#334155", anchor="middle"),
        text(990, 724, "direct aliases excluded", size=16, fill="#334155", anchor="middle"),
        rect(335, 762, 530, 38, fill="#eef2ff", stroke="#4f46e5", rx=8),
        text(
            600,
            787,
            f"Best fair stress detector: macro-F1 {pct(best_metrics['macro_f1'])}, false-clean {pct(best_metrics['false_clean_rate'])}",
            size=16,
            weight=700,
            fill="#312e81",
            anchor="middle",
        ),
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def build_caption(readiness: dict, mutation: dict) -> str:
    dist = readiness["target_distribution"]
    clean = dist["strict_n8"] + dist["extended_n8"]
    stress = dist["mutation_stress_n8"]
    best = next(row for row in mutation["results"] if row["name"] == mutation["best_fair_baseline"])
    metrics = best["metrics"]
    return "\n".join(
        [
            "# Clean vs Mutation-Stress Schematic Caption",
            "",
            "**Figure 1. Clean controls and mutation-stress rows are routed to different PQID-Bench tasks.** "
            f"The clean generation control set contains `{fmt(clean)}` repository-cleared rows (`strict_n8` plus `extended_n8`), "
            f"while `{fmt(stress)}` `mutation_stress_n8` rows are preserved as stress and robustness material rather than blended into the clean generation target set. "
            f"In the mutation-stress detection baseline, the best fair detector is `{best['name']}`, with macro-F1 `{pct(metrics['macro_f1'])}` and false-clean rate `{pct(metrics['false_clean_rate'])}` after direct mutation aliases are excluded.",
            "",
            "Source artifacts:",
            "",
            f"- `{display_source_path(READINESS_JSON)}`",
            f"- `{display_source_path(MUTATION_JSON)}`",
            "",
        ]
    )


def run() -> None:
    readiness = load_json(READINESS_JSON)
    mutation = load_json(MUTATION_JSON)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(build_svg(readiness, mutation), encoding="utf-8")
    CAPTION_PATH.write_text(build_caption(readiness, mutation), encoding="utf-8")
    print(f"Wrote {SVG_PATH.relative_to(SUBMISSION_DIR).as_posix()}")
    print(f"Wrote {CAPTION_PATH.relative_to(SUBMISSION_DIR).as_posix()}")


if __name__ == "__main__":
    run()
