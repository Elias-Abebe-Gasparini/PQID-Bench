"""Build the model-profile and cluster-aware inferential main-text figures.

Figure 4 organizes the final 21 x 154 primary matrix by model:
hierarchical clustering, PCA, and selected paired contrasts. Figure 5 organizes
the same roster by task feature: signature-cluster bootstrap
effects, a two-stage execution-versus-fidelity comparison, and
signature-grouped cross-validation.

The script deliberately consumes the frozen analytical artifacts rather than
refitting models during rendering. This keeps the figures synchronized with the
reported inferential tables and avoids introducing a second statistical path.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "artifacts/analysis_154"
FIGURES_DIR = ROOT / "figures"

MATRIX_CSV = ANALYSIS_DIR / "pqid_bench_model_by_prompt_structural_matrix.csv"
CLUSTER_JSON = ANALYSIS_DIR / "pqid_bench_clustering_logistic_analysis.json"
INFERENTIAL_JSON = ANALYSIS_DIR / "pqid_bench_inferential_analysis.json"
TERMS_CSV = ANALYSIS_DIR / "pqid_bench_inferential_model_terms.csv"
CV_CSV = ANALYSIS_DIR / "pqid_bench_grouped_cross_validation.csv"
PAIRS_CSV = ANALYSIS_DIR / "pqid_bench_paired_model_comparisons.csv"

FIGURE3_SVG = FIGURES_DIR / "clustering_logistic_panel.svg"
FIGURE3_PNG = FIGURES_DIR / "clustering_logistic_panel.png"
FIGURE3_CAPTION = FIGURES_DIR / "clustering_logistic_panel_caption.md"
FIGURE4_SVG = FIGURES_DIR / "regression_distribution_panel.svg"
FIGURE4_PNG = FIGURES_DIR / "regression_distribution_panel.png"
FIGURE4_CAPTION = FIGURES_DIR / "regression_distribution_panel_caption.md"


TEXT = "#000000"
MUTED = "#000000"
GRID = "#dfe7ef"
TEAL = "#147d73"
BLUE = "#315fa8"
RUST = "#bd4d00"
PLUM = "#7c3f72"
GOLD = "#b7791f"
SLATE = "#667085"
LIGHT = "#f7f9fb"

TIER_COLORS = {
    "frontier_api": TEAL,
    "strong_open_or_code": BLUE,
    "low_or_experimental": RUST,
}

TERM_LABELS = {
    "z_gate_entropy": "Gate entropy (per SD)",
    "z_gate_type_count": "Gate-type count (per SD)",
    "z_log_gate_count": "Log gate count (per SD)",
    "z_num_qubits": "Qubits (per SD)",
    "z_num_clbits": "Classical bits (per SD)",
    "has_barrier": "Barrier / staged structure",
}

PAIR_LABELS = {
    "Llama 8B -> 70B": "Llama 8B / 70B",
    "Llama 4 Scout -> Maverick": "Scout / Maverick",
    "GPT-OSS 20B -> 120B": "GPT-OSS 20B / 120B",
    "Gemini 2.5 -> 3.1": "Gemini 2.5 / 3.1",
    "Claude Sonnet -> Opus": "Sonnet / Opus",
    "Claude Opus -> Fable": "Opus / Fable",
    "DeepSeek Flash -> Pro": "DeepSeek Flash / Pro",
    "Qwen3 general -> Coder": "Qwen3 / Coder",
    "GPT-5.4 mini -> GPT-5.5": "GPT-5.4 mini / 5.5",
    "GPT-5.5 -> GPT-5.6 Sol": "GPT-5.5 / 5.6 Sol",
    "Mistral parent -> Qiskit specialist": "Mistral parent /\nQiskit specialist",
}

PCA_TIER_SPECS = [
    ("frontier_api", "Frontier API"),
    ("strong_open_or_code", "Strong open/code"),
    ("low_or_experimental", "Low/exp."),
]

PCA_KEY_LABELS = {
    "Claude Fable 5": "Fable 5",
    "Claude Opus 4.8": "Opus 4.8",
    "Claude Sonnet 4.6": "Sonnet 4.6",
    "DeepSeek V4 Flash": "DS V4 Flash",
    "DeepSeek V4 Pro": "DS V4 Pro",
    "Gemini 2.5 Pro": "Gemini 2.5",
    "Gemini 3.1 Pro Preview": "Gemini 3.1",
    "GPT-5.4 mini": "GPT-5.4 mini",
    "GPT-5.5": "GPT-5.5",
    "GPT-5.6 Sol": "GPT-5.6 Sol",
    "Codestral 25.01": "Codestral",
    "GPT-OSS 120B": "GPT-OSS 120B",
    "GPT-OSS 20B": "GPT-OSS 20B",
    "Llama 3.3 70B": "Llama 70B",
    "Qwen3-Coder-Next": "Qwen3-Coder",
    "Llama 3.1 8B": "Llama 8B",
    "Llama 4 Scout": "Scout",
    "Llama 4 Maverick": "Maverick",
    "Qwen3 32B": "Qwen3 32B",
    "Mistral Small 3.2 24B": "Mistral parent",
    "Qiskit Mistral 3.2 24B": "Qiskit specialist",
}

def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 14,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 14.5,
            "axes.labelcolor": TEXT,
            "axes.edgecolor": "#000000",
            "axes.linewidth": 0.9,
            "xtick.labelsize": 12.5,
            "ytick.labelsize": 12.5,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "legend.fontsize": 11.5,
            "text.color": TEXT,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def panel_title(ax: plt.Axes, letter: str, title: str, subtitle: str | None = None) -> None:
    ax.annotate(letter, (0, 1), xycoords="axes fraction", xytext=(-2, 15), textcoords="offset points", color=BLUE, fontsize=15.5, fontweight="bold", ha="left", va="bottom")
    ax.annotate(title, (0, 1), xycoords="axes fraction", xytext=(23, 15), textcoords="offset points", fontsize=15, fontweight="bold", ha="left", va="bottom")
    if subtitle:
        ax.annotate(subtitle, (0, 1), xycoords="axes fraction", xytext=(23, 1), textcoords="offset points", fontsize=10.4, color=MUTED, ha="left", va="bottom")


def clean_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)


def load_inputs() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matrix = pd.read_csv(MATRIX_CSV, sep=None, engine="python")
    clustering = json.loads(CLUSTER_JSON.read_text(encoding="utf-8"))
    inferential = json.loads(INFERENTIAL_JSON.read_text(encoding="utf-8"))
    terms = pd.read_csv(TERMS_CSV, sep=None, engine="python")
    cv = pd.read_csv(CV_CSV, sep=None, engine="python")
    pairs = pd.read_csv(PAIRS_CSV, sep=None, engine="python")
    return matrix, clustering, inferential, terms, cv, pairs


def draw_dendrogram(ax: plt.Axes, clustering: dict[str, Any]) -> None:
    models = clustering["models"]
    hierarchy = clustering["hierarchical_clustering"]
    clusters = {int(key): value for key, value in hierarchy["tree"]["clusters"].items()}
    root = int(hierarchy["tree"]["root"])
    order = [int(value) for value in hierarchy["leaf_order"]]
    y_by_leaf = {leaf: float(index) for index, leaf in enumerate(order)}

    def visit(cluster_id: int) -> tuple[float, float]:
        cluster = clusters[cluster_id]
        if cluster["leaf"] is not None:
            return 0.0, y_by_leaf[int(cluster["leaf"])]
        left_x, left_y = visit(int(cluster["left"]))
        right_x, right_y = visit(int(cluster["right"]))
        x = float(cluster["height"])
        ax.plot([left_x, x], [left_y, left_y], color="#000000", linewidth=1.45, zorder=2)
        ax.plot([right_x, x], [right_y, right_y], color="#000000", linewidth=1.45, zorder=2)
        ax.plot([x, x], [left_y, right_y], color="#000000", linewidth=1.45, zorder=2)
        return x, (left_y + right_y) / 2.0

    visit(root)
    labels = [str(models[leaf]["model_label"]) for leaf in order]
    tiers = [str(models[leaf]["model_tier"]) for leaf in order]
    rates = [float(models[leaf]["structural_all_match"]) for leaf in order]
    y = np.arange(len(order), dtype=float)
    ax.set_yticks(y, labels)
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.set_xlim(-0.025, 0.43)
    for yi, tier in zip(y, tiers):
        ax.scatter(-0.016, yi, s=52, color=TIER_COLORS.get(tier, SLATE), edgecolor="white", linewidth=0.7, zorder=4, clip_on=False)
    for yi, rate in zip(y, rates):
        ax.text(0.425, yi, f"{100 * rate:.1f}%", fontsize=11.5, color=MUTED, va="center", ha="right")
    ax.set_xlabel("Average-linkage Hamming distance")
    ax.set_xticks([0.0, 0.1, 0.2, 0.3])
    ax.tick_params(axis="y", pad=10, length=0)
    clean_axis(ax)
    ax.spines["left"].set_visible(False)
    ax.text(
        0.99,
        1.004,
        "Match rate",
        transform=ax.transAxes,
        fontsize=11.2,
        color=MUTED,
        ha="right",
        va="bottom",
        clip_on=False,
    )
    panel_title(ax, "A", "Model clusters", "Final 21-model roster")


def pca_scores(matrix: pd.DataFrame, clustering: dict[str, Any]) -> tuple[list[dict[str, Any]], np.ndarray]:
    models = clustering["models"]
    model_ids = [str(model["model"]) for model in models]
    values = matrix[model_ids].to_numpy(dtype=float).T
    centered = values - values.mean(axis=0, keepdims=True)
    u, singular, _ = np.linalg.svd(centered, full_matrices=False)
    scores = u[:, :2] * singular[:2]
    shares = singular**2 / np.sum(singular**2)
    rates = np.array([float(model["structural_all_match"]) for model in models])
    for axis in range(2):
        if np.corrcoef(scores[:, axis], rates)[0, 1] < 0:
            scores[:, axis] *= -1
    rows = []
    for index, model in enumerate(models):
        rows.append({**model, "pc1": float(scores[index, 0]), "pc2": float(scores[index, 1])})
    return rows, shares[:2]


def draw_pca(ax: plt.Axes, key_ax: plt.Axes, matrix: pd.DataFrame, clustering: dict[str, Any]) -> tuple[float, float]:
    rows, shares = pca_scores(matrix, clustering)
    key_groups: dict[str, list[dict[str, Any]]] = {}
    marker_ids: dict[str, int] = {}
    next_id = 1
    for tier, _ in PCA_TIER_SPECS:
        group = sorted(
            [row for row in rows if row["model_tier"] == tier],
            key=lambda row: str(row["model_label"]),
        )
        key_groups[tier] = group
        for row in group:
            marker_ids[str(row["model_label"])] = next_id
            next_id += 1

    for tier, _ in PCA_TIER_SPECS:
        subset = key_groups[tier]
        ax.scatter(
            [row["pc1"] for row in subset],
            [row["pc2"] for row in subset],
            s=96,
            color=TIER_COLORS[tier],
            edgecolor="white",
            linewidth=0.9,
            alpha=0.96,
            zorder=3,
        )
        for row in subset:
            marker_id = marker_ids[str(row["model_label"])]
            ax.text(
                float(row["pc1"]),
                float(row["pc2"]),
                str(marker_id),
                color="white",
                fontsize=8.2 if marker_id < 10 else 7.3,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=4,
            )

    x_values = np.array([row["pc1"] for row in rows])
    y_values = np.array([row["pc2"] for row in rows])
    x_span = float(np.ptp(x_values)) or 1.0
    y_span = float(np.ptp(y_values)) or 1.0
    ax.set_xlim(float(x_values.min() - 0.09 * x_span), float(x_values.max() + 0.09 * x_span))
    ax.set_ylim(float(y_values.min() - 0.12 * y_span), float(y_values.max() + 0.12 * y_span))
    ax.axhline(0, color=GRID, linewidth=0.9, zorder=0)
    ax.axvline(0, color=GRID, linewidth=0.9, zorder=0)
    ax.set_xlabel(f"PC1 ({100 * shares[0]:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({100 * shares[1]:.1f}% variance)")
    clean_axis(ax)
    ax.grid(axis="both", color=GRID, linewidth=0.75)
    panel_title(ax, "B", "Success-profile PCA", "Final 21-model roster; numbers identify models in the key")

    key_ax.set_axis_off()
    key_ax.plot([0.0, 1.0], [0.98, 0.98], transform=key_ax.transAxes, color=TEXT, linewidth=0.9)
    group_layout = {
        "frontier_api": {"heading_x": 0.00, "column_xs": [0.00, 0.205], "split": 5},
        "strong_open_or_code": {"heading_x": 0.43, "column_xs": [0.43, 0.64], "split": 4},
        "low_or_experimental": {"heading_x": 0.85, "column_xs": [0.85], "split": 5},
    }
    entry_y = [0.66, 0.50, 0.34, 0.18, 0.02]
    for tier, heading in PCA_TIER_SPECS:
        layout = group_layout[tier]
        heading_x = float(layout["heading_x"])
        key_ax.scatter(
            [heading_x + 0.008],
            [0.84],
            s=46,
            color=TIER_COLORS[tier],
            edgecolor="white",
            linewidth=0.7,
            transform=key_ax.transAxes,
            clip_on=False,
        )
        key_ax.text(
            heading_x + 0.025,
            0.84,
            heading,
            transform=key_ax.transAxes,
            fontsize=10.2,
            fontweight="bold",
            ha="left",
            va="center",
        )
        group = key_groups[tier]
        split = int(layout["split"])
        columns = [group[index : index + split] for index in range(0, len(group), split)]
        for column_x, column in zip(layout["column_xs"], columns):
            for y, row in zip(entry_y, column):
                marker_id = marker_ids[str(row["model_label"])]
                key_ax.text(
                    float(column_x),
                    y,
                    f"{marker_id:>2}",
                    transform=key_ax.transAxes,
                    fontsize=9.2,
                    fontweight="bold",
                    color=TIER_COLORS[tier],
                    ha="left",
                    va="center",
                )
                key_ax.text(
                    float(column_x) + 0.027,
                    y,
                    PCA_KEY_LABELS[str(row["model_label"])],
                    transform=key_ax.transAxes,
                    fontsize=9.2,
                    color=TEXT,
                    ha="left",
                    va="center",
                )
    key_ax.text(
        0.99,
        0.18,
        "Exp. = experimental",
        transform=key_ax.transAxes,
        fontsize=8.5,
        color=TEXT,
        ha="right",
        va="center",
    )
    key_ax.text(
        0.99,
        0.02,
        "Identifiers, not ranks",
        transform=key_ax.transAxes,
        fontsize=8.5,
        color=MUTED,
        ha="right",
        va="center",
        style="italic",
    )
    return float(shares[0]), float(shares[1])


def draw_paired_comparisons(ax: plt.Axes, pairs: pd.DataFrame) -> None:
    rows = pairs.to_dict("records")
    y = np.arange(len(rows), dtype=float)
    for yi, row in zip(y, rows):
        after_wins = int(row["after_wins"])
        ties = int(row["ties"])
        before_wins = int(row["before_wins"])
        estimate = 100 * float(row["difference"])
        significant = float(row["holm_adjusted_cluster_permutation_p"]) < 0.05
        ax.barh(yi, after_wins, height=0.58, color=TEAL, edgecolor="none", zorder=2)
        ax.barh(yi, ties, left=after_wins, height=0.58, color="#e7ebf0", edgecolor="none", zorder=2)
        ax.barh(yi, before_wins, left=after_wins + ties, height=0.58, color=RUST, edgecolor="none", zorder=2)
        outline = TEAL if significant else "#000000"
        ax.add_patch(Rectangle((0, yi - 0.29), 154, 0.58, fill=False, edgecolor=outline, linewidth=1.5 if significant else 0.65, zorder=3))
        if after_wins >= 4:
            ax.text(after_wins / 2, yi, str(after_wins), color="white", fontsize=10.5, fontweight="bold", ha="center", va="center")
        if before_wins >= 7:
            ax.text(after_wins + ties + before_wins / 2, yi, str(before_wins), color="white", fontsize=10.5, fontweight="bold", ha="center", va="center")
        suffix = " *" if significant else ""
        ax.text(
            0.99,
            yi,
            f"{estimate:+.1f} pp{suffix}",
            transform=ax.get_yaxis_transform(),
            fontsize=10.0,
            color=TEAL if significant else TEXT,
            fontweight="bold" if significant else "normal",
            ha="right",
            va="center",
        )
    ax.set_yticks(y, [PAIR_LABELS.get(str(value), str(value)) for value in pairs["comparison"]])
    ax.set_ylim(len(rows) - 0.5, -1.25)
    ax.set_xlim(0, 176)
    ax.set_xticks([0, 50, 100, 150])
    ax.set_xlabel("Held-out prompts (n = 154)")
    ax.tick_params(axis="y", length=0, pad=6, labelsize=10.7)
    for label in ax.get_yticklabels():
        label.set_multialignment("right")
        label.set_linespacing(0.98)
    clean_axis(ax)
    legend = [
        Patch(facecolor=TEAL, edgecolor="none", label="After-model wins"),
        Patch(facecolor="#e7ebf0", edgecolor="#cfd7e1", label="Ties"),
        Patch(facecolor=RUST, edgecolor="none", label="Before-model wins"),
    ]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.48, 0.995), frameon=False, ncol=3, borderaxespad=0.0, handletextpad=0.35, columnspacing=0.8, fontsize=10.5)
    panel_title(ax, "C", "Paired outcomes", "Wins, ties, and losses on 154 prompts; * Holm-adjusted p < 0.05")


def save_figure(fig: plt.Figure, svg_path: Path, png_path: Path) -> None:
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(svg_path, format="svg", bbox_inches="tight", pad_inches=0.035)
    fig.savefig(png_path, format="png", dpi=220, bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)
    with Image.open(png_path) as rendered:
        if rendered.mode != "RGB":
            rendered.convert("RGB").save(png_path)


def build_figure3(matrix: pd.DataFrame | None = None, clustering: dict[str, Any] | None = None, pairs: pd.DataFrame | None = None) -> None:
    configure_style()
    if matrix is None or clustering is None or pairs is None:
        matrix, clustering, _, _, _, pairs = load_inputs()
    fig = plt.figure(figsize=(14.35, 8.5), constrained_layout=False)
    grid = fig.add_gridspec(1, 2, width_ratios=[0.84, 1.26], wspace=0.40)
    right_grid = grid[0, 1].subgridspec(3, 1, height_ratios=[0.94, 0.33, 1.28], hspace=0.28)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(right_grid[0, 0])
    ax_key = fig.add_subplot(right_grid[1, 0])
    ax_c = fig.add_subplot(right_grid[2, 0])
    draw_dendrogram(ax_a, clustering)
    pc1, pc2 = draw_pca(ax_b, ax_key, matrix, clustering)
    draw_paired_comparisons(ax_c, pairs)
    fig.subplots_adjust(left=0.105, right=0.965, top=0.935, bottom=0.075)
    fig.set_size_inches(14.35, 8.5)
    save_figure(fig, FIGURE3_SVG, FIGURE3_PNG)

    nearest = clustering["nearest_pairs"][0]
    FIGURE3_CAPTION.write_text(
        "\n".join(
            [
                "# Model-Profile Structure And Paired Outcome Balance",
                "",
                "**Figure 4. Model-profile structure and paired outcome balance.** "
                f"Panel A clusters the final `21`-model roster by average-linkage Hamming distance over its `154` prompt-level reference-signature outcomes; the nearest pair is {nearest['left']} and {nearest['right']} (`d={float(nearest['hamming_distance']):.3f}`). "
                f"Panel B projects the same binary success profiles into two principal components (PC1=`{100 * pc1:.1f}%`; PC2=`{100 * pc2:.1f}%` of variance). Numbered markers identify models through the tier-grouped key beneath the axes; the numbers are identifiers rather than ranks. "
                "Panel C decomposes eleven selected comparisons into after-model wins, ties, and before-model wins across the same `154` prompts, including the matched Mistral-parent versus Qiskit-specialist comparison. Asterisks mark comparisons that survive Holm correction of signature-cluster sign-flip permutation tests; cluster-bootstrap intervals are reported in the supplemental comparison table.",
                "",
                "Source artifacts:",
                "",
                "- `artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv`",
                "- `artifacts/analysis_154/pqid_bench_clustering_logistic_analysis.json`",
                "- `artifacts/analysis_154/pqid_bench_paired_model_comparisons.csv`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def errorbar_row(
    ax: plt.Axes,
    y: float,
    estimate: float,
    low: float,
    high: float,
    *,
    color: str,
    marker: str = "o",
    filled: bool = True,
    size: float = 72,
) -> None:
    ax.plot([low, high], [y, y], color=color, linewidth=2.2, zorder=2)
    ax.plot([low, low], [y - 0.11, y + 0.11], color=color, linewidth=1.15, zorder=2)
    ax.plot([high, high], [y - 0.11, y + 0.11], color=color, linewidth=1.15, zorder=2)
    ax.scatter(estimate, y, s=size, marker=marker, facecolor=color if filled else "white", edgecolor=color, linewidth=1.5, zorder=3)


def select_terms(terms: pd.DataFrame, analysis: str, order: list[str]) -> pd.DataFrame:
    subset = terms[terms["analysis"] == analysis].copy()
    subset["_order"] = subset["term"].map({term: index for index, term in enumerate(order)})
    return subset.sort_values("_order")


def draw_adjusted_effects(ax: plt.Axes, terms: pd.DataFrame) -> None:
    order = ["z_gate_entropy", "z_log_gate_count", "z_num_qubits", "z_num_clbits", "has_barrier"]
    rows = select_terms(terms, "signature_entropy_full", order)
    y = np.arange(len(rows), dtype=float)
    for yi, (_, row) in zip(y, rows.iterrows()):
        estimate = float(row["average_marginal_effect_pp"])
        low = float(row["ame_ci_low_pp"])
        high = float(row["ame_ci_high_pp"])
        color = RUST if estimate < 0 else TEAL
        excludes = bool(row["interval_excludes_null"])
        errorbar_row(ax, yi, estimate, low, high, color=color, filled=excludes)
        ax.annotate(
            f"{estimate:+.1f}",
            (estimate, yi),
            xytext=(0, -18),
            textcoords="offset points",
            fontsize=11.5,
            color=color,
            va="top",
            ha="center",
        )
    ax.axvline(0, color="#8fa0b2", linewidth=1.1)
    ax.set_yticks(y, [TERM_LABELS[str(term)] for term in rows["term"]])
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xlim(-44, 19)
    ax.set_xticks([-40, -30, -20, -10, 0, 10])
    ax.set_xlabel("Average marginal effect (percentage points)")
    ax.tick_params(axis="y", length=0, pad=6)
    clean_axis(ax)
    panel_title(ax, "A", "Adjusted task effects", "Grouped-binomial AME; 95% signature-cluster intervals")


def draw_two_stage(ax: plt.Axes, terms: pd.DataFrame, inferential: dict[str, Any]) -> None:
    descriptors = ["z_gate_entropy", "has_barrier"]
    execution = select_terms(terms, "execution_entropy_full", descriptors).set_index("term")
    conditional = select_terms(terms, "signature_given_execution_entropy_full", descriptors).set_index("term")
    values = np.array(
        [
            [float(execution.loc[term, "average_marginal_effect_pp"]), float(conditional.loc[term, "average_marginal_effect_pp"])]
            for term in descriptors
        ]
    )
    lows = np.array(
        [
            [float(execution.loc[term, "ame_ci_low_pp"]), float(conditional.loc[term, "ame_ci_low_pp"])]
            for term in descriptors
        ]
    )
    highs = np.array(
        [
            [float(execution.loc[term, "ame_ci_high_pp"]), float(conditional.loc[term, "ame_ci_high_pp"])]
            for term in descriptors
        ]
    )
    effect_cmap = LinearSegmentedColormap.from_list("effect_matrix", [RUST, "#f4c7aa", "#fbfbfa", "#b9ded8", TEAL])
    ax.imshow(values, cmap=effect_cmap, norm=TwoSlopeNorm(vmin=-30, vcenter=0, vmax=8), aspect="auto", zorder=1)
    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            estimate = values[row_index, column_index]
            text_color = "white" if estimate <= -18 else TEXT
            ax.text(column_index, row_index - 0.10, f"{estimate:+.1f} pp", ha="center", va="center", fontsize=14, fontweight="bold", color=text_color)
            ax.text(
                column_index,
                row_index + 0.19,
                f"95% CI [{lows[row_index, column_index]:+.1f}, {highs[row_index, column_index]:+.1f}]",
                ha="center",
                va="center",
                fontsize=10.2,
                color=text_color,
            )
    ax.set_xticks([0, 1], ["Execution", "Signature fidelity\namong executable outputs"])
    ax.set_yticks([0, 1], ["Gate entropy\n(per SD)", "Barrier / staged"])
    ax.tick_params(axis="both", length=0, pad=7)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, 2, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 2, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)
    panel_title(ax, "B", "Where difficulty enters", "AME in percentage points; 95% signature-cluster intervals")


def cv_improvements(cv: pd.DataFrame) -> list[dict[str, Any]]:
    labels = {
        "auc": "AUC gain",
        "brier": "Brier reduction",
        "log_loss": "Log-loss reduction",
    }
    rows: list[dict[str, Any]] = []
    for metric in ["auc", "brier", "log_loss"]:
        for model, model_label, color, marker in [
            ("entropy_plus_barrier", "Entropy + barrier", PLUM, "o"),
            ("gate_type_plus_barrier", "Gate types + barrier", TEAL, "s"),
        ]:
            row = cv[(cv["model"] == model) & (cv["metric"] == metric)].iloc[0]
            sign = 1.0 if metric == "auc" else -1.0
            estimate = sign * 100 * float(row["delta_vs_size"])
            raw_low = float(row["delta_ci_low"])
            raw_high = float(row["delta_ci_high"])
            low = min(sign * 100 * raw_low, sign * 100 * raw_high)
            high = max(sign * 100 * raw_low, sign * 100 * raw_high)
            rows.append(
                {
                    "metric": metric,
                    "metric_label": labels[metric],
                    "model": model,
                    "model_label": model_label,
                    "color": color,
                    "marker": marker,
                    "estimate": estimate,
                    "low": low,
                    "high": high,
                }
            )
    return rows


def draw_cross_validation(ax: plt.Axes, cv: pd.DataFrame) -> None:
    rows = cv_improvements(cv)
    metrics = ["auc", "brier", "log_loss"]
    centers = np.arange(len(metrics), dtype=float)
    offsets = {"entropy_plus_barrier": -0.19, "gate_type_plus_barrier": 0.19}
    width = 0.34
    for row in rows:
        xi = centers[metrics.index(row["metric"])] + offsets[str(row["model"])]
        excludes_zero = float(row["low"]) > 0
        bar = ax.bar(
            xi,
            float(row["estimate"]),
            width=width,
            color=str(row["color"]) if excludes_zero else "white",
            edgecolor=str(row["color"]),
            linewidth=1.5,
            hatch=None if excludes_zero else "///",
            zorder=3,
        )
        ax.text(xi, float(row["estimate"]) + 0.28, f"{float(row['estimate']):.1f}", ha="center", va="bottom", fontsize=10.5, color=str(row["color"]), fontweight="bold")
    ax.axhline(0, color="#8fa0b2", linewidth=1.0)
    ax.set_xticks(centers, ["AUC\n(higher better)", "Brier\n(lower better)", "Log loss\n(lower better)"])
    # Reserve a clear legend band above the tallest value label.
    ax.set_ylim(0, 12.2)
    ax.set_yticks([0, 2, 4, 6, 8, 10])
    ax.set_ylabel("Gain over size-only (x100)", fontsize=14.5, labelpad=5)
    ax.tick_params(axis="x", length=0, pad=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.legend(
        handles=[
            Patch(facecolor=PLUM, edgecolor=PLUM, label="Entropy + barrier"),
            Patch(facecolor=TEAL, edgecolor=TEAL, label="Gate types + barrier"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.62, 0.99),
        frameon=False,
        ncol=2,
        columnspacing=0.9,
        borderaxespad=0.1,
        handletextpad=0.35,
        fontsize=10.5,
    )
    panel_title(ax, "C", "Task-feature prediction", "All 21 model rows pooled; 10-fold grouped CV; hatched gains are uncertain")


def build_figure4(terms: pd.DataFrame | None = None, cv: pd.DataFrame | None = None, inferential: dict[str, Any] | None = None) -> None:
    configure_style()
    if terms is None or cv is None or inferential is None:
        _, _, inferential, terms, cv, _ = load_inputs()
    fig = plt.figure(figsize=(14.0, 8.15), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=[0.93, 1.07],
        height_ratios=[0.94, 1.06],
        wspace=0.24,
        hspace=0.42,
    )
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[1, 1])
    draw_adjusted_effects(ax_a, terms)
    draw_two_stage(ax_b, terms, inferential)
    draw_cross_validation(ax_c, cv)
    fig.subplots_adjust(left=0.145, right=0.985, top=0.925, bottom=0.10)
    save_figure(fig, FIGURE4_SVG, FIGURE4_PNG)

    FIGURE4_CAPTION.write_text(
        "\n".join(
            [
                "# Cluster-Aware Inference For Circuit Difficulty",
                "",
                "**Figure 5. Cluster-aware inference for circuit difficulty.** "
                "Panel A reports average marginal effects from a grouped-binomial model of prompt-level reference-signature matches across the final `21`-model roster, with `95%` target-signature-cluster bootstrap intervals. Gate entropy and barrier or staged structure remain the principal adjusted negative associations, whereas the size descriptors' intervals include zero. "
                "Panel B presents the adjusted execution and conditional-fidelity effects as a two-by-two matrix; each cell gives the average marginal effect and its `95%` signature-cluster interval. Gate entropy has a modest negative association with execution and barriers have an uncertain execution association, while both have substantially larger negative associations with conditional fidelity, locating the principal difficulty in executable reference-signature disagreement. "
                "Panel C compares task-feature predictor specifications against the size-only specification under `10`-fold target-signature-grouped cross-validation. It is not an individual-model performance panel: all `21` model rows contribute to every validation score. All intervals are release-bound and support association and prediction, not causal claims.",
                "",
                "Source artifacts:",
                "",
                "- `artifacts/analysis_154/pqid_bench_inferential_model_terms.csv`",
                "- `artifacts/analysis_154/pqid_bench_grouped_cross_validation.csv`",
                "- `artifacts/analysis_154/pqid_bench_inferential_analysis.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    matrix, clustering, inferential, terms, cv, pairs = load_inputs()
    build_figure3(matrix, clustering, pairs)
    build_figure4(terms, cv, inferential)
    print(f"Wrote {FIGURE3_SVG}")
    print(f"Wrote {FIGURE3_PNG}")
    print(f"Wrote {FIGURE3_CAPTION}")
    print(f"Wrote {FIGURE4_SVG}")
    print(f"Wrote {FIGURE4_PNG}")
    print(f"Wrote {FIGURE4_CAPTION}")


if __name__ == "__main__":
    main()
