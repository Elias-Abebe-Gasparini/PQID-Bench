"""Build the Supplemental Figure S4 retrieval-channel edge-case panel."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from publication_figure_style import PUBLICATION_SERIF_FONT_STACK


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "artifacts/pqid_bench_retrieval_channel_edge_case_0043.json"
FIGURE_PATH = ROOT / "figures/retrieval_channel_edge_case_0043_panel.svg"
CAPTION_PATH = ROOT / "figures/retrieval_channel_edge_case_0043_panel_caption.md"

TEXT = "#1f2933"
MUTED = "#5b677a"
GRID = "#d8e0e8"
CARD_BG = "#fbfdff"
TEAL = "#1f766d"
BLUE = "#315a9f"
RUST = "#b45309"
RED = "#b91c1c"
GOLD = "#a16207"
PALE_GREEN = "#e6f4ef"
PALE_RED = "#fff1f1"
PALE_GOLD = "#fff7ed"


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
    size: float = 13,
    weight: int = 400,
    fill: str = TEXT,
    anchor: str = "start",
) -> str:
    return tag(
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


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str = "none",
    rx: float = 0,
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


def circle(cx: float, cy: float, r: float, *, fill: str, stroke: str = "none", width: float = 1) -> str:
    return tag(
        "circle",
        {
            "cx": round(cx, 2),
            "cy": round(cy, 2),
            "r": round(r, 2),
            "fill": fill,
            "stroke": stroke,
            "stroke-width": width,
        },
    )


def wrap(value: str, width: int, max_lines: int | None = None) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        proposed = " ".join([*current, word])
        if len(proposed) <= width:
            current.append(word)
            continue
        if current:
            lines.append(" ".join(current))
        current = [word]
        if max_lines is not None and len(lines) >= max_lines:
            break
    if current and (max_lines is None or len(lines) < max_lines):
        lines.append(" ".join(current))
    if max_lines is not None and len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines


def chip(
    lines: list[str],
    x: float,
    y: float,
    value: str,
    *,
    width: float | None = None,
    fill: str = "#ffffff",
    stroke: str = "#cbd6e2",
    color: str = TEXT,
) -> float:
    chip_w = width if width is not None else max(38, len(value) * 6.0 + 15)
    lines.append(rect(x, y - 13, chip_w, 23, fill=fill, stroke=stroke, rx=4, stroke_width=0.9))
    lines.append(text(x + chip_w / 2, y + 3.0, value, size=9.8, weight=800, fill=color, anchor="middle"))
    return chip_w


def parse_gate_tape(gate_tape: list[str]) -> list[dict[str, object]]:
    ops: list[dict[str, object]] = []
    for raw in gate_tape:
        name = raw.split("(", 1)[0].strip().lower()
        inside = raw.split("(", 1)[1].rstrip(")") if "(" in raw else ""
        qubits: list[int] = []
        clbits: list[int] = []
        for token in inside.split(","):
            token = token.strip()
            if token.startswith("q") and token[1:].isdigit():
                qubits.append(int(token[1:]))
            elif token.startswith("c") and token[1:].isdigit():
                clbits.append(int(token[1:]))
        ops.append({"name": name, "qubits": qubits, "clbits": clbits, "raw": raw})
    return ops


def gate_label(name: str) -> str:
    labels = {"cx": "CX", "measure": "M", "x": "X", "h": "H"}
    return labels.get(name, name.upper())


def draw_gate_box(lines: list[str], x: float, y: float, label: str, *, fill: str = "#ffffff", stroke: str = TEAL) -> None:
    lines.append(rect(x - 17, y - 13, 34, 26, fill=fill, stroke=stroke, rx=4, stroke_width=1.25))
    lines.append(text(x, y + 4.5, label, size=11.2, weight=800, anchor="middle"))


def draw_circuit(lines: list[str], x: float, y: float, width: float, height: float, gate_tape: list[str], q_count: int) -> None:
    ops = parse_gate_tape(gate_tape)
    wire_gap = min(40, (height - 48) / max(q_count - 1, 1))
    top_wire = y + 33
    start_x = x + 48
    wire_end = x + width - 18
    usable_w = width - 92
    step = usable_w / max(len(ops), 1)
    lines.append(rect(x, y, width, height, fill="#ffffff", stroke="#cbd6e2", rx=5, stroke_width=0.9))
    for qubit in range(q_count):
        wy = top_wire + qubit * wire_gap
        lines.append(text(x + 8, wy + 4, f"q{qubit}", size=11.0, fill=MUTED))
        lines.append(line(start_x - 14, wy, wire_end, wy, stroke=GRID, width=1.25))

    for index, op in enumerate(ops):
        gx = start_x + index * step
        name = str(op["name"])
        qubits = op["qubits"]  # type: ignore[assignment]
        clbits = op["clbits"]  # type: ignore[assignment]
        ys = [top_wire + int(qubit) * wire_gap for qubit in qubits]
        if name == "cx" and len(ys) == 2:
            control_y, target_y = ys
            lines.append(line(gx, min(control_y, target_y), gx, max(control_y, target_y), stroke=BLUE, width=1.35))
            lines.append(circle(gx, control_y, 4.7, fill=BLUE))
            lines.append(circle(gx, target_y, 9.5, fill="#ffffff", stroke=BLUE, width=1.55))
            lines.append(line(gx - 7.5, target_y, gx + 7.5, target_y, stroke=BLUE, width=1.2))
            lines.append(line(gx, target_y - 7.5, gx, target_y + 7.5, stroke=BLUE, width=1.2))
        elif name == "measure":
            wy = ys[0] if ys else top_wire
            draw_gate_box(lines, gx, wy, "M", fill=PALE_GOLD, stroke=RUST)
            if clbits:
                lines.append(text(gx, wy + 25, f"c{clbits[0]}", size=9.4, fill=RUST, anchor="middle"))
        else:
            wy = ys[0] if ys else top_wire
            draw_gate_box(lines, gx, wy, gate_label(name))


def signature_label(signature: dict[str, object]) -> str:
    gates = signature["gate_types"]  # type: ignore[index]
    gate_text = ", ".join(f"{name}:{count}" for name, count in sorted(gates.items()))  # type: ignore[attr-defined]
    return f"{signature['num_qubits']}q/{signature['num_clbits']}c; {signature['gate_count']} gates; {gate_text}"


def draw_card(
    lines: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    panel_label: str,
    title: str,
    subtitle: str,
    signature: dict[str, object],
    gate_tape: list[str],
    q_count: int,
    pass_status: str,
    status_fill: str,
    status_color: str,
    note: str,
) -> None:
    lines.append(rect(x, y, width, height, fill=CARD_BG, stroke="#cbd6e2", rx=6, stroke_width=1.1))
    lines.append(text(x + 16, y + 28, f"{panel_label}. {title}", size=16.2, weight=800))
    status_width = 132 if "SIGNATURE" in pass_status else 92
    chip(
        lines,
        x + width - status_width - 16,
        y + 25,
        pass_status,
        width=status_width,
        fill=status_fill,
        stroke=status_color,
        color=status_color,
    )
    lines.append(text(x + 16, y + 49, subtitle, size=11.3, fill=MUTED, weight=700))

    metric_y = y + 75
    metric_x = x + 16
    for label, chip_w in [
        (f"q/c {signature['num_qubits']}/{signature['num_clbits']}", 60),
        (f"{signature['gate_count']} gates", 62),
        (f"{len(signature['gate_types'])} types", 60),
    ]:
        chip(lines, metric_x, metric_y, str(label), width=chip_w)
        metric_x += chip_w + 7

    draw_circuit(lines, x + 16, y + 98, width - 32, 148, gate_tape, q_count)
    lines.append(text(x + 16, y + 270, "Evaluator-facing signature:", size=11.0, fill=MUTED, weight=800))
    sig_lines = wrap(signature_label(signature), 54, max_lines=2)
    for offset, value in enumerate(sig_lines):
        lines.append(text(x + 16, y + 288 + offset * 13, value, size=10.8))
    lines.append(text(x + 16, y + 332, "Interpretation:", size=11.0, fill=MUTED, weight=800))
    for offset, value in enumerate(wrap(note, 58, max_lines=4)):
        lines.append(text(x + 16, y + 350 + offset * 14, value, size=11.0))


def build_svg(payload: dict[str, object]) -> str:
    target = payload["target"]  # type: ignore[index]
    external_context = payload["external_model_context"]  # type: ignore[index]
    channels = payload["retrieval_channels"]  # type: ignore[index]
    code_channel = channels[0]  # type: ignore[index]
    instruction_channel = channels[2]  # type: ignore[index]

    width = 1450
    full_height = 610
    crop_top = 60
    height = full_height - crop_top
    margin = 28
    gap = 22
    card_w = (width - 2 * margin - 2 * gap) / 3
    card_h = 430
    strip_y = 514
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 {crop_top} {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Retrieval-channel edge case for prompt 0043</title>',
        '<desc id="desc">Three cards compare the target circuit, code-metadata retrieval hit, and instruction retrieval miss for PQID-Bench prompt 0043.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{full_height}" fill="#ffffff"/>',
    ]

    positions = [(margin, 78), (margin + card_w + gap, 78), (margin + 2 * (card_w + gap), 78)]
    draw_card(
        lines,
        *positions[0],
        card_w,
        card_h,
        panel_label="A",
        title="Target 0043",
        subtitle=(
            "Low-difficulty prompt; external models clear "
            f"{external_context['external_structural_matches']}/"
            f"{external_context['completed_external_model_rows']}"
        ),
        signature=target["signature"],  # type: ignore[index]
        gate_tape=target["ordered_gate_tape"],  # type: ignore[index]
        q_count=int(target["signature"]["num_qubits"]),  # type: ignore[index]
        pass_status="TARGET",
        status_fill="#eef5ff",
        status_color=BLUE,
        note="Reference target: X, CX, X, then two measurements.",
    )
    draw_card(
        lines,
        *positions[1],
        card_w,
        card_h,
        panel_label="B",
        title="Code/metadata copy hit",
        subtitle="BM25 and TF-IDF code retrieve the same neighbor",
        signature=code_channel["retrieved_signature"],  # type: ignore[index]
        gate_tape=code_channel["ordered_gate_tape"],  # type: ignore[index]
        q_count=int(code_channel["retrieved_signature"]["num_qubits"]),  # type: ignore[index]
        pass_status="SIGNATURE PASS",
        status_fill=PALE_GREEN,
        status_color=TEAL,
        note="Passes the signature predicate, but the ordered gate tape differs from the target.",
    )
    draw_card(
        lines,
        *positions[2],
        card_w,
        card_h,
        panel_label="C",
        title="Instruction-copy miss",
        subtitle="Instruction TF-IDF retrieves a Hadamard/CX neighbor",
        signature=instruction_channel["retrieved_signature"],  # type: ignore[index]
        gate_tape=instruction_channel["ordered_gate_tape"],  # type: ignore[index]
        q_count=int(instruction_channel["retrieved_signature"]["num_qubits"]),  # type: ignore[index]
        pass_status="SIGNATURE FAIL",
        status_fill=PALE_RED,
        status_color=RED,
        note="Same qubit/classical-bit width, but wrong gate count and wrong gate vocabulary.",
    )

    lines.append(rect(margin, strip_y, width - 2 * margin, 68, fill="#fbfdff", stroke="#cbd6e2", rx=6, stroke_width=1.0))
    lines.append(text(margin + 18, strip_y + 25, "D. Scoring interpretation", size=15.0, weight=800))
    chip(lines, margin + 248, strip_y + 23, "signature predicate", width=128, fill="#eef5ff", stroke=BLUE, color=BLUE)
    lines.append(text(margin + 395, strip_y + 27, "B passes because q/c, counted gates, and gate multiset match.", size=12.0))
    chip(lines, margin + 835, strip_y + 23, "ordered tape", width=92, fill=PALE_GOLD, stroke=GOLD, color=GOLD)
    lines.append(text(margin + 945, strip_y + 27, "B is not an ordered-circuit-equivalence proof.", size=12.0))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def write_caption(payload: dict[str, object]) -> None:
    external_context = payload["external_model_context"]  # type: ignore[index]
    CAPTION_PATH.write_text(
        "\n".join(
            [
                "**Supplemental Figure S4. Retrieval-channel edge case for prompt 0043.**",
                "Panel A shows the target `X-CX-X-measure` circuit for `pqid_bench_external_gen_0043`, which matches the reference signature for "
                f"{external_context['external_structural_matches']} of the "
                f"{external_context['completed_external_model_rows']} completed external model rows.",
                "Panel B shows the source neighbor retrieved by both BM25 code/metadata copy and TF-IDF code/metadata copy; it passes the current PQID-Bench structural-signature predicate because the evaluator-facing signature matches.",
                "Panel C shows the TF-IDF instruction-copy neighbor, which preserves width but fails gate-count and gate-vocabulary checks.",
                "Panel D states the interpretation: the case supports metadata-neighbor complementarity, not ordered gate-tape equivalence.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.write_text(build_svg(payload), encoding="utf-8")
    write_caption(payload)
    print(f"Wrote {FIGURE_PATH}")
    print(f"Wrote {CAPTION_PATH}")


if __name__ == "__main__":
    main()
