"""Build manuscript result-panel figures for PQID-Bench."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from publication_figure_style import PUBLICATION_SERIF_FONT_STACK
from pqid_bench_model_registry import (
    EXPANDED_MODEL_ORDER,
    FRONTIER_MODELS,
    LOW_EXPERIMENTAL_MODELS,
    STRONG_OPEN_CODE_MODELS,
)
import run_pqid_bench_generation_copy_baseline as copy_baseline


ROOT = Path(__file__).resolve().parents[1]
MATRIX_CSV = ROOT / "artifacts/analysis_154/pqid_bench_model_by_prompt_structural_matrix.csv"
PROMPT_JSONL = ROOT / "artifacts/test_split_154/pqid_bench_external_generation_prompts_154.jsonl"
SPLIT_MANIFEST = ROOT / "artifacts/test_split_154/pqid_bench_split_154_manifest.json"
FIGURE_PATH = ROOT / "figures/model_by_prompt_structural_heatmap.svg"
CAPTION_PATH = ROOT / "figures/model_by_prompt_structural_heatmap_caption.md"

EXTERNAL_MODEL_ORDER = list(EXPANDED_MODEL_ORDER)

BASELINE_ORDER = [
    "bm25_code_metadata_copy",
    "word_tfidf_code_metadata_copy",
    "word_tfidf_train_instruction_copy",
]

MODEL_ORDER = EXTERNAL_MODEL_ORDER + BASELINE_ORDER

MODEL_LABELS = {
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "gpt-5.5": "GPT-5.5",
    "gpt-5.4-mini": "GPT-5.4 mini",
    "claude-fable-5": "Claude Fable 5",
    "claude-sonnet-4-6": "Sonnet 4.6",
    "claude-opus-4-8": "Opus 4.8",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "deepseek-v4-pro": "DeepSeek V4 Pro",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "mistral-ai/codestral-2501": "Codestral",
    "qwen/qwen3-coder-next": "Qwen3-Coder-Next",
    "meta/llama-4-maverick-17b-128e-instruct-fp8": "Llama 4 Maverick",
    "llama-3.3-70b-versatile": "Llama 70B",
    "openai/gpt-oss-120b": "GPT-OSS 120B",
    "openai/gpt-oss-20b": "GPT-OSS 20B",
    "mistralai/mistral-small-3.2-24b-instruct": "Mistral Small 3.2",
    "qiskit/mistral-small-3.2-24b-qiskit": "Qiskit Mistral 3.2",
    "qwen/qwen3-32b": "Qwen3 32B",
    "meta-llama/llama-4-scout-17b-16e-instruct": "Llama 4 Scout",
    "llama-3.1-8b-instant": "Llama 8B",
    "bm25_code_metadata_copy": "BM25 Copy",
    "word_tfidf_code_metadata_copy": "TF-IDF Code Copy",
    "word_tfidf_train_instruction_copy": "TF-IDF Instr. Copy",
}

TIER_RULES = {
    "frontier": set(FRONTIER_MODELS),
    "strong hosted open/code": set(STRONG_OPEN_CODE_MODELS),
    "low / experimental": set(LOW_EXPERIMENTAL_MODELS),
    "retrieval-copy baselines": set(BASELINE_ORDER),
}


def read_matrix(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_prompt_row_ids(path: Path) -> dict[str, str]:
    prompt_by_row_id: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        prompt_by_row_id[str(record["row_id"])] = str(record["prompt_id"])
    return prompt_by_row_id


def add_retrieval_copy_baselines(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    prompt_by_row_id = read_prompt_row_ids(PROMPT_JSONL)
    source_rows = copy_baseline.clean_rows(copy_baseline.DEFAULT_INPUT)
    splits = copy_baseline.split_rows(source_rows, split_manifest_path=SPLIT_MANIFEST)
    qiskit_env = copy_baseline.import_qiskit()
    if not qiskit_env.get("available"):
        raise RuntimeError(f"Qiskit is unavailable: {qiskit_env.get('error')}")

    _, records_by_name = copy_baseline.run_generators(
        train_rows=splits["train"],
        test_rows=splits["test"],
        qiskit_env=qiskit_env,
    )

    baseline_values: dict[str, dict[str, str]] = {}
    for baseline in BASELINE_ORDER:
        prompt_values: dict[str, str] = {}
        for record in records_by_name[baseline]:
            prompt_id = prompt_by_row_id.get(str(record["row_id"]))
            if prompt_id is None:
                continue
            match = bool(record.get("structural_checks", {}).get("all_match"))
            prompt_values[prompt_id] = "1" if match else "0"
        baseline_values[baseline] = prompt_values

    for row in rows:
        prompt_id = row["prompt_id"]
        for baseline in BASELINE_ORDER:
            row[baseline] = baseline_values[baseline].get(prompt_id, "")
    return rows


def model_tier(model: str) -> str:
    for tier, models in TIER_RULES.items():
        if model in models:
            return tier
    return "other"


def write_heatmap(rows: list[dict[str, str]], path: Path) -> None:
    cell_w = 7
    cell_h = 24
    group_gap = 10
    left = 176
    top = 102
    right = 62
    bottom = 88
    tier_sequence = [model_tier(model) for model in MODEL_ORDER]
    group_boundaries = sum(
        tier_sequence[i] != tier_sequence[i - 1] for i in range(1, len(tier_sequence))
    )
    matrix_h = cell_h * len(MODEL_ORDER) + group_gap * group_boundaries
    width = left + cell_w * len(rows) + right
    height = top + matrix_h + bottom
    success = "#1f766d"
    fail = "#f1eee8"
    missing = "#cfcfcf"
    grid = "#ffffff"
    text = "#1f2933"
    muted = "#1f2933"
    axis = "#1f2933"
    divider = "#c43c35"

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">PQID-Bench model-by-prompt reference-signature match heatmap</title>",
        "<desc id=\"desc\">Rows are models and retrieval-copy baselines; columns are 154 held-out prompts sorted from hardest to easiest. Dark cells indicate reference-signature match.</desc>",
        "<style>",
        f'text {{ font-family: "{PUBLICATION_SERIF_FONT_STACK}", Times, serif; fill: #1f2933; }}',
        ".small { font-size: 12px; }",
        ".tier { font-size: 15px; fill: #1f2933; font-weight: 700; }",
        ".label { font-size: 14px; font-weight: 600; }",
        ".axis { font-size: 16px; fill: #1f2933; font-weight: 600; }",
        ".legend { font-size: 13.5px; fill: #1f2933; }",
        ".note { font-size: 12.5px; fill: #1f2933; font-style: italic; }",
        "</style>",
        "<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\"/>",
    ]

    # Prompt difficulty guide.
    matrix_w = cell_w * len(rows)
    model_label_x = left - 10
    tier_label_x = 27
    divider_x1 = 8
    guide_y = top - 42
    guide_center = left + matrix_w / 2
    lines.append(f'<text class="axis" x="{left}" y="{guide_y - 11}" fill="{muted}">Harder Prompts</text>')
    lines.append(f'<text class="axis" x="{left + matrix_w}" y="{guide_y - 11}" text-anchor="end" fill="{muted}">Easier Prompts</text>')
    lines.append(f'<text class="axis" x="{guide_center:.1f}" y="{guide_y - 11}" text-anchor="middle" fill="{muted}">Columns Sorted Hardest To Easiest</text>')
    lines.append(
        f'<line x1="{left}" y1="{guide_y}" x2="{left + matrix_w}" y2="{guide_y}" stroke="{axis}" stroke-width="1"/>'
    )
    lines.append(f'<polygon points="{left},{guide_y} {left+7},{guide_y-4} {left+7},{guide_y+4}" fill="{axis}"/>')
    lines.append(
        f'<polygon points="{left + matrix_w},{guide_y} {left + matrix_w-7},{guide_y-4} {left + matrix_w-7},{guide_y+4}" fill="{axis}"/>'
    )

    # X-axis tick labels every twenty prompts, plus the final prompt.
    tick_step = 20
    for idx in range(0, len(rows), tick_step):
        x = left + idx * cell_w + cell_w / 2
        label = idx + 1
        lines.append(f'<line x1="{x:.1f}" y1="{top-5}" x2="{x:.1f}" y2="{top-1}" stroke="{axis}"/>')
        lines.append(f'<text class="small" x="{x:.1f}" y="{top-10}" text-anchor="middle">{label}</text>')
    x = left + (len(rows) - 1) * cell_w + cell_w / 2
    lines.append(f'<text class="small" x="{x:.1f}" y="{top-10}" text-anchor="middle">{len(rows)}</text>')

    tier_starts: dict[str, float] = {}
    tier_ends: dict[str, float] = {}
    current_tier = None
    y_cursor = top
    for r, model in enumerate(MODEL_ORDER):
        tier = model_tier(model)
        if tier != current_tier:
            if current_tier is not None:
                previous_cell_bottom = y_cursor - 2
                y_cursor += group_gap
                divider_y = (previous_cell_bottom + y_cursor) / 2
                lines.append(
                    f'<line x1="{divider_x1}" y1="{divider_y:.1f}" x2="{left + matrix_w}" y2="{divider_y:.1f}" stroke="{divider}" stroke-width="1.7" opacity="0.9"/>'
                )
            tier_starts[tier] = y_cursor
            current_tier = tier
        y = y_cursor
        label = MODEL_LABELS.get(model, model)
        lines.append(f'<text class="label" x="{model_label_x}" y="{y + 15}" text-anchor="end">{escape(label)}</text>')
        solved = 0
        for c, row in enumerate(rows):
            value = row.get(model, "")
            if value == "1":
                color = success
                solved += 1
            elif value == "0":
                color = fail
            else:
                color = missing
            x = left + c * cell_w
            lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 1}" height="{cell_h - 2}" fill="{color}" stroke="{grid}" stroke-width="0.4"/>'
            )
        lines.append(f'<text class="small" x="{left + matrix_w + 8}" y="{y + 16}" fill="{muted}">{solved}/{len(rows)}</text>')
        tier_ends[tier] = y + cell_h - 2
        y_cursor += cell_h

    tier_display = {
        "frontier": ["Frontier"],
        "strong hosted open/code": ["Hosted", "Open/Code"],
        "low / experimental": ["Low / Exp."],
        "retrieval-copy baselines": ["Retrieval", "Baselines"],
    }
    for tier, y in tier_starts.items():
        label_y = (y + tier_ends[tier]) / 2
        label_lines = tier_display.get(tier, [tier])
        line_gap = 13
        first_line_y = label_y - (len(label_lines) - 1) * line_gap / 2
        tspans = "".join(
            f'<tspan x="{tier_label_x}" y="{first_line_y + i * line_gap:.1f}">{escape(part)}</tspan>'
            for i, part in enumerate(label_lines)
        )
        lines.append(
            f'<text class="tier" text-anchor="middle" transform="rotate(-90 {tier_label_x} {label_y:.1f})">{tspans}</text>'
        )

    # Bottom difficulty markers.
    for idx, row in enumerate(rows):
        if idx % tick_step == 0 or idx == len(rows) - 1:
            x = left + idx * cell_w + cell_w / 2
            y = top + matrix_h + 21
            difficulty = float(row["difficulty"])
            lines.append(f'<text class="small" x="{x:.1f}" y="{y}" text-anchor="middle">{difficulty:.2f}</text>')
    axis_label_y = top + matrix_h + 53
    lines.append(
        f'<text class="note" x="10" y="{axis_label_y}">Exp. = Experimental</text>'
    )
    lines.append(
        f'<text class="axis" x="{left + cell_w * len(rows) / 2 - 215}" y="{axis_label_y}" text-anchor="middle" fill="{muted}">Item Difficulty (1 - Share Of Models With Signature Match)</text>'
    )

    legend_y = axis_label_y
    legend_x = left + matrix_w / 2 + 102
    lines.extend(
        [
            f'<rect x="{legend_x}" y="{legend_y-11}" width="12" height="12" fill="{success}"/>',
            f'<text class="legend" x="{legend_x+18}" y="{legend_y-1}">Signature Match</text>',
            f'<rect x="{legend_x+126}" y="{legend_y-11}" width="12" height="12" fill="{fail}" stroke="#d0d5dd"/>',
            f'<text class="legend" x="{legend_x+144}" y="{legend_y-1}">No Signature Match</text>',
        ]
    )

    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_caption(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                f"**Figure 2. Model-by-prompt reference-signature match matrix.** Rows are the {len(EXTERNAL_MODEL_ORDER)} completed model evaluations plus {len(BASELINE_ORDER)} retrieval-copy baselines; columns are the {154} held-out prompts sorted by item difficulty under the final model matrix. A dark cell indicates that the generated or copied program executed as a circuit matching the target qubit count, classical-bit count, gate count, and gate-type multiset. The Mistral parent and Qiskit-specialized derivative appear as ordinary roster members within the hosted open/code block, enabling a matched specialization comparison without changing the denominator. The bottom baseline block shows how sparse retrieval-copy methods compare with the model rows without treating retrieval as a language model. The mixed middle region demonstrates that PQID-Bench distinguishes model behavior beyond a single aggregate score.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = read_matrix(MATRIX_CSV)
    rows = add_retrieval_copy_baselines(rows)
    write_heatmap(rows, FIGURE_PATH)
    write_caption(CAPTION_PATH)
    print(f"Wrote {FIGURE_PATH}")
    print(f"Wrote {CAPTION_PATH}")


if __name__ == "__main__":
    main()
