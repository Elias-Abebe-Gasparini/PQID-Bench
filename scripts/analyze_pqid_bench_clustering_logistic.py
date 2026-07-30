"""Hierarchical clustering and logistic-regression diagnostics for PQID-Bench.

This diagnostic complements the PCA/regression panel. Hierarchical clustering
asks whether models share the same prompt-level success/failure profile, while
logistic regression fits the binary structural-match outcome directly.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any
from xml.sax.saxutils import escape

from publication_figure_style import PUBLICATION_SERIF_FONT_STACK


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
FIGURES_DIR = ROOT / "figures"

PROMPTS_JSONL = ARTIFACTS_DIR / "test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
MATRIX_CSV = ARTIFACTS_DIR / "analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv"
REGRESSION_JSON = ARTIFACTS_DIR / "analysis_154/pqid_bench_model_regression_analysis.json"
JSON_OUT = ARTIFACTS_DIR / "analysis_154/pqid_bench_clustering_logistic_analysis.json"
MD_OUT = ARTIFACTS_DIR / "analysis_154/pqid_bench_clustering_logistic_analysis.md"
SVG_OUT = FIGURES_DIR / "clustering_logistic_panel.svg"
CAPTION_OUT = FIGURES_DIR / "clustering_logistic_panel_caption.md"


TEXT = "#1f2933"
MUTED = "#64748b"
GRID = "#edf2f7"
AXIS = "#516174"
TEAL = "#1f766d"
BLUE = "#315a9f"
RUST = "#b45309"
PLUM = "#7c3f72"
SLATE = "#475467"
PANEL_BG = "#ffffff"

MODEL_COLORS = {
    "frontier_api": TEAL,
    "strong_open_or_code": BLUE,
    "low_or_experimental": RUST,
}

CONTROLLED_OR_ENTANGLING_GATES = {
    "cx",
    "cz",
    "cp",
    "ch",
    "cs",
    "ct",
    "ccx",
    "swap",
    "rxx",
    "rzz",
}
ROTATION_GATES = {"rx", "ry", "rz", "p", "u", "u1", "u2", "u3", "rxx", "rzz"}

PREDICTOR_LABELS = {
    "tier_strong_open_or_code": "strong open/code tier",
    "tier_low_or_experimental": "low/experimental tier",
    "z_gate_entropy": "gate entropy",
    "has_barrier": "barrier / staged structure",
    "z_gate_type_count": "gate-type count",
    "has_controlled_or_entangling": "controlled / entangling",
    "z_num_clbits": "classical bits",
    "z_num_qubits": "qubits",
    "z_gate_count": "gate count",
    "has_rotation": "rotation gate",
    "has_measure": "measurement",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_matrix(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.2f} pp"


def gate_entropy(gates: dict[str, int]) -> float:
    total = sum(gates.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in gates.values():
        p = count / total
        entropy -= p * math.log(p)
    return entropy


def prompt_features(prompt: dict[str, Any]) -> dict[str, Any]:
    metadata = prompt["target_metadata"]
    gates = {str(key): int(value) for key, value in metadata["gate_types"].items()}
    gate_names = set(gates)
    return {
        "prompt_id": prompt["prompt_id"],
        "num_qubits": int(metadata["num_qubits"]),
        "num_clbits": int(metadata["num_clbits"]),
        "gate_count": int(metadata["gate_count"]),
        "gate_type_count": len(gates),
        "gate_entropy": gate_entropy(gates),
        "has_barrier": int("barrier" in gate_names),
        "has_controlled_or_entangling": int(bool(gate_names & CONTROLLED_OR_ENTANGLING_GATES)),
        "has_rotation": int(bool(gate_names & ROTATION_GATES)),
        "has_measure": int("measure" in gate_names),
    }


def safe_sd(values: list[float]) -> float:
    if len(values) < 2:
        return 1.0
    avg = mean(values)
    sd = math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))
    return sd or 1.0


def model_metadata(regression_data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(regression_data["model_distribution"])


def model_vectors(models: list[dict[str, Any]], matrix_rows: list[dict[str, str]]) -> list[list[int]]:
    return [[int(row[str(model["model"])]) for row in matrix_rows] for model in models]


def hamming_distance(a: list[int], b: list[int]) -> float:
    return sum(left != right for left, right in zip(a, b)) / len(a)


def pairwise_hamming(models: list[dict[str, Any]], vectors: list[list[int]]) -> list[list[float]]:
    n = len(models)
    distances = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            distance = hamming_distance(vectors[i], vectors[j])
            distances[i][j] = distance
            distances[j][i] = distance
    return distances


def average_linkage_distance(left: list[int], right: list[int], distances: list[list[float]]) -> float:
    values = [distances[i][j] for i in left for j in right]
    return sum(values) / len(values)


def hierarchical_average_linkage(models: list[dict[str, Any]], distances: list[list[float]]) -> dict[str, Any]:
    clusters: dict[int, dict[str, Any]] = {
        index: {
            "id": index,
            "leaf": index,
            "left": None,
            "right": None,
            "height": 0.0,
            "size": 1,
            "leaves": [index],
            "label": models[index]["model_label"],
        }
        for index in range(len(models))
    }
    active = list(clusters)
    next_id = len(models)
    merges: list[dict[str, Any]] = []
    while len(active) > 1:
        best: tuple[float, int, int] | None = None
        for a_index, left_id in enumerate(active):
            for right_id in active[a_index + 1 :]:
                distance = average_linkage_distance(
                    clusters[left_id]["leaves"],
                    clusters[right_id]["leaves"],
                    distances,
                )
                candidate = (distance, min(left_id, right_id), max(left_id, right_id))
                if best is None or candidate < best:
                    best = candidate
        assert best is not None
        distance, left_id, right_id = best
        left = clusters[left_id]
        right = clusters[right_id]
        merged = {
            "id": next_id,
            "leaf": None,
            "left": left_id,
            "right": right_id,
            "height": distance,
            "size": left["size"] + right["size"],
            "leaves": left["leaves"] + right["leaves"],
            "label": f"cluster_{next_id}",
        }
        clusters[next_id] = merged
        merges.append(
            {
                "id": next_id,
                "left": left_id,
                "right": right_id,
                "height": distance,
                "size": merged["size"],
                "members": [models[index]["model_label"] for index in merged["leaves"]],
            }
        )
        active = [cluster_id for cluster_id in active if cluster_id not in {left_id, right_id}]
        active.append(next_id)
        next_id += 1
    return {"clusters": clusters, "root": active[0], "merges": merges}


def leaf_order(tree: dict[str, Any], cluster_id: int) -> list[int]:
    cluster = tree["clusters"][cluster_id]
    if cluster["leaf"] is not None:
        return [int(cluster["leaf"])]
    return leaf_order(tree, int(cluster["left"])) + leaf_order(tree, int(cluster["right"]))


def nearest_pairs(
    models: list[dict[str, Any]],
    distances: list[list[float]],
    prompt_count: int,
    limit: int = 12,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for i, left in enumerate(models):
        for j, right in enumerate(models[i + 1 :], start=i + 1):
            pairs.append(
                {
                    "left": left["model_label"],
                    "right": right["model_label"],
                    "left_tier": left["model_tier"],
                    "right_tier": right["model_tier"],
                    "hamming_distance": distances[i][j],
                    "prompt_disagreements": round(distances[i][j] * prompt_count),
                }
            )
    return sorted(pairs, key=lambda row: (row["hamming_distance"], row["left"], row["right"]))[:limit]


def build_logistic_rows(
    prompts: list[dict[str, Any]],
    matrix_rows: list[dict[str, str]],
    models: list[dict[str, Any]],
) -> list[dict[str, float]]:
    features = {prompt["prompt_id"]: prompt_features(prompt) for prompt in prompts}
    continuous = ["num_qubits", "num_clbits", "gate_count", "gate_type_count", "gate_entropy"]
    stats = {}
    for key in continuous:
        values = [float(row[key]) for row in features.values()]
        stats[key] = (mean(values), safe_sd(values))
    rows: list[dict[str, float]] = []
    for matrix_row in matrix_rows:
        prompt_feature = features[matrix_row["prompt_id"]]
        for model_index, model in enumerate(models):
            item: dict[str, float] = {
                "y": float(matrix_row[str(model["model"])]),
                "model_index": float(model_index),
                "tier_strong_open_or_code": float(model["model_tier"] == "strong_open_or_code"),
                "tier_low_or_experimental": float(model["model_tier"] == "low_or_experimental"),
                "has_barrier": float(prompt_feature["has_barrier"]),
                "has_controlled_or_entangling": float(prompt_feature["has_controlled_or_entangling"]),
                "has_rotation": float(prompt_feature["has_rotation"]),
                "has_measure": float(prompt_feature["has_measure"]),
                "gate_type_count_raw": float(prompt_feature["gate_type_count"]),
            }
            for key in continuous:
                avg, sd = stats[key]
                item[f"z_{key}"] = (float(prompt_feature[key]) - avg) / sd
            rows.append(item)
    return rows


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def invert_matrix(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    aug = [
        [float(matrix[row][col]) for col in range(size)]
        + [1.0 if row == col else 0.0 for col in range(size)]
        for row in range(size)
    ]
    for col in range(size):
        pivot = max(range(col, size), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular matrix")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        pivot_value = aug[col][col]
        for j in range(2 * size):
            aug[col][j] /= pivot_value
        for row in range(size):
            if row == col:
                continue
            factor = aug[row][col]
            if factor == 0.0:
                continue
            for j in range(2 * size):
                aug[row][j] -= factor * aug[col][j]
    return [row[size:] for row in aug]


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    inverse = invert_matrix(matrix)
    return [sum(inverse[row][col] * vector[col] for col in range(len(vector))) for row in range(len(vector))]


def logistic_fit(
    rows: list[dict[str, float]],
    predictors: list[str],
    ridge: float = 1e-4,
    max_iter: int = 100,
    tol: float = 1e-8,
) -> dict[str, Any]:
    names = ["intercept", *predictors]
    beta = [0.0 for _ in names]
    x_rows = [[1.0, *[row[name] for name in predictors]] for row in rows]
    y = [row["y"] for row in rows]
    for _ in range(max_iter):
        gradient = [0.0 for _ in names]
        hessian = [[0.0 for _ in names] for _ in names]
        for x, target in zip(x_rows, y):
            p = sigmoid(sum(coef * value for coef, value in zip(beta, x)))
            w = max(p * (1.0 - p), 1e-8)
            residual = target - p
            for i in range(len(names)):
                gradient[i] += x[i] * residual
                for j in range(len(names)):
                    hessian[i][j] += x[i] * x[j] * w
        for i in range(1, len(names)):
            gradient[i] -= ridge * beta[i]
            hessian[i][i] += ridge
        step = solve_linear_system(hessian, gradient)
        beta = [coef + delta for coef, delta in zip(beta, step)]
        if max(abs(delta) for delta in step) < tol:
            break
    probabilities = [sigmoid(sum(coef * value for coef, value in zip(beta, x))) for x in x_rows]
    final_hessian = [[0.0 for _ in names] for _ in names]
    for x in x_rows:
        p = sigmoid(sum(coef * value for coef, value in zip(beta, x)))
        w = max(p * (1.0 - p), 1e-8)
        for i in range(len(names)):
            for j in range(len(names)):
                final_hessian[i][j] += x[i] * x[j] * w
    for i in range(1, len(names)):
        final_hessian[i][i] += ridge
    covariance = invert_matrix(final_hessian)
    standard_errors = [math.sqrt(max(covariance[i][i], 0.0)) for i in range(len(names))]
    loglik = sum(
        target * math.log(max(prob, 1e-12)) + (1.0 - target) * math.log(max(1.0 - prob, 1e-12))
        for target, prob in zip(y, probabilities)
    )
    base_rate = sum(y) / len(y)
    null_loglik = sum(
        target * math.log(max(base_rate, 1e-12)) + (1.0 - target) * math.log(max(1.0 - base_rate, 1e-12))
        for target in y
    )
    auc = roc_auc(y, probabilities)
    average_marginal_effects = marginal_effects(rows, predictors, beta)
    return {
        "n": len(rows),
        "positive_rate": base_rate,
        "predictors": predictors,
        "coefficients": [
            {
                "name": name,
                "label": PREDICTOR_LABELS.get(name, name),
                "log_odds": coef,
                "standard_error": standard_errors[index],
                "wald_95_low": coef - 1.96 * standard_errors[index],
                "wald_95_high": coef + 1.96 * standard_errors[index],
                "odds_ratio": math.exp(coef) if -20 < coef < 20 else None,
                "average_marginal_effect": average_marginal_effects.get(name),
            }
            for index, (name, coef) in enumerate(zip(names, beta))
        ],
        "log_likelihood": loglik,
        "null_log_likelihood": null_loglik,
        "mcfadden_pseudo_r2": 1.0 - loglik / null_loglik if null_loglik else None,
        "auc": auc,
    }


def roc_auc(y: list[float], scores: list[float]) -> float:
    pairs = sorted(zip(scores, y), key=lambda pair: pair[0])
    rank_sum = 0.0
    pos = 0
    neg = 0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and pairs[end][0] == pairs[index][0]:
            end += 1
        avg_rank = (index + 1 + end) / 2.0
        positives = sum(1 for _, target in pairs[index:end] if target == 1.0)
        negatives = (end - index) - positives
        rank_sum += positives * avg_rank
        pos += positives
        neg += negatives
        index = end
    if pos == 0 or neg == 0:
        return 0.5
    return (rank_sum - pos * (pos + 1) / 2.0) / (pos * neg)


def marginal_effects(rows: list[dict[str, float]], predictors: list[str], beta: list[float]) -> dict[str, float]:
    effects = {"intercept": None}
    for predictor_index, predictor in enumerate(predictors, start=1):
        binary_values = {row[predictor] for row in rows}
        if binary_values <= {0.0, 1.0}:
            diffs = []
            for row in rows:
                x0 = [1.0, *[row[name] for name in predictors]]
                x1 = list(x0)
                x0[predictor_index] = 0.0
                x1[predictor_index] = 1.0
                p0 = sigmoid(sum(coef * value for coef, value in zip(beta, x0)))
                p1 = sigmoid(sum(coef * value for coef, value in zip(beta, x1)))
                diffs.append(p1 - p0)
            effects[predictor] = sum(diffs) / len(diffs)
        else:
            derivatives = []
            for row in rows:
                x = [1.0, *[row[name] for name in predictors]]
                p = sigmoid(sum(coef * value for coef, value in zip(beta, x)))
                derivatives.append(p * (1.0 - p) * beta[predictor_index])
            effects[predictor] = sum(derivatives) / len(derivatives)
    return effects


def design_means(rows: list[dict[str, float]], predictors: list[str]) -> dict[str, float]:
    return {
        predictor: sum(row[predictor] for row in rows) / len(rows)
        for predictor in predictors
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
    size: int = 14,
    weight: int = 400,
    fill: str = TEXT,
    anchor: str = "start",
    rotate: float | None = None,
) -> str:
    attrs: dict[str, object] = {
        "x": round(x, 2),
        "y": round(y, 2),
        "font-size": size,
        "font-weight": weight,
        "fill": fill,
        "text-anchor": anchor,
        "font-family": PUBLICATION_SERIF_FONT_STACK,
    }
    if rotate is not None:
        attrs["transform"] = f"rotate({rotate} {round(x, 2)} {round(y, 2)})"
    return tag(
        "text",
        attrs,
        escape(value),
    )


def rect(x: float, y: float, width: float, height: float, *, fill: str, stroke: str = "none", rx: int = 0) -> str:
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


def circle(
    cx: float,
    cy: float,
    r: float,
    *,
    fill: str,
    stroke: str = "none",
    opacity: float | None = None,
) -> str:
    attrs: dict[str, object] = {
        "cx": round(cx, 2),
        "cy": round(cy, 2),
        "r": r,
        "fill": fill,
        "stroke": stroke,
    }
    if opacity is not None:
        attrs["opacity"] = opacity
    return tag("circle", attrs)


def draw_dendrogram(lines: list[str], result: dict[str, Any], x0: float, y0: float) -> None:
    models = result["models"]
    tree = result["hierarchical_clustering"]["tree"]
    root = int(tree["root"])
    clusters = {int(key): value for key, value in tree["clusters"].items()}
    order = result["hierarchical_clustering"]["leaf_order"]
    max_height = max(float(merge["height"]) for merge in result["hierarchical_clustering"]["merges"]) or 1.0
    label_x = x0
    branch_x = x0 + 258
    branch_w = 320
    top = y0 + 46
    row_h = 39
    y_by_leaf = {leaf: top + index * row_h for index, leaf in enumerate(order)}
    y_by_cluster: dict[int, float] = {}
    x_by_cluster: dict[int, float] = {}

    def draw_cluster(cluster_id: int) -> tuple[float, float]:
        cluster = clusters[cluster_id]
        if cluster["leaf"] is not None:
            leaf = int(cluster["leaf"])
            y = y_by_leaf[leaf]
            x = branch_x
            y_by_cluster[cluster_id] = y
            x_by_cluster[cluster_id] = x
            model = models[leaf]
            color = MODEL_COLORS.get(model["model_tier"], SLATE)
            lines.append(text(label_x, y + 4, model["model_label"], size=13, weight=600, fill=TEXT))
            lines.append(circle(branch_x - 12, y, 4.8, fill=color))
            return x, y
        left_x, left_y = draw_cluster(int(cluster["left"]))
        right_x, right_y = draw_cluster(int(cluster["right"]))
        x = branch_x + float(cluster["height"]) / max_height * branch_w
        lines.append(line(left_x, left_y, x, left_y, stroke=AXIS, width=1.25))
        lines.append(line(right_x, right_y, x, right_y, stroke=AXIS, width=1.25))
        lines.append(line(x, left_y, x, right_y, stroke=AXIS, width=1.25))
        y = (left_y + right_y) / 2.0
        y_by_cluster[cluster_id] = y
        x_by_cluster[cluster_id] = x
        return x, y

    lines.append(text(x0, y0, "A", size=15, weight=800, fill=BLUE))
    lines.append(text(x0 + 26, y0, "Model-profile clustering", size=20, weight=800))
    lines.append(text(x0 - 30, top + (len(order) - 1) * row_h / 2, "Model rows", size=14, fill=MUTED, anchor="middle", rotate=-90))
    for tick in [0.0, 0.1, 0.2, 0.3]:
        tx = branch_x + min(tick / max_height, 1.0) * branch_w
        lines.append(line(tx, top - 20, tx, top + len(order) * row_h - 12, stroke=GRID))
        lines.append(text(tx, top - 26, f"{tick:.1f}", size=12, fill=MUTED, anchor="middle"))
    draw_cluster(root)
    lines.append(text(branch_x + branch_w / 2, top + len(order) * row_h + 20, "Hamming distance", size=14, fill=MUTED, anchor="middle"))
    legend_y = top + len(order) * row_h + 62
    tier_legend = [
        ("frontier/API", TEAL),
        ("strong open/code", BLUE),
        ("low/experimental", RUST),
    ]
    for index, (label, color) in enumerate(tier_legend):
        x = x0 + index * 170
        lines.append(circle(x, legend_y - 4, 4.2, fill=color))
        lines.append(text(x + 13, legend_y, label, size=14, fill=MUTED))


def draw_logistic_effects(lines: list[str], result: dict[str, Any], x0: float, y0: float) -> None:
    logistic = result["primary_logistic_regression"]
    order = [
        "tier_low_or_experimental",
        "tier_strong_open_or_code",
        "z_gate_type_count",
        "has_barrier",
        "has_controlled_or_entangling",
        "z_num_clbits",
        "z_num_qubits",
        "z_gate_count",
        "has_rotation",
        "has_measure",
    ]
    by_name = {term["name"]: term for term in logistic["coefficients"] if term["name"] != "intercept"}
    terms = [by_name[name] for name in order if name in by_name]
    lines.append(text(x0, y0, "B", size=15, weight=800, fill=BLUE))
    lines.append(text(x0 + 26, y0, "Logistic coefficient forest", size=20, weight=800))
    chart_x = x0 + 238
    chart_y = y0 + 46
    chart_w = 338
    row_h = 29
    lows = [float(term["wald_95_low"]) for term in terms]
    highs = [float(term["wald_95_high"]) for term in terms]
    xmin = min(-3.2, min(lows) - 0.2)
    xmax = max(3.0, max(highs) + 0.2)
    zero_x = chart_x + (0 - xmin) / (xmax - xmin) * chart_w
    row_center_y = chart_y + (len(terms) - 1) * row_h / 2
    lines.append(text(x0 - 34, row_center_y, "Predictor rows", size=14, fill=MUTED, anchor="middle", rotate=-90))
    lines.append(line(zero_x, chart_y - 20, zero_x, chart_y + len(terms) * row_h, stroke="#9aa8b6", width=1.35))
    lines.append(text(zero_x + 6, chart_y + len(terms) * row_h + 18, "0 = no effect", size=12, fill=MUTED))
    tick_start = math.ceil(xmin)
    tick_end = math.floor(xmax)
    for tick in range(tick_start, tick_end + 1):
        tx = chart_x + (tick - xmin) / (xmax - xmin) * chart_w
        lines.append(line(tx, chart_y - 12, tx, chart_y + len(terms) * row_h, stroke=GRID))
        lines.append(text(tx, chart_y - 18, str(tick), size=12, fill=MUTED, anchor="middle"))
    for index, term in enumerate(terms):
        y = chart_y + index * row_h
        coef = float(term["log_odds"])
        low = float(term["wald_95_low"])
        high = float(term["wald_95_high"])
        low_x = chart_x + (low - xmin) / (xmax - xmin) * chart_w
        high_x = chart_x + (high - xmin) / (xmax - xmin) * chart_w
        end_x = chart_x + (coef - xmin) / (xmax - xmin) * chart_w
        color = RUST if coef < 0 else TEAL
        lines.append(text(x0, y + 5, term["label"], size=13, weight=600))
        lines.append(line(low_x, y, high_x, y, stroke=color, width=2.15))
        lines.append(line(low_x, y - 4.5, low_x, y + 4.5, stroke=color, width=1.25))
        lines.append(line(high_x, y - 4.5, high_x, y + 4.5, stroke=color, width=1.25))
        lines.append(circle(end_x, y, 4.8, fill=color, stroke="#ffffff"))
        odds = term["odds_ratio"]
        odds_text = "--" if odds is None else f"{odds:.2f}"
        lines.append(text(chart_x + chart_w + 12, y + 5, odds_text, size=12, fill=MUTED))
    lines.append(text(chart_x + chart_w + 72, row_center_y, "Odds ratios", size=14, fill=MUTED, anchor="middle", rotate=-90))
    lines.append(text(chart_x + chart_w / 2, chart_y + len(terms) * row_h + 30, "Log-odds coefficient (95% Wald CI)", size=14, fill=MUTED, anchor="middle"))
def draw_probability_curves(lines: list[str], result: dict[str, Any], x0: float, y0: float) -> None:
    logistic = result["primary_logistic_regression"]
    predictors = logistic["predictors"]
    coefficients = {term["name"]: float(term["log_odds"]) for term in logistic["coefficients"]}
    rows = result["logistic_design_means"]
    outcome_points = result["logistic_outcome_points"]
    lines.append(text(x0, y0, "C", size=15, weight=800, fill=BLUE))
    lines.append(text(x0 + 26, y0, "Logistic fit", size=20, weight=800))
    chart_x = x0 + 64
    chart_y = y0 + 38
    chart_w = 560
    chart_h = 210
    x_values = [float(point["z_gate_type_count"]) for point in outcome_points]
    xmin = min(-1.5, min(x_values) - 0.25)
    xmax = max(2.0, max(x_values) + 0.25)
    lines.append(rect(chart_x, chart_y, chart_w, chart_h, fill="#fbfdff", stroke="#e5ebf2"))
    tick_start = math.ceil(xmin)
    tick_end = math.floor(xmax)
    for tick in range(tick_start, tick_end + 1):
        tx = chart_x + (tick - xmin) / (xmax - xmin) * chart_w
        lines.append(line(tx, chart_y, tx, chart_y + chart_h, stroke=GRID))
        label = "0" if tick == 0 else f"{tick:+d}"
        lines.append(text(tx, chart_y + chart_h + 20, label, size=13, fill=MUTED, anchor="middle"))
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        ty = chart_y + chart_h - tick * chart_h
        lines.append(line(chart_x, ty, chart_x + chart_w, ty, stroke=GRID))
        lines.append(text(chart_x - 10, ty + 4, f"{int(tick * 100)}", size=13, fill=MUTED, anchor="end"))
    tier_offsets = {
        "frontier": -6.0,
        "strong open/code": 0.0,
        "low/experimental": 6.0,
    }
    for point in outcome_points:
        x = chart_x + (float(point["z_gate_type_count"]) - xmin) / (xmax - xmin) * chart_w
        model_index = int(point.get("model_index", 0))
        x += tier_offsets.get(str(point["tier"]), 0.0) + ((model_index % 3) - 1) * 1.2
        target = float(point["y"])
        y_offset = ((model_index % 7) - 3) * 1.15
        y = chart_y + 12 + y_offset if target == 1.0 else chart_y + chart_h - 12 + y_offset
        y = max(chart_y + 4, min(chart_y + chart_h - 4, y))
        lines.append(circle(x, y, 1.8, fill=SLATE, stroke="none", opacity=0.22))
    bins: dict[float, list[float]] = {}
    for point in outcome_points:
        bins.setdefault(float(point["gate_type_count_raw"]), []).append(float(point["y"]))
    for gate_type_count, values in sorted(bins.items()):
        z_values_for_bin = [
            float(point["z_gate_type_count"])
            for point in outcome_points
            if float(point["gate_type_count_raw"]) == gate_type_count
        ]
        x = chart_x + (mean(z_values_for_bin) - xmin) / (xmax - xmin) * chart_w
        empirical = sum(values) / len(values)
        y = chart_y + chart_h - empirical * chart_h
        lines.append(circle(x, y, 5.2, fill="#ffffff", stroke=TEXT))
    tier_defs = [
        ("frontier_api", "frontier", TEAL, 0.0, 0.0),
        ("strong_open_or_code", "strong open/code", BLUE, 1.0, 0.0),
        ("low_or_experimental", "low/experimental", RUST, 0.0, 1.0),
    ]
    z_values = [xmin + step * ((xmax - xmin) / 90) for step in range(91)]
    for _, label, color, strong_value, low_value in tier_defs:
        points = []
        for z_gate_type in z_values:
            x_values = {"intercept": 1.0}
            for predictor in predictors:
                x_values[predictor] = float(rows.get(predictor, 0.0))
            x_values["tier_strong_open_or_code"] = strong_value
            x_values["tier_low_or_experimental"] = low_value
            x_values["z_gate_type_count"] = z_gate_type
            logit = sum(coefficients[name] * value for name, value in x_values.items() if name in coefficients)
            probability = sigmoid(logit)
            x = chart_x + (z_gate_type - xmin) / (xmax - xmin) * chart_w
            y = chart_y + chart_h - probability * chart_h
            points.append((x, y))
        for left, right in zip(points, points[1:]):
            lines.append(line(left[0], left[1], right[0], right[1], stroke=color, width=2.5))
    lines.append(text(chart_x + chart_w / 2, chart_y + chart_h + 46, "Gate-type count (z)", size=15, fill=MUTED, anchor="middle"))
    lines.append(text(chart_x - 52, chart_y + chart_h / 2, "P(structural match)", size=15, fill=MUTED, anchor="middle", rotate=-90))
    legend_x = chart_x + 8
    legend_y = chart_y + chart_h + 66
    legend_items = [
        ("line", "frontier", TEAL, 0),
        ("line", "strong open/code", BLUE, 92),
        ("line", "low/experimental", RUST, 236),
        ("dot", "observed", SLATE, 378),
        ("hollow", "bin rate", TEXT, 456),
    ]
    for kind, label, color, offset in legend_items:
        x = legend_x + offset
        if kind == "line":
            lines.append(line(x, legend_y, x + 18, legend_y, stroke=color, width=2.4))
            lines.append(text(x + 24, legend_y + 4, label, size=14, fill=MUTED))
        elif kind == "dot":
            lines.append(circle(x + 3, legend_y, 2.0, fill=color, opacity=0.3))
            lines.append(text(x + 12, legend_y + 4, label, size=14, fill=MUTED))
        else:
            lines.append(circle(x + 4, legend_y, 4.6, fill="#ffffff", stroke=color))
            lines.append(text(x + 14, legend_y + 4, label, size=14, fill=MUTED))


def write_svg(result: dict[str, Any]) -> None:
    width = 1400
    height = 740
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "PQID-Bench hierarchical clustering and logistic regression panel"),
        tag("desc", {"id": "desc"}, "Hierarchical clustering of model structural-success profiles, logistic-regression coefficient forest, and fitted logistic outcome distribution."),
        rect(0, 0, width, height, fill=PANEL_BG),
    ]
    draw_dendrogram(lines, result, 56, 28)
    draw_logistic_effects(lines, result, 738, 28)
    draw_probability_curves(lines, result, 738, 420)
    lines.append("</svg>")
    SVG_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(result: dict[str, Any], path: Path = MD_OUT) -> None:
    primary = result["primary_logistic_regression"]
    sensitivity = result["entropy_sensitivity_logistic_regression"]
    collinear = result["full_collinear_logistic_regression"]
    lines = [
        "# PQID-Bench Hierarchical Clustering And Logistic Regression",
        "",
        f"- prompts: `{result['prompt_count']}`",
        f"- models: `{result['model_count']}`",
        f"- prompt-model rows for logistic regression: `{primary['n']}`",
        f"- logistic positive rate: `{pct(primary['positive_rate'])}`",
        f"- primary logistic AUC: `{primary['auc']:.3f}`",
        f"- primary McFadden pseudo-R2: `{primary['mcfadden_pseudo_r2']:.3f}`",
        f"- entropy-only sensitivity AUC: `{sensitivity['auc']:.3f}`",
        f"- entropy-only sensitivity McFadden pseudo-R2: `{sensitivity['mcfadden_pseudo_r2']:.3f}`",
        "",
        "## Nearest Model-Profile Pairs",
        "",
        "| model A | model B | Hamming distance | prompt disagreements |",
        "| --- | --- | ---: | ---: |",
    ]
    for pair in result["nearest_pairs"]:
        lines.append(f"| {pair['left']} | {pair['right']} | {pair['hamming_distance']:.3f} | {pair['prompt_disagreements']} |")
    lines.extend(
        [
            "",
            "## Logistic Regression Average Marginal Effects",
            "",
            "Primary specification: model-tier indicators plus gate-type count and other circuit descriptors. Gate entropy is omitted from this primary model because it is strongly related to gate-type count.",
            "",
            "| predictor | log-odds | odds ratio | average marginal effect |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for term in primary["coefficients"]:
        if term["name"] == "intercept":
            continue
        odds = "--" if term["odds_ratio"] is None else f"{term['odds_ratio']:.3f}"
        lines.append(
            f"| {term['label']} | {term['log_odds']:.3f} | {odds} | {pp(term['average_marginal_effect'])} |"
        )
    lines.extend(
        [
            "",
            "## Entropy Sensitivity Specification",
            "",
            "This specification replaces gate-type count with gate entropy. It checks whether the entropy result survives when the collinear gate-vocabulary count is not included in the same logistic model.",
            "",
            "| predictor | log-odds | odds ratio | average marginal effect |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for term in sensitivity["coefficients"]:
        if term["name"] == "intercept":
            continue
        odds = "--" if term["odds_ratio"] is None else f"{term['odds_ratio']:.3f}"
        lines.append(
            f"| {term['label']} | {term['log_odds']:.3f} | {odds} | {pp(term['average_marginal_effect'])} |"
        )
    entropy_full = next(term for term in collinear["coefficients"] if term["name"] == "z_gate_entropy")
    gate_types_full = next(term for term in collinear["coefficients"] if term["name"] == "z_gate_type_count")
    lines.extend(
        [
            "",
            "## Collinearity Note",
            "",
            f"When gate entropy and gate-type count are included together, the model assigns the main heterogeneity penalty to gate-type count ({pp(gate_types_full['average_marginal_effect'])}) and the gate-entropy term becomes small ({pp(entropy_full['average_marginal_effect'])}). This is a descriptor-collinearity warning, not evidence that entropy is unimportant.",
            "",
            "## Interpretation",
            "",
            "Hierarchical clustering is useful here because it compares models by which prompts they solve, not just by aggregate score. The nearest-pair table shows that some models with different providers can share nearly identical structural-success profiles on this held-out split.",
            "",
            "The logistic regression is the binary-outcome counterpart to the linear probability model. It preserves the same directional story for model tier, gate-vocabulary complexity, and staged/barrier structure. The entropy-only sensitivity confirms that gate entropy is negative when it is not competing with gate-type count inside the same logistic model. The estimates remain descriptive because prompt-model rows share prompts and models.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_caption(result: dict[str, Any]) -> None:
    best_pair = result["nearest_pairs"][0]
    primary = result["primary_logistic_regression"]
    sensitivity = result["entropy_sensitivity_logistic_regression"]
    CAPTION_OUT.write_text(
        "\n".join(
            [
                "# Clustering And Logistic Regression Panel Caption",
                "",
                f"**Figure 4. Hierarchical clustering and logistic regression diagnostics.** Panel A clusters the `{result['model_count']}` model rows by Hamming distance over the same `{result['prompt_count']}` prompt-level reference-signature indicators; the vertical guide lines are Hamming-distance ticks, so farther-right merges indicate less similar prompt-level success profiles. The nearest pair is {best_pair['left']} and {best_pair['right']} (`d={best_pair['hamming_distance']:.3f}`). Panel B shows a coefficient forest from a descriptive logistic regression over the `{result['model_count'] * result['prompt_count']}` prompt-model binary signature-match outcomes (AUC=`{primary['auc']:.3f}`, McFadden `R^2={primary['mcfadden_pseudo_r2']:.3f}`); the y-axis rows are predictors, the x-axis is the log-odds coefficient scale, the darker zero line marks no effect, and the right-side column reports odds ratios. Intervals are unclustered Wald intervals shown for scale. Panel C shows observed binary outcomes, empirical signature-match rates by raw gate-type count, and fitted tier-specific sigmoid curves over standardized gate-type count. An entropy-only sensitivity model gives AUC=`{sensitivity['auc']:.3f}` and McFadden `R^2={sensitivity['mcfadden_pseudo_r2']:.3f}`. The analysis is exploratory and release-bound.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts-jsonl", type=Path, default=PROMPTS_JSONL)
    parser.add_argument("--matrix-csv", type=Path, default=MATRIX_CSV)
    parser.add_argument("--regression-json", type=Path, default=REGRESSION_JSON)
    parser.add_argument("--json-out", type=Path, default=JSON_OUT)
    parser.add_argument("--md-out", type=Path, default=MD_OUT)
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Write analytical artifacts without invoking the manuscript figure builder.",
    )
    args = parser.parse_args()

    regression_data = json.loads(args.regression_json.read_text(encoding="utf-8"))
    prompts = read_jsonl(args.prompts_jsonl)
    matrix_rows = read_matrix(args.matrix_csv)
    models = model_metadata(regression_data)
    vectors = model_vectors(models, matrix_rows)
    distances = pairwise_hamming(models, vectors)
    tree = hierarchical_average_linkage(models, distances)
    primary_predictors = [
        "tier_strong_open_or_code",
        "tier_low_or_experimental",
        "has_barrier",
        "z_gate_type_count",
        "has_controlled_or_entangling",
        "z_num_clbits",
        "z_num_qubits",
        "z_gate_count",
        "has_rotation",
        "has_measure",
    ]
    entropy_sensitivity_predictors = [
        "tier_strong_open_or_code",
        "tier_low_or_experimental",
        "z_gate_entropy",
        "has_barrier",
        "has_controlled_or_entangling",
        "z_num_clbits",
        "z_num_qubits",
        "z_gate_count",
        "has_rotation",
        "has_measure",
    ]
    full_collinear_predictors = [
        "tier_strong_open_or_code",
        "tier_low_or_experimental",
        "z_gate_entropy",
        "has_barrier",
        "z_gate_type_count",
        "has_controlled_or_entangling",
        "z_num_clbits",
        "z_num_qubits",
        "z_gate_count",
        "has_rotation",
        "has_measure",
    ]
    logistic_rows = build_logistic_rows(prompts, matrix_rows, models)
    logistic_outcome_points = []
    for row in logistic_rows:
        if row["tier_low_or_experimental"] == 1.0:
            tier = "low/experimental"
        elif row["tier_strong_open_or_code"] == 1.0:
            tier = "strong open/code"
        else:
            tier = "frontier"
        logistic_outcome_points.append(
            {
                "z_gate_type_count": row["z_gate_type_count"],
                "gate_type_count_raw": row["gate_type_count_raw"],
                "model_index": row["model_index"],
                "y": row["y"],
                "tier": tier,
            }
        )
    primary_logistic = logistic_fit(logistic_rows, primary_predictors)
    entropy_sensitivity_logistic = logistic_fit(logistic_rows, entropy_sensitivity_predictors)
    full_collinear_logistic = logistic_fit(logistic_rows, full_collinear_predictors)
    result = {
        "prompt_count": len(prompts),
        "model_count": len(models),
        "models": models,
        "distance_metric": "Hamming distance over binary all-structure-match prompt outcomes",
        "linkage": "average",
        "nearest_pairs": nearest_pairs(models, distances, len(prompts)),
        "hierarchical_clustering": {
            "leaf_order": leaf_order(tree, int(tree["root"])),
            "merges": tree["merges"],
            "tree": {
                "root": tree["root"],
                "clusters": {str(key): value for key, value in tree["clusters"].items()},
            },
        },
        "primary_logistic_regression": primary_logistic,
        "entropy_sensitivity_logistic_regression": entropy_sensitivity_logistic,
        "full_collinear_logistic_regression": full_collinear_logistic,
        "logistic_design_means": design_means(logistic_rows, primary_predictors),
        "logistic_outcome_points": logistic_outcome_points,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(result, args.md_out)
    # The manuscript-facing panel now combines this clustering result with PCA
    # and prespecified cluster-aware paired contrasts. Keep this command as the
    # canonical clustering refresh, then delegate rendering to the joint builder.
    if not args.no_render:
        from build_pqid_bench_inferential_figures import build_figure3

        build_figure3()
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")
    if not args.no_render:
        print(f"Wrote {SVG_OUT}")
        print(f"Wrote {CAPTION_OUT}")


if __name__ == "__main__":
    main()
