from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from pqid_bench.download import OFFICIAL_CORE_RELEASES
from pqid_bench.manifest import sha256_file

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts" / "build_pqid_bench_core_bundle.py"


def load_builder():
    name = "pqid_bench_core_builder"
    spec = importlib.util.spec_from_file_location(name, BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import core builder: {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CoreBundleTests(unittest.TestCase):
    def test_core_bundle_matches_package_pin_and_scope(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            archive, sidecar = builder.build(Path(directory))
            expected = OFFICIAL_CORE_RELEASES["1.0.0"]
            self.assertEqual(sha256_file(archive), expected.sha256)
            self.assertIn(expected.sha256, sidecar.read_text(encoding="utf-8"))

            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
                self.assertEqual(len(names), 32)
                self.assertIn(
                    f"{expected.root_name}/data/splits/test.jsonl",
                    names,
                )
                self.assertIn(
                    f"{expected.root_name}/"
                    "artifacts/test_split_154/"
                    "pqid_bench_external_generation_prompts_154.jsonl",
                    names,
                )
                forbidden = (
                    ".github/",
                    "artifacts/analysis_154/",
                    "artifacts/external_model_batches_154/",
                    "docs/",
                    "manuscript",
                )
                self.assertFalse(
                    any(
                        marker in name.casefold()
                        for name in names
                        for marker in forbidden
                    )
                )


if __name__ == "__main__":
    unittest.main()
