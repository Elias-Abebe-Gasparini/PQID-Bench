"""Build the supplemental methodological and result-expansion figures S6--S11.

The builder reads the frozen benchmark artifacts wherever a panel reports data.
Diagram-only panels encode the analysis contract documented in Supplemental
Methods SM1--SM13.  No model output is regenerated or rescored here.
"""

from __future__ import annotations

import csv
import json
import textwrap
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
FIGURES = ROOT / "figures"
TABLES = ROOT / "tables_copy_ready"

ROBUSTNESS_JSON = (
    ARTIFACTS / "analysis_154/pqid_bench_replication_crossed_family_vendor_robustness.json"
)
IDENTIFIABILITY_JSON = ARTIFACTS / "analysis_154/pqid_bench_prompt_identifiability_sensitivity.json"
ORDERED_JSON = ARTIFACTS / "analysis_154/pqid_bench_ordered_operand_validation.json"
EVALUATOR_JSON = (
    ARTIFACTS / "analysis_154/evaluator_builtin_correction/evaluator_builtin_correction_report.json"
)
CONTEXT_JSON = ARTIFACTS / "pqid_bench_context_recovery_ablation_report.json"
REPEATABILITY_JSON = (
    ARTIFACTS
    / "stochastic_repeatability_21x72/consolidated/analysis/"
    / "pqid_bench_stochastic_repeatability_analysis.json"
)
ALGORITHM_FAMILY_TSV = TABLES / "table_s34_canonical_algorithm_family_results.tsv"
ALGORITHM_PROMPT_TSV = TABLES / "table_s34_canonical_algorithm_prompt_audit.tsv"


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
PALE_TEAL = "#e9f6f3"
PALE_BLUE = "#edf3fb"
PALE_RUST = "#fff4e8"
PALE_PLUM = "#f6eff7"
PALE_GOLD = "#fff8e7"
PALE_GRAY = "#f3f5f7"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 12,
            "text.color": TEXT,
            "axes.labelcolor": TEXT,
            "axes.edgecolor": GRID,
            "xtick.color": MUTED,
            "ytick.color": TEXT,
            "mathtext.fontset": "stix",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "figure.facecolor": PAPER,
            "savefig.facecolor": PAPER,
        }
    )


def wrap(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(value, width=width, break_long_words=False))


def card(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    face: str = PANEL_BG,
    edge: str = "#cbd5e1",
    linewidth: float = 1.0,
    radius: float = 0.012,
    zorder: int = 0,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        transform=ax.transAxes,
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def panel_heading(
    ax: plt.Axes,
    x: float,
    y: float,
    letter: str,
    title: str,
    *,
    size: float = 14.5,
) -> None:
    ax.text(
        x,
        y,
        letter,
        transform=ax.transAxes,
        fontsize=size,
        fontweight="bold",
        color=BLUE,
        ha="left",
        va="top",
    )
    ax.text(
        x + 0.025,
        y,
        title,
        transform=ax.transAxes,
        fontsize=size,
        fontweight="bold",
        color=TEXT,
        ha="left",
        va="top",
    )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = "#94a3b8",
    width: float = 1.5,
    style: str = "-|>",
    mutation_scale: float = 12,
    zorder: int = 3,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle=style,
            mutation_scale=mutation_scale,
            linewidth=width,
            color=color,
            shrinkA=1,
            shrinkB=1,
            zorder=zorder,
        )
    )


def node(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    accent: str,
    face: str = PAPER,
    title_size: float = 11.8,
    body_size: float = 9.7,
    body_width: int = 34,
) -> None:
    card(ax, x, y, width, height, face=face, edge="#cbd5e1", radius=0.009)
    ax.add_patch(
        Rectangle(
            (x, y + height - 0.012),
            width,
            0.012,
            transform=ax.transAxes,
            facecolor=accent,
            edgecolor=accent,
            zorder=2,
        )
    )
    ax.text(
        x + 0.015,
        y + height - 0.035,
        title,
        transform=ax.transAxes,
        fontsize=title_size,
        fontweight="bold",
        color=TEXT,
        ha="left",
        va="top",
    )
    ax.text(
        x + 0.015,
        y + height - 0.064,
        wrap(body, body_width),
        transform=ax.transAxes,
        fontsize=body_size,
        color=MUTED,
        ha="left",
        va="top",
        linespacing=1.25,
    )


def save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    svg = FIGURES / f"{stem}.svg"
    png = FIGURES / f"{stem}.png"
    fig.savefig(svg, format="svg", bbox_inches="tight", pad_inches=0.025)
    fig.savefig(png, format="png", dpi=300, bbox_inches="tight", pad_inches=0.025)
    plt.close(fig)
    with Image.open(png) as rendered:
        if rendered.mode != "RGB":
            rendered.convert("RGB").save(png)
    return svg, png


