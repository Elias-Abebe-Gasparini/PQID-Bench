"""Build the supplemental release/readiness accounting panel for PQID-Bench."""

from __future__ import annotations

import json
import math
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

from publication_figure_style import PUBLICATION_SERIF_FONT_STACK


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
FIGURES_DIR = ROOT / "figures"

READINESS_JSON = ARTIFACTS_DIR / "pqid_bench_readiness_and_packaging_report.json"
MUTATION_JSON = ARTIFACTS_DIR / "pqid_bench_mutation_stress_baseline_report.json"

OUTPUT_SVG = FIGURES_DIR / "supplemental_release_readiness_accounting_panel.svg"
OUTPUT_PNG = FIGURES_DIR / "supplemental_release_readiness_accounting_panel.png"
CAPTION_PATH = FIGURES_DIR / "supplemental_release_readiness_accounting_panel_caption.md"

WIDTH = 1500
HEIGHT = 900
MARGIN = 46

TEXT = "#18212b"
MUTED = "#526071"
GRID = "#d8e0e8"
PUBLIC = "#0f766e"
OBLIG = "#74a7a1"
REVIEW = "#e0a13a"
INTERNAL = "#b91c1c"
BLUE = "#315f9e"
PURPLE = "#6d4c8d"
PAPER = "#ffffff"
PANEL_BG = "#f8fafc"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_int(value: int | float) -> str:
    return f"{int(value):,}"


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def svg_tag(name: str, attrs: dict[str, object] | None = None, content: str | None = None) -> str:
    attrs = attrs or {}
    attr_text = "".join(f' {key}="{escape(str(value))}"' for key, value in attrs.items())
    if content is None:
        return f"<{name}{attr_text}/>"
    return f"<{name}{attr_text}>{content}</{name}>"


def svg_text(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 18,
    weight: int | str = 400,
    fill: str = TEXT,
    anchor: str = "start",
) -> str:
    return svg_tag(
        "text",
        {
            "x": round(x, 2),
            "y": round(y, 2),
            "font-family": PUBLICATION_SERIF_FONT_STACK,
            "font-size": size,
            "font-weight": weight,
            "fill": fill,
            "text-anchor": anchor,
        },
        escape(value),
    )


def svg_wrapped(
    x: float,
    y: float,
    value: str,
    *,
    width: int = 72,
    size: int = 17,
    line_height: int = 22,
    fill: str = MUTED,
) -> str:
    parts = []
    for i, line in enumerate(textwrap.wrap(value, width=width)):
        parts.append(svg_text(x, y + i * line_height, line, size=size, fill=fill))
    return "\n".join(parts)


def svg_rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = PAPER,
    stroke: str = GRID,
    rx: int = 8,
    stroke_width: float = 1.5,
) -> str:
    return svg_tag(
        "rect",
        {
            "x": round(x, 2),
            "y": round(y, 2),
            "width": round(w, 2),
            "height": round(h, 2),
            "rx": rx,
            "fill": fill,
            "stroke": stroke,
            "stroke-width": stroke_width,
        },
    )


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
        Path("C:/Windows/Fonts/timesbi.ttf" if bold else "C:/Windows/Fonts/timesi.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    *,
    wrap: int,
    fill: str,
    size: int,
    line_height: int,
) -> None:
    x, y = xy
    for i, line in enumerate(textwrap.wrap(value, width=wrap)):
        draw.text((x, y + i * line_height), line, fill=fill, font=font(size))


def release_rows(readiness: dict) -> list[tuple[str, int, dict[str, int]]]:
    dist = readiness["target_distribution"]
    buckets = readiness["slice_by_release_bucket"]
    labels = [
        ("strict n/8", "strict_n8"),
        ("extended n/8", "extended_n8"),
        ("validated broad", "validated_broad_n8"),
        ("validated master", "validated_master_only"),
        ("mutation stress", "mutation_stress_n8"),
        ("tier-2 diagnostic", "tier2_unvalidated"),
    ]
    return [(label, int(dist[key]), {name: int(value) for name, value in buckets[key].items()}) for label, key in labels]


