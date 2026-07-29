from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from pqid_bench.manifest import verify_manifest


class ManifestTests(unittest.TestCase):
    def test_valid_and_modified_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "example.txt"
            payload.write_text("frozen\n", encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            (root / "ARTIFACT_MANIFEST.tsv").write_text(
                f"path\tbytes\tsha256\nexample.txt\t{payload.stat().st_size}\t{digest}\n",
                encoding="utf-8",
            )
            self.assertTrue(verify_manifest(root).valid)
            payload.write_text("changed\n", encoding="utf-8")
            result = verify_manifest(root)
            self.assertFalse(result.valid)
            self.assertEqual(result.size_mismatches, ("example.txt",))

    def test_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ARTIFACT_MANIFEST.tsv").write_text(
                "path\tbytes\tsha256\n../outside\t0\t" + "0" * 64 + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Unsafe manifest path"):
                verify_manifest(root)


if __name__ == "__main__":
    unittest.main()