def bare_canvas(figsize: tuple[float, float]) -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def build_design_estimand_map() -> None:
    ident = load_json(IDENTIFIABILITY_JSON)
    primary = ident["primary"]
    identifiable = ident["identifiable_sensitivity"]

    fig, ax = bare_canvas((14.0, 7.4))
    panels = [
        (0.025, 0.525, 0.46, 0.445),
        (0.515, 0.525, 0.46, 0.445),
        (0.025, 0.035, 0.46, 0.445),
        (0.515, 0.035, 0.46, 0.445),
    ]
    for x, y, w, h in panels:
        card(ax, x, y, w, h)

    # A. Frozen crossed panel.
    x, y, w, h = panels[0]
    panel_heading(ax, x + 0.018, y + h - 0.025, "A", "Frozen crossed panel")
    grid_x, grid_y = x + 0.045, y + 0.085
    cols, rows = 12, 7
    cell_w, cell_h = 0.0105, 0.021
    for row in range(rows):
        for col in range(cols):
            color = PALE_BLUE if (row + col) % 4 else PALE_TEAL
            ax.add_patch(
                Rectangle(
                    (grid_x + col * (cell_w + 0.002), grid_y + row * (cell_h + 0.004)),
                    cell_w,
                    cell_h,
                    transform=ax.transAxes,
                    facecolor=color,
                    edgecolor=PAPER,
                    linewidth=0.4,
                )
            )
    ax.text(grid_x + 0.071, grid_y - 0.026, "154 held-out prompts", transform=ax.transAxes, fontsize=10.8, ha="center", color=MUTED)
    ax.text(grid_x - 0.018, grid_y + 0.085, "21 model routes", transform=ax.transAxes, fontsize=10.8, ha="center", va="center", rotation=90, color=MUTED)
    metrics = [
        ("3,234", "model-prompt cells", TEAL),
        ("144", "target-signature clusters", BLUE),
        ("one", "canonical result per cell", PLUM),
    ]
    for idx, (value, label, color) in enumerate(metrics):
        my = y + 0.275 - idx * 0.092
        ax.text(x + 0.255, my, value, transform=ax.transAxes, fontsize=21, fontweight="bold", color=color, ha="left", va="center")
        ax.text(x + 0.335, my, wrap(label, 20), transform=ax.transAxes, fontsize=10.8, color=MUTED, ha="left", va="center")
    ax.text(x + 0.045, y + 0.325, "schematic matrix", transform=ax.transAxes, fontsize=10.2, fontweight="bold", color=TEXT, ha="left")

    # B. Mutually exclusive observed states under M <= E.
    x, y, w, h = panels[1]
    panel_heading(ax, x + 0.018, y + h - 0.025, "B", "Cell states under the scored predicate")
    states = [
        ("E = 0", "nonexecution", "#64748b", PALE_GRAY),
        ("E = 1, M = 0", "executable disagreement", RUST, PALE_RUST),
        ("E = 1, M = 1", "signature recovery", TEAL, PALE_TEAL),
    ]
    for idx, (symbol, label, color, face) in enumerate(states):
        cx = x + 0.083 + idx * 0.145
        cy = y + 0.235
        circle = plt.Circle((cx, cy), 0.047, transform=ax.transAxes, facecolor=face, edgecolor=color, linewidth=2)
        ax.add_patch(circle)
        ax.text(cx, cy + 0.003, symbol, transform=ax.transAxes, fontsize=11.3, fontweight="bold", color=color, ha="center", va="center")
        ax.text(cx, cy - 0.078, wrap(label, 19), transform=ax.transAxes, fontsize=10.8, color=TEXT, ha="center", va="top")
    ax.text(x + w / 2, y + 0.080, r"$M_{if}\leq E_{if}$: a signature pass is always executable", transform=ax.transAxes, fontsize=13.0, fontweight="bold", color=BLUE, ha="center", va="center")

    # C. Denominator map.
    x, y, w, h = panels[2]
    panel_heading(ax, x + 0.018, y + h - 0.025, "C", "Primary and identifiable denominators")
    bands = [
        (
            r"$\mathcal{T}$",
            "154 prompts · 3,234 cells",
            f"E {primary['execution_count']:,} · M {primary['structural_count']:,} · ES-Gap {100 * primary['execution_structure_gap_rate']:.2f} pp",
            BLUE,
            PALE_BLUE,
        ),
        (
            r"$\mathcal{T}_{id}$",
            "150 prompts · 3,150 cells",
            f"E {identifiable['execution_count']:,} · M {identifiable['structural_count']:,} · SHR {100 * identifiable['signature_wrong_given_execution']:.2f}%",
            TEAL,
            PALE_TEAL,
        ),
    ]
    for idx, (symbol, subtitle, detail, color, face) in enumerate(bands):
        by = y + 0.235 - idx * 0.145
        card(ax, x + 0.035, by, w - 0.070, 0.115, face=face, edge=color, radius=0.008)
        ax.text(x + 0.060, by + 0.074, symbol, transform=ax.transAxes, fontsize=17, fontweight="bold", color=color, ha="left", va="center")
        ax.text(x + 0.130, by + 0.080, subtitle, transform=ax.transAxes, fontsize=11.8, fontweight="bold", color=TEXT, ha="left", va="center")
        ax.text(x + 0.130, by + 0.038, detail, transform=ax.transAxes, fontsize=10.6, color=MUTED, ha="left", va="center")
    ax.text(
        x + 0.035,
        y + 0.030,
        wrap(
            "Four wording exceptions are removed only for structural-hallucination attribution; all rates are recomputed on one common subset denominator.",
            72,
        ),
        transform=ax.transAxes,
        fontsize=9.5,
        color=MUTED,
        ha="left",
        va="bottom",
        linespacing=1.15,
    )

    # D. Inference units.
    x, y, w, h = panels[3]
    panel_heading(ax, x + 0.018, y + h - 0.025, "D", "Observed units and dependence controls")
    units = [
        ("Prompt", "grouped-binomial counts\nover 21 routes", TEAL),
        ("Signature", "cluster resampling\nover 144 targets", BLUE),
        ("Model pair", "paired prompt contrasts\nwith multiplicity control", PLUM),
    ]
    for idx, (title, body, color) in enumerate(units):
        ux = x + 0.032 + idx * 0.142
        card(ax, ux, y + 0.125, 0.122, 0.190, face=PAPER, edge=color, radius=0.008)
        ax.text(ux + 0.061, y + 0.270, title, transform=ax.transAxes, fontsize=12.2, fontweight="bold", color=color, ha="center", va="center")
        ax.text(ux + 0.061, y + 0.205, body, transform=ax.transAxes, fontsize=10.1, color=MUTED, ha="center", va="center", linespacing=1.22)
    ax.text(
        x + w / 2,
        y + 0.052,
        wrap(
            "Finite crossed panel: uncertainty describes composition sensitivity, not universal-population sampling.",
            66,
        ),
        transform=ax.transAxes,
        fontsize=9.7,
        fontweight="bold",
        color=TEXT,
        ha="center",
        va="center",
        linespacing=1.15,
    )

    save(fig, "supplemental_experimental_design_estimand_map")


