"""Generate the 1280x640 GitHub social-preview image for PQID-Bench."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 640
BACKGROUND = "#F7F8F6"
INK = "#151918"
MUTED = "#52605C"
TEAL = "#13756D"
BLUE = "#2469A0"
GREEN = "#3A7758"
RULE = "#CED6D2"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _metric(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    label: str,
    value: str,
    color: str,
) -> None:
    draw.rounded_rectangle((x, 368, x + 290, 506), radius=8, fill="#FFFFFF", outline=RULE, width=2)
    draw.rectangle((x, 368, x + 8, 506), fill=color)
    draw.text((x + 30, 390), value, font=_font(42, bold=True), fill=INK)
    draw.text((x + 30, 455), label, font=_font(20), fill=MUTED)


def build(output: Path) -> Path:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 22, HEIGHT), fill=TEAL)
    draw.text((74, 62), "PQID-Bench", font=_font(72, bold=True), fill=INK)
    draw.text(
        (78, 160),
        "Validation-aware quantum-program generation benchmark",
        font=_font(31),
        fill=MUTED,
    )
    draw.text(
        (78, 228),
        "Operational admissibility is not structural recovery.",
        font=_font(34, bold=True),
        fill=TEAL,
    )

    _metric(draw, x=78, label="Python execution", value="91.22%", color=BLUE)
    _metric(draw, x=385, label="Assembly admissibility", value="91.03%", color=GREEN)
    _metric(draw, x=692, label="Signature recovery", value="52.66%", color=TEAL)

    draw.text((78, 556), "21 models  |  154 prompts  |  3,234 outputs", font=_font(24), fill=INK)
    draw.text((1010, 418), "ES-Gap", font=_font(22, bold=True), fill=MUTED)
    draw.text((1010, 451), "38.56 pp", font=_font(38, bold=True), fill=INK)
    draw.text((1010, 500), "frozen v1.0.0", font=_font(18), fill=MUTED)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".github/assets/pqid-bench-social-preview.png"),
    )
    args = parser.parse_args()
    print(build(args.output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
