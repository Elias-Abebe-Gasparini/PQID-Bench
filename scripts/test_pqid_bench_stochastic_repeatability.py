"""Focused invariance tests for the stochastic-repeatability analyzer."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analyze_pqid_bench_stochastic_repeatability as audit
import build_pqid_bench_stochastic_repeatability_extension as extension


class RepeatabilityAnalyzerTests(unittest.TestCase):
    def test_augmentation_allocation_preserves_frozen_margins(self) -> None:
        capacities = {
            ("1-2", "pilot"): [None] * 11,
            ("1-2", "extension"): [None] * 17,
            ("3-4", "pilot"): [None] * 25,
            ("3-4", "extension"): [None] * 37,
            ("5+", "pilot"): [None] * 5,
            ("5+", "extension"): [None] * 9,
        }
        quotas = extension.choose_cross_stratum_quotas(capacities)
        self.assertEqual(sum(quotas.values()), 36)
        self.assertEqual(
            sum(value for (gate_bin, _), value in quotas.items() if gate_bin == "1-2"),
            12,
        )
        self.assertEqual(
            sum(value for (gate_bin, _), value in quotas.items() if gate_bin == "3-4"),
            12,
        )
        self.assertEqual(
            sum(value for (gate_bin, _), value in quotas.items() if gate_bin == "5+"),
            12,
        )
        self.assertEqual(
            sum(value for (_, cohort), value in quotas.items() if cohort == "pilot"),
            18,
        )
        self.assertEqual(
            sum(value for (_, cohort), value in quotas.items() if cohort == "extension"),
            18,
        )
        self.assertEqual(quotas[("5+", "pilot")], 5)

    def test_augmentation_seed_is_bound_to_original_panel(self) -> None:
        expected = hashlib.sha256(
            (
                "pqid-bench-stochastic-repeatability-augmentation-v1"
                + "\x00"
                + extension.EXPECTED_BASE_PANEL_SHA256
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(extension.SELECTION_SEED, expected)

    def test_text_and_ast_contracts_are_distinct(self) -> None:
        first = "```python\r\nx = 1  \r\n\r\n\r\nprint(x)\r\n```"
        second = "x=1\nprint(x)  # comment"
        normalized_first = audit.normalize_code_text(first)
        normalized_second = audit.normalize_code_text(second)
        self.assertEqual(normalized_first, "x = 1\n\nprint(x)")
        self.assertNotEqual(normalized_first, normalized_second)
        self.assertEqual(
            audit.ast_canonical_form(normalized_first),
            audit.ast_canonical_form(normalized_second),
        )

    def test_duplicate_response_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responses.jsonl"
            rows = [{"prompt_id": "p1"}, {"prompt_id": "p1"}]
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate response"):
                audit.canonical_responses(path)

    def test_joint_bootstrap_detects_perfect_shift_with_singular_covariance(self) -> None:
        rows = []
        for run in (1, 2, 3):
            for model in audit.PRIMARY_MODEL_ORDER:
                for prompt_id in ("p1", "p2"):
                    rows.append(
                        {
                            "run": run,
                            "model": model,
                            "prompt_id": prompt_id,
                            "execution": int(run > 1),
                        }
                    )
        replicates = 99
        crossed = {
            "pair_1_2_delta": [1.0] * replicates,
            "pair_1_3_delta": [1.0] * replicates,
            "pair_2_3_delta": [0.0] * replicates,
        }
        result = audit.two_way_fixed_effect_run_model(rows, "execution", crossed)
        self.assertAlmostEqual(result["contrasts"][0]["rate_delta_pp"], 100.0)
        self.assertAlmostEqual(result["contrasts"][1]["rate_delta_pp"], 100.0)
        self.assertEqual(result["joint_run_effect_p_value"], 0.01)

    def test_joint_bootstrap_returns_null_for_identical_runs(self) -> None:
        rows = []
        for run in (1, 2, 3):
            for model_index, model in enumerate(audit.PRIMARY_MODEL_ORDER):
                for prompt_id in ("p1", "p2"):
                    rows.append(
                        {
                            "run": run,
                            "model": model,
                            "prompt_id": prompt_id,
                            "execution": int(model_index % 2 == 0),
                        }
                    )
        crossed = {
            "pair_1_2_delta": [0.0] * 99,
            "pair_1_3_delta": [0.0] * 99,
            "pair_2_3_delta": [0.0] * 99,
        }
        result = audit.two_way_fixed_effect_run_model(rows, "execution", crossed)
        self.assertEqual(result["joint_run_effect_statistic"], 0.0)
        self.assertEqual(result["joint_run_effect_p_value"], 1.0)


if __name__ == "__main__":
    unittest.main()
