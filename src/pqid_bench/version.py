"""Independent version dimensions carried by every PQID-Bench report."""

PACKAGE_VERSION = "1.0.0"
BENCHMARK_RELEASE = "1.0.0"
EVALUATOR_VERSION = "pqid-bench-evaluator-1.1.0-safe-builtins"
PREDICATE_VERSION = "pqid-bench-reference-signature-1.0.0-count-map"
SCHEMA_VERSION = "1.0.0"
ARTIFACT_MANIFEST_VERSION = "1.0.0"


def version_record(*, run_type: str) -> dict[str, str]:
    return {
        "package_version": PACKAGE_VERSION,
        "benchmark_release": BENCHMARK_RELEASE,
        "evaluator_version": EVALUATOR_VERSION,
        "predicate_version": PREDICATE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "artifact_manifest_version": ARTIFACT_MANIFEST_VERSION,
        "run_type": run_type,
    }

