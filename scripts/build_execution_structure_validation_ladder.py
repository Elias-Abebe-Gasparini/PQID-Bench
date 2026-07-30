"""Build the layered operational-to-structure validation schematic.

The figure consumes frozen analysis artifacts rather than duplicating reported
counts in drawing code. It separates executable-circuit materialization and
OpenQASM 3 assembly admissibility from the complete 21 x 154 reconstruction
ladder, the identifiable-subset structural-hallucination diagnostic, and
semantic equivalence, which is not nested in the reference ladder.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
FIGURES_DIR = ROOT / "figures"

ORDERED_JSON = ANALYSIS_DIR / "pqid_bench_ordered_operand_validation.json"
IDENTIFIABILITY_JSON = ANALYSIS_DIR / "pqid_bench_prompt_identifiability_sensitivity.json"
ASSEMBLY_JSON = ANALYSIS_DIR / "pqid_bench_operational_assembly_layer_audit.json"

SVG_PATH = FIGURES_DIR / "execution_structure_validation_ladder.svg"
PNG_PATH = FIGURES_DIR / "execution_structure_validation_ladder.png"
CAPTION_PATH = FIGURES_DIR / "execution_structure_validation_ladder_caption.md"


TEXT = "#18212f"
MUTED = "#465568"
TEAL = "#147d73"
CYAN = "#287f98"
BLUE = "#315fa8"
PLUM = "#7c3f72"
GOLD = "#b7791f"
RUST = "#bd4d00"
LINE = "#8f9daf"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 13,
            "text.color": TEXT,
            "mathtext.fontset": "custom",
            "mathtext.rm": "Times New Roman",
            "mathtext.it": "Times New Roman:italic",
            "mathtext.bf": "Times New Roman:bold",
            "mathtext.cal": "Times New Roman",
            "mathtext.sf": "Times New Roman",
            "mathtext.tt": "Times New Roman",
            "mathtext.fallback": "stix",
            "mathtext.default": "it",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    face: str,
    edge: str,
    linewidth: float = 1.4,
    linestyle: str = "-",
    radius: float = 0.08,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle=f"round,pad=0.018,rounding_size={radius}",
            facecolor=face,
            edgecolor=edge,
            linewidth=linewidth,
            linestyle=linestyle,
        )
    )


def draw_stage(
    ax: plt.Axes,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    color: str,
    face: str,
    symbol: str,
    title: str,
    description: str,
    count: int,
    denominator: int,
) -> None:
    rounded_box(ax, x, y, width, height, face=face, edge=color)
    ax.plot([x + 0.17, x + width - 0.17], [y + height - 0.18, y + height - 0.18], color=color, linewidth=4.2, solid_capstyle="round")
    title_size = 13.6 if len(title) > 20 else 15.2
    ax.text(x + width / 2, y + height - 0.48, symbol, fontsize=16.5, fontweight="bold", color=color, ha="center", va="top")
    ax.text(x + width / 2, y + height - 0.82, title, fontsize=title_size, fontweight="bold", color=TEXT, ha="center", va="top")
    ax.text(x + width / 2, y + height - 1.17, description, fontsize=11.4, color=MUTED, ha="center", va="top")
    ax.text(x + width / 2, y + 0.68, f"{count:,} / {denominator:,}", fontsize=16.2, fontweight="bold", color=TEXT, ha="center", va="center")
    ax.text(x + width / 2, y + 0.28, f"{100 * count / denominator:.2f}%", fontsize=20.5, fontweight="bold", color=color, ha="center", va="center")


def save_figure(fig: plt.Figure) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(SVG_PATH, format="svg", bbox_inches="tight", pad_inches=0.025)
    fig.savefig(PNG_PATH, format="png", dpi=240, bbox_inches="tight", pad_inches=0.025)
    plt.close(fig)
    with Image.open(PNG_PATH) as rendered:
        if rendered.mode != "RGB":
            rendered.convert("RGB").save(PNG_PATH)


def build_figure() -> dict[str, Any]:
    configure_style()
    ordered = load_json(ORDERED_JSON)
    identifiability = load_json(IDENTIFIABILITY_JSON)
    assembly_audit = load_json(ASSEMBLY_JSON)

    overall = ordered["overall"]
    design = ordered["design"]
    primary = identifiability["primary"]
    identifiable = identifiability["identifiable_sensitivity"]

    cells = int(design["cell_count"])
    executable = int(overall["report_executable"])
    assembly = int(assembly_audit["counts"]["A"])
    signature = int(overall["report_signature_matches"])
    ordered_wire = int(overall["ordered_wire_tape_given_signature"]["count"])
    parameter_aware = int(overall["parameter_aware_tape_given_signature"]["count"])

    assert cells == int(primary["n"])
    assert executable == int(primary["execution_count"])
    assert signature == int(primary["structural_count"])
    assert cells == int(assembly_audit["panel"]["cells"])
    assert executable == int(assembly_audit["counts"]["E"])
    assert signature == int(assembly_audit["counts"]["M_sig"])
    assert assembly_audit["nesting"]["A_not_E"] == 0
    assert assembly_audit["nesting"]["M_sig_not_A"] == 0
    assert parameter_aware <= ordered_wire <= signature <= assembly <= executable <= cells

    stages = [
        {
            "symbol": r"$E$",
            "title": "Executable circuit",
            "description": "Python completes; circuit selected",
            "count": executable,
            "color": TEAL,
            "face": "#eaf7f4",
        },
        {
            "symbol": r"$A$",
            "title": "Assembly admissible",
            "description": "OpenQASM 3 serialization",
            "count": assembly,
            "color": CYAN,
            "face": "#eaf6f9",
        },
        {
            "symbol": r"$M^{sig}$",
            "title": "Reference signature",
            "description": "Width and complete count map",
            "count": signature,
            "color": BLUE,
            "face": "#edf3fb",
        },
        {
            "symbol": r"$M^{ord}$",
            "title": "Ordered operation + wire",
            "description": "Names and operands in sequence",
            "count": ordered_wire,
            "color": PLUM,
            "face": "#f6eff7",
        },
        {
            "symbol": r"$M^{par}$",
            "title": "Parameter-aware",
            "description": "Ordered tape plus values",
            "count": parameter_aware,
            "color": GOLD,
            "face": "#fff6e8",
        },
    ]

    fig, ax = plt.subplots(figsize=(16.4, 6.1))
    ax.set_xlim(0, 16.4)
    ax.set_ylim(0, 6.1)
    ax.axis("off")

    ax.text(0.30, 5.74, "Complete frozen matrix", fontsize=14.2, fontweight="bold", ha="left", va="center")
    ax.text(0.30, 5.43, f"{design['model_count']} models x {design['prompt_count']} prompts = {cells:,} outputs", fontsize=12.1, color=MUTED, ha="left", va="center")
    ax.text(
        16.10,
        5.59,
        r"$M^{par}\ \preceq\ M^{ord}\ \preceq\ M^{sig}\ \preceq\ A\ \preceq\ E$",
        fontsize=18.5,
        fontweight="bold",
        color=TEXT,
        ha="right",
        va="center",
    )

    xs = [0.30, 3.48, 6.66, 9.84, 13.02]
    card_y = 2.72
    card_width = 2.62
    card_height = 2.30
    for x, stage in zip(xs, stages, strict=True):
        draw_stage(
            ax,
            x=x,
            y=card_y,
            width=card_width,
            height=card_height,
            color=stage["color"],
            face=stage["face"],
            symbol=stage["symbol"],
            title=stage["title"],
            description=stage["description"],
            count=stage["count"],
            denominator=cells,
        )

    for left_x, right_x in zip(xs[:-1], xs[1:], strict=True):
        ax.add_patch(
            FancyArrowPatch(
                (left_x + card_width + 0.05, card_y + 1.15),
                (right_x - 0.08, card_y + 1.15),
                arrowstyle="-|>",
                mutation_scale=15,
                linewidth=1.5,
                color=LINE,
            )
        )

    arrow_centers = [
        (left_x + card_width + right_x) / 2
        for left_x, right_x in zip(xs[:-1], xs[1:], strict=True)
    ]
    losses = [
        (
            arrow_centers[0],
            executable - assembly,
            f"{100 * (executable - assembly) / cells:.2f} pp",
            "operational attrition",
            MUTED,
        ),
        (
            arrow_centers[1],
            assembly - signature,
            f"{100 * (assembly - signature) / cells:.2f} pp",
            "AS-Gap",
            RUST,
        ),
        (
            arrow_centers[2],
            signature - ordered_wire,
            f"{100 * (signature - ordered_wire) / cells:.2f} pp",
            "signature-only passes",
            MUTED,
        ),
        (
            arrow_centers[3],
            ordered_wire - parameter_aware,
            f"{100 * (ordered_wire - parameter_aware) / cells:.2f} pp",
            "parameter mismatches",
            MUTED,
        ),
    ]
    for x, count, difference, label, color in losses:
        ax.text(x, 2.48, f"{count:,} | {difference}", fontsize=11.3, fontweight="bold", color=color, ha="center", va="top")
        ax.text(x, 2.24, label, fontsize=10.0, color=MUTED, ha="center", va="top")

    gap_labels = [
        ("Operational baseline", MUTED),
        (f"E-A  {100 * (executable - assembly) / cells:.2f} pp", CYAN),
        (f"ES-Gap  {100 * (executable - signature) / cells:.2f} pp", BLUE),
        (f"ES-Gap  {100 * (executable - ordered_wire) / cells:.2f} pp", PLUM),
        (f"ES-Gap  {100 * (executable - parameter_aware) / cells:.2f} pp", GOLD),
    ]
    for x, (label, color) in zip(xs, gap_labels, strict=True):
        ax.text(
            x + card_width / 2,
            1.83,
            label,
            fontsize=11.6 if label == "Operational baseline" else 12.0,
            fontweight="bold" if label != "Operational baseline" else "normal",
            color=color,
            ha="center",
        )

    rounded_box(ax, 0.30, 0.38, 7.62, 1.02, face="#fff7ed", edge=RUST, linewidth=1.2)
    ax.text(0.52, 1.10, "Identifiable 150-prompt subset", fontsize=12.5, fontweight="bold", color=RUST, ha="left", va="center")
    ax.text(
        0.52,
        0.72,
        f"{int(identifiable['execution_structure_gap_count']):,} structural hallucinations / "
        f"{int(identifiable['execution_count']):,} executable outputs = "
        f"{100 * float(identifiable['signature_wrong_given_execution']):.2f}% structural-hallucination rate",
        fontsize=11.2,
        color=TEXT,
        ha="left",
        va="center",
    )

    rounded_box(ax, 8.20, 0.38, 7.90, 1.02, face="#f8fafc", edge="#7b8794", linewidth=1.2, linestyle="--")
    ax.text(8.42, 1.10, "Semantic equivalence is a separate axis", fontsize=12.5, fontweight="bold", color=TEXT, ha="left", va="center")
    ax.text(
        8.42,
        0.72,
        "Reference-tape recovery neither proves nor is required for physical or semantic equivalence.",
        fontsize=11.5,
        color=MUTED,
        ha="left",
        va="center",
    )

    fig.subplots_adjust(left=0.012, right=0.988, top=0.975, bottom=0.035)
    save_figure(fig)

    return {
        "cells": cells,
        "executable": executable,
        "assembly": assembly,
        "signature": signature,
        "ordered_wire": ordered_wire,
        "parameter_aware": parameter_aware,
        "identifiable_n": int(identifiable["n"]),
        "identifiable_executable": int(identifiable["execution_count"]),
        "structural_hallucinations": int(identifiable["execution_structure_gap_count"]),
        "structural_hallucination_rate": float(identifiable["signature_wrong_given_execution"]),
    }


def write_caption(values: dict[str, Any]) -> None:
    operational_attrition = 100 * (values["executable"] - values["assembly"]) / values["cells"]
    assembly_gap = 100 * (values["assembly"] - values["signature"]) / values["cells"]
    signature_gap = 100 * (values["executable"] - values["signature"]) / values["cells"]
    ordered_gap = 100 * (values["executable"] - values["ordered_wire"]) / values["cells"]
    parameter_gap = 100 * (values["executable"] - values["parameter_aware"]) / values["cells"]
    CAPTION_PATH.write_text(
        "\n".join(
            [
                "# Layered Operational-To-Structure Validation",
                "",
                "**Figure 3. Operational-admissibility and nested reference-reconstruction ladder.** "
                f"On the complete `21 x 154` matrix (`N={values['cells']:,}`), `{values['executable']:,}` outputs materialize an executable circuit, "
                f"`{values['assembly']:,}` are quantum-assembly admissible through successful OpenQASM 3 serialization, "
                f"`{values['signature']:,}` recover the frozen reference signature, `{values['ordered_wire']:,}` additionally recover the ordered operation-and-wire tape, "
                f"and `{values['parameter_aware']:,}` additionally recover evaluator-normalized parameter values. "
                f"Operational attrition from `E` to `A` is only `{operational_attrition:.2f}` percentage points, whereas the Assembly-Structure Gap (AS-Gap) is `{assembly_gap:.2f}` points "
                f"and accounts for `{100 * (values['assembly'] - values['signature']) / (values['executable'] - values['signature']):.2f}%` of the `{signature_gap:.2f}`-point signature-level ES-Gap. "
                f"The cumulative ordered and parameter-aware ES-Gaps are `{ordered_gap:.2f}` and `{parameter_gap:.2f}` points. "
                f"The lower-left callout uses the distinct identifiable `150`-prompt denominator: `{values['structural_hallucinations']:,} / {values['identifiable_executable']:,} = "
                f"{100 * values['structural_hallucination_rate']:.2f}%` of executable outputs are structural hallucinations under the frozen reference-signature predicate. "
                "Semantic equivalence is shown separately because it is not nested in exact reference reconstruction.",
                "",
                "Source artifacts:",
                "",
                "- `artifacts/analysis_154/pqid_bench_ordered_operand_validation.json`",
                "- `artifacts/analysis_154/pqid_bench_prompt_identifiability_sensitivity.json`",
                "- `artifacts/analysis_154/pqid_bench_operational_assembly_layer_audit.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    values = build_figure()
    write_caption(values)
    print(f"Wrote {SVG_PATH}")
    print(f"Wrote {PNG_PATH}")
    print(f"Wrote {CAPTION_PATH}")


if __name__ == "__main__":
    main()
