"""Stable internal records used at package boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    """Normalized metadata for one provider request attempt.

    Raw payloads remain separate files. The record stores only their location
    and digest so provider-specific response structures cannot leak into the
    shared evaluator contract.
    """

    attempt_id: str
    run_id: str
    prompt_id: str
    provider: str
    route: str
    requested_model: str
    resolved_model: str | None
    request_sha256: str
    response_text: str | None
    raw_response_path: str | None
    raw_response_sha256: str | None
    provider_request_id: str | None
    finish_reason: str | None
    status: str
    attempt_index: int
    started_at: datetime
    completed_at: datetime | None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    transport_affected: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["started_at"] = self.started_at.isoformat()
        payload["completed_at"] = (
            self.completed_at.isoformat() if self.completed_at is not None else None
        )
        return payload