def build_inference_workflow() -> None:
    fig, ax = bare_canvas((14.0, 8.0))
    lanes = [
        (0.755, TEAL, PALE_TEAL, "A", "Task-feature association"),
        (0.515, BLUE, PALE_BLUE, "B", "Signature-grouped prediction"),
        (0.275, PLUM, PALE_PLUM, "C", "Paired model contrasts"),
        (0.035, RUST, PALE_RUST, "D", "Composition-aware uncertainty"),
    ]
    for y, color, face, letter, title in lanes:
        card(ax, 0.025, y, 0.95, 0.205, face=face, edge=color, radius=0.010)
        panel_heading(ax, 0.043, y + 0.178, letter, title, size=13.8)

    # Lane A.
    y = lanes[0][0]
    node(ax, 0.055, y + 0.020, 0.185, 0.125, "Aggregate by prompt", r"$Y_i^E$, $Y_i^A$, $Y_i^M$, and $Y_i^M\mid Y_i^E$ over 21 routes", accent=TEAL, face=PAPER, body_width=31)
    node(ax, 0.300, y + 0.020, 0.205, 0.125, "Fit separate layers", "Grouped-binomial logit for execution, signature, and signature conditional on execution", accent=TEAL, face=PAPER, body_width=34)
    node(ax, 0.565, y + 0.020, 0.175, 0.125, "Report effects", "Odds ratios per SD and average marginal effects", accent=TEAL, face=PAPER, body_width=26)
    node(ax, 0.800, y + 0.020, 0.145, 0.125, "Interpretation", "Adjusted association, not causal identification", accent=TEAL, face=PAPER, body_width=22)
    for start, end in [((0.242, y + 0.088), (0.296, y + 0.088)), ((0.507, y + 0.088), (0.561, y + 0.088)), ((0.742, y + 0.088), (0.796, y + 0.088))]:
        arrow(ax, start, end, color=TEAL)

    # Lane B.
    y = lanes[1][0]
    node(ax, 0.055, y + 0.020, 0.180, 0.125, "Assign whole signatures", "All prompts sharing a target signature enter the same fold", accent=BLUE, face=PAPER, body_width=30)
    node(ax, 0.295, y + 0.020, 0.180, 0.125, "Ten grouped folds", "Training-only standardization; observed-model fixed effects", accent=BLUE, face=PAPER, body_width=29)
    node(ax, 0.535, y + 0.020, 0.180, 0.125, "Out-of-fold scores", "AUC, Brier score, and log loss for each specification", accent=BLUE, face=PAPER, body_width=29)
    node(ax, 0.775, y + 0.020, 0.170, 0.125, "Compare models", "Cluster-bootstrap differences from size-only prediction", accent=BLUE, face=PAPER, body_width=27)
    for start, end in [((0.237, y + 0.088), (0.291, y + 0.088)), ((0.477, y + 0.088), (0.531, y + 0.088)), ((0.717, y + 0.088), (0.771, y + 0.088))]:
        arrow(ax, start, end, color=BLUE)

    # Lane C.
    y = lanes[2][0]
    node(ax, 0.055, y + 0.020, 0.180, 0.125, "Pair on prompts", r"Compute $M_{ib}-M_{ia}$ for declared model pairs", accent=PLUM, face=PAPER, body_width=28)
    node(ax, 0.295, y + 0.020, 0.180, 0.125, "Respect signatures", "Bootstrap complete signature clusters; preserve prompt pairing", accent=PLUM, face=PAPER, body_width=29)
    node(ax, 0.535, y + 0.020, 0.180, 0.125, "Test the null", "50,000 cluster-level random sign flips", accent=PLUM, face=PAPER, body_width=28)
    node(ax, 0.775, y + 0.020, 0.170, 0.125, "Control the family", "Holm adjustment; McNemar retained as a diagnostic", accent=PLUM, face=PAPER, body_width=27)
    for start, end in [((0.237, y + 0.088), (0.291, y + 0.088)), ((0.477, y + 0.088), (0.531, y + 0.088)), ((0.717, y + 0.088), (0.771, y + 0.088))]:
        arrow(ax, start, end, color=PLUM)

    # Lane D.
    y = lanes[3][0]
    node(ax, 0.055, y + 0.020, 0.205, 0.125, "One-way signature bootstrap", "Resample 144 complete signature clusters; condition on the 21-model roster", accent=RUST, face=PAPER, body_width=33)
    node(ax, 0.330, y + 0.020, 0.205, 0.125, "Crossed bootstrap", "Resample model rows and signature clusters independently", accent=RUST, face=PAPER, body_width=33)
    node(ax, 0.605, y + 0.020, 0.155, 0.125, "Percentile intervals", "Recompute the full statistic in every replicate", accent=RUST, face=PAPER, body_width=25)
    node(ax, 0.830, y + 0.020, 0.115, 0.125, "Scope", "Panel-composition sensitivity", accent=RUST, face=PAPER, body_width=18)
    for start, end in [((0.262, y + 0.088), (0.326, y + 0.088)), ((0.537, y + 0.088), (0.601, y + 0.088)), ((0.762, y + 0.088), (0.826, y + 0.088))]:
        arrow(ax, start, end, color=RUST)

    save(fig, "supplemental_dependence_aware_inference_workflow")


