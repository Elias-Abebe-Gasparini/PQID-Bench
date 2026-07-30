"""Build a representative circuit-exemplar panel for PQID-Bench."""

from __future__ import annotations

import csv
import json
import math
import textwrap
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
FIGURES_DIR = ROOT / "figures"

PROMPTS_JSONL = ARTIFACTS_DIR / "test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
MATRIX_CSV = ARTIFACTS_DIR / "analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv"
ORDERED_AUDIT_JSONL = ARTIFACTS_DIR / "analysis_154/pqid_bench_ordered_operand_cell_audit.jsonl"

SELECTION_JSON = ARTIFACTS_DIR / "pqid_bench_circuit_exemplar_selection.json"
FIGURE_PATH = FIGURES_DIR / "circuit_exemplar_difficulty_panel.svg"
CAPTION_PATH = FIGURES_DIR / "circuit_exemplar_difficulty_panel_caption.md"


TEXT = "#1f2933"
MUTED = "#64748b"
GRID = "#edf2f7"
AXIS = "#516174"
TEAL = "#1f766d"
BLUE = "#315a9f"
RUST = "#b45309"
PLUM = "#7c3f72"
GOLD = "#b7791f"
PANEL_BG = "#ffffff"
CARD_BG = "#fbfdff"
FIGURE_FONT = "Times New Roman"
CIRCUIT_MUTED = "#5b677a"
CIRCUIT_GRID = "#d8e0e8"
CIRCUIT_BORDER = "#cbd6e2"


EXEMPLAR_LABELS = ["easiest", "lower-middle", "upper-middle", "hardest"]

GATE_TAPES: dict[str, list[dict[str, Any]]] = {
    "pqid_bench_external_gen_0003": [
        {"gate": "H", "qubits": [0]},
        {"gate": "H", "qubits": [0]},
        {"gate": "M", "qubits": [0, 1, 2]},
    ],
    "pqid_bench_external_gen_0048": [
        {"gate": "H", "qubits": [2, 3, 4]},
        {"gate": "barrier", "qubits": [0, 1, 2, 3, 4]},
        {"gate": "X", "qubits": [0]},
        {"gate": "H", "qubits": [0]},
    ],
    "pqid_bench_external_gen_0023": [
        {"gate": "CX", "qubits": [0, 1]},
        {"gate": "barrier", "qubits": [0, 1]},
        {"gate": "M", "qubits": [0, 1]},
    ],
    "pqid_bench_external_gen_0044": [
        {"gate": "X", "qubits": [1]},
        {"gate": "X", "qubits": [0]},
        {"gate": "CX", "qubits": [0, 1]},
        {"gate": "X", "qubits": [0]},
        {"gate": "M", "qubits": [0, 1]},
    ],
    "pqid_bench_external_gen_0123": [
        {"gate": "H", "qubits": [0, 1, 2, 3, 4, 5, 6]},
        {"gate": "Z", "qubits": [6]},
        {"gate": "CX", "qubits": [1, 6]},
        {"gate": "CX", "qubits": [3, 6]},
        {"gate": "CX", "qubits": [5, 6]},
        {"gate": "H", "qubits": [0, 1, 2, 3, 4, 5]},
        {"gate": "M", "qubits": [0, 1, 2, 3, 4, 5]},
    ],
    "pqid_bench_external_gen_0060": [
        {"gate": "Z", "qubits": [0]},
        {"gate": "RZ(pi)", "qubits": [2]},
        {"gate": "RZ(pi/2)", "qubits": [0]},
        {"gate": "H", "qubits": [2]},
        {"gate": "Z", "qubits": [0]},
        {"gate": "Z", "qubits": [1]},
        {"gate": "RZZ", "qubits": [2, 1]},
        {"gate": "X", "qubits": [2]},
        {"gate": "X", "qubits": [1]},
        {"gate": "ID", "qubits": [0]},
        {"gate": "H", "qubits": [1]},
        {"gate": "RY(pi/3)", "qubits": [0]},
        {"gate": "S", "qubits": [1]},
        {"gate": "RXX", "qubits": [0, 2]},
        {"gate": "RXX", "qubits": [2, 1]},
        {"gate": "S", "qubits": [0]},
        {"gate": "Y", "qubits": [2]},
        {"gate": "P(pi/2)", "qubits": [0]},
        {"gate": "Y", "qubits": [0]},
        {"gate": "P(pi/1100)", "qubits": [1]},
        {"gate": "X", "qubits": [1]},
        {"gate": "SWAP", "qubits": [2, 0]},
        {"gate": "RXX(pi/3)", "qubits": [1, 2]},
        {"gate": "S", "qubits": [0]},
        {"gate": "Z", "qubits": [2]},
    ],
}


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
    size: float = 12,
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
            "font-family": FIGURE_FONT,
        },
        escape(value),
    )


