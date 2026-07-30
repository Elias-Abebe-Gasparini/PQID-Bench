"""Access to the versioned JSON Schemas installed with pqid-bench."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

SCHEMA_NAMES = (
    "benchmark-record",
    "prompt",
    "response",
    "evaluation",
    "run-manifest",
    "provider-attempt",
)


def load_schema(name: str) -> dict[str, Any]:
    if name not in SCHEMA_NAMES:
        raise KeyError(f"Unknown schema {name!r}; choose from {SCHEMA_NAMES}")
    resource = files("pqid_bench").joinpath("schemas", f"{name}.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))

