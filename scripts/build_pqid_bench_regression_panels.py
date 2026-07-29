"""Build PCA, binomial dose-response, and regression panels for PQID-Bench."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any
from xml.sax.saxutils import escape

from acm_figure_style import ACM_SERIF_FONT_STACK


ROOT = Path("PQID/submissions/acm_tqc_benchmark")
ARTIFACTS_DIR = ROOT / "artifacts"
FIGURES_DIR = ROOT / "figures"

PROMPTS_JSONL = ARTIFACTS_DIR / "test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
MATRIX_CSV = ARTIFACTS_DIR / "analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv"
REGRESSION_JSON = ARTIFACTS_DIR / "analysis_154/pqid_bench_model_regression_analysis.json"

REGRESSION_SVG = FIGURES_DIR / "regression_distribution_panel.svg"
REGRESSION_CAPTION = FIGURES_DIR / "regression_distribution_panel_caption.md"

FONT_SCALE = 1.25


TEXT = "#1f2933"
MUTED = "#64748b"
GRID = "#edf2f7"
AXIS = "#516174"
TEAL = "#1f766d"
GOLD = "#b7791f"
RUST = "#b45309"
BLUE = "#315a9f"
PLUM = "#7c3f72"
SLATE = "#475467"
PANEL_BG = "#ffffff"
GATE_LOW = "#0072B2"
GATE_MID = "#009E73"
GATE_HIGH = "#D55E00"

MODEL_COLORS = {
    "frontier_api": TEAL,
    "strong_open_or_code": BLUE,
    "low_or_experimental": RUST,
}

COEFFICIENT_LABELS = {
    "z_num_qubits": "qubits",
    "z_num_clbits": "classical bits",
    "z_gate_count": "gate count",
    "z_gate_type_count": "gate types",
    "z_gate_entropy": "gate entropy",
    "has_barrier": "barrier",
    "has_controlled_or_entangling": "controlled / entangling",
    "has_rotation": "rotation",
    "has_measure": "measurement",
}


def scaled_font(size: int | float) -> float:
    return round(float(size) * FONT_SCALE, 1)


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
        "font-size": scaled_font(size),
        "font-weight": weight,
        "fill": fill,
        "text-anchor": anchor,
        "font-family": ACM_SERIF_FONT_STACK,
    }
    if rotate is not None:
        attrs["transform"] = f"rotate({rotate} {round(x, 2)} {round(y, 2)})"
    return tag(
        "text",
        attrs,
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
    rx: int = 0,
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


def circle(cx: float, cy: float, r: float, *, fill: str, stroke: str = "none", stroke_width: float = 1) -> str:
    return tag(
        "circle",
        {
            "cx": round(cx, 2),
            "cy": round(cy, 2),
            "r": round(r, 2),
            "fill": fill,
            "stroke": stroke,
            "stroke-width": stroke_width,
        },
    )


def path_element(
    d: str,
    *,
    fill: str = "none",
    stroke: str = "none",
    stroke_width: float = 1,
    opacity: float | None = None,
) -> str:
    attrs: dict[str, object] = {
        "d": d,
        "fill": fill,
        "stroke": stroke,
        "stroke-width": stroke_width,
    }
    if opacity is not None:
        attrs["opacity"] = opacity
    return tag("path", attrs)


def pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def pp(value: float) -> str:
    return f"{100.0 * value:+.1f} pp"


def model_short_label(label: str) -> str:
    replacements = {
        "GPT-5.4 mini": "GPT-5.4m",
        "Claude Sonnet 4.6": "Sonnet 4.6",
        "Claude Opus 4.8": "Opus 4.8",
        "Gemini 2.5 Pro": "G2.5 Pro",
        "Gemini 3.1 Pro Preview": "G3.1 Pro",
        "Gemini 3.1 Pro": "G3.1 Pro",
        "DeepSeek V4 Pro": "DS V4 Pro",
        "DeepSeek V4 Flash": "DS V4 Flash",
        "GPT-OSS 120B": "OSS 120B",
        "GPT-OSS 20B": "OSS 20B",
        "Qwen3 32B": "Qwen3",
        "Llama 4 Scout": "L4 Scout",
        "Llama 8B": "L8B",
    }
    return replacements.get(label, label)


def text_box(x: float, y: float, label: str, *, size: int, anchor: str) -> tuple[float, float, float, float]:
    display_size = scaled_font(size)
    width = max(24.0, len(label) * display_size * 0.58 + 8.0)
    height = display_size + 7.0
    if anchor == "end":
        x1 = x - width
    elif anchor == "middle":
        x1 = x - width / 2
    else:
        x1 = x
    y1 = y - height + 4.0
    return (x1, y1, x1 + width, y1 + height)


def boxes_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], pad: float = 3.0) -> bool:
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])


def outside_penalty(box: tuple[float, float, float, float], bounds: tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = box
    bx1, by1, bx2, by2 = bounds
    return (
        max(0.0, bx1 - x1)
        + max(0.0, by1 - y1)
        + max(0.0, x2 - bx2)
        + max(0.0, y2 - by2)
    )


def r_squared_text(
    x: float,
    y: float,
    prefix: str,
    value: float,
    *,
    size: int = 10,
    fill: str = MUTED,
    anchor: str = "start",
) -> str:
    attrs = {
        "x": round(x, 2),
        "y": round(y, 2),
        "font-size": scaled_font(size),
        "font-weight": 400,
        "fill": fill,
        "text-anchor": anchor,
        "font-family": ACM_SERIF_FONT_STACK,
    }
    content = (
        f"{escape(prefix)}R"
        f'<tspan baseline-shift="super" font-size="{round(scaled_font(size) * 0.7, 1)}">2</tspan>'
        f"={value:.3f}"
    )
    return tag("text", attrs, content)


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


def gate_entropy(gates: dict[str, int]) -> float:
    total = sum(gates.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in gates.values():
        p = count / total
        entropy -= p * math.log(p)
    return entropy


def panel_label(x: float, y: float, letter: str, title: str) -> list[str]:
    return [
        text(x, y, letter, size=14, weight=800, fill=BLUE),
        text(x + 28, y, title, size=18, weight=800),
    ]


def simple_regression(points: list[tuple[float, float]]) -> tuple[float, float]:
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    x_mean = mean(x_values)
    y_mean = mean(y_values)
    denom = sum((x - x_mean) ** 2 for x in x_values)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / denom if denom else 0.0
    intercept = y_mean - slope * x_mean
    return intercept, slope


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def binomial_logit_fit(points: list[dict[str, float]], model_count: int, features: list[str] | None = None) -> dict[str, Any]:
    features = features or ["gate_entropy"]
    x_values = [float(point["gate_entropy"]) for point in points]
    successes = [int(point["solved_models"]) for point in points]
    total_successes = sum(successes)
    total_trials = len(points) * model_count
    base_rate = min(max(total_successes / total_trials, 1e-6), 1.0 - 1e-6)
    beta = [0.0] * (len(features) + 1)
    beta[0] = math.log(base_rate / (1.0 - base_rate))
    for _ in range(100):
        size = len(beta)
        hessian = [[0.0 for _ in range(size)] for _ in range(size)]
        gradient = [0.0 for _ in range(size)]
        for point, k in zip(points, successes):
            x = [1.0] + [float(point[feature]) for feature in features]
            eta = sum(b * value for b, value in zip(beta, x))
            p = min(max(sigmoid(eta), 1e-8), 1.0 - 1e-8)
            residual = k - model_count * p
            weight = model_count * p * (1.0 - p)
            for i in range(size):
                gradient[i] += residual * x[i]
                for j in range(size):
                    hessian[i][j] += weight * x[i] * x[j]
        delta = solve_linear_system(hessian, gradient)
        beta = [b + d for b, d in zip(beta, delta)]
        if max(abs(d) for d in delta) < 1e-9:
            break
    size = len(beta)
    hessian = [[0.0 for _ in range(size)] for _ in range(size)]
    log_likelihood = 0.0
    null_log_likelihood = 0.0
    for point, k in zip(points, successes):
        x = [1.0] + [float(point[feature]) for feature in features]
        p = min(max(sigmoid(sum(b * value for b, value in zip(beta, x))), 1e-8), 1.0 - 1e-8)
        weight = model_count * p * (1.0 - p)
        for i in range(size):
            for j in range(size):
                hessian[i][j] += weight * x[i] * x[j]
        log_likelihood += k * math.log(p) + (model_count - k) * math.log(1.0 - p)
        null_log_likelihood += k * math.log(base_rate) + (model_count - k) * math.log(1.0 - base_rate)
    covariance = invert_matrix(hessian)
    x_mean = mean(x_values)
    x_sd = math.sqrt(sum((x - x_mean) ** 2 for x in x_values) / max(len(x_values) - 1, 1))
    entropy_index = features.index("gate_entropy") + 1
    odds_ratio_sd = math.exp(beta[entropy_index] * x_sd)
    pseudo_r2 = 1.0 - (log_likelihood / null_log_likelihood) if null_log_likelihood else 0.0
    return {
        "beta": beta,
        "features": features,
        "covariance": covariance,
        "odds_ratio_sd": odds_ratio_sd,
        "pseudo_r2": pseudo_r2,
        "x_sd": x_sd,
    }


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda row: abs(augmented[row][i]))
        augmented[i], augmented[pivot] = augmented[pivot], augmented[i]
        if abs(augmented[i][i]) < 1e-10:
            augmented[i][i] += 1e-6
        divisor = augmented[i][i]
        for col in range(i, n + 1):
            augmented[i][col] /= divisor
        for row in range(n):
            if row == i:
                continue
            factor = augmented[row][i]
            for col in range(i, n + 1):
                augmented[row][col] -= factor * augmented[i][col]
    return [augmented[i][n] for i in range(n)]


def invert_matrix(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)
    inverse: list[list[float]] = []
    for col in range(n):
        basis = [1.0 if row == col else 0.0 for row in range(n)]
        inverse.append(solve_linear_system([row[:] for row in matrix], basis))
    return [[inverse[col][row] for col in range(n)] for row in range(n)]


def logit_prediction(fit: dict[str, Any], values: dict[str, float]) -> tuple[float, float, float]:
    x = [1.0] + [float(values[feature]) for feature in fit["features"]]
    eta = sum(float(beta) * value for beta, value in zip(fit["beta"], x))
    covariance = fit["covariance"]
    var_eta = 0.0
    for i, xi in enumerate(x):
        for j, xj in enumerate(x):
            var_eta += xi * xj * float(covariance[i][j])
    se_eta = math.sqrt(max(var_eta, 0.0))
    y = sigmoid(eta)
    low = sigmoid(eta - 1.96 * se_eta)
    high = sigmoid(eta + 1.96 * se_eta)
    return y, low, high


def prompt_scatter_points(prompts: list[dict[str, Any]], matrix_rows: list[dict[str, str]], model_count: int) -> list[dict[str, float]]:
    prompt_lookup = {prompt["prompt_id"]: prompt for prompt in prompts}
    points = []
    for row in matrix_rows:
        prompt = prompt_lookup[row["prompt_id"]]
        metadata = prompt["target_metadata"]
        gates = {str(key): int(value) for key, value in metadata["gate_types"].items()}
        points.append(
            {
                "gate_entropy": gate_entropy(gates),
                "has_barrier": 1 if "barrier" in gates else 0,
                "solved_models": int(row["solved_models"]),
                "structural_rate": int(row["solved_models"]) / model_count,
                "gate_type_count": len(gates),
                "gate_count": int(metadata["gate_count"]),
            }
        )
    return points


def regression_terms(regression: dict[str, Any], allowed: list[str]) -> list[dict[str, float | str]]:
    by_name = {
        str(term["name"]): float(term["coefficient"])
        for term in regression["terms"]
        if term["name"] != "intercept"
    }
    return [
        {"name": name, "label": COEFFICIENT_LABELS.get(name, name), "coefficient": by_name[name]}
        for name in allowed
        if name in by_name
    ]


def model_vectors(data: dict[str, Any], matrix_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[list[float]]]:
    models = data["model_distribution"]
    vectors = []
    for model in models:
        key = str(model["model"])
        vectors.append([float(row[key]) for row in matrix_rows])
    return models, vectors


def centered_by_prompt(vectors: list[list[float]]) -> list[list[float]]:
    rows = len(vectors)
    cols = len(vectors[0])
    means = [sum(vectors[row][col] for row in range(rows)) / rows for col in range(cols)]
    return [[vectors[row][col] - means[col] for col in range(cols)] for row in range(rows)]


def jacobi_eigen_symmetric(matrix: list[list[float]], max_iter: int = 10000, eps: float = 1e-12) -> tuple[list[float], list[list[float]]]:
    n = len(matrix)
    a = [[float(matrix[i][j]) for j in range(n)] for i in range(n)]
    vectors = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(max_iter):
        p, q = 0, 1
        max_value = abs(a[p][q])
        for i in range(n):
            for j in range(i + 1, n):
                value = abs(a[i][j])
                if value > max_value:
                    max_value = value
                    p, q = i, j
        if max_value < eps:
            break
        angle = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
        c = math.cos(angle)
        s = math.sin(angle)
        app = a[p][p]
        aqq = a[q][q]
        apq = a[p][q]
        a[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
        a[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
        a[p][q] = 0.0
        a[q][p] = 0.0
        for i in range(n):
            if i in {p, q}:
                continue
            aip = a[i][p]
            aiq = a[i][q]
            a[i][p] = c * aip - s * aiq
            a[p][i] = a[i][p]
            a[i][q] = s * aip + c * aiq
            a[q][i] = a[i][q]
        for i in range(n):
            vip = vectors[i][p]
            viq = vectors[i][q]
            vectors[i][p] = c * vip - s * viq
            vectors[i][q] = s * vip + c * viq
    eigenvalues = [a[i][i] for i in range(n)]
    return eigenvalues, vectors


def pca_model_scores(data: dict[str, Any], matrix_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], float, float]:
    models, vectors = model_vectors(data, matrix_rows)
    x = centered_by_prompt(vectors)
    n = len(x)
    cols = len(x[0])
    gram = [[0.0 for _ in range(n)] for _ in range(n)]
    scale = 1.0 / max(cols - 1, 1)
    for i in range(n):
        for j in range(n):
            gram[i][j] = sum(x[i][k] * x[j][k] for k in range(cols)) * scale
    eigenvalues, eigenvectors = jacobi_eigen_symmetric(gram)
    order = sorted(range(n), key=lambda index: eigenvalues[index], reverse=True)
    positive_total = sum(max(eigenvalues[index], 0.0) for index in order) or 1.0
    pc1, pc2 = order[0], order[1]
    scores = []
    for i, model in enumerate(models):
        score1 = eigenvectors[i][pc1] * math.sqrt(max(eigenvalues[pc1], 0.0))
        score2 = eigenvectors[i][pc2] * math.sqrt(max(eigenvalues[pc2], 0.0))
        scores.append(
            {
                **model,
                "pc1": score1,
                "pc2": score2,
            }
        )
    structural = [float(model["structural_all_match"]) for model in scores]
    pc1_values = [float(model["pc1"]) for model in scores]
    pc2_values = [float(model["pc2"]) for model in scores]
    if covariance(pc1_values, structural) < 0:
        for model in scores:
            model["pc1"] = -float(model["pc1"])
    if covariance(pc2_values, structural) < 0:
        for model in scores:
            model["pc2"] = -float(model["pc2"])
    pc1_share = max(eigenvalues[pc1], 0.0) / positive_total
    pc2_share = max(eigenvalues[pc2], 0.0) / positive_total
    return scores, pc1_share, pc2_share


def covariance(x_values: list[float], y_values: list[float]) -> float:
    x_mean = mean(x_values)
    y_mean = mean(y_values)
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))


def scale_value(value: float, low: float, high: float, length: float) -> float:
    if high == low:
        return length / 2.0
    return (value - low) / (high - low) * length


def draw_pca_panel(lines: list[str], data: dict[str, Any], matrix_rows: list[dict[str, str]], x0: float, y0: float) -> None:
    lines.extend(panel_label(x0, y0, "A", "PCA of model success profiles"))
    scores, pc1_share, pc2_share = pca_model_scores(data, matrix_rows)
    px, py = x0 + 52, y0 + 52
    pw, ph = 520, 304
    lines.append(rect(px, py, pw, ph, fill="#fbfdff", stroke="#e5ebf2"))
    pc1_values = [float(row["pc1"]) for row in scores]
    pc2_values = [float(row["pc2"]) for row in scores]
    pad_x = (max(pc1_values) - min(pc1_values)) * 0.12 or 0.1
    pad_y = (max(pc2_values) - min(pc2_values)) * 0.12 or 0.1
    x_low, x_high = min(pc1_values) - pad_x, max(pc1_values) + pad_x
    y_low, y_high = min(pc2_values) - pad_y, max(pc2_values) + pad_y
    zero_x = px + scale_value(0.0, x_low, x_high, pw)
    zero_y = py + ph - scale_value(0.0, y_low, y_high, ph)
    if px <= zero_x <= px + pw:
        lines.append(line(zero_x, py, zero_x, py + ph, stroke=GRID))
    if py <= zero_y <= py + ph:
        lines.append(line(px, zero_y, px + pw, zero_y, stroke=GRID))
    point_records: list[dict[str, Any]] = []
    for row in scores:
        cx = px + scale_value(float(row["pc1"]), x_low, x_high, pw)
        cy = py + ph - scale_value(float(row["pc2"]), y_low, y_high, ph)
        color = MODEL_COLORS.get(str(row["model_tier"]), SLATE)
        radius = 5.0 + 6.0 * float(row["structural_all_match"])
        lines.append(circle(cx, cy, radius, fill=color, stroke="#ffffff", stroke_width=1.1))
        point_records.append(
            {
                "cx": cx,
                "cy": cy,
                "radius": radius,
                "label": model_short_label(str(row["model_label"])),
            }
        )
    label_candidates = [
        (13, 4, "start"),
        (-13, 4, "end"),
        (13, -9, "start"),
        (-13, -9, "end"),
        (0, -15, "middle"),
        (0, 20, "middle"),
        (22, 14, "start"),
        (-22, 14, "end"),
        (22, -18, "start"),
        (-22, -18, "end"),
        (0, 34, "middle"),
        (0, -29, "middle"),
        (34, 2, "start"),
        (-34, 2, "end"),
    ]
    plot_bounds = (px + 4, py + 4, px + pw - 4, py + ph - 4)
    right_lane_x = px + pw + 12
    right_lane = [point for point in point_records if float(point["cx"]) >= px + pw * 0.54]
    local_points = [point for point in point_records if point not in right_lane]
    right_lane = sorted(right_lane, key=lambda item: float(item["cy"]))
    if right_lane:
        low_y = py + 18
        high_y = py + ph - 8
        gap = min(17.5, (high_y - low_y) / max(len(right_lane) - 1, 1))
        lane_y: list[float] = []
        for point in right_lane:
            proposed = max(float(point["cy"]), low_y if not lane_y else lane_y[-1] + gap)
            lane_y.append(proposed)
        overflow = max(0.0, lane_y[-1] - high_y)
        if overflow:
            lane_y = [value - overflow for value in lane_y]
        for point, ly in zip(right_lane, lane_y):
            point["lane_x"] = right_lane_x
            point["lane_y"] = ly
    occupied: list[tuple[float, float, float, float]] = []
    placements: list[dict[str, Any]] = []
    for point in right_lane:
        lx = float(point["lane_x"])
        ly = float(point["lane_y"])
        box = text_box(lx, ly, str(point["label"]), size=9, anchor="start")
        occupied.append(box)
        placements.append({"point": point, "x": lx, "y": ly, "anchor": "start", "box": box, "penalty": 0.0})
    for point in sorted(local_points, key=lambda item: -len(str(item["label"]))):
        best: dict[str, Any] | None = None
        for dx, dy, anchor in label_candidates:
            lx = float(point["cx"]) + dx
            ly = float(point["cy"]) + dy
            label = str(point["label"])
            box = text_box(lx, ly, label, size=9, anchor=anchor)
            overlaps = sum(1 for used in occupied if boxes_overlap(box, used))
            penalty = overlaps * 1000.0 + outside_penalty(box, plot_bounds) * 25.0 + abs(dx) + abs(dy) * 0.2
            candidate = {"point": point, "x": lx, "y": ly, "anchor": anchor, "box": box, "penalty": penalty}
            if best is None or penalty < float(best["penalty"]):
                best = candidate
            if overlaps == 0 and outside_penalty(box, plot_bounds) == 0:
                break
        if best is not None:
            occupied.append(best["box"])
            placements.append(best)
    for placement in placements:
        point = placement["point"]
        box = placement["box"]
        bx1, by1, bx2, by2 = box
        lines.append(line(float(point["cx"]), float(point["cy"]), float(placement["x"]), float(placement["y"]) - 4, stroke="#b8c4d0", width=0.75))
        lines.append(rect(bx1, by1, bx2 - bx1, by2 - by1, fill="#ffffff", stroke="#d8e0ea", rx=3, stroke_width=0.65))
        lines.append(text(float(placement["x"]), float(placement["y"]), str(point["label"]), size=9, weight=700, fill=TEXT, anchor=str(placement["anchor"])))
    lines.append(text(px + pw / 2, py + ph + 28, f"PC1 ({pct(pc1_share)} variance)", size=12, fill=MUTED, anchor="middle"))
    lines.append(text(px - 42, py + ph / 2, f"PC2 ({pct(pc2_share)} variance)", size=12, fill=MUTED, anchor="middle", rotate=-90))
    legend_y = py + ph + 56
    lx = px
    for tier, label in [("frontier_api", "frontier"), ("strong_open_or_code", "strong open/code"), ("low_or_experimental", "low/experimental")]:
        lines.append(circle(lx + 6, legend_y - 5, 5, fill=MODEL_COLORS[tier]))
        lines.append(text(lx + 18, legend_y, label, size=10, fill=MUTED))
        lx += 145


def draw_entropy_panel(lines: list[str], prompts: list[dict[str, Any]], matrix_rows: list[dict[str, str]], model_count: int, x0: float, y0: float) -> None:
    lines.extend(panel_label(x0, y0, "B", "Binomial logit: entropy + barrier"))
    scatter = prompt_scatter_points(prompts, matrix_rows, model_count)
    sx, sy = x0 + 56, y0 + 52
    sw, sh = 520, 304
    max_entropy = math.ceil(max(point["gate_entropy"] for point in scatter) * 10.0) / 10.0
    lines.append(rect(sx, sy, sw, sh, fill="#fbfdff", stroke="#e5ebf2"))
    for tick in [0.0, 0.5, 1.0, 1.5, 2.0]:
        if tick <= max_entropy:
            tx = sx + (tick / max_entropy) * sw
            lines.append(line(tx, sy, tx, sy + sh, stroke=GRID))
            lines.append(text(tx, sy + sh + 18, f"{tick:.1f}", size=10, fill=MUTED, anchor="middle"))
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        ty = sy + sh - tick * sh
        lines.append(line(sx, ty, sx + sw, ty, stroke=GRID))
        lines.append(text(sx - 10, ty + 4, f"{int(tick * 100)}", size=10, fill=MUTED, anchor="end"))
    fit = binomial_logit_fit(scatter, model_count, ["gate_entropy", "has_barrier"])
    for barrier_value, color, band_fill in [(0.0, TEAL, "#dcefeb"), (1.0, PLUM, "#ead9e7")]:
        curve_points: list[tuple[float, float, float, float]] = []
        for idx in range(101):
            entropy = max_entropy * idx / 100.0
            y_hat, y_low, y_high = logit_prediction(fit, {"gate_entropy": entropy, "has_barrier": barrier_value})
            px = sx + (entropy / max_entropy) * sw
            curve_points.append((px, sy + sh - y_hat * sh, sy + sh - y_low * sh, sy + sh - y_high * sh))
        band = (
            "M "
            + " L ".join(f"{x:.2f},{y_high:.2f}" for x, _, _, y_high in curve_points)
            + " L "
            + " L ".join(f"{x:.2f},{y_low:.2f}" for x, _, y_low, _ in reversed(curve_points))
            + " Z"
        )
        curve = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y, _, _ in curve_points)
        lines.append(path_element(band, fill=band_fill, opacity=0.72))
        lines.append(path_element(curve, stroke=color, stroke_width=4.0))
    for point in scatter:
        cx = sx + (point["gate_entropy"] / max_entropy) * sw
        cy = sy + sh - point["structural_rate"] * sh
        radius = 3.8 + min(float(point["gate_type_count"]), 8.0) * 0.42
        fill = GATE_LOW if point["gate_type_count"] <= 2 else GATE_MID if point["gate_type_count"] <= 4 else GATE_HIGH
        stroke = PLUM if point["has_barrier"] else "#ffffff"
        stroke_width = 1.45 if point["has_barrier"] else 0.8
        lines.append(circle(cx, cy, radius, fill=fill, stroke=stroke, stroke_width=stroke_width))
    lines.append(text(sx + sw / 2, sy + sh + 44, "Gate entropy", size=12, fill=MUTED, anchor="middle"))
    lines.append(text(sx - 46, sy + sh / 2, "P(structural match) (%)", size=12, fill=MUTED, anchor="middle", rotate=-90))
    lines.append(text(sx + sw - 2, sy + 18, f"OR/SD = {float(fit['odds_ratio_sd']):.2f}", size=12, fill=PLUM, anchor="end", weight=700))
    lines.append(r_squared_text(sx + sw - 2, sy + 40, "McFadden ", float(fit["pseudo_r2"]), size=10, fill=PLUM, anchor="end"))
    legend_y = sy + sh + 66
    legend_x = sx + 62
    lines.append(text(legend_x - 60, legend_y, "Gate types:", size=10, fill=MUTED, weight=700))
    for fill, label in [(GATE_LOW, "1-2"), (GATE_MID, "3-4"), (GATE_HIGH, "5+")]:
        lines.append(circle(legend_x + 6, legend_y - 4, 5, fill=fill, stroke="#ffffff", stroke_width=0.6))
        lines.append(text(legend_x + 17, legend_y, label, size=10, fill=MUTED))
        legend_x += 66
    line_y = legend_y + 20
    lines.append(line(sx + 2, line_y - 4, sx + 26, line_y - 4, stroke=TEAL, width=3.2))
    lines.append(text(sx + 32, line_y, "no barrier", size=10, fill=MUTED))
    lines.append(line(sx + 124, line_y - 4, sx + 148, line_y - 4, stroke=PLUM, width=3.2))
    lines.append(text(sx + 156, line_y, "barrier / staged", size=10, fill=MUTED))


def draw_coefficients_panel(lines: list[str], data: dict[str, Any], x0: float, y0: float) -> None:
    lines.extend(panel_label(x0, y0, "C", "Adjusted regression effects"))
    prompt_regression = data["prompt_level_regression"]
    row_regression = data["prompt_model_linear_probability_model"]
    prompt_terms = regression_terms(
        prompt_regression,
        [
            "z_gate_entropy",
            "has_barrier",
            "z_gate_type_count",
            "has_controlled_or_entangling",
            "z_num_clbits",
            "z_num_qubits",
            "z_gate_count",
            "has_rotation",
            "has_measure",
        ],
    )
    cx0, cy0 = x0 + 212, y0 + 52
    cscale = 790
    xmin, xmax = -0.35, 0.30
    zero_x = cx0 + scale_value(0.0, xmin, xmax, cscale)
    lines.append(line(zero_x, cy0 - 20, zero_x, cy0 + len(prompt_terms) * 34 + 2, stroke="#9aa8b6", width=1.35))
    for tick in [-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30]:
        tx = cx0 + scale_value(tick, xmin, xmax, cscale)
        lines.append(line(tx, cy0 - 10, tx, cy0 + len(prompt_terms) * 34 + 2, stroke=GRID))
        lines.append(text(tx, cy0 - 16, f"{int(tick * 100)}", size=10, fill=MUTED, anchor="middle"))
    for idx, term in enumerate(prompt_terms):
        coef = float(term["coefficient"])
        y = cy0 + idx * 34
        end_x = cx0 + scale_value(coef, xmin, xmax, cscale)
        color = RUST if coef < 0 else TEAL
        lines.append(text(x0, y + 5, str(term["label"]), size=12, weight=600))
        lines.append(line(zero_x, y, end_x, y, stroke=color, width=6.5))
        lines.append(circle(end_x, y, 4.6, fill=color))
        lines.append(text(end_x + (10 if coef >= 0 else -10), y + 4, pp(coef), size=11, fill=color, anchor="start" if coef >= 0 else "end"))
    note_x = x0 + 1060
    note_y = cy0 + 18
    lines.append(text(note_x + 16, note_y - 8, "Tier offsets", size=13, weight=800))
    lines.append(text(note_x + 16, note_y + 20, "frontier: ref.", size=11, fill=MUTED))
    row_terms = {str(term["name"]): term for term in row_regression["terms"]}
    strong_offset = float(row_terms["tier_strong_open_or_code"]["coefficient_pp"])
    low_offset = float(row_terms["tier_low_or_experimental"]["coefficient_pp"])
    lines.append(text(note_x + 16, note_y + 46, f"strong open/code: {strong_offset:+.2f} pp", size=11, fill=BLUE, weight=700))
    lines.append(text(note_x + 16, note_y + 72, f"low/experimental: {low_offset:+.2f} pp", size=11, fill=RUST, weight=700))
    lines.append(r_squared_text(note_x + 16, note_y + 100, "row ", float(row_regression["r_squared"]), size=11, fill=MUTED))
    lines.append(text(cx0 + cscale / 2, cy0 + len(prompt_terms) * 34 + 34, "Coefficient (percentage points)", size=12, fill=MUTED, anchor="middle"))
    lines.append(r_squared_text(x0, y0 + 396, f"Prompt-level model: n={int(data['prompt_count'])}, ", float(prompt_regression["r_squared"]), size=12, fill=MUTED))


def write_regression_panel(data: dict[str, Any], prompts: list[dict[str, Any]], matrix_rows: list[dict[str, str]]) -> None:
    width = 1400
    height = 920
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        tag("title", {"id": "title"}, "PQID-Bench PCA, binomial dose-response, and regression panel"),
        tag(
            "desc",
            {"id": "desc"},
            "Panel showing PCA of model success profiles, a binomial logistic dose-response for gate entropy, and adjusted regression effects.",
        ),
        rect(0, 0, width, height, fill=PANEL_BG),
    ]
    draw_pca_panel(lines, data, matrix_rows, 54, 70)
    draw_entropy_panel(lines, prompts, matrix_rows, int(data["model_count"]), 754, 70)
    draw_coefficients_panel(lines, data, 54, 520)
    lines.append("</svg>")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REGRESSION_SVG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_caption(data: dict[str, Any], matrix_rows: list[dict[str, str]], prompts: list[dict[str, Any]]) -> None:
    scores, pc1_share, pc2_share = pca_model_scores(data, matrix_rows)
    del scores
    prompt_r2 = data["prompt_level_regression"]["r_squared"]
    row_r2 = data["prompt_model_linear_probability_model"]["r_squared"]
    scatter = prompt_scatter_points(prompts, matrix_rows, int(data["model_count"]))
    entropy_fit = binomial_logit_fit(scatter, int(data["model_count"]), ["gate_entropy", "has_barrier"])
    REGRESSION_CAPTION.write_text(
        "\n".join(
            [
                "# PCA, Binomial Dose-Response, And Regression Panel Caption",
                "",
                f"**Figure 5. PCA, binomial dose-response, and regression diagnostics.** The panel summarizes the `{data['model_count']}`-row external-model matrix without duplicating the heatmap. Panel A projects each model's `{data['prompt_count']}`-prompt reference-signature vector into the first two principal components (PC1={pct(pc1_share)} variance; PC2={pct(pc2_share)}). Panel B shows a binomial logistic dose-response fitted to prompt-level signature-match counts with gate entropy and barrier/staged-structure status as predictors; the fitted gate-entropy effect is OR/SD={float(entropy_fit['odds_ratio_sd']):.2f} with McFadden $R^2={float(entropy_fit['pseudo_r2']):.3f}$. Panel C reports adjusted prompt-level regression effects; tier offsets are shown as a compact textual callout. The prompt-level model has $R^2={prompt_r2:.3f}$ and the prompt-model linear-probability model has $R^2={row_r2:.3f}$; all summaries are descriptive rather than causal estimates.",
                "",
                "Source artifacts:",
                "",
                "- `artifacts/analysis_154/pqid_bench_model_regression_analysis.json`",
                "- `artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv`",
                "- `artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    # The main-text regression panel is now driven by the frozen cluster-aware
    # inferential artifacts. Retain this entry point for reproducibility while
    # delegating rendering to the joint Figure 4/5 builder.
    from build_pqid_bench_inferential_figures import build_figure4

    build_figure4()
    print(f"Wrote {REGRESSION_SVG}")
    print(f"Wrote {REGRESSION_CAPTION}")


if __name__ == "__main__":
    main()
