"""Contract-behavior tests.

These pin the version-defaulting semantics STATUS_SPEC §8 (back-compat)
requires of every reader: later-version fields default to "the device did not
say", never to a positive claim. They mirror the checks that validated the
lab-skills copy before extraction.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdl_lab_contract import (
    PROTOCOL_VERSION,
    SPEC_VERSION,
    ClaimedBy,
    ClaimRejection,
    EquipmentStatus,
)

BASE = {
    "equipment_id": "shaker_sc25xr",
    "equipment_name": "Torrey Pines SC25XR",
    "equipment_kind": "shaker",
    "equipment_status": "ready",
    "device_time": "2026-04-29T22:50:01Z",
}


def test_spec_and_default_versions_are_distinct_on_purpose():
    # SPEC_VERSION tracks the doc; PROTOCOL_VERSION is the parse-time default
    # for devices that omit the field — a silent device is a v1.0 device.
    assert SPEC_VERSION == "1.2"
    assert PROTOCOL_VERSION == "1.0"


def test_v12_envelope_round_trips_activity():
    s = EquipmentStatus.model_validate({
        **BASE,
        "protocol_version": "1.2",
        "equipment_status": "degraded",
        "activity": "running",
        "activity_since": "2026-04-29T22:49:44Z",
    })
    assert s.activity == "running"
    assert s.activity_since is not None


def test_pre_v12_envelope_reads_unknown_never_idle():
    for version in ({}, {"protocol_version": "1.0"}, {"protocol_version": "1.1"}):
        s = EquipmentStatus.model_validate({**BASE, **version})
        assert s.activity == "unknown"
        assert s.activity_since is None


def test_v10_envelope_defaults_v11_fields():
    s = EquipmentStatus.model_validate(BASE)
    assert s.protocol_version == "1.0"
    assert s.allowed_actions == []
    assert s.required_actions == []
    assert s.details == {}


def test_out_of_enum_values_are_rejected_not_coerced():
    with pytest.raises(ValidationError):
        EquipmentStatus.model_validate({**BASE, "activity": "shaking"})
    with pytest.raises(ValidationError):
        EquipmentStatus.model_validate({**BASE, "equipment_status": "unreachable"})


def test_claim_rejection_parses_spec_example():
    r = ClaimRejection.model_validate({
        "detail": "already claimed",
        "claimed_by": {
            "session_id": "f1f1c1a2",
            "owner": "agent:solubility-screening",
            "expires_at": "2026-04-29T22:50:31Z",
        },
        "retry_after_s": 5,
    })
    assert isinstance(r.claimed_by, ClaimedBy)
    assert r.claimed_by.owner == "agent:solubility-screening"
    # both optional fields default when the device sends a bare detail
    bare = ClaimRejection.model_validate({"detail": "nope"})
    assert bare.claimed_by is None and bare.retry_after_s is None