def best_mutation_result(mutation: dict) -> dict:
    name = mutation["best_fair_baseline"]
    return next(row for row in mutation["results"] if row["name"] == name)


def build_svg(readiness: dict, mutation: dict) -> str:
    rows = release_rows(readiness)
    best = best_mutation_result(mutation)
    best_metrics = best["metrics"]
    test_counts = mutation["test_counts"]

    clean = readiness["target_distribution"]["strict_n8"] + readiness["target_distribution"]["extended_n8"]
    broad = readiness["target_distribution"]["validated_broad_n8"] + readiness["target_distribution"]["validated_master_only"]
    stress = readiness["target_distribution"]["mutation_stress_n8"]
    diagnostic = readiness["target_distribution"]["tier2_unvalidated"]

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
        svg_tag("title", {"id": "title"}, "Supplemental release and readiness accounting panel"),
        svg_tag(
            "desc",
            {"id": "desc"},
            "Release bucket composition, readiness view counts, and mutation-stress detector checks for PQID-Bench.",
        ),
        svg_rect(0, 0, WIDTH, HEIGHT, fill=PAPER, stroke=PAPER, rx=0, stroke_width=0),
        svg_text(MARGIN, 54, "Supplemental release and readiness accounting", size=31, weight=800),
        svg_wrapped(
            MARGIN,
            86,
            "This supplemental panel expands the release-accounting evidence behind Table S1 and the mutation-stress sanity check behind Table S15; it is not the main-text routing schematic.",
            width=130,
            size=18,
            line_height=24,
        ),
    ]

    # Panel A: release bucket composition.
    ax, ay, aw, ah = MARGIN, 150, 910, 425
    parts += [
        svg_rect(ax, ay, aw, ah, fill=PANEL_BG, stroke="#cbd5e1"),
        svg_text(ax + 22, ay + 34, "A. Release-bucket composition by benchmark view", size=22, weight=800),
        svg_text(ax + 22, ay + 63, "Bars show the effective release view used for the benchmark package.", size=16, fill=MUTED),
    ]
    legend = [
        ("public open", PUBLIC),
        ("with obligations", OBLIG),
        ("review required", REVIEW),
        ("restricted/internal", INTERNAL),
    ]
    lx = ax + 520
    for i, (label, color) in enumerate(legend):
        x = lx + (i % 2) * 188
        y = ay + 68 + (i // 2) * 21
        parts.append(svg_rect(x, y, 16, 11, fill=color, stroke=color, rx=2, stroke_width=0))
        parts.append(svg_text(x + 22, y + 11, label, size=13, fill=MUTED))

    bar_x = ax + 270
    bar_w = 500
    bar_h = 30
    y0 = ay + 124
    bucket_order = [
        ("public_open", PUBLIC),
        ("public_open_with_obligations", OBLIG),
        ("public_review_required", REVIEW),
        ("restricted_internal_only", INTERNAL),
    ]
    for i, (label, total, buckets) in enumerate(rows):
        y = y0 + i * 49
        parts.append(svg_text(ax + 24, y + 22, label, size=17, weight=700))
        parts.append(svg_text(ax + 218, y + 22, fmt_int(total), size=15, fill=MUTED, anchor="end"))
        x = bar_x
        for bucket, color in bucket_order:
            value = buckets.get(bucket, 0)
            segment = bar_w * (value / total) if total else 0
            if segment > 0:
                parts.append(svg_rect(x, y, max(segment, 1.5), bar_h, fill=color, stroke=color, rx=0, stroke_width=0))
            x += segment
        parts.append(svg_rect(bar_x, y, bar_w, bar_h, fill="none", stroke="#94a3b8", rx=5, stroke_width=1.2))
        open_share = buckets["public_open"] / total if total else 0
        parts.append(svg_text(bar_x + bar_w + 16, y + 22, f"{pct(open_share)} open", size=15, fill=MUTED))

    # Panel B: view roles.
    bx, by, bw, bh = 990, 150, 464, 425
    parts += [
        svg_rect(bx, by, bw, bh, fill=PANEL_BG, stroke="#cbd5e1"),
        svg_text(bx + 22, by + 34, "B. Readiness views are task-specific", size=22, weight=800),
        svg_wrapped(
            bx + 22,
            by + 64,
            "Counts are not interpreted as one flat generation benchmark. Each view is routed to a different evidence role.",
            width=45,
            size=16,
            line_height=21,
        ),
    ]
    cards = [
        ("clean generation", clean, "strict + extended n/8 rows; live model and retrieval-copy tests", PUBLIC),
        ("broader validated", broad, "repair, explanation, and future expansion material", BLUE),
        ("mutation stress", stress, "robustness and stress-detection material", "#c2410c"),
        ("diagnostic rows", diagnostic, "non-clean rows used for diagnosis, not as generation targets", PURPLE),
    ]
    for i, (name, count, detail, color) in enumerate(cards):
        cy = by + 132 + i * 69
        parts.append(svg_rect(bx + 22, cy, bw - 44, 54, fill=PAPER, stroke="#d7e0e8", rx=7, stroke_width=1.2))
        parts.append(svg_text(bx + 40, cy + 23, name, size=17, weight=800, fill=color))
        parts.append(svg_text(bx + bw - 40, cy + 23, fmt_int(count), size=18, weight=800, fill=color, anchor="end"))
        parts.append(svg_text(bx + 40, cy + 43, detail, size=13, fill=MUTED))

    # Panel C: mutation-stress fair baseline.
    cx, cy, cw, ch = MARGIN, 610, 1408, 225
    parts += [
        svg_rect(cx, cy, cw, ch, fill=PANEL_BG, stroke="#cbd5e1"),
        svg_text(cx + 22, cy + 34, "C. Mutation-stress separation check", size=22, weight=800),
        svg_text(
            cx + 22,
            cy + 64,
            "Fair baselines exclude direct mutation aliases; the best code-token detector separates stress rows from clean controls with no false-clean errors.",
            size=16,
            fill=MUTED,
        ),
    ]
    metric_cards = [
        ("clean controls", fmt_int(test_counts["clean_control"]), "test rows", PUBLIC),
        ("mutation stress", fmt_int(test_counts["mutation_stress"]), "test rows", "#c2410c"),
        ("macro-F1", pct(best_metrics["macro_f1"]), "code-token Naive Bayes", BLUE),
        ("false-clean rate", pct(best_metrics["false_clean_rate"]), "stress rows mislabeled clean", INTERNAL),
        ("AUROC", f"{best_metrics['auroc']:.4f}", "best fair baseline", PURPLE),
    ]
    card_w = 252
    for i, (title, value, subtitle, color) in enumerate(metric_cards):
        mx = cx + 24 + i * 274
        parts.append(svg_rect(mx, cy + 92, card_w, 92, fill=PAPER, stroke="#d7e0e8", rx=8, stroke_width=1.2))
        parts.append(svg_text(mx + 18, cy + 119, title, size=16, weight=800, fill=color))
        parts.append(svg_text(mx + 18, cy + 154, value, size=25, weight=800, fill=TEXT))
        parts.append(svg_wrapped(mx + 18, cy + 177, subtitle, width=26, size=12, line_height=15, fill=MUTED))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build_png(readiness: dict, mutation: dict) -> Image.Image:
    rows = release_rows(readiness)
    best = best_mutation_result(mutation)
    best_metrics = best["metrics"]
    test_counts = mutation["test_counts"]

    clean = readiness["target_distribution"]["strict_n8"] + readiness["target_distribution"]["extended_n8"]
    broad = readiness["target_distribution"]["validated_broad_n8"] + readiness["target_distribution"]["validated_master_only"]
    stress = readiness["target_distribution"]["mutation_stress_n8"]
    diagnostic = readiness["target_distribution"]["tier2_unvalidated"]

    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((MARGIN, 25), "Supplemental release and readiness accounting", fill=TEXT, font=font(34, bold=True))
    draw_wrapped(
        draw,
        (MARGIN, 72),
        "This supplemental panel expands the release-accounting evidence behind Table S1 and the mutation-stress sanity check behind Table S15; it is not the main-text routing schematic.",
        wrap=132,
        fill=MUTED,
        size=19,
        line_height=24,
    )

    # Panel A.
    ax, ay, aw, ah = MARGIN, 150, 910, 425
    draw.rounded_rectangle((ax, ay, ax + aw, ay + ah), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((ax + 22, ay + 16), "A. Release-bucket composition by benchmark view", fill=TEXT, font=font(24, bold=True))
    draw.text((ax + 22, ay + 48), "Bars show the effective release view used for the benchmark package.", fill=MUTED, font=font(16))
    legend = [("public open", PUBLIC), ("with obligations", OBLIG), ("review required", REVIEW), ("restricted/internal", INTERNAL)]
    lx = ax + 520
    for i, (label, color) in enumerate(legend):
        x = lx + (i % 2) * 188
        y = ay + 68 + (i // 2) * 21
        draw.rectangle((x, y, x + 16, y + 11), fill=color)
        draw.text((x + 22, y - 2), label, fill=MUTED, font=font(13))

    bar_x = ax + 270
    bar_w = 500
    bar_h = 30
    y0 = ay + 124
    bucket_order = [
        ("public_open", PUBLIC),
        ("public_open_with_obligations", OBLIG),
        ("public_review_required", REVIEW),
        ("restricted_internal_only", INTERNAL),
    ]
    for i, (label, total, buckets) in enumerate(rows):
        y = y0 + i * 49
        draw.text((ax + 24, y + 4), label, fill=TEXT, font=font(18, bold=True))
        total_txt = fmt_int(total)
        draw.text((ax + 218 - draw.textlength(total_txt, font=font(15)), y + 7), total_txt, fill=MUTED, font=font(15))
        x = bar_x
        for bucket, color in bucket_order:
            value = buckets.get(bucket, 0)
            segment = bar_w * (value / total) if total else 0
            if segment > 0:
                draw.rectangle((x, y, x + max(segment, 1.5), y + bar_h), fill=color)
            x += segment
        draw.rounded_rectangle((bar_x, y, bar_x + bar_w, y + bar_h), radius=5, outline="#94a3b8", width=1)
        open_share = buckets["public_open"] / total if total else 0
        draw.text((bar_x + bar_w + 16, y + 6), f"{pct(open_share)} open", fill=MUTED, font=font(15))

    # Panel B.
    bx, by, bw, bh = 990, 150, 464, 425
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((bx + 22, by + 16), "B. Readiness views are task-specific", fill=TEXT, font=font(24, bold=True))
    draw_wrapped(
        draw,
        (bx + 22, by + 53),
        "Counts are not interpreted as one flat generation benchmark. Each view is routed to a different evidence role.",
        wrap=46,
        fill=MUTED,
        size=16,
        line_height=21,
    )
    cards = [
        ("clean generation", clean, "strict + extended n/8 rows; live model and retrieval-copy tests", PUBLIC),
        ("broader validated", broad, "repair, explanation, and future expansion material", BLUE),
        ("mutation stress", stress, "robustness and stress-detection material", "#c2410c"),
        ("diagnostic rows", diagnostic, "non-clean rows used for diagnosis, not as generation targets", PURPLE),
    ]
    for i, (name, count, detail, color) in enumerate(cards):
        yy = by + 132 + i * 69
        draw.rounded_rectangle((bx + 22, yy, bx + bw - 22, yy + 54), radius=7, fill=PAPER, outline="#d7e0e8", width=1)
        draw.text((bx + 40, yy + 8), name, fill=color, font=font(18, bold=True))
        value = fmt_int(count)
        draw.text((bx + bw - 40 - draw.textlength(value, font=font(19, bold=True)), yy + 8), value, fill=color, font=font(19, bold=True))
        draw.text((bx + 40, yy + 33), detail, fill=MUTED, font=font(13))

    # Panel C.
    cx, cy, cw, ch = MARGIN, 610, 1408, 225
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((cx + 22, cy + 16), "C. Mutation-stress separation check", fill=TEXT, font=font(24, bold=True))
    draw.text(
        (cx + 22, cy + 48),
        "Fair baselines exclude direct mutation aliases; the best code-token detector separates stress rows from clean controls with no false-clean errors.",
        fill=MUTED,
        font=font(16),
    )
    metric_cards = [
        ("clean controls", fmt_int(test_counts["clean_control"]), "test rows", PUBLIC),
        ("mutation stress", fmt_int(test_counts["mutation_stress"]), "test rows", "#c2410c"),
        ("macro-F1", pct(best_metrics["macro_f1"]), "code-token Naive Bayes", BLUE),
        ("false-clean rate", pct(best_metrics["false_clean_rate"]), "stress rows mislabeled clean", INTERNAL),
        ("AUROC", f"{best_metrics['auroc']:.4f}", "best fair baseline", PURPLE),
    ]
    card_w = 252
    for i, (title, value, subtitle, color) in enumerate(metric_cards):
        mx = cx + 24 + i * 274
        draw.rounded_rectangle((mx, cy + 92, mx + card_w, cy + 184), radius=8, fill=PAPER, outline="#d7e0e8", width=1)
        draw.text((mx + 18, cy + 108), title, fill=color, font=font(17, bold=True))
        draw.text((mx + 18, cy + 139), value, fill=TEXT, font=font(27, bold=True))
        draw_wrapped(draw, (mx + 18, cy + 169), subtitle, wrap=26, fill=MUTED, size=12, line_height=15)

    return image


def build_caption(readiness: dict, mutation: dict) -> str:
    clean = readiness["target_distribution"]["strict_n8"] + readiness["target_distribution"]["extended_n8"]
    stress = readiness["target_distribution"]["mutation_stress_n8"]
    diagnostic = readiness["target_distribution"]["tier2_unvalidated"]
    best = best_mutation_result(mutation)
    metrics = best["metrics"]
    return "\n".join(
        [
            "# Supplemental Release/Readiness Accounting Caption",
            "",
            "**Supplemental Figure S1. Release and readiness accounting for PQID-Bench.** "
            "Panel A reports the effective release-bucket composition for each benchmark view, separating current repository-cleared release status from the older raw source-metadata audit reported in Supplemental Table S1. "
            f"Panel B summarizes the task-specific readiness views: `{fmt_int(clean)}` clean generation rows, `{fmt_int(stress)}` mutation-stress rows, and `{fmt_int(diagnostic)}` tier-2 diagnostic rows. "
            f"Panel C reports the fair mutation-stress separation check after direct mutation aliases are excluded; the best fair baseline is `{best['name']}` with macro-F1 `{pct(metrics['macro_f1'])}`, AUROC `{metrics['auroc']:.4f}`, and false-clean rate `{pct(metrics['false_clean_rate'])}`.",
            "",
            "Source artifacts:",
            "",
            f"- `{READINESS_JSON.relative_to(ROOT).as_posix()}`",
            f"- `{MUTATION_JSON.relative_to(ROOT).as_posix()}`",
            f"- `scripts/{Path(__file__).name}`",
            "",
        ]
    )


def run() -> None:
    readiness = load_json(READINESS_JSON)
    mutation = load_json(MUTATION_JSON)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_SVG.write_text(build_svg(readiness, mutation), encoding="utf-8")
    build_png(readiness, mutation).save(OUTPUT_PNG)
    CAPTION_PATH.write_text(build_caption(readiness, mutation), encoding="utf-8")
    print(f"wrote {OUTPUT_SVG}")
    print(f"wrote {OUTPUT_PNG}")
    print(f"wrote {CAPTION_PATH}")


if __name__ == "__main__":
    run()