def justified_text(
    x: float,
    y: float,
    value: str,
    *,
    target_width: float,
    size: float,
    fill: str = TEXT,
    weight: int = 400,
    justify: bool = True,
    word_spacing: float | None = None,
) -> str:
    attrs: dict[str, object] = {
        "x": round(x, 2),
        "y": round(y, 2),
        "font-size": size,
        "font-weight": weight,
        "fill": fill,
        "text-anchor": "start",
        "font-family": FIGURE_FONT,
    }
    if justify and " " in value:
        attrs["textLength"] = round(target_width, 2)
        attrs["lengthAdjust"] = "spacing"
    if word_spacing is not None:
        attrs["word-spacing"] = round(word_spacing, 2)
    return tag("text", attrs, escape(value))


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


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = GRID,
    width: float = 1,
    dash: str | None = None,
) -> str:
    attrs: dict[str, object] = {
        "x1": round(x1, 2),
        "y1": round(y1, 2),
        "x2": round(x2, 2),
        "y2": round(y2, 2),
        "stroke": stroke,
        "stroke-width": width,
    }
    if dash:
        attrs["stroke-dasharray"] = dash
    return tag("line", attrs)


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


def gate_entropy(gates: dict[str, int]) -> float:
    total = sum(gates.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in gates.values():
        p = count / total
        entropy -= p * math.log(p)
    return entropy


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                rows.append(json.loads(raw))
    return rows


def read_matrix(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_reference_tapes(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load one frozen ordered target tape per prompt from the replay audit."""
    tapes: dict[str, list[dict[str, Any]]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            row = json.loads(raw)
            prompt_id = str(row["prompt_id"])
            if prompt_id not in tapes and row.get("reference_tape") is not None:
                tapes[prompt_id] = list(row["reference_tape"])
    return tapes


def pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def wrap_lines(value: str, width: int, max_lines: int | None = None) -> list[str]:
    lines = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
    if max_lines is None or len(lines) <= max_lines:
        return lines
    clipped = lines[:max_lines]
    clipped[-1] = clipped[-1].rstrip(".") + "..."
    return clipped


def chip(lines: list[str], x: float, y: float, value: str, *, fill: str, stroke: str, color: str = TEXT) -> None:
    w = max(30, len(value) * 6.1 + 12)
    lines.append(rect(x, y - 12, w, 20, fill=fill, stroke=stroke, rx=4, stroke_width=0.7))
    lines.append(text(x + w / 2, y + 1.5, value, size=8.7, weight=700, fill=color, anchor="middle"))


def metric_chip(lines: list[str], x: float, y: float, width: float, value: str) -> None:
    lines.append(rect(x, y - 12, width, 20, fill="#ffffff", stroke="#b8c6d6", rx=4, stroke_width=1))
    lines.append(text(x + width / 2, y + 1.5, value, size=8.6, weight=800, fill=TEXT, anchor="middle"))


def pretty_family(value: str) -> str:
    labels = []
    for raw_part in str(value).split(";"):
        cleaned = raw_part.replace("_or_", " / ").replace("_", " ")
        cleaned = " ".join(cleaned.split())
        labels.append(cleaned.title())
    return ", ".join(labels)


def select_exemplars(
    matrix_rows: list[dict[str, str]],
    prompts: dict[str, dict[str, Any]],
    reference_tapes: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    model_count = len(matrix_rows[0]) - 10 if matrix_rows else 0
    rows = []
    for row in matrix_rows:
        prompt = prompts[row["prompt_id"]]
        metadata = prompt["target_metadata"]
        gates = {str(name): int(count) for name, count in metadata["gate_types"].items()}
        rows.append(
            {
                **row,
                "instruction": prompt["instruction"],
                "row_id": prompt["row_id"],
                "gates": gates,
                "gate_entropy": gate_entropy(gates),
                "model_count": model_count,
                "reference_tape": reference_tapes.get(row["prompt_id"], []),
            }
        )
    ordered = sorted(
        rows,
        key=lambda row: (
            float(row["difficulty"]),
            int(row["gate_type_count"]),
            int(row["gate_count"]),
            row["prompt_id"],
        ),
    )
    positions = [0, round((len(ordered) - 1) / 3), round(2 * (len(ordered) - 1) / 3), len(ordered) - 1]
    selected = []
    for label, position in zip(EXEMPLAR_LABELS, positions):
        row = dict(ordered[position])
        row["difficulty_band"] = label
        row["difficulty_rank"] = position + 1
        row["rank_denominator"] = len(ordered)
        selected.append(row)
    return selected


def draw_progress_guide(lines: list[str], selected: list[dict[str, Any]], x: float, y: float, width: float) -> None:
    lines.append(text(x, y, "selected by sorted difficulty rank", size=12.2, fill=MUTED, weight=700))
    lines.append(line(x + 210, y - 4, x + width - 8, y - 4, stroke=AXIS, width=1.35))
    lines.append(tag("polygon", {"points": f"{x + width - 8},{y - 4} {x + width - 18},{y - 9} {x + width - 18},{y + 1}", "fill": AXIS}))
    for idx, row in enumerate(selected):
        px = x + 210 + idx * ((width - 240) / 3)
        lines.append(circle(px, y - 4, 4.6, fill=TEAL if idx < 2 else RUST, stroke="#ffffff", width=0.8))
        lines.append(text(px, y + 17, f"{row['difficulty_rank']}/{row['rank_denominator']}", size=10.8, fill=MUTED, anchor="middle"))
    lines.append(text(x + width - 6, y - 16, "harder to clear", size=12.0, fill=MUTED, weight=700, anchor="end"))


def draw_gate_box(
    lines: list[str],
    x: float,
    y: float,
    label: str,
    *,
    fill: str = "#ffffff",
    stroke: str = BLUE,
    compact: bool = False,
) -> None:
    label = label.upper()
    box_h = 16 if compact else 24
    font_size = 7.1 if compact else 9.2
    width = max(18 if compact else 25, min(34 if compact else 48, len(label) * (4.3 if compact else 5.5) + 10))
    lines.append(rect(x - width / 2, y - box_h / 2, width, box_h, fill=fill, stroke=stroke, rx=3, stroke_width=1.0))
    lines.append(text(x, y + (2.7 if compact else 4.0), label, size=font_size, weight=800, fill=TEXT, anchor="middle"))


def draw_target(lines: list[str], x: float, y: float, *, color: str, compact: bool) -> None:
    radius = 6.2 if compact else 8.5
    lines.append(circle(x, y, radius, fill="#ffffff", stroke=color, width=1.3))
    lines.append(line(x - radius * 0.68, y, x + radius * 0.68, y, stroke=color, width=1.2))
    lines.append(line(x, y - radius * 0.68, x, y + radius * 0.68, stroke=color, width=1.2))


def draw_swap(lines: list[str], x: float, y: float, *, color: str, compact: bool) -> None:
    radius = 4.6 if compact else 6.2
    lines.append(line(x - radius, y - radius, x + radius, y + radius, stroke=color, width=1.35))
    lines.append(line(x - radius, y + radius, x + radius, y - radius, stroke=color, width=1.35))


def draw_operation(
    lines: list[str],
    gx: float,
    op: dict[str, Any],
    wire_y: dict[int, float],
    *,
    top: float,
    bottom: float,
    classical_y: float | None,
    compact: bool,
) -> None:
    qubits = [int(q) for q in op.get("qubits", []) if int(q) in wire_y]
    if not qubits:
        return
    ys = [wire_y[q] for q in qubits]
    name = str(op.get("name", op.get("gate", ""))).lower()
    control_radius = 3.2 if compact else 4.4

    if name == "barrier":
        lines.append(line(gx, top, gx, bottom, stroke=RUST, width=1.1, dash="3 3"))
        lines.append(
            text(
                gx,
                top - 4,
                "B" if compact else "barrier",
                size=6.5 if compact else 7.4,
                fill=RUST,
                weight=700,
                anchor="middle",
            )
        )
        return
    if name == "cx" and len(ys) == 2:
        lines.append(line(gx, min(ys), gx, max(ys), stroke=BLUE, width=1.3))
        lines.append(circle(gx, ys[0], control_radius, fill=BLUE))
        draw_target(lines, gx, ys[1], color=BLUE, compact=compact)
        return
    if name == "ccx" and len(ys) == 3:
        lines.append(line(gx, min(ys), gx, max(ys), stroke=PLUM, width=1.3))
        lines.append(circle(gx, ys[0], control_radius, fill=PLUM))
        lines.append(circle(gx, ys[1], control_radius, fill=PLUM))
        draw_target(lines, gx, ys[2], color=PLUM, compact=compact)
        return
    if name == "cz" and len(ys) == 2:
        lines.append(line(gx, min(ys), gx, max(ys), stroke=BLUE, width=1.3))
        lines.append(circle(gx, ys[0], control_radius, fill=BLUE))
        draw_gate_box(lines, gx, ys[1], "Z", stroke=BLUE, compact=compact)
        return
    if name == "swap" and len(ys) == 2:
        lines.append(line(gx, min(ys), gx, max(ys), stroke=RUST, width=1.3))
        draw_swap(lines, gx, ys[0], color=RUST, compact=compact)
        draw_swap(lines, gx, ys[1], color=RUST, compact=compact)
        return
    if name == "cswap" and len(ys) == 3:
        lines.append(line(gx, min(ys), gx, max(ys), stroke=RUST, width=1.3))
        lines.append(circle(gx, ys[0], control_radius, fill=RUST))
        draw_swap(lines, gx, ys[1], color=RUST, compact=compact)
        draw_swap(lines, gx, ys[2], color=RUST, compact=compact)
        return
    if name in {"rxx", "rzz"} and len(ys) == 2:
        color = RUST
        lines.append(line(gx, min(ys), gx, max(ys), stroke=color, width=1.2))
        short = "XX" if name == "rxx" else "ZZ"
        draw_gate_box(lines, gx, ys[0], short, stroke=color, compact=compact)
        draw_gate_box(lines, gx, ys[1], short, stroke=color, compact=compact)
        return
    if name == "measure":
        draw_gate_box(lines, gx, ys[0], "M", fill="#fff7ed", stroke=RUST, compact=compact)
        if classical_y is not None:
            box_half = 8 if compact else 12
            lines.append(line(gx, ys[0] + box_half, gx, classical_y - 3, stroke=RUST, width=1.0))
            lines.append(
                tag(
                    "polygon",
                    {
                        "points": f"{gx},{classical_y} {gx - 3},{classical_y - 5} {gx + 3},{classical_y - 5}",
                        "fill": RUST,
                    },
                )
            )
        return

    label = {
        "id": "I",
        "measure": "M",
    }.get(name, name.upper())
    color = RUST if name in {"rx", "ry", "rz", "p"} else TEAL
    for wy in ys:
        draw_gate_box(lines, gx, wy, label, stroke=color, compact=compact)


def draw_circuit_band(
    lines: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    operations: list[dict[str, Any]],
    operation_offset: int,
    num_qubits: int,
    num_clbits: int,
    compact: bool,
    final_band: bool,
) -> None:
    show_classical = num_clbits > 0 and final_band
    classical_y = y + h - 7 if show_classical else None
    top_limit = y + (12 if compact else 16)
    bottom_limit = (classical_y - 13) if classical_y is not None else y + h - 7
    if num_qubits == 1:
        quantum_top = (top_limit + bottom_limit) / 2
        wire_y = {0: quantum_top}
    else:
        wire_gap = min(24 if not compact else 17, (bottom_limit - top_limit) / max(num_qubits - 1, 1))
        total_h = wire_gap * (num_qubits - 1)
        quantum_top = (top_limit + bottom_limit - total_h) / 2
        wire_y = {q: quantum_top + q * wire_gap for q in range(num_qubits)}

    label_x = x + 19
    wire_start = x + 27
    wire_end = x + w - 5
    for q, wy in wire_y.items():
        lines.append(text(label_x, wy + 3.2, f"q{q}", size=7.8 if compact else 9.2, fill=CIRCUIT_MUTED, anchor="end"))
        lines.append(line(wire_start, wy, wire_end, wy, stroke=CIRCUIT_GRID, width=1.15))
    if classical_y is not None:
        lines.append(text(label_x, classical_y + 3.0, f"c[{num_clbits}]", size=7.8 if compact else 9.0, fill=CIRCUIT_MUTED, anchor="end"))
        lines.append(line(wire_start, classical_y - 1.5, wire_end, classical_y - 1.5, stroke=CIRCUIT_GRID, width=0.9))
        lines.append(line(wire_start, classical_y + 1.5, wire_end, classical_y + 1.5, stroke=CIRCUIT_GRID, width=0.9))

    if compact:
        start = operation_offset + 1
        end = operation_offset + len(operations)
        lines.append(text(wire_end, y + 7, f"ops {start}-{end}", size=6.8, fill=CIRCUIT_MUTED, anchor="end"))

    timeline_start = wire_start + 5
    timeline_width = wire_end - timeline_start
    step = timeline_width / (len(operations) + 1)
    for index, op in enumerate(operations):
        gx = timeline_start + (index + 1) * step
        draw_operation(
            lines,
            gx,
            op,
            wire_y,
            top=min(wire_y.values()) - (6 if compact else 10),
            bottom=max(wire_y.values()) + (6 if compact else 10),
            classical_y=classical_y,
            compact=compact,
        )


def draw_circuit_schematic(lines: list[str], x: float, y: float, w: float, h: float, row: dict[str, Any]) -> None:
    prompt_id = str(row["prompt_id"])
    gates = list(row.get("reference_tape") or [])
    if not gates and prompt_id in GATE_TAPES:
        gates = [
            {
                "name": str(op["gate"]).lower(),
                "qubits": list(op["qubits"]),
                "clbits": [],
                "params": [],
            }
            for op in GATE_TAPES[prompt_id]
        ]
    if not gates:
        draw_gate_multiset(lines, x, y, w, row["gates"])
        return
    max_per_band = 7
    band_count = math.ceil(len(gates) / max_per_band)
    band_gap = 5
    band_h = (h - band_gap * (band_count - 1)) / band_count
    for band_index in range(band_count):
        operation_offset = band_index * max_per_band
        operations = gates[operation_offset : operation_offset + max_per_band]
        draw_circuit_band(
            lines,
            x,
            y + band_index * (band_h + band_gap),
            w,
            band_h,
            operations=operations,
            operation_offset=operation_offset,
            num_qubits=int(row["num_qubits"]),
            num_clbits=int(row["num_clbits"]),
            compact=band_count > 1,
            final_band=band_index == band_count - 1,
        )


def draw_gate_tape(lines: list[str], x: float, y: float, w: float, h: float, gates: list[dict[str, Any]]) -> None:
    lines.append(text(x, y + 11, "ordered target gate tape", size=10.8, fill=MUTED, weight=700))
    chip_w = 50
    chip_h = 27
    gap = 4
    max_cols = 5 if len(gates) == 25 and 5 * chip_w + 4 * gap <= w else max(1, int((w + gap) // (chip_w + gap)))
    grid_w = max_cols * chip_w + (max_cols - 1) * gap
    grid_x = x + max(0, (w - grid_w) / 2)
    for idx, op in enumerate(gates):
        row = idx // max_cols
        col = idx % max_cols
        cx = grid_x + col * (chip_w + gap)
        cy = y + 29 + row * (chip_h + 5)
        gate = str(op["gate"]).upper()
        color = RUST if gate in {"RXX", "RZZ", "SWAP", "RXX(PI/3)"} else TEAL
        label = (
            gate.replace("RZ(PI)", "RZp")
            .replace("RZ(PI/2)", "RZp/2")
            .replace("RY(PI/3)", "RYp/3")
            .replace("P(PI/2)", "Pp/2")
            .replace("P(PI/1100)", "P*")
            .replace("RXX(PI/3)", "RXXp/3")
        )
        operands = ",".join(f"q{qubit}" for qubit in op["qubits"])
        lines.append(rect(cx, cy, chip_w, chip_h, fill="#ffffff", stroke=color, rx=4, stroke_width=0.8))
        lines.append(text(cx + chip_w / 2, cy + 11, label, size=7.6, weight=800, fill=color, anchor="middle"))
        lines.append(text(cx + chip_w / 2, cy + 22, operands, size=6.8, weight=700, fill=MUTED, anchor="middle"))


def draw_gate_multiset(lines: list[str], x: float, y: float, w: float, gates: dict[str, int]) -> None:
    lines.append(text(x, y + 11, "target gate multiset (order not encoded)", size=10.8, fill=MUTED, weight=700))
    items = sorted(gates.items(), key=lambda item: (-item[1], item[0]))
    chip_w = 54
    chip_h = 30
    gap = 5
    max_cols = max(1, int((w + gap) // (chip_w + gap)))
    grid_w = min(max_cols, len(items)) * chip_w + max(0, min(max_cols, len(items)) - 1) * gap
    grid_x = x + max(0, (w - grid_w) / 2)
    for idx, (name, count) in enumerate(items):
        row_idx = idx // max_cols
        col_idx = idx % max_cols
        cx = grid_x + col_idx * (chip_w + gap)
        cy = y + 31 + row_idx * (chip_h + 7)
        color = RUST if name in {"ccx", "cswap", "cz", "rxx", "rzz", "swap"} else TEAL
        lines.append(rect(cx, cy, chip_w, chip_h, fill="#ffffff", stroke=color, rx=4, stroke_width=0.9))
        lines.append(text(cx + chip_w / 2, cy + 19, f"{name.upper()}x{count}", size=8.4, weight=800, fill=color, anchor="middle"))


def draw_card(lines: list[str], row: dict[str, Any], x: float, y: float, w: float, h: float, index: int) -> None:
    difficulty = float(row["difficulty"])
    solved = int(row["solved_models"])
    edge_color = TEAL if solved >= 15 else BLUE if solved >= 8 else RUST
    lines.append(rect(x, y, w, h, fill=CARD_BG, stroke="#d9e2ec", rx=7, stroke_width=1))
    lines.append(rect(x, y, w, 8, fill=edge_color, rx=7))
    lines.append(text(x + 14, y + 31, f"{chr(65 + index)}. {row['difficulty_band']}", size=13.5, weight=800))
    lines.append(text(x + w - 14, y + 31, f"{solved}/{row['model_count']}", size=18, weight=800, fill=edge_color, anchor="end"))
    lines.append(text(x + w - 14, y + 50, "models clear", size=10.6, fill=MUTED, anchor="end"))
    lines.append(text(x + 14, y + 54, str(row["prompt_id"]).replace("pqid_bench_external_gen_", "prompt "), size=10.0, fill=MUTED))
    metric_y = y + 77
    metrics = [
        (49, f"diff {difficulty:.2f}"),
        (43, f"q/c {row['num_qubits']}/{row['num_clbits']}"),
        (47, f"{row['gate_count']} gates"),
        (47, f"{row['gate_type_count']} types"),
        (45, f"H {float(row['gate_entropy']):.2f}"),
    ]
    metric_x = x + 14
    for metric_width, value in metrics:
        metric_chip(lines, metric_x, metric_y, metric_width, value)
        metric_x += metric_width + 5
    schematic_label_y = y + 116
    lines.append(
        text(
            x + 14,
            schematic_label_y,
            f"Target circuit: operates on {row['num_qubits']} qubits and {row['num_clbits']} classical bits",
            size=10.0,
            fill=MUTED,
            weight=700,
        )
    )
    schematic_y = y + 131
    schematic_h = 272
    lines.append(rect(x + 14, schematic_y, w - 28, schematic_h, fill="#ffffff", stroke=CIRCUIT_BORDER, rx=5, stroke_width=0.9))
    draw_circuit_schematic(lines, x + 28, schematic_y + 20, w - 56, schematic_h - 38, row)
    vocab_y = y + 432
    lines.append(text(x + 14, vocab_y, "gate vocabulary", size=10.0, weight=800, fill=MUTED))
    gx = x + 14
    gy = vocab_y + 22
    for gate, count in sorted(row["gates"].items(), key=lambda item: (-item[1], item[0])):
        label = f"{gate}x{count}"
        chip_width = max(30, len(label) * 6.1 + 12)
        if gx + chip_width > x + w - 14:
            gx = x + 14
            gy += 27
        chip(lines, gx, gy, label, fill="#ffffff", stroke="#d8e0ea", color=TEXT)
        gx += chip_width + 6
    family_y = max(y + 526, gy + 34)
    family = pretty_family(str(row["families"]))
    lines.append(text(x + 14, family_y, f"Family: {family}", size=10.2, fill=PLUM, weight=700))
    prompt_y = family_y + 30
    prompt_x = x + 14
    prompt_width = w - 28
    prompt_lines = wrap_lines(str(row["instruction"]), width=54)
    lines.append(text(prompt_x, prompt_y, "Prompt:", size=12.2, fill=MUTED, weight=800))
    for line_idx, wrapped in enumerate(prompt_lines):
        justify_line = line_idx < len(prompt_lines) - 1
        lines.append(
            justified_text(
                prompt_x,
                prompt_y + 19 + line_idx * 16,
                wrapped,
                target_width=prompt_width,
                size=12.8,
                fill=TEXT,
                justify=justify_line,
            )
        )


def write_svg(selected: list[dict[str, Any]]) -> None:
    width = 1400
    height = 760
    margin = 24
    col_gap = 18
    card_w = (width - 2 * margin - 3 * col_gap) / 4
    card_h = 680
    progress_y = 40
    card_y = 64
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "PQID-Bench representative circuit exemplars"),
        tag(
            "desc",
            {"id": "desc"},
            "Four representative held-out circuit targets selected from easiest to hardest by model structural-match difficulty.",
        ),
        rect(0, 0, width, height, fill=PANEL_BG),
    ]
    draw_progress_guide(lines, selected, margin, progress_y, width - margin * 2)
    for idx, row in enumerate(selected):
        draw_card(
            lines,
            row,
            margin + idx * (card_w + col_gap),
            card_y,
            card_w,
            card_h,
            idx,
        )
    lines.append("</svg>")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_selection(selected: list[dict[str, Any]]) -> None:
    payload = {
        "selection_rule": (
            "Sort all 154 held-out prompts by ascending item difficulty, then by gate-type count, "
            "gate count, and prompt_id. Select rank positions 1, round((n-1)/3)+1, "
            "round(2*(n-1)/3)+1, and n."
        ),
        "n_prompts": selected[0]["rank_denominator"] if selected else 0,
        "selected": [
            {
                "difficulty_band": row["difficulty_band"],
                "difficulty_rank": row["difficulty_rank"],
                "prompt_id": row["prompt_id"],
                "row_id": row["row_id"],
                "solved_models": int(row["solved_models"]),
                "model_count": int(row["model_count"]),
                "difficulty": float(row["difficulty"]),
                "num_qubits": int(row["num_qubits"]),
                "num_clbits": int(row["num_clbits"]),
                "gate_count": int(row["gate_count"]),
                "gate_type_count": int(row["gate_type_count"]),
                "gate_entropy": float(row["gate_entropy"]),
                "families": row["families"],
                "gate_types": row["gates"],
                "reference_tape": row["reference_tape"],
                "instruction": row["instruction"],
            }
            for row in selected
        ],
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    SELECTION_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_caption(selected: list[dict[str, Any]]) -> None:
    hardest = selected[-1]
    surprising = selected[2]
    CAPTION_PATH.write_text(
        "\n".join(
            [
                "# Circuit Exemplar Difficulty Panel Caption",
                "",
                "**Main Figure 6A component. Representative target circuits across the PQID-Bench difficulty gradient.** "
                "The four cards are selected by a fixed rank rule after sorting the 154 held-out prompts "
                "from easiest to hardest by item difficulty. Each card reports the prompt identifier, "
                "model structural-match count, target width, gate count, gate-type count, gate entropy, "
                "family tags, and a wrapped rendering of the frozen ordered operation-and-operand tape on labeled qubit wires. "
                "The progression shows that "
                "difficulty is not reducible to size alone: "
                f"`{surprising['prompt_id']}` is a small `{surprising['num_qubits']}`-qubit target cleared by only "
                f"`{surprising['solved_models']}/{surprising['model_count']}` models, whereas the hardest exemplar "
                f"`{hardest['prompt_id']}` combines `{hardest['gate_count']}` gates, "
                f"`{hardest['gate_type_count']}` gate types, and gate entropy `{float(hardest['gate_entropy']):.2f}`.",
                "",
                "Source artifacts:",
                "",
                "- `artifacts/pqid_bench_circuit_exemplar_selection.json`",
                "- `artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv`",
                "- `artifacts/analysis_154/pqid_bench_ordered_operand_cell_audit.jsonl`",
                "- `artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    prompts = {row["prompt_id"]: row for row in read_jsonl(PROMPTS_JSONL)}
    matrix_rows = read_matrix(MATRIX_CSV)
    reference_tapes = read_reference_tapes(ORDERED_AUDIT_JSONL)
    selected = select_exemplars(matrix_rows, prompts, reference_tapes)
    write_selection(selected)
    write_svg(selected)
    write_caption(selected)
    print(f"Wrote {SELECTION_JSON}")
    print(f"Wrote {FIGURE_PATH}")
    print(f"Wrote {CAPTION_PATH}")


if __name__ == "__main__":
    main()
