from __future__ import annotations

import csv
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UPLOADER = ROOT / "platforms" / "huggingface_dataset" / "upload_dataset.py"


def load_uploader():
    spec = importlib.util.spec_from_file_location("pqid_bench_hf_uploader", UPLOADER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import publication adapter: {UPLOADER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicationAdapterTests(unittest.TestCase):
    def test_hugging_face_upload_set_matches_manifest(self) -> None:
        uploader = load_uploader()
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in uploader.package_files()
        }

        manifest = ROOT / "ARTIFACT_MANIFEST.tsv"
        with manifest.open(encoding="utf-8", newline="") as handle:
            expected = {
                row["path"]
                for row in csv.DictReader(handle, delimiter="\t")
            }
        expected.add("ARTIFACT_MANIFEST.tsv")

        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
