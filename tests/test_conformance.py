"""§2.3 consistency-invariant checks.

The regression these exist for is real: the Cytation's first v1.2 attempt
(device repo b86da09) shipped `requires_init` paired with `activity: unknown`
and derived activity from `equipment_status` — the one thing §2.3 forbids. It
reached production and was caught by hand afterwards. A device repo asserting
`check_consistency(...) == []` over its snapshot fixtures catches that class
in its own test suite instead.
"""

from __future__ import annotations

import pytest

from sdl_lab_contract import EquipmentStatus, check_consistency, reports_activity

BASE = {
    "equipment_id": "shaker_sc25xr",
    "equipment_name": "Torrey Pines SC25XR",
    "equipment_kind": "shaker",
    "equipment_status": "ready",
    "device_time": "2026-04-29T22:50:01Z",
}


def status(**overrides) -> EquipmentStatus:
    return EquipmentStatus.model_validate({**BASE, **overrides})


# --- the invariant table (§2.3), for a device that actually reports activity ---


@pytest.mark.parametrize(
    "equipment_status,activity",
    [
        ("busy", "running"),
        ("ready", "idle"),
        ("requires_init", "idle"),
        ("e_stop", "idle"),
        # `degraded` takes either — the pairing v1.2 exists to express.
        ("degraded", "running"),
        ("degraded", "idle"),
        # These constrain nothing.
        ("error", "running"),
        ("error", "idle"),
        ("error", "unknown"),
        ("dry_run", "running"),
        ("unknown", "unknown"),
    ],
)
def test_conformant_pairings_report_no_violation(equipment_status, activity):
    s = status(protocol_version="1.2", equipment_status=equipment_status, activity=activity)
    assert check_consistency(s) == []


@pytest.mark.parametrize(
    "equipment_status,activity",
    [
        ("busy", "idle"),
        ("ready", "running"),
        ("requires_init", "running"),
        ("e_stop", "running"),
        # `unknown` IS a violation where the table pins the value: a v1.2 device
        # that knows it is busy knows it is running (§2.3 — observed, not derived).
        ("busy", "unknown"),
        ("ready", "unknown"),
        ("requires_init", "unknown"),  # the b86da09 bug
        ("e_stop", "unknown"),
        ("degraded", "unknown"),
    ],
)
def test_violations_are_reported(equipment_status, activity):
    s = status(protocol_version="1.2", equipment_status=equipment_status, activity=activity)
    violations = check_consistency(s)
    assert len(violations) == 1
    assert "§2.3" in violations[0]
    assert activity in violations[0]


# --- version awareness: the table binds only devices that report activity ---


@pytest.mark.parametrize("version", ["1.0", "1.1"])
def test_pre_v12_devices_are_not_checked(version):
    """A v1.0/v1.1 device omits `activity`; the reader's `"unknown"` default is
    correct (§8), not a device bug. Checking it would flag the entire fleet."""
    s = status(protocol_version=version, equipment_status="busy")
    assert s.activity == "unknown"
    assert reports_activity(s) is False
    assert check_consistency(s) == []


def test_v12_and_later_are_checked():
    assert reports_activity(status(protocol_version="1.2")) is True
    assert reports_activity(status(protocol_version="1.3")) is True
    assert reports_activity(status(protocol_version="2.0")) is True


def test_unparseable_version_is_not_checked_and_never_raises():
    """A malformed version must not crash a reader mid-poll — §2.1's discipline
    is to record what the device said, not to reject it."""
    s = status(protocol_version="not-a-version", equipment_status="busy")
    assert reports_activity(s) is False
    assert check_consistency(s) == []


def test_checker_does_not_reject_the_envelope():
    """Nonconformant envelopes must still parse — the check is opt-in, never a
    validator. A reader that crashed on a buggy device would lose the very
    evidence the operator needs."""
    s = status(protocol_version="1.2", equipment_status="ready", activity="running")
    assert s.equipment_status == "ready" and s.activity == "running"
    assert check_consistency(s)
