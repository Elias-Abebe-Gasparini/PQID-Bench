"""Combine circuit difficulty and retrieval-copy panels into one overview figure."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = ROOT / "figures"

DIFFICULTY_PNG = FIGURES_DIR / "circuit_exemplar_difficulty_panel.png"
DIFFICULTY_SVG = FIGURES_DIR / "circuit_exemplar_difficulty_panel.svg"
RETRIEVAL_PNG = FIGURES_DIR / "retrieval_copy_complementarity_circuit_panel.png"
RETRIEVAL_SVG = FIGURES_DIR / "retrieval_copy_complementarity_circuit_panel.svg"
OUTPUT_PNG = FIGURES_DIR / "circuit_difficulty_and_retrieval_overview_panel.png"
OUTPUT_SVG = FIGURES_DIR / "circuit_difficulty_and_retrieval_overview_panel.svg"
CAPTION_PATH = FIGURES_DIR / "circuit_difficulty_and_retrieval_overview_panel_caption.md"

TEXT = "#1f2933"
MUTED = "#526071"
WHITE = "#ffffff"


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
        ROOT / "fonts" / ("LinLibertine_RBah.ttf" if bold else "LinLibertine_Rah.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def resize_to_width(image: Image.Image, width: int) -> Image.Image:
    scale = width / image.width
    height = round(image.height * scale)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def trim_white_margin(
    image: Image.Image,
    *,
    padding: int = 4,
    threshold: int = 250,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Trim near-white outer margin and return the crop box in source pixels."""
    rgb = image.convert("RGB")
    white = Image.new("RGB", rgb.size, WHITE)
    diff = ImageChops.difference(rgb, white).convert("L")
    mask = diff.point(lambda px: 255 if px > (255 - threshold) else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return rgb, (0, 0, rgb.width, rgb.height)

    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(rgb.width, right + padding)
    bottom = min(rgb.height, bottom + padding)
    return rgb.crop((left, top, right, bottom)), (left, top, right, bottom)


def draw_header(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    subtitle: str,
) -> None:
    draw.text((x, y), title, fill=TEXT, font=font(24, bold=True))
    draw.text((x, y + 26), subtitle, fill=MUTED, font=font(15))


def svg_text(x: int, y: int, text: str, *, size: int, weight: str = "400", fill: str = TEXT) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return (
        f'<text x="{x}" y="{y}" font-family="Times New Roman" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="start">{escaped}</text>'
    )


def svg_inner(path: Path, *, strip_visual_header: bool = False) -> str:
    """Return SVG body content without nested document metadata."""
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*>\s*", "", raw, count=1)
    body = re.sub(r"^.*?<svg\b[^>]*>", "", raw, count=1, flags=re.S)
    body = re.sub(r"</svg>\s*$", "", body, count=1, flags=re.S)
    body = re.sub(r"<title\b[^>]*>.*?</title>\s*", "", body, flags=re.S)
    body = re.sub(r"<desc\b[^>]*>.*?</desc>\s*", "", body, flags=re.S)
    body = re.sub(
        r"<rect\b(?=[^>]*(?:width=\"100%\"|width=\"1400\"))(?=[^>]*(?:height=\"100%\"|height=\"730\"))[^>]*/>\s*",
        "",
        body,
        count=1,
        flags=re.S,
    )
    if strip_visual_header:
        body = re.sub(r"<text\b[^>]*\by=\"34\"[^>]*>.*?</text>\s*", "", body, count=1, flags=re.S)
        body = re.sub(r"<text\b[^>]*\by=\"58\"[^>]*>.*?</text>\s*", "", body, count=1, flags=re.S)
        body = re.sub(r"<text\b[^>]*\by=\"59\"[^>]*>.*?</text>\s*", "", body, count=1, flags=re.S)
    return body.strip()


def inline_svg_panel(
    *,
    panel_id: str,
    source_body: str,
    x: int,
    y: int,
    width: int,
    height: int,
    crop_box: tuple[int, int, int, int],
) -> str:
    left, top, right, bottom = crop_box
    crop_width = right - left
    crop_height = bottom - top
    sx = width / crop_width
    sy = height / crop_height
    return "\n".join(
        [
            (
                f'<g id="{panel_id}" '
                f'transform="translate({x} {y}) scale({sx:.8f} {sy:.8f}) translate({-left} {-top})">'
            ),
            source_body,
            "</g>",
        ]
    )


def write_svg(
    *,
    canvas_width: int,
    canvas_height: int,
    side_margin: int,
    top_margin: int,
    header_height: int,
    retrieval_header_height: int,
    section_gap: int,
    difficulty_crop_box: tuple[int, int, int, int],
    difficulty_scaled_size: tuple[int, int],
    retrieval_crop_box: tuple[int, int, int, int],
    retrieval_scaled_size: tuple[int, int],
) -> None:
    diff_left, diff_top, diff_right, diff_bottom = difficulty_crop_box
    ret_left, ret_top, ret_right, ret_bottom = retrieval_crop_box
    diff_width = diff_right - diff_left
    diff_height = diff_bottom - diff_top
    ret_width = ret_right - ret_left
    ret_height = ret_bottom - ret_top
    difficulty_body = svg_inner(DIFFICULTY_SVG)
    retrieval_body = svg_inner(RETRIEVAL_SVG, strip_visual_header=True)

    y = top_margin
    diff_y = y + header_height
    retrieval_header_y = diff_y + difficulty_scaled_size[1] + section_gap
    retrieval_y = retrieval_header_y + retrieval_header_height

    svg = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" '
                f'height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" '
                'role="img" aria-labelledby="title desc">'
            ),
            "<title id=\"title\">Target-circuit difficulty and retrieval-copy complementarity</title>",
            (
                "<desc id=\"desc\">Combined PQID-Bench panel showing target-circuit "
                "difficulty exemplars and retrieval-copy-only complementarity templates.</desc>"
            ),
            f'<rect width="{canvas_width}" height="{canvas_height}" fill="{WHITE}"/>',
            svg_text(
                side_margin,
                y + 22,
                "A. Representative target circuits from easiest to hardest",
                size=24,
                weight="700",
            ),
            svg_text(
                side_margin,
                y + 43,
                "Fixed-rank examples from the 154 held-out prompts, sorted by external-model signature-match difficulty.",
                size=15,
                fill=MUTED,
            ),
            inline_svg_panel(
                panel_id="difficulty",
                source_body=difficulty_body,
                x=side_margin,
                y=diff_y,
                width=difficulty_scaled_size[0],
                height=difficulty_scaled_size[1],
                crop_box=(diff_left, diff_top, diff_right, diff_bottom),
            ),
            svg_text(
                side_margin,
                retrieval_header_y + 22,
                "B. Signature hits only by retrieval-copy baselines",
                size=24,
                weight="700",
            ),
            inline_svg_panel(
                panel_id="retrieval",
                source_body=retrieval_body,
                x=side_margin,
                y=retrieval_y,
                width=retrieval_scaled_size[0],
                height=retrieval_scaled_size[1],
                crop_box=(ret_left, ret_top, ret_right, ret_bottom),
            ),
            "</svg>",
            "",
        ]
    )
    OUTPUT_SVG.write_text(svg, encoding="utf-8")


