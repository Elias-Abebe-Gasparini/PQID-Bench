from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from pqid_bench.download import download_core_release

ROOT_NAME = "PQID-Bench-v1.0.0-core"
TEST_URL = "https://example.test/PQID-Bench-v1.0.0-core.zip"


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes, url: str = TEST_URL) -> None:
        super().__init__(payload)
        self._url = url
        self.headers = {"Content-Length": str(len(payload))}

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def core_archive(*, unsafe_member: str | None = None) -> bytes:
    benchmark = (
        json.dumps(
            {
                "name": "PQID-Bench",
                "benchmark_release": "1.0.0",
                "distribution_profile": "core",
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()
    payload = b'{"row_id":"row-1"}\n'
    entries = {
        "benchmark.json": benchmark,
        "data/splits/test.jsonl": payload,
    }
    manifest_rows = ["path\tbytes\tsha256"]
    for name, content in entries.items():
        manifest_rows.append(
            f"{name}\t{len(content)}\t{hashlib.sha256(content).hexdigest()}"
        )
    manifest = ("\n".join(manifest_rows) + "\n").encode()

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, content in entries.items():
            bundle.writestr(f"{ROOT_NAME}/{name}", content)
        bundle.writestr(f"{ROOT_NAME}/ARTIFACT_MANIFEST.tsv", manifest)
        if unsafe_member is not None:
            bundle.writestr(unsafe_member, b"unsafe")
    return output.getvalue()


class DownloadTests(unittest.TestCase):
    def test_download_verifies_extracts_and_reuses_release(self) -> None:
        payload = core_archive()
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch(
                "pqid_bench.download.urllib.request.urlopen",
                return_value=FakeResponse(payload),
            ) as request:
                first = download_core_release(
                    output_dir=output,
                    url=TEST_URL,
                    sha256=digest,
                )
            self.assertTrue(first.downloaded)
            self.assertEqual(first.manifest_entries, 2)
            self.assertTrue(Path(first.release_dir, "benchmark.json").is_file())
            self.assertTrue(Path(first.archive_path).is_file())
            request.assert_called_once()

            with patch(
                "pqid_bench.download.urllib.request.urlopen"
            ) as second_request:
                second = download_core_release(
                    output_dir=output,
                    url=TEST_URL,
                    sha256=digest,
                )
            self.assertFalse(second.downloaded)
            second_request.assert_not_called()

    def test_download_rejects_checksum_mismatch_without_installing(self) -> None:
        payload = core_archive()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch(
                "pqid_bench.download.urllib.request.urlopen",
                return_value=FakeResponse(payload),
            ):
                with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                    download_core_release(
                        output_dir=output,
                        url=TEST_URL,
                        sha256="0" * 64,
                    )
            self.assertFalse((output / ROOT_NAME).exists())

    def test_download_rejects_zip_path_traversal(self) -> None:
        payload = core_archive(unsafe_member="../outside.txt")
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch(
                "pqid_bench.download.urllib.request.urlopen",
                return_value=FakeResponse(payload),
            ):
                with self.assertRaisesRegex(ValueError, "Unsafe ZIP member path"):
                    download_core_release(
                        output_dir=output,
                        url=TEST_URL,
                        sha256=digest,
                    )
            self.assertFalse((output.parent / "outside.txt").exists())

    def test_custom_url_requires_custom_hash(self) -> None:
        with self.assertRaisesRegex(ValueError, "both --url and --sha256"):
            download_core_release(url=TEST_URL)

    def test_download_requires_https(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            download_core_release(
                url="http://example.test/core.zip",
                sha256="0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
