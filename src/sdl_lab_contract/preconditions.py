"""STATUS_SPEC §6 precondition-refusal body (HTTP 412).

The §5 claim rejection (409/423) has always been typed here as
:class:`sdl_lab_contract.claims.ClaimRejection`; this is its §6 sibling, for
the *other* structured refusal a device issues — "your request would be valid
if a precondition were met, and it isn't right now" (heater out of band, stage
not loaded, an uncleared operational failure).

**Only the common base lives here.** §6.1 requires bodies to be
distinguishable by *shape* rather than by ``detail`` string-matching, so the
precondition-specific fields are per-device by design and belong in the device
repo — this package's scope is the shared contract, not one instrument's
interlock catalog. Subclass to declare yours::

    class TemperatureInterlock(PreconditionFailure):
        actual_c: float
        setpoint_c: float
        tolerance_c: float

A reader that does not recognise a shape can still parse it as the base and
keep the unknown fields: ``extra="allow"`` is load-bearing, because dropping
them would destroy the very thing the reader branches on.

Two rules from §6 that this type does not enforce but every caller owes:

- **412 responses MUST NOT mutate ``last_error``** (§6.3). A refusal is not an
  execution failure; the equipment is healthy, the request just doesn't apply.
- **``allowed_actions`` must mirror the refusal** (§6.2): if POSTing an action
  would 412 right now, ``/status`` must omit it. Drive both from one helper.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict


class PreconditionFailure(BaseModel):
    """Body of an HTTP 412 Precondition Failed response (§6.1)."""

    # Per-device fields are the point of the shape (§6.1), so never drop them —
    # neither when a device subclasses this, nor when a reader parses a body
    # whose shape it has never seen.
    model_config = ConfigDict(extra="allow")

    detail: str
    """Short human-readable summary. The fallback for a client that does not
    recognise the body shape — never the thing it branches on."""

    retry_after_s: float | None = None
    """Best-effort seconds until the precondition is expected to clear, when it
    resolves over time (heater ramp, queue drain). ``None`` when recovery is
    operator-driven (load a plate) and no waiting will help."""

    def retry_after_header(self) -> dict[str, str]:
        """The ``Retry-After`` header §6.1 says to set alongside a non-null
        ``retry_after_s`` — empty dict when there is nothing to advertise.

        Exists because the header is defined in **integer** seconds while
        ``retry_after_s`` is a float estimate: emitting ``"2.4"`` produces a
        header clients are entitled to ignore. Rounds up, so the value is
        never an invitation to retry before the precondition can have cleared,
        and floors at 1 to avoid a meaningless ``Retry-After: 0``.
        """
        if self.retry_after_s is None:
            return {}
        return {"Retry-After": str(max(1, math.ceil(self.retry_after_s)))}
