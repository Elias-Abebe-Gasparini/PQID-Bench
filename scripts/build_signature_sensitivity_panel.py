"""Build a supplemental reference-signature sensitivity panel for PQID-Bench."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

from acm_figure_style import ACM_SERIF_FONT_STACK
from pqid_bench_model_registry import MODEL_LABELS


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
FIGURES_DIR = ROOT / "figures"

SIGNATURE_JSON = ARTIFACTS_DIR / "analysis_154/pqid_bench_signature_sensitivity_report.json"

OUTPUT_SVG = FIGURES_DIR / "signature_sensitivity_panel.svg"
OUTPUT_PNG = FIGURES_DIR / "signature_sensitivity_panel.png"
CAPTION_PATH = FIGURES_DIR / "signature_sensitivity_panel_caption.md"

WIDTH = 1500
HEIGHT = 730
CROP_TOP = 120
CROPPED_HEIGHT = HEIGHT - CROP_TOP
MARGIN = 44

TEXT = "#17212f"
MUTED = "#526071"
GRID = "#d8e0e8"
PANEL_BG = "#f8fafc"
PAPER = "#ffffff"
TEAL = "#0f766e"
BLUE = "#315f9e"
RUST = "#b45309"
PLUM = "#6d4c8d"
RED = "#b91c1c"
GOLD = "#a16207"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def pp(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f} pp"


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
    size: int = 18,
    weight: int | str = 400,
    fill: str = TEXT,
    anchor: str = "start",
) -> str:
    return tag(
        "text",
        {
            "x": round(x, 2),
            "y": round(y, 2),
            "font-family": ACM_SERIF_FONT_STACK,
            "font-size": size,
            "font-weight": weight,
            "fill": fill,
            "text-anchor": anchor,
        },
        escape(value),
    )


def wrapped_svg(
    x: float,
    y: float,
    value: str,
    *,
    width: int = 72,
    size: int = 16,
    line_height: int = 22,
    fill: str = MUTED,
) -> str:
    return "\n".join(
        text(x, y + i * line_height, line, size=size, fill=fill)
        for i, line in enumerate(textwrap.wrap(value, width=width))
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = PAPER,
    stroke: str = GRID,
    rx: int = 8,
    stroke_width: float = 1.4,
) -> str:
    return tag(
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
    bold: bool = False,
) -> None:
    x, y = xy
    for i, line_value in enumerate(textwrap.wrap(value, width=wrap)):
        draw.text((x, y + i * line_height), line_value, fill=fill, font=font(size, bold=bold))


def signature_label(group: dict) -> str:
    signature = group["signature"]
    gate_types = ", ".join(f"{name}:{count}" for name, count in signature["gate_types"].items())
    return f"{signature['num_qubits']}q/{signature['num_clbits']}c; {signature['gate_count']} gates; {gate_types}"


def short_ids(group: dict) -> str:
    return ", ".join(prompt["prompt_id"].rsplit("_", 1)[-1] for prompt in group["prompts"])


def short_id_lines(group: dict) -> list[str]:
    ids = [prompt["prompt_id"].rsplit("_", 1)[-1] for prompt in group["prompts"]]
    return [", ".join(ids[index : index + 2]) for index in range(0, len(ids), 2)]


def group_rate_range(group: dict) -> str:
    values = [100 * prompt["mean_structural_success"] for prompt in group["prompts"]]
    if min(values) == max(values):
        return f"{values[0]:.1f}%"
    return f"{min(values):.1f}-{max(values):.1f}%"


def build_svg(payload: dict) -> str:
    summary = payload["summary"]
    per_model = payload["per_model"]
    groups = payload["duplicate_signature_groups"]

    prompt_rate = summary["prompt_level_structural_match"]
    collapsed_rate = summary["signature_collapsed_structural_match"]
    delta = summary["signature_collapsed_delta_pp"]
    max_abs_delta = max(abs(row["delta_pp"]) for row in per_model)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{CROPPED_HEIGHT}" viewBox="0 {CROP_TOP} {WIDTH} {CROPPED_HEIGHT}" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "Structural-signature sensitivity panel"),
        tag(
            "desc",
            {"id": "desc"},
            "Supplemental robustness panel comparing prompt-level and signature-collapsed reference-signature match rates.",
        ),
        rect(0, 0, WIDTH, HEIGHT, fill=PAPER, stroke=PAPER, rx=0, stroke_width=0),
    ]

    # Panel A: denominator cards.
    ax, ay, aw, ah = MARGIN, 145, 430, 270
    parts += [
        rect(ax, ay, aw, ah, fill=PANEL_BG, stroke="#cbd5e1"),
        text(ax + 22, ay + 34, "A. Duplicate-template denominator", size=22, weight=800),
        wrapped_svg(ax + 22, ay + 64, "The collapsed analysis averages by target-metadata signature instead of prompt instance.", width=45, size=15),
    ]
    cards = [
        ("prompt instances", summary["prompt_count"], TEAL),
        ("unique signatures", summary["unique_metadata_signatures"], BLUE),
        ("duplicate groups", summary["duplicate_signature_groups"], RUST),
        ("prompts in duplicates", summary["prompts_in_duplicate_signature_groups"], PLUM),
    ]
    card_w = 180
    card_h = 58
    for idx, (label, value, color) in enumerate(cards):
        cx = ax + 22 + (idx % 2) * (card_w + 22)
        cy = ay + 124 + (idx // 2) * 76
        parts += [
            rect(cx, cy, card_w, card_h, fill=PAPER, stroke="#d7e0e8", rx=7),
            text(cx + 14, cy + 22, label, size=14, weight=700, fill=color),
            text(cx + card_w - 14, cy + 46, f"{value}", size=26, weight=800, fill=TEXT, anchor="end"),
        ]

    # Panel B: prompt versus collapsed rate.
    bx, by, bw, bh = 506, 145, 430, 270
    parts += [
        rect(bx, by, bw, bh, fill=PANEL_BG, stroke="#cbd5e1"),
        text(bx + 22, by + 34, "B. Headline rate is stable", size=22, weight=800),
        wrapped_svg(bx + 22, by + 64, "Collapsing repeated signatures changes reference-signature match by less than one percentage point.", width=46, size=15),
    ]
    chart_x = bx + 70
    chart_y = by + 120
    chart_w = 280
    chart_h = 92
    parts.append(line(chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h, stroke="#94a3b8", width=1.2))
    bars = [
        ("Prompt level", prompt_rate, TEAL),
        ("Signature collapsed", collapsed_rate, BLUE),
    ]
    for idx, (label, value, color) in enumerate(bars):
        x = chart_x + idx * 146
        h = chart_h * value
        parts += [
            rect(x, chart_y + chart_h - h, 86, h, fill=color, stroke=color, rx=5),
            text(x + 43, chart_y + chart_h - h - 10, pct(value), size=18, weight=800, fill=color, anchor="middle"),
            text(x + 43, chart_y + chart_h + 24, label, size=14, fill=MUTED, anchor="middle"),
        ]
    parts += [
        rect(bx + 286, by + 32, 112, 44, fill=PAPER, stroke="#d7e0e8", rx=7),
        text(bx + 342, by + 60, pp(delta), size=21, weight=800, fill=RED if delta < 0 else TEAL, anchor="middle"),
    ]

    # Panel C: duplicate groups.
    cx, cy, cw, ch = 968, 145, 488, 560
    parts += [
        rect(cx, cy, cw, ch, fill=PANEL_BG, stroke="#cbd5e1"),
        text(cx + 22, cy + 34, "C. Six repeated target signatures", size=22, weight=800),
        wrapped_svg(cx + 22, cy + 64, "Rows report prompt ids, target signature, group size, and observed prompt-level success range.", width=52, size=15),
    ]
    row_y = cy + 120
    header_y = row_y - 14
    parts += [
        text(cx + 24, header_y, "ids", size=13, weight=800, fill=MUTED),
        text(cx + 112, header_y, "signature", size=13, weight=800, fill=MUTED),
        text(cx + cw - 82, header_y, "success", size=13, weight=800, fill=MUTED, anchor="end"),
    ]
    for idx, group in enumerate(groups):
        yy = row_y + idx * 69
        fill = "#fff7ed" if idx == 0 else PAPER
        stroke = "#f59e0b" if idx == 0 else "#d7e0e8"
        parts += [
            rect(cx + 18, yy - 22, cw - 36, 58, fill=fill, stroke=stroke, rx=7, stroke_width=1.1),
            "\n".join(
                text(cx + 34, yy - 6 + line_idx * 16, line_value, size=13, weight=800, fill=RUST if idx == 0 else BLUE)
                for line_idx, line_value in enumerate(short_id_lines(group))
            ),
            wrapped_svg(cx + 132, yy - 4, signature_label(group), width=36, size=12, line_height=15, fill=TEXT),
            text(cx + cw - 44, yy + 8, group_rate_range(group), size=13, weight=800, fill=RED if idx == 0 else TEAL, anchor="end"),
        ]
    parts.append(
        wrapped_svg(
            cx + 22,
            cy + ch - 28,
            "The highlighted Bell-barrier group contains the largest repeat and remains signature-unmatched by all external model rows.",
            width=64,
            size=13,
            line_height=16,
            fill=MUTED,
        )
    )

    # Panel D: per-model delta strip.
    dx, dy, dw, dh = MARGIN, 430, 892, 275
    parts += [
        rect(dx, dy, dw, dh, fill=PANEL_BG, stroke="#cbd5e1"),
        text(dx + 22, dy + 34, "D. Per-model sensitivity remains small", size=22, weight=800),
        wrapped_svg(dx + 22, dy + 64, f"Across individual model rows, the largest absolute prompt-to-signature delta is {max_abs_delta:.2f} percentage points.", width=78, size=15),
    ]
    plot_x = dx + 220
    plot_y = dy + 112
    plot_w = 604
    plot_h = 112
    zero_x = plot_x + plot_w / 2
    scale = plot_w / 7.0  # +/- 3.5 pp
    parts += [
        line(plot_x, plot_y + plot_h / 2, plot_x + plot_w, plot_y + plot_h / 2, stroke="#94a3b8", width=1),
        line(zero_x, plot_y + 10, zero_x, plot_y + plot_h - 10, stroke="#64748b", width=1.4),
        text(plot_x, plot_y + plot_h + 30, "-3 pp", size=13, fill=MUTED),
        text(zero_x, plot_y + plot_h + 30, "0", size=13, fill=MUTED, anchor="middle"),
        text(plot_x + plot_w, plot_y + plot_h + 30, "+3 pp", size=13, fill=MUTED, anchor="end"),
    ]
    sorted_rows = sorted(per_model, key=lambda row: row["delta_pp"])
    for idx, row in enumerate(sorted_rows):
        x = zero_x + row["delta_pp"] * scale
        y = plot_y + 18 + (idx % 5) * 18
        color = RED if row["delta_pp"] < -0.25 else TEAL if row["delta_pp"] > 0.25 else BLUE
        parts.append(tag("circle", {"cx": round(x, 2), "cy": y, "r": 5.8, "fill": color, "stroke": PAPER, "stroke-width": 1}))
    min_row = sorted_rows[0]
    max_row = sorted_rows[-1]
    parts += [
        text(dx + 24, dy + 135, "most negative", size=14, weight=800, fill=RED),
        text(dx + 24, dy + 158, f"{MODEL_LABELS.get(min_row['model'], min_row['model'])}: {pp(min_row['delta_pp'])}", size=14, fill=TEXT),
        text(dx + 24, dy + 193, "most positive", size=14, weight=800, fill=TEAL),
        text(dx + 24, dy + 216, f"{MODEL_LABELS.get(max_row['model'], max_row['model'])}: {pp(max_row['delta_pp'])}", size=14, fill=TEXT),
        wrapped_svg(dx + 565, dy + 238, "Each dot is one completed external model row; vertical position only separates overlapping points.", width=38, size=13, line_height=16, fill=MUTED),
    ]

    parts += [
        "</svg>",
    ]
    return "\n".join(parts)


def build_png(payload: dict) -> Image.Image:
    summary = payload["summary"]
    per_model = payload["per_model"]
    groups = payload["duplicate_signature_groups"]
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)

    # A.
    ax, ay, aw, ah = MARGIN, 145, 430, 270
    draw.rounded_rectangle((ax, ay, ax + aw, ay + ah), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((ax + 22, ay + 14), "A. Duplicate-template denominator", fill=TEXT, font=font(24, bold=True))
    draw_wrapped(draw, (ax + 22, ay + 52), "The collapsed analysis averages by target-metadata signature instead of prompt instance.", wrap=45, fill=MUTED, size=16, line_height=21)
    cards = [
        ("prompt instances", summary["prompt_count"], TEAL),
        ("unique signatures", summary["unique_metadata_signatures"], BLUE),
        ("duplicate groups", summary["duplicate_signature_groups"], RUST),
        ("prompts in duplicates", summary["prompts_in_duplicate_signature_groups"], PLUM),
    ]
    for idx, (label, value, color) in enumerate(cards):
        x = ax + 22 + (idx % 2) * 202
        y = ay + 124 + (idx // 2) * 76
        draw.rounded_rectangle((x, y, x + 180, y + 58), radius=7, fill=PAPER, outline="#d7e0e8")
        draw.text((x + 14, y + 7), label, fill=color, font=font(15, bold=True))
        value_text = str(value)
        draw.text((x + 166 - draw.textlength(value_text, font=font(28, bold=True)), y + 26), value_text, fill=TEXT, font=font(28, bold=True))

    # B.
    bx, by, bw, bh = 506, 145, 430, 270
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((bx + 22, by + 14), "B. Headline rate is stable", fill=TEXT, font=font(24, bold=True))
    draw_wrapped(draw, (bx + 22, by + 52), "Collapsing repeated signatures changes reference-signature match by less than one percentage point.", wrap=46, fill=MUTED, size=16, line_height=21)
    chart_x, chart_y, chart_w, chart_h = bx + 70, by + 120, 280, 92
    draw.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill="#94a3b8", width=2)
    for idx, (label, value, color) in enumerate(
        [
            ("Prompt level", summary["prompt_level_structural_match"], TEAL),
            ("Signature collapsed", summary["signature_collapsed_structural_match"], BLUE),
        ]
    ):
        x = chart_x + idx * 146
        h = chart_h * value
        draw.rounded_rectangle((x, chart_y + chart_h - h, x + 86, chart_y + chart_h), radius=5, fill=color)
        p = pct(value)
        draw.text((x + 43 - draw.textlength(p, font=font(20, bold=True)) / 2, chart_y + chart_h - h - 32), p, fill=color, font=font(20, bold=True))
        draw.text((x + 43 - draw.textlength(label, font=font(15)) / 2, chart_y + chart_h + 8), label, fill=MUTED, font=font(15))
    delta = pp(summary["signature_collapsed_delta_pp"])
    draw.rounded_rectangle((bx + 286, by + 32, bx + 398, by + 76), radius=7, fill=PAPER, outline="#d7e0e8")
    draw.text((bx + 342 - draw.textlength(delta, font=font(22, bold=True)) / 2, by + 42), delta, fill=RED, font=font(22, bold=True))

    # C.
    cx, cy, cw, ch = 968, 145, 488, 560
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((cx + 22, cy + 14), "C. Six repeated target signatures", fill=TEXT, font=font(24, bold=True))
    draw_wrapped(draw, (cx + 22, cy + 52), "Rows report prompt ids, target signature, group size, and observed prompt-level success range.", wrap=52, fill=MUTED, size=16, line_height=21)
    draw.text((cx + 24, cy + 106), "ids", fill=MUTED, font=font(14, bold=True))
    draw.text((cx + 112, cy + 106), "signature", fill=MUTED, font=font(14, bold=True))
    draw.text((cx + cw - 116, cy + 106), "success", fill=MUTED, font=font(14, bold=True))
    for idx, group in enumerate(groups):
        y = cy + 120 + idx * 69
        fill = "#fff7ed" if idx == 0 else PAPER
        outline = "#f59e0b" if idx == 0 else "#d7e0e8"
        draw.rounded_rectangle((cx + 18, y - 22, cx + cw - 18, y + 36), radius=7, fill=fill, outline=outline)
        for line_idx, line_value in enumerate(short_id_lines(group)):
            draw.text((cx + 34, y - 10 + line_idx * 16), line_value, fill=RUST if idx == 0 else BLUE, font=font(14, bold=True))
        draw_wrapped(draw, (cx + 132, y - 10), signature_label(group), wrap=36, fill=TEXT, size=13, line_height=16)
        rate = group_rate_range(group)
        draw.text((cx + cw - 44 - draw.textlength(rate, font=font(14, bold=True)), y + 1), rate, fill=RED if idx == 0 else TEAL, font=font(14, bold=True))
    draw_wrapped(
        draw,
        (cx + 22, cy + ch - 44),
        "The highlighted Bell-barrier group contains the largest repeat and remains signature-unmatched by all external model rows.",
        wrap=64,
        fill=MUTED,
        size=14,
        line_height=16,
    )

    # D.
    dx, dy, dw, dh = MARGIN, 430, 892, 275
    draw.rounded_rectangle((dx, dy, dx + dw, dy + dh), radius=9, fill=PANEL_BG, outline="#cbd5e1", width=2)
    draw.text((dx + 22, dy + 14), "D. Per-model sensitivity remains small", fill=TEXT, font=font(24, bold=True))
    max_abs_delta = max(abs(row["delta_pp"]) for row in per_model)
    draw_wrapped(draw, (dx + 22, dy + 52), f"Across individual model rows, the largest absolute prompt-to-signature delta is {max_abs_delta:.2f} percentage points.", wrap=78, fill=MUTED, size=16, line_height=21)
    plot_x, plot_y, plot_w, plot_h = dx + 220, dy + 112, 604, 112
    zero_x = plot_x + plot_w / 2
    scale = plot_w / 7.0
    draw.line((plot_x, plot_y + plot_h / 2, plot_x + plot_w, plot_y + plot_h / 2), fill="#94a3b8", width=1)
    draw.line((zero_x, plot_y + 10, zero_x, plot_y + plot_h - 10), fill="#64748b", width=2)
    sorted_rows = sorted(per_model, key=lambda row: row["delta_pp"])
    for idx, row in enumerate(sorted_rows):
        x = zero_x + row["delta_pp"] * scale
        y = plot_y + 18 + (idx % 5) * 18
        color = RED if row["delta_pp"] < -0.25 else TEAL if row["delta_pp"] > 0.25 else BLUE
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color, outline=PAPER, width=1)
    min_row, max_row = sorted_rows[0], sorted_rows[-1]
    draw.text((dx + 24, dy + 118), "most negative", fill=RED, font=font(15, bold=True))
    draw.text((dx + 24, dy + 142), f"{MODEL_LABELS.get(min_row['model'], min_row['model'])}: {pp(min_row['delta_pp'])}", fill=TEXT, font=font(14))
    draw.text((dx + 24, dy + 177), "most positive", fill=TEAL, font=font(15, bold=True))
    draw.text((dx + 24, dy + 201), f"{MODEL_LABELS.get(max_row['model'], max_row['model'])}: {pp(max_row['delta_pp'])}", fill=TEXT, font=font(14))
    draw.text((plot_x, plot_y + plot_h + 14), "-3 pp", fill=MUTED, font=font(13))
    draw.text((zero_x - draw.textlength("0", font=font(13)) / 2, plot_y + plot_h + 14), "0", fill=MUTED, font=font(13))
    draw.text((plot_x + plot_w - draw.textlength("+3 pp", font=font(13)), plot_y + plot_h + 14), "+3 pp", fill=MUTED, font=font(13))
    draw_wrapped(draw, (dx + 565, dy + 238), "Each dot is one completed external model row; vertical position only separates overlapping points.", wrap=38, fill=MUTED, size=13, line_height=16)

    return image.crop((0, CROP_TOP, WIDTH, HEIGHT))


def build_caption(payload: dict) -> str:
    summary = payload["summary"]
    max_abs_delta = max(abs(row["delta_pp"]) for row in payload["per_model"])
    return "\n".join(
        [
            "# Reference-Signature Sensitivity Caption",
            "",
            "**Supplemental Figure S3. Reference-signature sensitivity check.** "
            "The panel checks whether repeated evaluator-facing target-metadata signatures drive the headline external-generation result. "
            f"Panel A reports `{summary['prompt_count']}` prompt instances, `{summary['unique_metadata_signatures']}` unique target-metadata signatures, `{summary['duplicate_signature_groups']}` duplicate-signature groups, and `{summary['prompts_in_duplicate_signature_groups']}` prompt instances inside duplicate groups. "
            f"Panel B compares prompt-level reference-signature match (`{pct(summary['prompt_level_structural_match'])}`) with signature-collapsed reference-signature match (`{pct(summary['signature_collapsed_structural_match'])}`), a change of `{pp(summary['signature_collapsed_delta_pp'])}`. "
            "Panel C lists the six duplicate-signature groups; the highlighted Bell-barrier group is the largest repeated signature and remains unmatched by all external model rows. "
            f"Panel D shows that per-model prompt-to-signature deltas remain small, with maximum absolute delta `{max_abs_delta:.2f}` percentage points. "
            "The result supports the manuscript's duplicate-template disclosure: repeated signatures should be reported, but they do not drive the headline execution-structure-gap conclusion.",
            "",
            "Source artifacts:",
            "",
            f"- `{SIGNATURE_JSON.relative_to(ROOT).as_posix()}`",
            f"- `scripts/{Path(__file__).name}`",
            "",
        ]
    )


def run() -> None:
    payload = load_json(SIGNATURE_JSON)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_SVG.write_text(build_svg(payload), encoding="utf-8")
    build_png(payload).save(OUTPUT_PNG)
    CAPTION_PATH.write_text(build_caption(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_SVG}")
    print(f"wrote {OUTPUT_PNG}")
    print(f"wrote {CAPTION_PATH}")


if __name__ == "__main__":
    run()