def build_robustness_atlas() -> None:
    robustness = load_json(ROBUSTNESS_JSON)
    ident = load_json(IDENTIFIABILITY_JSON)
    ordered = load_json(ORDERED_JSON)

    crossed = robustness["crossed_model_signature_bootstrap"]
    replication = robustness["pilot_extension_replication"]["final_21"]
    family = robustness["family_and_developer_sensitivity"]
    primary_family_gap = (
        family["execution_family_balance"]["primary_family_macro_rate"]
        - family["signature_family_balance"]["primary_family_macro_rate"]
    )
    rare_family_gap = (
        family["execution_family_balance"]["rare_pooled_primary_family_macro_rate"]
        - family["signature_family_balance"]["rare_pooled_primary_family_macro_rate"]
    )
    overall_ordered = ordered["overall"]
    cells = ordered["design"]["cell_count"]
    execution = overall_ordered["report_executable"]
    ordered_count = overall_ordered["ordered_wire_tape_given_signature"]["count"]
    parameter_count = overall_ordered["parameter_aware_tape_given_signature"]["count"]

    rows = [
        ("Primary complete matrix", 100 * crossed["execution_structure_gap"], tuple(100 * x for x in crossed["gap_crossed_bootstrap_95"]), TEAL, "o"),
        ("Pilot cohort", 100 * replication["pilot"]["execution_structure_gap"], tuple(100 * x for x in replication["pilot"]["gap_cluster_bootstrap_95"]), BLUE, "o"),
        ("Signature-disjoint extension", 100 * replication["extension"]["execution_structure_gap"], tuple(100 * x for x in replication["extension"]["gap_cluster_bootstrap_95"]), BLUE, "o"),
        ("Identifiable 150-prompt subset", 100 * ident["identifiable_sensitivity"]["execution_structure_gap_rate"], None, PLUM, "D"),
        ("Equal primary-family weights", 100 * primary_family_gap, None, PLUM, "D"),
        ("Rare-family-pooled weights", 100 * rare_family_gap, None, PLUM, "D"),
        ("Ordered operation + wire", 100 * (execution - ordered_count) / cells, None, RUST, "s"),
        ("Parameter-aware tape", 100 * (execution - parameter_count) / cells, None, RUST, "s"),
    ]
    y_positions = [8.0, 7.0, 6.0, 4.55, 3.55, 2.55, 1.05, 0.05]

    fig = plt.figure(figsize=(14.0, 8.0))
    ax_a = fig.add_axes([0.245, 0.10, 0.365, 0.83])
    ax_b = fig.add_axes([0.730, 0.56, 0.240, 0.35])
    ax_c = fig.add_axes([0.760, 0.09, 0.210, 0.36])

    # A. Forest/specification plot.
    for (label, estimate, ci, color, marker), y in zip(rows, y_positions, strict=True):
        if ci is not None:
            low, high = ci
            ax_a.plot([low, high], [y, y], color=color, linewidth=2.2, solid_capstyle="round")
            ax_a.plot([low, low], [y - 0.09, y + 0.09], color=color, linewidth=1.4)
            ax_a.plot([high, high], [y - 0.09, y + 0.09], color=color, linewidth=1.4)
        ax_a.scatter(estimate, y, s=78, color=color, edgecolor=PAPER, linewidth=0.9, marker=marker, zorder=4)
        ax_a.text(51.2, y, f"{estimate:.2f}", fontsize=10.5, fontweight="bold", color=color, ha="right", va="center", clip_on=True)
    ax_a.axvline(100 * crossed["execution_structure_gap"], color="#94a3b8", linestyle="--", linewidth=1.2, zorder=0)
    ax_a.set_xlim(22, 52)
    ax_a.set_ylim(-0.7, 9.1)
    ax_a.set_yticks(y_positions)
    ax_a.set_yticklabels([row[0] for row in rows], fontsize=11.0)
    ax_a.set_xlabel("Execution-Structure Gap (percentage points)", fontsize=11.5, fontweight="bold")
    ax_a.grid(axis="x", color=GRID, linewidth=0.8)
    ax_a.spines[["top", "right", "left"]].set_visible(False)
    ax_a.tick_params(axis="y", length=0)
    ax_a.text(22.0, 8.75, "A  Replication and specification atlas", fontsize=14.3, fontweight="bold", color=TEXT, ha="left")
    ax_a.text(22.0, 8.37, "Same signature-level estimand", fontsize=10.5, fontweight="bold", color=TEAL, ha="left")
    ax_a.text(22.0, 5.25, "Denominator or weighting sensitivity", fontsize=10.5, fontweight="bold", color=PLUM, ha="left")
    ax_a.text(22.0, 1.72, "Stricter reconstruction predicates", fontsize=10.5, fontweight="bold", color=RUST, ha="left")
    legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=TEAL, markersize=7, label="interval reported"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor=PLUM, markersize=7, label="point sensitivity"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=RUST, markersize=7, label="predicate extension"),
    ]
    ax_a.legend(handles=legend, loc="lower left", frameon=False, fontsize=9.8, ncol=3, bbox_to_anchor=(-0.02, -0.13))

    # B. Leave-one-developer-out lollipops.
    lodo = [row for row in family["leave_one_developer_out"] if row["omitted_developer"] != "none"]
    lodo.sort(key=lambda row: row["execution_structure_gap"])
    y = np.arange(len(lodo))
    vals = np.array([100 * row["execution_structure_gap"] for row in lodo])
    full = 100 * crossed["execution_structure_gap"]
    for idx, value in enumerate(vals):
        ax_b.plot([full, value], [idx, idx], color="#aab7c6", linewidth=2)
        ax_b.scatter(value, idx, s=55, color=BLUE if value >= full else RUST, zorder=3)
    ax_b.axvline(full, color=TEAL, linewidth=1.4, linestyle="--")
    ax_b.set_yticks(y)
    ax_b.set_yticklabels([row["omitted_developer"] for row in lodo], fontsize=9.8)
    ax_b.set_xlim(36.5, 40.3)
    ax_b.set_xlabel("ES-Gap (pp)", fontsize=10.5, fontweight="bold")
    ax_b.grid(axis="x", color=GRID, linewidth=0.7)
    ax_b.spines[["top", "right", "left"]].set_visible(False)
    ax_b.tick_params(axis="y", length=0)
    ax_b.text(36.5, len(lodo) - 0.05, "B  Leave one developer out", fontsize=13.3, fontweight="bold", ha="left", va="bottom")
    ax_b.text(36.5, len(lodo) - 0.55, f"range {vals.min():.2f}-{vals.max():.2f} pp; full {full:.2f}", fontsize=9.7, color=MUTED, ha="left", va="bottom")

    # C. Audit-dimension matrix.
    matrix_rows = [
        ("Pilot / extension", [1, 0, 0, 0]),
        ("Crossed bootstrap", [1, 1, 0, 0]),
        ("Family balance", [0, 0, 1, 0]),
        ("Developer omission", [0, 1, 0, 0]),
        ("Identifiable subset", [1, 0, 0, 0]),
        ("Ordered / parameter", [0, 0, 0, 1]),
    ]
    columns = ["Prompts", "Models", "Weights", "Predicate"]
    ax_c.set_xlim(-0.5, 3.5)
    ax_c.set_ylim(-0.65, len(matrix_rows) - 0.1)
    for row_idx, (_, values) in enumerate(matrix_rows):
        for col_idx, active in enumerate(values):
            face = [PALE_TEAL, PALE_BLUE, PALE_PLUM, PALE_RUST][col_idx] if active else PALE_GRAY
            edge = [TEAL, BLUE, PLUM, RUST][col_idx] if active else GRID
            ax_c.add_patch(Rectangle((col_idx - 0.38, row_idx - 0.35), 0.76, 0.70, facecolor=face, edgecolor=edge, linewidth=1.0))
            if active:
                ax_c.text(col_idx, row_idx, "●", fontsize=12, color=edge, ha="center", va="center")
    ax_c.set_xticks(range(4))
    ax_c.set_xticklabels(columns, fontsize=9.4, rotation=30, ha="right")
    ax_c.set_yticks(range(len(matrix_rows)))
    ax_c.set_yticklabels([row[0] for row in matrix_rows], fontsize=8.9)
    ax_c.invert_yaxis()
    ax_c.tick_params(length=0)
    ax_c.spines[:].set_visible(False)
    ax_c.text(-0.5, -0.88, "C  What each audit changes", fontsize=13.3, fontweight="bold", ha="left", va="bottom")
    ax_c.text(3.5, len(matrix_rows) - 0.05, "filled cell = deliberately varied dimension", fontsize=9.5, color=MUTED, ha="right", va="bottom")

    save(fig, "supplemental_robustness_atlas")