def main() -> None:
    difficulty = Image.open(DIFFICULTY_PNG).convert("RGB")
    retrieval = Image.open(RETRIEVAL_PNG).convert("RGB")

    # The retrieval panel already has its own title in the source image. Crop it
    # here so the combined figure has one consistent panel-header system.
    retrieval_crop_top = 52
    retrieval_cards = retrieval.crop((0, retrieval_crop_top, retrieval.width, retrieval.height))

    canvas_width = 1500
    side_margin = 6
    content_width = canvas_width - 2 * side_margin
    top_margin = 0
    header_height = 48
    retrieval_header_height = 32
    section_gap = 16
    bottom_margin = 0

    difficulty_trimmed, difficulty_crop_box = trim_white_margin(difficulty, padding=1)
    retrieval_trimmed, retrieval_crop_box_relative = trim_white_margin(retrieval_cards, padding=1)
    if difficulty_crop_box[1] < 18:
        difficulty_crop_box = (
            difficulty_crop_box[0],
            18,
            difficulty_crop_box[2],
            difficulty_crop_box[3],
        )
        difficulty_trimmed = difficulty.crop(difficulty_crop_box)
    retrieval_crop_box = (
        retrieval_crop_box_relative[0],
        retrieval_crop_box_relative[1] + retrieval_crop_top,
        retrieval_crop_box_relative[2],
        retrieval_crop_box_relative[3] + retrieval_crop_top,
    )

    difficulty_scaled = resize_to_width(difficulty_trimmed, content_width)
    retrieval_scaled = resize_to_width(retrieval_trimmed, content_width)

    canvas_height = (
        top_margin
        + header_height
        + difficulty_scaled.height
        + section_gap
        + retrieval_header_height
        + retrieval_scaled.height
        + bottom_margin
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), WHITE)
    draw = ImageDraw.Draw(canvas)

    y = top_margin
    draw_header(
        draw,
        side_margin,
        y,
        "A. Representative target circuits from easiest to hardest",
        "Fixed-rank examples from the 154 held-out prompts, sorted by external-model signature-match difficulty.",
    )
    y += header_height
    canvas.paste(difficulty_scaled, (side_margin, y))

    y += difficulty_scaled.height + section_gap
    draw.text(
        (side_margin, y),
        "B. Signature hits only by retrieval-copy baselines",
        fill=TEXT,
        font=font(24, bold=True),
    )
    y += retrieval_header_height
    canvas.paste(retrieval_scaled, (side_margin, y))

    canvas.save(OUTPUT_PNG, dpi=(300, 300))
    write_svg(
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        side_margin=side_margin,
        top_margin=top_margin,
        header_height=header_height,
        retrieval_header_height=retrieval_header_height,
        section_gap=section_gap,
        difficulty_crop_box=difficulty_crop_box,
        difficulty_scaled_size=difficulty_scaled.size,
        retrieval_crop_box=retrieval_crop_box,
        retrieval_scaled_size=retrieval_scaled.size,
    )

    CAPTION_PATH.write_text(
        "\n".join(
            [
                "**Figure 6. Target-circuit difficulty and retrieval-copy complementarity.** "
                "Panel A shows four representative target circuits selected by fixed rank after sorting the `154` held-out prompts from easiest to hardest by external-model item difficulty. "
                "Each frozen ordered reference tape is rendered on labeled qubit wires, with long tapes wrapped onto repeated temporal bands. "
                "Panel B groups retrieval-copy-only signature hits: `6` prompt targets are matched under the current reference-signature predicate by at least one retrieval-copy baseline and by `0 / 21` model rows, collapsing to `4` signatures with the Bell-barrier card grouping three prompt variants. "
                "Together the panels show that PQID-Bench difficulty is not only a matter of raw circuit size: models can clear simple-looking targets when the frozen structure is regular, but can also generate runnable code that drifts away from barriers, gate vocabularies, measurement subcircuits, or source-specific skeletons. "
                "The ordered renderings are audit aids and do not change the four-component reference-signature predicate.",
                "",
                "Figure file:",
                "",
                "- `figures/circuit_difficulty_and_retrieval_overview_panel.png`",
                "- `figures/circuit_difficulty_and_retrieval_overview_panel.svg`",
                "",
                "Component source figures:",
                "",
                "- `figures/circuit_exemplar_difficulty_panel.png`",
                "- `figures/retrieval_copy_complementarity_circuit_panel.png`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT_PNG} and {OUTPUT_SVG} ({canvas_width}x{canvas_height})")


if __name__ == "__main__":
    main()
