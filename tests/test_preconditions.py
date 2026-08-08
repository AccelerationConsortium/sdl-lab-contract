"""§6.1 precondition-refusal (HTTP 412) body."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sdl_lab_contract import PreconditionFailure


def test_parses_the_spec_temperature_interlock_example():
    body = PreconditionFailure.model_validate({
        "detail": "Temperature outside seal band",
        "actual_c": 166.0,
        "setpoint_c": 170.0,
        "tolerance_c": 2.0,
        "retry_after_s": 2,
    })
    assert body.detail == "Temperature outside seal band"
    assert body.retry_after_s == 2


def test_unknown_shape_keeps_its_device_specific_fields():
    """§6.1's whole design is branching on *shape*. A reader parsing a body it
    has never seen must keep the fields it would branch on — dropping them
    would leave only `detail`, i.e. exactly the string-matching §6.1 forbids."""
    body = PreconditionFailure.model_validate({
        "detail": "Stage not loaded",
        "stage_state": "out",
        "required": "in",
    })
    dumped = body.model_dump()
    assert dumped["stage_state"] == "out"
    assert dumped["required"] == "in"


def test_operator_driven_recovery_has_no_retry_after():
    """`retry_after_s` is None when waiting cannot help (load a plate), and the
    header is then omitted rather than advertising a meaningless delay."""
    body = PreconditionFailure.model_validate({"detail": "Stage not loaded"})
    assert body.retry_after_s is None
    assert body.retry_after_header() == {}


def test_detail_is_required():
    with pytest.raises(ValidationError):
        PreconditionFailure.model_validate({"retry_after_s": 5})


@pytest.mark.parametrize(
    "retry_after_s,expected",
    [
        (2, "2"),
        (2.0, "2"),
        # Rounds UP: a client must never be invited back before the
        # precondition can have cleared.
        (2.4, "3"),
        (0.1, "1"),
        # Floors at 1 — `Retry-After: 0` tells a client nothing.
        (0, "1"),
    ],
)
def test_retry_after_header_is_integer_seconds(retry_after_s, expected):
    body = PreconditionFailure(detail="Heater warming up", retry_after_s=retry_after_s)
    assert body.retry_after_header() == {"Retry-After": expected}


def test_subclass_declares_its_own_shape():
    class HealthInterlock(PreconditionFailure):
        last_error_code: str
        last_error_message: str

    body = HealthInterlock.model_validate({
        "detail": "Recent operational failure not cleared",
        "last_error_code": "low_air_pressure",
        "last_error_message": "StartCycle returned error code -2147221503",
        "retry_after_s": 47,
    })
    assert body.last_error_code == "low_air_pressure"
    assert body.retry_after_header() == {"Retry-After": "47"}