def build_evaluator_integrity_audit() -> None:
    evaluator = load_json(EVALUATOR_JSON)
    context = load_json(CONTEXT_JSON)
    legacy = evaluator["legacy"]
    canonical = evaluator["canonical"]
    summary = context["summary"]

    fig, ax = bare_canvas((14.0, 7.2))
    card(ax, 0.025, 0.09, 0.46, 0.84)
    card(ax, 0.515, 0.48, 0.46, 0.45)
    card(ax, 0.515, 0.09, 0.46, 0.33)

    # A. Evaluator counterfactual.
    panel_heading(ax, 0.045, 0.90, "A", "Paired evaluator-version counterfactual")
    x0, x1 = 0.15, 0.435
    rate_min, rate_max = 45.0, 95.0

    def scale(value: float) -> float:
        return x0 + (100 * value - rate_min) / (rate_max - rate_min) * (x1 - x0)

    for tick in [50, 60, 70, 80, 90]:
        tx = x0 + (tick - rate_min) / (rate_max - rate_min) * (x1 - x0)
        ax.plot([tx, tx], [0.33, 0.75], transform=ax.transAxes, color=GRID, linewidth=0.8, zorder=0)
        ax.text(tx, 0.305, f"{tick}%", transform=ax.transAxes, fontsize=9.7, color=MUTED, ha="center")
    outcomes = [
        ("Execution", legacy["execution_rate"], canonical["execution_rate"], evaluator["execution_transition"]["gained"], 0.66, TEAL),
        ("Reference signature", legacy["signature_rate"], canonical["signature_rate"], evaluator["signature_transition"]["gained"], 0.45, BLUE),
    ]
    for label, before, after, gained, yy, color in outcomes:
        xb, xa = scale(before), scale(after)
        ax.plot([xb, xa], [yy, yy], transform=ax.transAxes, color="#94a3b8", linewidth=3.0, solid_capstyle="round")
        ax.scatter([xb], [yy], transform=ax.transAxes, s=95, facecolor=PAPER, edgecolor="#64748b", linewidth=2.0, zorder=4)
        ax.scatter([xa], [yy], transform=ax.transAxes, s=105, facecolor=color, edgecolor=PAPER, linewidth=1.0, zorder=4)
        display_label = "Reference\nsignature" if label == "Reference signature" else label
        ax.text(0.055, yy, display_label, transform=ax.transAxes, fontsize=12.0, fontweight="bold", color=TEXT, ha="left", va="center", linespacing=1.05)
        ax.text(xb - 0.004, yy + 0.045, f"{100 * before:.2f}%", transform=ax.transAxes, fontsize=10.1, color="#64748b", ha="right")
        ax.text(xa + 0.004, yy + 0.045, f"{100 * after:.2f}%", transform=ax.transAxes, fontsize=10.3, fontweight="bold", color=color, ha="left")
        ax.text((xb + xa) / 2, yy - 0.058, f"+{gained} cells; 0 losses", transform=ax.transAxes, fontsize=10.5, fontweight="bold", color=color, ha="center")
    ax.text(0.095, 0.795, "restricted built-ins", transform=ax.transAxes, fontsize=10.2, color="#64748b", ha="center")
    ax.text(0.415, 0.795, "safe built-ins", transform=ax.transAxes, fontsize=10.2, color=TEAL, ha="center")
    ax.text(0.055, 0.205, wrap("Only ordinary Python built-ins print and reversed change. The 154 prompts, 3,234 frozen responses, targets, hashes, and count-map predicate remain identical.", 64), transform=ax.transAxes, fontsize=11.0, color=MUTED, ha="left", va="top", linespacing=1.30)
    ax.text(0.055, 0.115, "paired deterministic replay · no regeneration", transform=ax.transAxes, fontsize=11.7, fontweight="bold", color=RUST, ha="left", va="center")

    # B. Source context-recovery funnel.
    panel_heading(ax, 0.535, 0.90, "B", "Metadata-assisted source context recovery")
    total = summary["total_clean_rows"]
    strict = summary["strict_execution_success"]
    targets = summary["target_rows"]
    rec_exec = summary["recovered_execution_success"]
    rec_sig = summary["recovered_structural_match"]
    bar_x, bar_y, bar_w, bar_h = 0.55, 0.715, 0.39, 0.075
    strict_w = bar_w * strict / total
    ax.add_patch(Rectangle((bar_x, bar_y), strict_w, bar_h, transform=ax.transAxes, facecolor=TEAL, edgecolor=PAPER))
    ax.add_patch(Rectangle((bar_x + strict_w, bar_y), bar_w - strict_w, bar_h, transform=ax.transAxes, facecolor=PALE_RUST, edgecolor=RUST))
    ax.text(bar_x + strict_w / 2, bar_y + bar_h / 2, f"{strict} strict successes", transform=ax.transAxes, fontsize=11.2, fontweight="bold", color=PAPER, ha="center", va="center")
    ax.text(bar_x + strict_w + (bar_w - strict_w) / 2, bar_y + bar_h / 2, f"{targets}", transform=ax.transAxes, fontsize=10.4, fontweight="bold", color=RUST, ha="center", va="center")
    ax.text(bar_x, bar_y + 0.105, f"{total} clean source rows", transform=ax.transAxes, fontsize=11.5, fontweight="bold", color=TEXT, ha="left")
    ax.text(bar_x + bar_w, bar_y + 0.105, f"{targets} strict NameError targets", transform=ax.transAxes, fontsize=10.5, fontweight="bold", color=RUST, ha="right")
    arrow(ax, (0.745, 0.695), (0.745, 0.640), color=RUST)
    recovery_nodes = [
        ("69 / 69", "execute after\ncontext recovery", TEAL, PALE_TEAL),
        ("67 / 69", "match stored\nsignature", BLUE, PALE_BLUE),
        ("18 / 18", "eligible simulations\nsucceed", PLUM, PALE_PLUM),
    ]
    for idx, (value, label, color, face) in enumerate(recovery_nodes):
        nx = 0.545 + idx * 0.137
        card(ax, nx, 0.515, 0.120, 0.105, face=face, edge=color, radius=0.007)
        ax.text(nx + 0.060, 0.583, value, transform=ax.transAxes, fontsize=14.3, fontweight="bold", color=color, ha="center", va="center")
        ax.text(nx + 0.060, 0.535, label, transform=ax.transAxes, fontsize=9.8, color=MUTED, ha="center", va="center", linespacing=1.15)

    # C. Scope boundary.
    panel_heading(ax, 0.535, 0.39, "C", "Two audits, two scientific questions")
    node(ax, 0.545, 0.165, 0.185, 0.145, "External-model evaluator", "Does evaluator admissibility alter outcomes when every generated response is frozen?", accent=RUST, face=PAPER, body_width=31)
    node(ax, 0.765, 0.165, 0.180, 0.145, "Clean-source validity", "Can missing local context explain strict source-snippet failures?", accent=PLUM, face=PAPER, body_width=29)
    ax.plot([0.747, 0.747], [0.145, 0.325], transform=ax.transAxes, color="#94a3b8", linewidth=1.2, linestyle="--")
    ax.text(0.745, 0.120, "reported separately; neither audit changes model outputs or target definitions", transform=ax.transAxes, fontsize=10.5, fontweight="bold", color=TEXT, ha="center", va="center")

    save(fig, "supplemental_evaluator_integrity_audit")


