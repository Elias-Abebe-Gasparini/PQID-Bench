from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

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

    def test_hugging_face_staging_is_explicit_and_dataset_only(self) -> None:
        uploader = load_uploader()
        archive_bytes = io.BytesIO()
        with zipfile.ZipFile(archive_bytes, "w") as bundle:
            bundle.writestr(
                f"{uploader.CORE_ROOT}/benchmark.json",
                json.dumps(
                    {
                        "benchmark_release": "1.0.0",
                        "distribution_profile": "core",
                    }
                ),
            )
        archive_payload = archive_bytes.getvalue()
        digest = hashlib.sha256(archive_payload).hexdigest()

        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            archive = temporary / uploader.CORE_ARCHIVE_NAME
            sidecar = temporary / f"{uploader.CORE_ARCHIVE_NAME}.sha256"
            archive.write_bytes(archive_payload)
            sidecar.write_text(
                f"{digest}  {uploader.CORE_ARCHIVE_NAME}\n",
                encoding="utf-8",
            )
            stage = temporary / "stage"
            with patch.object(uploader, "CORE_SHA256", digest):
                files = uploader.stage_dataset(
                    stage,
                    core_archive=archive,
                    core_sidecar=sidecar,
                )

            actual = {
                path.relative_to(stage).as_posix()
                for path in files
            }
            expected = {
                destination for _, destination in uploader.SOURCE_FILES
            }
            expected.update(
                {
                    "benchmark.json",
                    "DATASET_FILES.tsv",
                    f"downloads/{uploader.CORE_ARCHIVE_NAME}",
                    f"downloads/{uploader.CORE_ARCHIVE_NAME}.sha256",
                }
            )
            self.assertEqual(expected, actual)
            self.assertFalse(
                any(
                    path.startswith(
                        (
                            ".github/",
                            "artifacts/analysis_154/",
                            "docs/",
                            "scripts/",
                            "src/",
                        )
                    )
                    for path in actual
                )
            )


if __name__ == "__main__":
    unittest.main()
