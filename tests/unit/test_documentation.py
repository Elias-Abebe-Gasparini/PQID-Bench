from __future__ import annotations

import argparse
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote

from pqid_bench.cli import parser

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
MANUAL = DOCS / "user-manual"

MANUAL_CHAPTERS = {
    "index.md",
    "installation.md",
    "core-concepts.md",
    "capabilities.md",
    "live-model-testing.md",
    "cli-reference.md",
    "reporting-and-exports.md",
    "python-api.md",
    "data-dictionary.md",
    "metrics-and-invariants.md",
    "workflows.md",
    "reproducibility-contract.md",
    "security-governance.md",
    "troubleshooting.md",
    "glossary.md",
}


class DocumentationContractTests(unittest.TestCase):
    def test_manual_chapters_and_mkdocs_navigation_exist(self) -> None:
        observed = {path.name for path in MANUAL.glob("*.md")}
        self.assertTrue(
            MANUAL_CHAPTERS.issubset(observed),
            f"missing manual chapters: {sorted(MANUAL_CHAPTERS - observed)}",
        )

        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        nav_paths = {
            match.group(1)
            for match in re.finditer(
                r"^\s*-\s+[^:]+:\s+([^\s]+\.md)\s*$",
                config,
                flags=re.MULTILINE,
            )
        }
        expected_nav = {f"user-manual/{name}" for name in MANUAL_CHAPTERS}
        self.assertTrue(
            expected_nav.issubset(nav_paths),
            f"manual pages absent from navigation: "
            f"{sorted(expected_nav - nav_paths)}",
        )
        for relative in nav_paths:
            with self.subTest(nav_path=relative):
                self.assertTrue((DOCS / relative).is_file())

    def test_local_markdown_links_resolve(self) -> None:
        sources = [
            ROOT / "README.md",
            ROOT / "REPRODUCIBILITY_ARTIFACTS.md",
            *sorted(DOCS.rglob("*.md")),
        ]
        link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        failures: list[str] = []

        for source in sources:
            text = source.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(text):
                target = raw_target.strip().strip("<>")
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = unquote(target.split(maxsplit=1)[0])
                target = target.split("#", 1)[0].split("?", 1)[0]
                resolved = (source.parent / target).resolve()
                if not resolved.exists():
                    failures.append(
                        f"{source.relative_to(ROOT)} -> {raw_target}"
                    )

        self.assertEqual([], failures, "broken local links:\n" + "\n".join(failures))

    def test_cli_reference_covers_the_released_parser(self) -> None:
        reference = (MANUAL / "cli-reference.md").read_text(encoding="utf-8")
        command_parser = parser()
        subparsers = next(
            action
            for action in command_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )

        self.assertIn("`--version`", reference)
        for command, child_parser in subparsers.choices.items():
            with self.subTest(command=command):
                self.assertIn(f"## `{command}`", reference)
            for action in child_parser._actions:
                for option in action.option_strings:
                    if option in {"-h", "--help"}:
                        continue
                    with self.subTest(command=command, option=option):
                        self.assertIn(f"`{option}`", reference)

    def test_data_dictionary_covers_every_schema_property(self) -> None:
        dictionary = (MANUAL / "data-dictionary.md").read_text(encoding="utf-8")
        schema_dir = ROOT / "src" / "pqid_bench" / "schemas"

        for path in sorted(schema_dir.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            for field in schema.get("properties", {}):
                with self.subTest(schema=path.name, field=field):
                    self.assertIn(f"`{field}`", dictionary)


if __name__ == "__main__":
    unittest.main()
