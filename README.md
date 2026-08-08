# sdl-lab-contract

STATUS_SPEC device-contract types for the AC Organic Self-Driving Lab —
the shared Pydantic models every device REST service and every reader
(the `lab-skills` SDK, the dashboard) agree on.

**The normative text is not here.** It lives at
[`ac-organic-lab/docs/STATUS_SPEC.md`](https://github.com/AccelerationConsortium/ac-organic-lab/blob/main/docs/STATUS_SPEC.md);
this package mirrors it. Spec ships before code: these models never change
ahead of a merged spec revision.

## What's in the box

- `models` — the `/status` envelope (`EquipmentStatus`) and its parts
  (`ComponentStatus`, `MetricValue`, `ErrorInfo`), the `EquipmentKind` /
  `EquipmentState` / `Activity` enums, and the `GET /` / `GET /health`
  bodies (`ProbeResponse`, `HealthResponse`).
- `claims` — the §5 claim-protocol bodies (`ClaimRequest`, `ClaimResponse`,
  `ClaimRejection`, `ClaimedBy`).
- `preconditions` — `PreconditionFailure`, the §6.1 HTTP 412 refusal body.
  Only the common base (`detail`, `retry_after_s` + its `Retry-After` header);
  §6.1 wants bodies distinguishable by *shape*, so declare your device's own
  fields by subclassing. A reader can parse an unrecognised shape as the base
  without losing the fields it branches on.
- `conformance` — `check_consistency()`, the §2.3 invariant table
  (`busy`⇒`running`, `ready`/`requires_init`/`e_stop`⇒`idle`, …) that the types
  cannot express. A function, not a validator: readers must parse a
  nonconformant envelope, not crash on it. Assert it empty over your §9
  snapshot fixtures:

  ```python
  from sdl_lab_contract import EquipmentStatus, check_consistency

  def test_fixtures_are_spec_consistent(fixture_json):
      assert check_consistency(EquipmentStatus.model_validate(fixture_json)) == []
  ```

  It skips pre-v1.2 devices on purpose — they omit `activity`, so the reader's
  `"unknown"` default is correct rather than a bug (§8).

Deliberately **not** here: reader/aggregator runtime types (`FetchError`,
`EquipmentSnapshot`, …) — those describe a reader's view, not the contract,
and live in `lab_skills.models`. Nor any one device's precondition catalog —
that is the device repo's, per §6.1.

## Versioning — lockstep with the spec

`major.minor` of this package **is** the spec revision the types mirror
(`1.2.x` ⇄ STATUS_SPEC v1.2). The patch digit is free for packaging fixes
that do not touch the wire contract. Spec revisions are additive within a
major (v1.0 → v1.1 → v1.2), so a reader on a newer package parses every
older device — later-version fields default to "the device did not say"
(`activity` → `"unknown"`, never a false `"idle"`).

`PROTOCOL_VERSION` (`"1.0"`) is the parse-time default for devices that omit
`protocol_version` — a silent device is a pre-spec device. Report the version
your service actually implements on your own responses; `SPEC_VERSION`
(`"1.2"`) is what this package mirrors, not what your device speaks.

## Install

```bash
uv add git+https://github.com/AccelerationConsortium/sdl-lab-contract
# pin a spec revision:
uv add "sdl-lab-contract @ git+https://github.com/AccelerationConsortium/sdl-lab-contract@v1.2.0"
```

## Migrating a device repo off its vendored copy

1. Delete the STATUS_SPEC section of your `models.py` (keep any
   device-local models).
2. `from sdl_lab_contract import EquipmentStatus, ProbeResponse, ...`
3. Keep reporting your own `protocol_version` explicitly.
4. Run your snapshot-fixture tests (STATUS_SPEC §9) — they should pass
   unchanged; the types are verbatim-identical to the vendored copies.

Device repos are expected to take this swap together with their v1.2
migration (native `activity` reporting) — one visit per repo.

## Dev

```bash
uv sync
uv run pytest
```