def _parse_fraction_rate(value: str) -> tuple[int, int, float]:
    fraction, parenthetical = value.split(" ", 1)
    numerator, denominator = fraction.split("/")
    rate = float(parenthetical.strip("()%")) / 100
    return int(numerator), int(denominator), rate


def build_canonical_algorithm_recovery() -> None:
    family_rows = [row for row in load_tsv(ALGORITHM_FAMILY_TSV) if row["algorithm_family"] != "Combined"]
    prompt_rows = load_tsv(ALGORITHM_PROMPT_TSV)
    family_colors = {
        "Deutsch / Deutsch--Jozsa": BLUE,
        "Deutsch--Jozsa": BLUE,
        "Deutsch": BLUE,
        "Deutsch setup": BLUE,
        "Bernstein--Vazirani": RUST,
        "Simon setup": TEAL,
        "Grover setup": PLUM,
    }

    fig = plt.figure(figsize=(14.0, 8.6))
    ax_a = fig.add_axes([0.105, 0.13, 0.335, 0.78])
    ax_b = fig.add_axes([0.57, 0.10, 0.385, 0.82])

    # A. Family execution-signature dumbbells.
    labels: list[str] = []
    for idx, row in enumerate(family_rows):
        y = len(family_rows) - 1 - idx
        _, _, execution = _parse_fraction_rate(row["execution"])
        _, _, signature = _parse_fraction_rate(row["signature_match"])
        color = family_colors[row["algorithm_family"]]
        ax_a.plot([100 * signature, 100 * execution], [y, y], color=color, linewidth=4.0, alpha=0.55, solid_capstyle="round")
        ax_a.scatter(100 * execution, y, s=100, color=TEAL, edgecolor=PAPER, linewidth=1.0, zorder=4)
        ax_a.scatter(100 * signature, y, s=95, color=BLUE, marker="s", edgecolor=PAPER, linewidth=1.0, zorder=4)
        ax_a.text(101.5, y, f"gap {float(row['signature_level_es_gap_pp']):.2f} pp", fontsize=10.2, fontweight="bold", color=color, ha="left", va="center")
        labels.append(row["algorithm_family"].replace("--", "-") + f"  (n={row['prompts']})")
    ax_a.set_yticks(range(len(family_rows)))
    ax_a.set_yticklabels(list(reversed(labels)), fontsize=10.8)
    ax_a.set_xlim(0, 118)
    ax_a.set_ylim(-0.7, len(family_rows) - 0.15)
    ax_a.set_xlabel("Model-prompt rate (%)", fontsize=11.3, fontweight="bold")
    ax_a.grid(axis="x", color=GRID, linewidth=0.8)
    ax_a.spines[["top", "right", "left"]].set_visible(False)
    ax_a.tick_params(axis="y", length=0)
    ax_a.text(0, len(family_rows) - 0.02, "A  Named-family execution and signature recovery", fontsize=14.2, fontweight="bold", ha="left", va="bottom")
    ax_a.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=TEAL, markersize=8, label="execution"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor=BLUE, markersize=8, label="reference signature"),
        ],
        frameon=False,
        fontsize=10.2,
        loc="lower left",
        bbox_to_anchor=(-0.02, -0.17),
        ncol=2,
    )

    # B. Prompt-level lollipop profile.
    family_order = ["Deutsch--Jozsa", "Deutsch", "Deutsch setup", "Bernstein--Vazirani", "Simon setup", "Grover setup"]
    prompt_rows.sort(key=lambda row: (family_order.index(row["algorithm_family"]), row["prompt_id"]))
    count = len(prompt_rows)
    for idx, row in enumerate(prompt_rows):
        y = count - 1 - idx
        matches = int(row["signature_matches"])
        color = family_colors[row["algorithm_family"]]
        ax_b.plot([0, matches], [y, y], color=color, linewidth=2.7, alpha=0.60, solid_capstyle="round")
        marker_size = 35 + 11 * int(row["operation_types"])
        ax_b.scatter(matches, y, s=marker_size, color=color, edgecolor=PAPER, linewidth=0.9, zorder=4)
        ax_b.text(21.5, y, f"{matches}/21", fontsize=9.8, fontweight="bold", color=color, ha="left", va="center")
    labels = [
        f"{row['prompt_id']}  ·  {row['counted_operations']} ops  ·  {row['operation_types']} types"
        for row in prompt_rows
    ]
    ax_b.set_yticks(range(count))
    ax_b.set_yticklabels(list(reversed(labels)), fontsize=9.5)
    ax_b.set_xlim(0, 23.5)
    ax_b.set_ylim(-0.8, count - 0.2)
    ax_b.set_xticks([0, 5, 10, 15, 20, 21])
    ax_b.set_xlabel("Models matching the frozen reference signature (of 21)", fontsize=11.3, fontweight="bold")
    ax_b.grid(axis="x", color=GRID, linewidth=0.8)
    ax_b.spines[["top", "right", "left"]].set_visible(False)
    ax_b.tick_params(axis="y", length=0)
    ax_b.text(0, count - 0.02, "B  Prompt-level recovery varies within familiar labels", fontsize=14.2, fontweight="bold", ha="left", va="bottom")

    save(fig, "supplemental_canonical_algorithm_recovery")


