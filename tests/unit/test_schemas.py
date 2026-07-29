from __future__ import annotations

import unittest

from pqid_bench.schemas import SCHEMA_NAMES, load_schema


class SchemaTests(unittest.TestCase):
    def test_all_packaged_schemas_load(self) -> None:
        for name in SCHEMA_NAMES:
            with self.subTest(name=name):
                schema = load_schema(name)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["type"], "object")

    def test_evaluation_schema_exposes_optional_assembly_endpoint(self) -> None:
        schema = load_schema("evaluation")
        self.assertIn("report_assembly_admissible", schema["properties"])
        self.assertNotIn("report_assembly_admissible", schema["required"])


if __name__ == "__main__":
    unittest.main()
