"""Public Python interface for PQID-Bench collection and reproduction."""

from .live import (
    PROVIDER_PRESETS,
    LiveRunConfig,
    LiveRunResult,
    ProviderPreset,
    plan_live_model_run,
    provider_preset,
    run_live_model,
)
from .metrics import BenchmarkSummary, reproduce_release, summarize_evaluation_records
from .records import ProviderAttempt
from .replay import (
    ReplayPlan,
    canonicalize_harness_report,
    execute_replay,
    replay_plan,
    write_replay_derivatives,
)
from .reporting import (
    REPORT_FORMATS,
    render_comparison,
    render_summary,
    summary_rows,
)
from .version import (
    ARTIFACT_MANIFEST_VERSION,
    BENCHMARK_RELEASE,
    EVALUATOR_VERSION,
    PACKAGE_VERSION,
    PREDICATE_VERSION,
    SCHEMA_VERSION,
)

__all__ = [
    "ARTIFACT_MANIFEST_VERSION",
    "BENCHMARK_RELEASE",
    "EVALUATOR_VERSION",
    "PACKAGE_VERSION",
    "PREDICATE_VERSION",
    "PROVIDER_PRESETS",
    "REPORT_FORMATS",
    "SCHEMA_VERSION",
    "BenchmarkSummary",
    "LiveRunConfig",
    "LiveRunResult",
    "ProviderAttempt",
    "ProviderPreset",
    "ReplayPlan",
    "canonicalize_harness_report",
    "execute_replay",
    "plan_live_model_run",
    "provider_preset",
    "render_comparison",
    "render_summary",
    "replay_plan",
    "reproduce_release",
    "run_live_model",
    "summarize_evaluation_records",
    "summary_rows",
    "write_replay_derivatives",
]

__version__ = PACKAGE_VERSION
