from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pqid_bench.replay import (
    CANONICAL_EVALUATIONS,
    EVALUATOR_OUTPUTS,
    SUMMARY_OUTPUTS,
    canonicalize_harness_report,
    replay_plan,
    write_replay_derivatives,
)


class ReplayPlanTests(unittest.TestCase):
    def test_plan_enforces_isolation_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docker" / "evaluator").mkdir(parents=True)
            (root / "docker" / "evaluator" / "Dockerfile").write_text(
                "FROM scratch\n", encoding="utf-8"
            )
            response = root / "responses.jsonl"
            response.write_text("{}\n", encoding="utf-8")
            plan = replay_plan(
                release_dir=root,
                response_file=response,
                output_dir=root / "output",
                build_image=True,
            )
            command = plan.run_command
            self.assertIn("none", command)
            self.assertIn("ALL", command)
            self.assertIn("no-new-privileges", command)
            self.assertIn("--read-only", command)
            self.assertIn(
                "/release/data/pqid_bench_evaluator_source_734.jsonl",
                command,
            )
            self.assertIn("/release/responses.jsonl", command)
            self.assertNotIn("/responses/responses.jsonl", command)
            self.assertEqual(command[0:2], ("docker", "run"))
            self.assertEqual(plan.release_dir, root.resolve())
            self.assertEqual(plan.response_file, response.resolve())
            self.assertEqual(plan.output_dir, (root / "output").resolve())

    def test_harness_report_becomes_canonical_cells_and_r_style_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / EVALUATOR_OUTPUTS[0]
            report.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "model": "model-a",
                                "provider": "provider-a",
                                "prompt_id": "prompt-1",
                                "row_id": "row-1",
                                "execution": {
                                    "execution_success": True,
                                    "circuit_found": True,
                                    "selected_circuit_name": "qc",
                                    "qasm3_export": {"success": True},
                                },
                                "structural_checks": {
                                    "all_match": True,
                                    "gate_types_match": True,
                                    "gate_count_match": True,
                                    "num_qubits_match": True,
                                    "num_clbits_match": True,
                                },
                            },
                            {
                                "model": "model-a",
                                "provider": "provider-a",
                                "prompt_id": "prompt-2",
                                "row_id": "row-2",
                                "execution": {
                                    "execution_success": True,
                                    "circuit_found": True,
                                    "selected_circuit_name": "qc",
                                    "qasm3_export": {"success": False},
                                },
                                "structural_checks": {
                                    "all_match": False,
                                    "gate_types_match": False,
                                    "gate_count_match": False,
                                    "num_qubits_match": True,
                                    "num_clbits_match": True,
                                },
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            rows = canonicalize_harness_report(report)
            self.assertEqual(len(rows), 2)
            self.assertTrue(rows[0]["report_signature_match"])
            self.assertFalse(rows[1]["report_assembly_admissible"])

            write_replay_derivatives(root)
            evaluations = root / CANONICAL_EVALUATIONS
            self.assertTrue(evaluations.is_file())
            for filename in SUMMARY_OUTPUTS.values():
                self.assertTrue((root / filename).is_file())
            summary = json.loads(
                (root / SUMMARY_OUTPUTS["json"]).read_text(encoding="utf-8")
            )
            self.assertEqual(summary["cells"], 2)
            self.assertEqual(summary["execution_count"], 2)
            self.assertEqual(summary["assembly_count"], 1)
            self.assertEqual(summary["signature_count"], 1)
            self.assertEqual(summary["es_gap_count"], 1)


if __name__ == "__main__":
    unittest.main()