def build_repeatability_workflow() -> None:
    repeat = load_json(REPEATABILITY_JSON)
    design = repeat["design"]
    complete = repeat["canonical_completeness"]
    unaffected = repeat["recorded_transport_unaffected_repeatability"]
    exact = repeat["exact_code_agreement"]

    fig, ax = bare_canvas((14.0, 7.6))

    # A. Frozen panel construction.
    card(ax, 0.025, 0.69, 0.95, 0.275, face=PALE_BLUE, edge=BLUE, radius=0.010)
    panel_heading(ax, 0.043, 0.935, "A", "Outcome-blind panel construction")
    node(ax, 0.060, 0.745, 0.185, 0.125, "Original audit", "36 prompts · 36 unique signatures · selected without model outcomes", accent=BLUE, body_width=29)
    node(ax, 0.305, 0.745, 0.205, 0.125, "Confirmatory augmentation", "36 new identifiable prompts · signature-disjoint · frozen before transmission", accent=PLUM, body_width=33)
    node(ax, 0.585, 0.735, 0.340, 0.145, "Pooled 72-prompt panel", "36 pilot + 36 extension; 24 prompts in each 1-2, 3-4, and 5+ operation-type band; one prompt per target signature", accent=TEAL, face=PALE_TEAL, body_width=53)
    arrow(ax, (0.247, 0.807), (0.298, 0.807), color=BLUE)
    arrow(ax, (0.512, 0.807), (0.578, 0.807), color=PLUM)

    # B. Three invocation paths.
    card(ax, 0.025, 0.385, 0.95, 0.255, face=PANEL_BG, edge="#cbd5e1", radius=0.010)
    panel_heading(ax, 0.043, 0.610, "B", "Three runs under one frozen request contract")
    run_nodes = [
        ("Run 1", "canonical benchmark\nresponse archive", BLUE),
        ("Run 2", "fresh single-generation\nAPI invocation", TEAL),
        ("Run 3", "fresh single-generation\nAPI invocation", TEAL),
    ]
    for idx, (title, body, color) in enumerate(run_nodes):
        nx = 0.060 + idx * 0.205
        node(ax, nx, 0.435, 0.165, 0.115, title, body, accent=color, body_width=25)
    node(ax, 0.700, 0.425, 0.225, 0.135, "Frozen across runs", "Prompt text · request body · model route · hidden target · evaluator · structural predicate", accent=RUST, face=PALE_RUST, body_width=37)
    arrow(ax, (0.225, 0.492), (0.695, 0.492), color="#94a3b8", style="-[", mutation_scale=8)
    ax.text(0.460, 0.402, f"21 routes · {design['cells_per_run']:,} cells per run · {design['new_api_calls']:,} new API calls", transform=ax.transAxes, fontsize=10.7, fontweight="bold", color=TEXT, ha="center")

    # C. Canonicalization and analysis fork.
    card(ax, 0.025, 0.035, 0.95, 0.305, face=PALE_GOLD, edge=GOLD, radius=0.010)
    panel_heading(ax, 0.043, 0.310, "C", "Canonicalization separates deployment availability from output repeatability")
    node(ax, 0.055, 0.105, 0.190, 0.135, "Canonical cell matrix", f"{complete['observed_cells']:,} / {complete['expected_cells']:,} cells; no missing, duplicate, request-hash, or target mismatches", accent=GOLD, face=PAPER, body_width=31)
    node(ax, 0.305, 0.155, 0.205, 0.100, "Deployment-inclusive", "All 4,536 cells; terminal provider failures retained", accent=RUST, face=PALE_RUST, body_width=32, body_size=9.3)
    node(ax, 0.305, 0.060, 0.205, 0.082, "Transport-unaffected", "Common U = 1,122 in all three runs", accent=TEAL, face=PALE_TEAL, body_width=31, body_size=9.3)
    node(ax, 0.580, 0.105, 0.160, 0.135, "Endpoint stability", f"E AC1 {unaffected['execution']['gwet_ac1']:.3f}\nM AC1 {unaffected['signature']['gwet_ac1']:.3f}\npaired churn and run effects", accent=BLUE, face=PAPER, body_width=25)
    node(ax, 0.800, 0.105, 0.145, 0.135, "Code stability", f"Text identical {100 * exact['normalized_text']['all_three_equal_rate']:.2f}%\nAST identical {100 * exact['canonical_ast']['all_three_equal_rate']:.2f}%", accent=PLUM, face=PAPER, body_width=22)
    arrow(ax, (0.247, 0.173), (0.298, 0.207), color=RUST)
    arrow(ax, (0.247, 0.145), (0.298, 0.102), color=TEAL)
    arrow(ax, (0.512, 0.183), (0.573, 0.183), color=BLUE)
    arrow(ax, (0.742, 0.173), (0.793, 0.173), color=PLUM)
    ax.text(0.725, 0.060, "Result panel: Fig. S5 · numerical audits: Tables S32-S33", transform=ax.transAxes, fontsize=10.3, fontweight="bold", color=TEXT, ha="center")

    save(fig, "supplemental_stochastic_repeatability_workflow")


def main() -> None:
    configure_style()
    required: Iterable[Path] = (
        ROBUSTNESS_JSON,
        IDENTIFIABILITY_JSON,
        ORDERED_JSON,
        EVALUATOR_JSON,
        CONTEXT_JSON,
        REPEATABILITY_JSON,
        ALGORITHM_FAMILY_TSV,
        ALGORITHM_PROMPT_TSV,
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing figure source artifacts: " + ", ".join(str(path) for path in missing))

    build_design_estimand_map()
    build_inference_workflow()
    build_robustness_atlas()
    build_evaluator_integrity_audit()
    build_canonical_algorithm_recovery()
    build_repeatability_workflow()

    for stem in [
        "supplemental_experimental_design_estimand_map",
        "supplemental_dependence_aware_inference_workflow",
        "supplemental_robustness_atlas",
        "supplemental_evaluator_integrity_audit",
        "supplemental_canonical_algorithm_recovery",
        "supplemental_stochastic_repeatability_workflow",
    ]:
        print(f"Wrote {FIGURES / (stem + '.svg')}")
        print(f"Wrote {FIGURES / (stem + '.png')}")


if __name__ == "__main__":
    main()
