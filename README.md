# sdl-lab-contract

STATUS_SPEC device-contract types for the AC Organic Self-Driving Lab —
the shared Pydantic models every device REST service and every reader
(the `lab-skills` SDK, the dashboard) agree on.

**The normative text is not here.** It lives at
[`ac-organic-lab/docs/STATUS_SPEC.md`](https://github.com/cyrilcaoyang/ac-organic-lab/blob/main/docs/STATUS_SPEC.md);
this package mirrors it. Spec ships before code: these models never change
ahead of a merged spec revision.

## What's in the box

- `models` — the `/status` envelope (`EquipmentStatus`) and its parts
  (`ComponentStatus`, `MetricValue`, `ErrorInfo`), the `EquipmentKind` /
  `EquipmentState` / `Activity` enums, and the `GET /` / `GET /health`
  bodies (`ProbeResponse`, `HealthResponse`).
- `claims` — the §5 claim-protocol bodies (`ClaimRequest`, `ClaimResponse`,
  `ClaimRejection`, `ClaimedBy`).

Deliberately **not** here: reader/aggregator runtime types (`FetchError`,
`EquipmentSnapshot`, …) — those describe a reader's view, not the contract,
and live in `lab_skills.models`.

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
uv add git+https://github.com/cyrilcaoyang/sdl-lab-contract
# pin a spec revision:
uv add "sdl-lab-contract @ git+https://github.com/cyrilcaoyang/sdl-lab-contract@v1.2.0"
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
