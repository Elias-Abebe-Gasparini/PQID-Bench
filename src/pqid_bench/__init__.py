"""Public Python interface for PQID-Bench collection and reproduction."""

from .download import (
    OFFICIAL_CORE_RELEASES,
    CoreRelease,
    DownloadResult,
    download_core_release,
)
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
from .visualization import (
    DashboardData,
    build_dashboard,
    load_dashboard_data,
    write_site_assets,
)

__all__ = [
    "ARTIFACT_MANIFEST_VERSION",
    "BENCHMARK_RELEASE",
    "EVALUATOR_VERSION",
    "OFFICIAL_CORE_RELEASES",
    "PACKAGE_VERSION",
    "PREDICATE_VERSION",
    "PROVIDER_PRESETS",
    "REPORT_FORMATS",
    "SCHEMA_VERSION",
    "BenchmarkSummary",
    "CoreRelease",
    "DashboardData",
    "DownloadResult",
    "LiveRunConfig",
    "LiveRunResult",
    "ProviderAttempt",
    "ProviderPreset",
    "ReplayPlan",
    "build_dashboard",
    "canonicalize_harness_report",
    "execute_replay",
    "download_core_release",
    "load_dashboard_data",
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
    "write_site_assets",
]

__version__ = PACKAGE_VERSION
