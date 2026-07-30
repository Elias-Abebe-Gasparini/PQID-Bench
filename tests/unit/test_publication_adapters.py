from __future__ import annotations

import csv
import importlib.util
import json
import unittest
from pathlib import Path, PurePosixPath

from pqid_bench.version import PACKAGE_VERSION

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
    def test_github_package_contract_is_explicit(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "publish-ghcr.yml"
        ).read_text(encoding="utf-8")
        dockerfile = (ROOT / "docker" / "evaluator" / "Dockerfile").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        image = "ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator"
        self.assertIn("packages: write", workflow)
        self.assertIn(image, workflow)
        self.assertIn(
            "org.opencontainers.image.source="
            '"https://github.com/Elias-Abebe-Gasparini/PQID-Bench"',
            dockerfile,
        )
        self.assertIn(f"docker pull {image}:1.0.0", readme)

    def test_python_sbom_tracks_the_package_release(self) -> None:
        sbom_path = (
            ROOT / "sbom" / f"pqid-bench-python-{PACKAGE_VERSION}.cdx.json"
        )
        payload = json.loads(sbom_path.read_text(encoding="utf-8"))
        component = payload["metadata"]["component"]
        self.assertEqual(PACKAGE_VERSION, component["version"])
        references = {
            item["url"] for item in component.get("externalReferences", [])
        }
        self.assertIn(
            "https://elias-abebe-gasparini.github.io/PQID-Bench/"
            "interactive/overview.html",
            references,
        )
        self.assertFalse(
            any("PQID-Bench-Gateway" in url for url in references)
        )

    def test_pages_build_products_are_not_dataset_artifacts(self) -> None:
        uploader = load_uploader()
        self.assertTrue(
            uploader.is_ignored_path(
                PurePosixPath("docs/interactive/overview.html")
            )
        )
        self.assertTrue(
            uploader.is_ignored_path(
                PurePosixPath("docs/interactive/assets/measurement-ladder.svg")
            )
        )

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
