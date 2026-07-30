from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RepositoryContractTests(unittest.TestCase):
    def test_community_health_files_exist(self) -> None:
        required = (
            "CHANGELOG.md",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "SUPPORT.md",
            ".github/dependabot.yml",
            ".github/pull_request_template.md",
            ".github/workflows/release-metadata.yml",
        )
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_examples_are_importable_and_offline_examples_run(self) -> None:
        environment = {
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
        }
        for name in ("reproduce_frozen.py", "build_dashboard.py", "plan_live_run.py"):
            with self.subTest(example=name):
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(ROOT / "examples" / name)],
                    check=False,
                    capture_output=True,
                    text=True,
                    env=environment,
                )
                self.assertEqual(0, result.returncode, result.stderr)

        reproduce = subprocess.run(
            [sys.executable, str(ROOT / "examples" / "reproduce_frozen.py")],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=environment,
        )
        self.assertEqual(0, reproduce.returncode, reproduce.stderr)
        self.assertIn("PQID-Bench Evaluation Summary", reproduce.stdout)
        self.assertIn("3,234", reproduce.stdout)

        plan = subprocess.run(
            [
                sys.executable,
                str(ROOT / "examples" / "plan_live_run.py"),
                "--provider",
                "groq",
                "--model",
                "example/model",
                "--limit",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=environment,
        )
        self.assertEqual(0, plan.returncode, plan.stderr)
        self.assertIn('"contacts_provider": false', plan.stdout)


if __name__ == "__main__":
    unittest.main()
