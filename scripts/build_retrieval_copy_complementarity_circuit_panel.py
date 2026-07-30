"""Build a supplemental circuit panel for retrieval-copy complementarity cases."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import run_pqid_bench_generation_copy_baseline as copy_baseline
import run_pqid_bench_executable_validity_check as validity
from publication_figure_style import PUBLICATION_SERIF_FONT_STACK


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = ROOT / "artifacts/analysis_154/pqid_bench_retrieval_copy_complementarity_cases.json"
FIGURE_PATH = ROOT / "figures/retrieval_copy_complementarity_circuit_panel.svg"
CAPTION_PATH = ROOT / "figures/retrieval_copy_complementarity_circuit_panel_caption.md"

TEXT = "#1f2933"
MUTED = "#5b677a"
GRID = "#d8e0e8"
CARD_BG = "#fbfdff"
TEAL = "#1f766d"
RUST = "#b45309"
BLUE = "#315a9f"
PLUM = "#7c3f72"
GOLD = "#a16207"
RED = "#b91c1c"

CASE_TITLES = {
    "pqid_bench_external_gen_0004": "Bell state with barrier",
    "pqid_bench_external_gen_0028": "Bell pair with barrier",
    "pqid_bench_external_gen_0033": "E91 basis measurement",
    "pqid_bench_external_gen_0064": "Bell pair on fake backend",
    "pqid_bench_external_gen_0022": "Phase-flip error correction",
    "pqid_bench_external_gen_0108": "Three-basis measurement",
}

TEMPLATE_GROUPS = [
    {
        "title": "Bell-barrier prompt variants",
        "prompt_ids": [
            "pqid_bench_external_gen_0004",
            "pqid_bench_external_gen_0028",
            "pqid_bench_external_gen_0064",
        ],
    },
    {
        "title": "E91 basis measurement",
        "prompt_ids": ["pqid_bench_external_gen_0033"],
    },
    {
        "title": "Phase-flip error correction",
        "prompt_ids": ["pqid_bench_external_gen_0022"],
    },
    {
        "title": "Three-basis measurement",
        "prompt_ids": ["pqid_bench_external_gen_0108"],
    },
]

PROMPT_SUMMARIES = {
    "pqid_bench_external_gen_0004": "Prepare an H-CX Bell pair, preserve the target barrier, and measure both qubits.",
    "pqid_bench_external_gen_0022": "Encode a phase-flip code, inject a Z error, decode, correct with CCX, and measure qubit 0.",
    "pqid_bench_external_gen_0033": "Construct the named Alice and Bob E91 basis-measurement subcircuits, including S-H-T-H basis changes.",
    "pqid_bench_external_gen_0108": "Construct separate X-, Y-, and Z-basis measurement circuits for three prepared qubits.",
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
) -> str:
    attrs: dict[str, object] = {
        "x": round(x, 2),
        "y": round(y, 2),
        "font-family": PUBLICATION_SERIF_FONT_STACK,
        "font-size": size,
        "font-weight": weight,
        "fill": fill,
        "text-anchor": "start",
    }
    if justify and " " in value:
        attrs["textLength"] = round(target_width, 2)
        attrs["lengthAdjust"] = "spacing"
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
        if max_lines is not None and len(lines) == max_lines:
            break
    if current and (max_lines is None or len(lines) < max_lines):
        lines.append(" ".join(current))
    if max_lines is not None and len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".,;:") + "..."
    return lines


def chip(lines: list[str], x: float, y: float, value: str, *, stroke: str = "#d8e0ea", fill: str = "#ffffff", color: str = TEXT, width: float | None = None) -> float:
    chip_w = width if width is not None else max(34, len(value) * 6.0 + 14)
    lines.append(rect(x, y - 12, chip_w, 21, fill=fill, stroke=stroke, rx=4, stroke_width=0.8))
    lines.append(text(x + chip_w / 2, y + 2.2, value, size=9.1, weight=800, fill=color, anchor="middle"))
    return chip_w


def gate_vocab_chips(lines: list[str], x: float, y: float, max_x: float, gates: dict[str, int]) -> float:
    gx = x
    gy = y
    for gate, count in sorted(gates.items(), key=lambda item: (-item[1], item[0])):
        label = f"{gate}x{count}"
        chip_w = max(34, len(label) * 6.0 + 14)
        if gx + chip_w > max_x:
            gx = x
            gy += 27
        chip(lines, gx, gy, label, color=TEXT, width=chip_w)
        gx += chip_w + 6
    return gy


def pretty_family(value: str) -> str:
    return ", ".join(part.replace("_", " ").title() for part in value.split(";") if part)


def metadata_summary(metadata: dict[str, Any]) -> str:
    gates = ", ".join(f"{name}:{count}" for name, count in sorted(metadata["gate_types"].items()))
    return f"{metadata['num_qubits']}q/{metadata['num_clbits']}c; {metadata['gate_count']} counted gates; {gates}"


def short_prompt_id(prompt_id: str) -> str:
    return prompt_id.replace("pqid_bench_external_gen_", "p")


def circuit_ops(circuit: Any) -> list[dict[str, Any]]:
    ops = []
    for inst in circuit.data:
        op = inst.operation
        ops.append(
            {
                "name": str(op.name).lower(),
                "qubits": [circuit.find_bit(qubit).index for qubit in inst.qubits],
                "clbits": [circuit.find_bit(clbit).index for clbit in inst.clbits],
            }
        )
    return ops


def load_target_circuits() -> list[dict[str, Any]]:
    payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    rows_by_id = {row["row_id"]: row for row in copy_baseline.clean_rows(copy_baseline.DEFAULT_INPUT)}
    qiskit_env = validity.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is unavailable: {qiskit_env.get('error')}")

    cases = []
    for case in payload["cases"]:
        row = rows_by_id[case["row_id"]]
        namespace = validity.execution_namespace(row["metadata"], qiskit_env)
        exec(row["code"], namespace, namespace)
        circuits = validity.collect_circuits(namespace, qiskit_env)
        circuit_name, circuit = validity.choose_circuit(circuits, row["metadata"])
        cases.append(
            {
                **case,
                "circuit_name": circuit_name,
                "ops": circuit_ops(circuit),
                "num_qubits": circuit.num_qubits,
                "num_clbits": circuit.num_clbits,
            }
        )
    return cases


def grouped_templates(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_by_prompt = {case["prompt_id"]: case for case in cases}
    groups: list[dict[str, Any]] = []
    for spec in TEMPLATE_GROUPS:
        members = [case_by_prompt[prompt_id] for prompt_id in spec["prompt_ids"]]
        representative = members[0]
        baseline_labels = sorted(
            {
                hit["baseline_label"]
                for member in members
                for hit in member["successful_copy_baselines"]
            }
        )
        failure = {
            "model_rows": sum(member["external_failure_summary"]["model_rows"] for member in members),
            "execution_success": sum(member["external_failure_summary"]["execution_success"] for member in members),
            "qasm3_success": sum(member["external_failure_summary"]["qasm3_success"] for member in members),
            "gate_types_match": sum(member["external_failure_summary"]["gate_types_match"] for member in members),
            "all_match": sum(member["external_failure_summary"]["all_match"] for member in members),
        }
        groups.append(
            {
                **representative,
                "title": spec["title"],
                "members": members,
                "prompt_ids": [member["prompt_id"] for member in members],
                "prompt_id_label": ", ".join(short_prompt_id(member["prompt_id"]) for member in members),
                "copy_hit_label": ", ".join(baseline_labels),
                "external_failure_summary": failure,
            }
        )
    return groups


def gate_label(name: str) -> str:
    labels = {
        "barrier": "B",
        "measure": "M",
        "cx": "CX",
        "ccx": "CCX",
    }
    return labels.get(name, name.upper())


def draw_gate_box(
    lines: list[str],
    x: float,
    y: float,
    label: str,
    *,
    fill: str = "#ffffff",
    stroke: str = TEAL,
    compact: bool = False,
) -> None:
    box_w = 27 if compact else 34
    box_h = 19 if compact else 26
    lines.append(rect(x - box_w / 2, y - box_h / 2, box_w, box_h, fill=fill, stroke=stroke, rx=4, stroke_width=1.1))
    lines.append(text(x, y + (3.0 if compact else 4.5), label, size=8.2 if compact else 10.5, weight=700, fill=TEXT, anchor="middle"))


def draw_target(lines: list[str], x: float, y: float, *, color: str, compact: bool) -> None:
    radius = 6.3 if compact else 9
    lines.append(circle(x, y, radius, fill="#ffffff", stroke=color, width=1.4))
    lines.append(line(x - radius * 0.72, y, x + radius * 0.72, y, stroke=color, width=1.2))
    lines.append(line(x, y - radius * 0.72, x, y + radius * 0.72, stroke=color, width=1.2))


def draw_circuit_band(
    lines: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    ops: list[dict[str, Any]],
    operation_offset: int,
    q_count: int,
    c_count: int,
    compact: bool,
    final_band: bool,
) -> None:
    show_classical = c_count > 0 and final_band
    classical_y = y + height - 7 if show_classical else None
    top_limit = y + (13 if compact else 17)
    bottom_limit = classical_y - 13 if classical_y is not None else y + height - 8
    if q_count == 1:
        top_wire = (top_limit + bottom_limit) / 2
        wire_y = {0: top_wire}
    else:
        wire_gap = min(23 if compact else 30, (bottom_limit - top_limit) / max(q_count - 1, 1))
        used_h = wire_gap * (q_count - 1)
        top_wire = (top_limit + bottom_limit - used_h) / 2
        wire_y = {qubit: top_wire + qubit * wire_gap for qubit in range(q_count)}

    wire_end = x + width - 12
    label_x = x + 19
    start_x = x + 30
    for qubit in range(q_count):
        wy = wire_y[qubit]
        lines.append(text(label_x, wy + 3.2, f"q{qubit}", size=8.2 if compact else 10.0, fill=MUTED, anchor="end"))
        lines.append(line(start_x, wy, wire_end, wy, stroke=GRID, width=1.2))
    if classical_y is not None:
        lines.append(text(label_x, classical_y + 3.0, f"c[{c_count}]", size=8.0 if compact else 9.4, fill=MUTED, anchor="end"))
        lines.append(line(start_x, classical_y - 1.5, wire_end, classical_y - 1.5, stroke=GRID, width=0.9))
        lines.append(line(start_x, classical_y + 1.5, wire_end, classical_y + 1.5, stroke=GRID, width=0.9))
    if compact:
        lines.append(
            text(
                wire_end,
                y + 8,
                f"ops {operation_offset + 1}-{operation_offset + len(ops)}",
                size=7.0,
                fill=MUTED,
                anchor="end",
            )
        )

    timeline_width = wire_end - start_x
    step = timeline_width / (len(ops) + 1)
    for index, op in enumerate(ops):
        gx = start_x + (index + 1) * step
        qubits = [int(qubit) for qubit in op["qubits"]]
        ys = [wire_y[qubit] for qubit in qubits]
        name = op["name"]
        if name == "barrier":
            lines.append(line(gx, min(wire_y.values()) - 7, gx, max(wire_y.values()) + 7, stroke=RUST, width=1.1, dash="3 3"))
            lines.append(
                text(
                    gx,
                    min(wire_y.values()) - 10,
                    "B" if compact else "barrier",
                    size=6.5 if compact else 7.4,
                    fill=RUST,
                    weight=700,
                    anchor="middle",
                )
            )
        elif name == "cx" and len(ys) == 2:
            control_y, target_y = ys
            lines.append(line(gx, min(control_y, target_y), gx, max(control_y, target_y), stroke=BLUE, width=1.3))
            lines.append(circle(gx, control_y, 3.3 if compact else 4.5, fill=BLUE))
            draw_target(lines, gx, target_y, color=BLUE, compact=compact)
        elif name == "ccx" and len(ys) == 3:
            target_y = ys[-1]
            lines.append(line(gx, min(ys), gx, max(ys), stroke=PLUM, width=1.3))
            for control_y in ys[:-1]:
                lines.append(circle(gx, control_y, 3.3 if compact else 4.5, fill=PLUM))
            draw_target(lines, gx, target_y, color=PLUM, compact=compact)
        elif name == "measure":
            wy = ys[0] if ys else top_wire
            draw_gate_box(lines, gx, wy, "M", fill="#fff7ed", stroke=RUST, compact=compact)
            if classical_y is not None:
                lines.append(line(gx, wy + (10 if compact else 13), gx, classical_y - 3, stroke=RUST, width=1.0))
                lines.append(
                    tag(
                        "polygon",
                        {
                            "points": f"{gx},{classical_y} {gx - 3},{classical_y - 5} {gx + 3},{classical_y - 5}",
                            "fill": RUST,
                        },
                    )
                )
        else:
            wy = ys[0] if ys else top_wire
            draw_gate_box(lines, gx, wy, gate_label(name), compact=compact)


def draw_circuit(lines: list[str], x: float, y: float, width: float, height: float, case: dict[str, Any]) -> None:
    q_count = int(case["num_qubits"])
    c_count = int(case["num_clbits"])
    ops = case["ops"]
    max_per_band = 7
    band_count = max(1, math.ceil(len(ops) / max_per_band))
    band_gap = 5
    band_h = (height - band_gap * (band_count - 1)) / band_count

    lines.append(rect(x, y, width, height, fill="#ffffff", stroke="#cbd6e2", rx=5, stroke_width=0.9))
    for band_index in range(band_count):
        operation_offset = band_index * max_per_band
        band_ops = ops[operation_offset : operation_offset + max_per_band]
        draw_circuit_band(
            lines,
            x,
            y + band_index * (band_h + band_gap),
            width,
            band_h,
            ops=band_ops,
            operation_offset=operation_offset,
            q_count=q_count,
            c_count=c_count,
            compact=band_count > 1,
            final_band=band_index == band_count - 1,
        )


def draw_card(lines: list[str], x: float, y: float, width: float, height: float, case: dict[str, Any], index: int) -> None:
    title = case.get("title") or CASE_TITLES.get(case["prompt_id"], case["families"])
    failure = case["external_failure_summary"]
    metadata = case["target_metadata"]
    model_rows = failure["model_rows"]
    all_match = failure["all_match"]
    lines.append(rect(x, y, width, height, fill=CARD_BG, stroke="#cbd6e2", rx=6, stroke_width=1.1))
    lines.append(text(x + 16, y + 29, f"{chr(64 + index)}. {title}", size=14.5, weight=800))
    lines.append(text(x + width - 16, y + 29, f"{all_match}/{model_rows}", size=19.0, weight=800, fill=RED, anchor="end"))
    lines.append(text(x + width - 16, y + 48, "model matches", size=11.2, fill=MUTED, anchor="end"))
    lines.append(text(x + 16, y + 54, f"prompt {case['prompt_id_label']}", size=10.7, fill=MUTED))

    metric_y = y + 78
    metric_x = x + 16
    metrics = [
        (58, f"q/c {metadata['num_qubits']}/{metadata['num_clbits']}"),
        (58, f"{metadata['gate_count']} gates"),
        (58, f"{len(metadata['gate_types'])} types"),
        (72, f"LLM {all_match}/{model_rows}"),
    ]
    for chip_width, value in metrics:
        color = TEAL if value == "signature hit" else RED if value.startswith("LLM") else TEXT
        stroke = TEAL if value == "signature hit" else "#b8c6d6"
        chip(lines, metric_x, metric_y, value, width=chip_width, stroke=stroke, color=color)
        metric_x += chip_width + 5

    target_y = y + 112
    lines.append(
        text(
            x + 16,
            target_y,
            f"Target circuit: operates on {metadata['num_qubits']} qubits and {metadata['num_clbits']} classical bits",
            size=10.7,
            fill=MUTED,
            weight=700,
        )
    )
    draw_circuit(lines, x + 16, y + 123, width - 32, 185, case)

    evaluator_y = y + 330
    lines.append(text(x + 16, evaluator_y, "Evaluator-selected circuit:", size=11.2, weight=800, fill=MUTED))
    lines.append(text(x + 158, evaluator_y, str(case["circuit_name"]), size=11.2, fill=MUTED))

    vocab_y = y + 351
    lines.append(text(x + 16, vocab_y, "gate vocabulary", size=10.7, weight=800, fill=MUTED))
    last_chip_y = gate_vocab_chips(lines, x + 16, vocab_y + 22, x + width - 16, metadata["gate_types"])

    evidence_y = max(y + 382, last_chip_y + 28)
    hit_lines = wrap(f"Signature hit: {case['copy_hit_label']}", 48)
    hit_box_top = evidence_y - 13
    hit_box_height = 25 + max(0, len(hit_lines) - 1) * 14
    lines.append(
        rect(
            x + 12,
            hit_box_top,
            width - 24,
            hit_box_height,
            fill="#edf8f6",
            stroke="#9acdc6",
            rx=4,
            stroke_width=0.9,
        )
    )
    for line_index, hit_line in enumerate(hit_lines):
        lines.append(
            text(
                x + 18,
                evidence_y + 3 + line_index * 14,
                hit_line,
                size=10.8,
                weight=700,
                fill=TEAL,
            )
        )
    external_y = hit_box_top + hit_box_height + 18
    lines.append(
        text(
            x + 16,
            external_y,
            f"External models: signature {all_match}/{model_rows}; execution {failure['execution_success']}/{model_rows}",
            size=11.7,
            fill=RED,
        )
    )
    family = pretty_family(str(case.get("families", "")))
    if family:
        family_y = external_y + 18
        lines.append(text(x + 16, family_y, f"Family: {family}", size=10.9, weight=700, fill=PLUM))
        prompt_y = family_y + 26
    else:
        prompt_y = external_y + 27
    lines.append(text(x + 16, prompt_y, "Prompt:", size=13.0, weight=800, fill=MUTED))
    prompt_width = width - 32
    prompt_value = PROMPT_SUMMARIES.get(case["prompt_id"], case["instruction"])
    prompt_lines = wrap(prompt_value, 48)
    for offset, value in enumerate(prompt_lines):
        lines.append(
            justified_text(
                x + 16,
                prompt_y + 18 + offset * 15.5,
                value,
                target_width=prompt_width,
                size=13.5,
                fill=TEXT,
                justify=offset < len(prompt_lines) - 1,
            )
        )


def build_svg(cases: list[dict[str, Any]]) -> str:
    templates = grouped_templates(cases)
    model_count = int(cases[0]["external_failure_summary"]["model_rows"])
    width = 1500
    height = 648
    margin = 24
    gap = 16
    card_w = (width - margin * 2 - gap * 3) / 4
    card_h = 552
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Targets matched only by retrieval-copy baselines</title>',
        f'<desc id="desc">Four structural-signature templates covering six held-out PQID-Bench prompt targets matched by retrieval-copy baselines and missed by all {model_count} external model rows.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        text(margin, 34, "Targets matched only by retrieval-copy baselines", size=21, weight=800),
    ]
    positions = [
        (margin, 64),
        (margin + card_w + gap, 64),
        (margin + 2 * (card_w + gap), 64),
        (margin + 3 * (card_w + gap), 64),
    ]
    for index, (case, (x, y)) in enumerate(zip(templates, positions), start=1):
        draw_card(lines, x, y, card_w, card_h, case, index)
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    cases = load_target_circuits()
    model_count = int(cases[0]["external_failure_summary"]["model_rows"])
    attempts = sum(int(case["external_failure_summary"]["model_rows"]) for case in cases)
    execution = sum(int(case["external_failure_summary"]["execution_success"]) for case in cases)
    qasm3 = sum(int(case["external_failure_summary"]["qasm3_success"]) for case in cases)
    gate_types = sum(int(case["external_failure_summary"]["gate_types_match"]) for case in cases)
    signature = sum(int(case["external_failure_summary"]["all_match"]) for case in cases)
    FIGURE_PATH.write_text(build_svg(cases), encoding="utf-8")
    CAPTION_PATH.write_text(
        "\n".join(
            [
                "**Main Figure 6B component. Retrieval-copy complementarity target templates.**",
                f"The four cards group six held-out prompt targets matched under the current reference-signature predicate by at least one retrieval-copy baseline and by none of the {model_count} completed external model rows.",
                "The first card groups three Bell-barrier prompt variants; the remaining cards show phase-flip error correction, an E91 basis-measurement subcircuit, and a three-basis measurement template.",
                f"Across the six prompt targets, external models execute in {execution}/{attempts} attempts and export QASM3 in {qasm3}/{attempts}; gate-type count-map agreement occurs in {gate_types}/{attempts} attempts, and reference-signature match is {signature}/{attempts}.",
                "The successful retrieval-copy cases preserve the four-component evaluator signature; they are not claimed as ordered-circuit or semantic-equivalence proofs.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {FIGURE_PATH}")
    print(f"Wrote {CAPTION_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
