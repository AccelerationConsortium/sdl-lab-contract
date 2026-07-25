"""STATUS_SPEC §5 claim-protocol bodies (v1.1+).

Request/response shapes for ``POST /control/claim`` / ``heartbeat`` /
``release``. Devices implement these; the ``lab-skills`` ``ClaimManager`` and
the dashboard's control passthrough consume them. Claims are cooperative, not
authenticated (spec §5) — a concurrency guard, not a security boundary.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ClaimedBy(BaseModel):
    """Identity of the current claim holder.

    Surfaced on ``/status`` under ``details.claimed_by`` so every reader sees
    who currently controls the device without a side trip.
    """

    session_id: str
    owner: str
    expires_at: datetime


class ClaimRequest(BaseModel):
    """Body of ``POST /control/claim``."""

    owner: str            # human or agent identifier; surfaced in details.claimed_by
    session_id: str       # opaque per-session id (UUID is recommended)
    ttl_s: float = 30.0   # device may clamp to its own min/max


class ClaimResponse(BaseModel):
    """Success body (HTTP 200) of ``POST /control/claim``."""

    claim_token: str
    heartbeat_interval_s: float   # caller MUST heartbeat more often than this
    expires_at: datetime          # absolute UTC; claim dies here without a heartbeat


class ClaimRejection(BaseModel):
    """Rejection body (HTTP 409 Conflict / 423 Locked) of ``POST /control/claim``."""

    detail: str
    claimed_by: ClaimedBy | None = None   # who currently holds it (best-effort)
    retry_after_s: float | None = None    # advisory; clients SHOULD also honor Retry-After
