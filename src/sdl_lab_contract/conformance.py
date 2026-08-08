"""Opt-in conformance checks derived from STATUS_SPEC (not wire shapes).

:mod:`sdl_lab_contract.models` mirrors the spec's *types*. This module holds
the *rules* those types cannot express — today, the §2.3 consistency
invariants between ``equipment_status`` and ``activity``.

Deliberately **not** a Pydantic validator. A reader must be able to parse a
nonconformant device's envelope, not crash on it: the spec says a reader *MAY*
treat a violation as a device bug, and §2.1's discipline is that you record
what a device actually said. So this is a function you call — device repos
assert it empty in their snapshot-fixture tests (§9), readers log it.
"""

from __future__ import annotations

from .models import EquipmentStatus

# §2.3 invariant table. A state absent from this mapping constrains nothing:
# `error` / `dry_run` / `unknown` accept any activity, by design.
#
# `degraded` accepts both — that pairing is the whole motivation for v1.2
# (a shaker with a dead heater RTD, mid-cycle, is `degraded` + `running`).
_ACTIVITY_INVARIANTS: dict[str, frozenset[str]] = {
    "busy": frozenset({"running"}),
    "ready": frozenset({"idle"}),
    "requires_init": frozenset({"idle"}),
    "e_stop": frozenset({"idle"}),
    "degraded": frozenset({"running", "idle"}),
}

# The invariants bind only devices that actually report `activity`, i.e. v1.2+.
_ACTIVITY_SINCE_VERSION = (1, 2)


def _version_tuple(raw: str) -> tuple[int, ...] | None:
    """Parse ``"1.2"`` → ``(1, 2)``. None when unparseable (never raises)."""
    try:
        return tuple(int(part) for part in raw.split("."))
    except (AttributeError, ValueError):
        return None


def reports_activity(status: EquipmentStatus) -> bool:
    """True when ``activity`` is a device claim rather than a reader default.

    A v1.0/v1.1 device omits the field and every reader fills in ``"unknown"``
    (§8) — that is correct, not a violation, and the distinction is invisible
    on the parsed model. Deciding it from ``protocol_version`` is the only
    signal available, which is exactly why this belongs here once instead of
    in fifteen device repos.
    """
    parsed = _version_tuple(status.protocol_version)
    return parsed is not None and parsed >= _ACTIVITY_SINCE_VERSION


def check_consistency(status: EquipmentStatus) -> list[str]:
    """Return §2.3 invariant violations; empty list when conformant.

    Skips devices below v1.2 entirely (see :func:`reports_activity`). For a
    v1.2 device, ``"unknown"`` **does** violate a state that pins the activity:
    §2.3 requires deriving activity from observed hardware, so a device that
    knows it is ``busy`` knows it is ``running``. ``unknown`` stays the honest
    answer of last resort only where the table constrains nothing.

    Returned strings are human-readable and stable enough to assert on; they
    are diagnostics, not error codes.
    """
    if not reports_activity(status):
        return []

    permitted = _ACTIVITY_INVARIANTS.get(status.equipment_status)
    if permitted is None or status.activity in permitted:
        return []

    expected = " or ".join(sorted(permitted))
    return [
        f"equipment_status={status.equipment_status!r} requires "
        f"activity={expected} (STATUS_SPEC §2.3), got {status.activity!r}"
    ]
