# Changelog

Versioning is **lockstep with the spec**: `major.minor` is the STATUS_SPEC
revision these types mirror (`1.2.x` ⇄ spec v1.2). The patch digit is free for
additions that do not change the wire contract. A minor bump REQUIRES a merged
`STATUS_SPEC.md` revision first — spec ships before code (ac-organic-lab
ARCHITECTURE.md decision #8).

## 1.2.1 — 2026-08-07

Additive library surface only. **No wire-contract change**, hence a patch bump:
everything here models shapes and rules spec v1.2 already defines, so no device
has to change anything to stay conformant.

### Added

- **`py.typed`** (PEP 561). Without the marker, mypy and pyright treated this
  package as untyped and silently gave consumers no checking — from the one
  package whose entire purpose is distributing types. Verified present in the
  built wheel.
- **`PreconditionFailure`** (`preconditions`) — the §6.1 HTTP 412 refusal body.
  The §5 claim rejection (409/423) has always been typed here; this is its
  missing sibling. Only the common base (`detail`, `retry_after_s`) ships:
  §6.1 requires bodies to be distinguishable by *shape*, so per-device fields
  are declared by subclassing in the device repo. `extra="allow"` so a reader
  parsing an unrecognised shape keeps the fields it would branch on.
  `retry_after_header()` emits the paired `Retry-After` in integer seconds
  (rounds up, floors at 1) — a float in that header is ignorable by clients.
- **`check_consistency()` / `reports_activity()`** (`conformance`) — the §2.3
  invariant table (`busy`⇒`running`, `ready`/`requires_init`/`e_stop`⇒`idle`,
  `degraded`⇒either), which the types cannot express. Deliberately a function,
  not a validator: a reader must parse a nonconformant device's envelope rather
  than crash on it, and the spec says a reader *MAY* treat a violation as a
  device bug. Device repos assert it empty over their §9 snapshot fixtures.

  Version-aware, which is the reason it belongs here once rather than in every
  device repo: a v1.0/v1.1 device omits `activity` and every reader fills in
  `"unknown"` (§8) — correct, not a violation, and indistinguishable on the
  parsed model except via `protocol_version`. Checking it naively would flag
  the entire unmigrated fleet.

  The regression it exists for is real: the Cytation's first v1.2 attempt
  (device repo b86da09) shipped `requires_init` + `activity: unknown`, derived
  from `equipment_status`, and reached production before being caught by hand.

### Notes

- Test suite 6 → 41 tests.
- Still missing, deliberately deferred: a `cycles_total` reserved-key constant
  (§2.3.1), a heartbeat-200 body (§5), a typed accessor for
  `details.claimed_by`, `LICENSE` (pyproject declares MIT), and CI.

## 1.2.0 — 2026-07-25

Initial extraction from `lab_skills.models` (ARCHITECTURE.md LG5). STATUS_SPEC
v1.2 types: the `/status` envelope and its parts, the probe/health bodies, and
the §5 claim-protocol bodies. Reader/aggregator runtime types (`FetchError`,
`EquipmentSnapshot`) deliberately excluded — they describe a reader's view, not
the contract.
