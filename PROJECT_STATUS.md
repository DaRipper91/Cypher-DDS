# Cypher-DDS — Project Status

The core layer (serial, ELM327, PIDs, DTC, VIN) is fully implemented and
tested against a mock adapter. Profile data and the TUI's live wiring are
next. Update this file as pieces land.

## Core (`cypher_dds.core`) — brand-agnostic

| Module | Purpose | Status |
|---|---|---|
| `serial_conn.py` | Port discovery (`/dev/ttyUSB*`/`/dev/ttyACM*`), connect/disconnect, byte-level read-until-prompt framing | done |
| `elm327.py` | AT init sequence, command/response framing, error detection, `ATDPN` protocol name lookup | done |
| `pids.py` | Mode 01 PID table + decode math (RPM, speed, coolant temp, intake temp, MAF, throttle position, fuel level) | done |
| `dtc.py` | Mode 03/04 DTC read/clear, SAE J2012 byte decode, generic P0xxx table (~40 codes) | done |
| `vin.py` | Mode 09 VIN retrieval, WMI → manufacturer decode | done |
| `mock_adapter.py` | `MockELM327Adapter` — canned AT/PID/DTC/VIN responses (`default`, `no_adapter`, `malformed_vin` scenarios) for dev without hardware | done |

## Profiles (`cypher_dds.profiles`) — brand-specific

| Profile | Coverage target | Status |
|---|---|---|
| `base.py` | `VehicleProfile` interface + registry | stub |
| `gm.py` | GM, 1996+ (J1850 VPW pre-2008, CAN 2008+) | DTC_TABLE populated (402 P1xxx codes); 1 enhanced PID (trans fluid temp) |
| `ford.py` | Ford, 1996+ (J1850 PWM pre-2008, CAN 2008+). **Only the standard OBD2 bus is reachable via a basic ELM327 — MS-CAN (body/comfort systems) is out of scope for v1.** | DTC_TABLE populated (410 P1xxx codes, incl. Power Stroke diesel); 2 enhanced PIDs (trans fluid temp, engine oil temp) |
| `dodge_chrysler.py` | Dodge/Chrysler, 1996+ (ISO 9141-2/KWP2000 pre-2008, CAN 2008+). The proprietary SCI/CCD body bus is out of scope for v1 (same category as Ford's MS-CAN). | DTC_TABLE populated (97 P1xxx codes, incl. diesel/CNG variants); enhanced PIDs still stub |
| `toyota_lexus.py` | Toyota/Lexus, 1996+ (ISO 9141-2/KWP2000 pre-2008, CAN 2008+) | empty stub — proves plugin architecture is brand-agnostic |
| `honda_acura.py` | Honda/Acura, 1996+ (ISO 9141-2/KWP2000 pre-2008, CAN 2008+) | empty stub — proves plugin architecture is brand-agnostic |

Protocol selection is fully handled by the ELM327's auto-detect (`ATSP0`) —
`cypher_dds.core` already decodes Mode 01/03/09 identically regardless of
whether the transport is J1850, ISO 9141-2, KWP2000, or CAN, so widening
coverage from 2008+ to 1996+ needed no core changes, only updated scope
docs/profile metadata.

Explicitly out of scope for this phase: VAG, BMW, Mercedes (require UDS/ISO
14229 session handling — architecturally different), and anything
pre-1996 (before the US OBD-II mandate).

**Why DTC tables are large but enhanced-PID tables are small:** SAE J2012
means DTC codes and their meanings show up in consolidated public reference
sites (obd-codes.com, engine-light-help.com, etc.) — hundreds of entries per
brand. SAE J2190 (Mode 22) only standardizes the *mechanism* for enhanced
PIDs, not the PID assignments themselves, so those are scattered across
aftermarket-scanner community forums rather than published anywhere
consolidated. GM/Ford's enhanced-PID lists above are cross-referenced from
multiple independent community sources and kept intentionally small rather
than padded with unverified/conflicting hex codes.

## TUI (`cypher_dds.tui`)

| Module | Purpose | Status |
|---|---|---|
| `theme.py` | Brand accent colors (Royal Blue = connected/live + focus, Cherry Red = DTC alert), reserved for status meaning only | done |
| `app.py` | Textual app: connection status badge + DTC alert badge are real (styled, keyboard-toggleable via demo bindings `c`/`x`); live PID readout, real serial/DTC wiring | stub |

## Tests (`tests/`)

43 tests, 0 skipped. `test_pids.py`, `test_elm327.py`, `test_serial_conn.py`,
`test_dtc.py`, and `test_vin.py` all exercise real logic against
`MockELM327Adapter`: PID decode math, the full ELM327
init/command/protocol-detection flow, DTC byte decoding (all four
letter-prefix cases, padding, error paths), `DTCReader`, WMI decoding, and
`request_vin` (including the malformed-VIN length-validation path).
`test_profiles.py` locks in real GM, Ford, and Dodge/Chrysler P1xxx lookups
plus the GM/Ford enhanced-PID entries as regression checks.

## Next steps (not yet started)

1. Add Dodge/Chrysler enhanced PIDs and B/C/U-series codes for all three
   brands where documented; keep expanding GM/Ford enhanced PIDs as more
   are independently confirmed.
2. Expand `WMI_TABLE` beyond the current seed entries.
3. Wire up the Textual dashboard against `core` (or the mock adapter) —
   connect the demo status widgets to real serial/DTC/VIN state.
