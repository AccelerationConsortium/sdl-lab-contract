"""sdl-lab-contract — STATUS_SPEC device-contract types for the AC Organic
Self-Driving Lab.

The single shared source for the Pydantic models every device REST service
and every reader (the ``lab-skills`` SDK, the dashboard) agree on. The
normative text lives in ``ac-organic-lab/docs/STATUS_SPEC.md``; this package
mirrors it and versions in lockstep (package major.minor == spec revision).
"""

from .claims import (
    ClaimedBy,
    ClaimRejection,
    ClaimRequest,
    ClaimResponse,
)
from .models import (
    PROTOCOL_VERSION,
    SPEC_VERSION,
    Activity,
    ComponentStatus,
    EquipmentKind,
    EquipmentState,
    EquipmentStatus,
    ErrorInfo,
    ErrorSeverity,
    HealthResponse,
    MetricValue,
    ProbeResponse,
)

__version__ = "1.2.0"

__all__ = [
    "Activity",
    "ClaimedBy",
    "ClaimRejection",
    "ClaimRequest",
    "ClaimResponse",
    "ComponentStatus",
    "EquipmentKind",
    "EquipmentState",
    "EquipmentStatus",
    "ErrorInfo",
    "ErrorSeverity",
    "HealthResponse",
    "MetricValue",
    "PROTOCOL_VERSION",
    "ProbeResponse",
    "SPEC_VERSION",
    "__version__",
]
