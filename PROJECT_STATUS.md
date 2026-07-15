# Cypher-DDS — Project Status

Scaffolding pass only. Interfaces and module shapes are in place; serial and
protocol logic is not yet implemented. Update this file as pieces land.

## Core (`cypher_dds.core`) — brand-agnostic

| Module | Purpose | Status |
|---|---|---|
| `serial_conn.py` | Port discovery (`/dev/ttyUSB*`/`/dev/ttyACM*`), connect/disconnect, byte-level read-until-prompt framing | done |
| `elm327.py` | AT init sequence, command/response framing, error detection, `ATDPN` protocol name lookup | done |
| `pids.py` | Mode 01 PID table + decode math (RPM, speed, coolant temp, intake temp, MAF, throttle position, fuel level) | done |
| `dtc.py` | Mode 03/04 DTC read/clear, SAE J2012 byte decode, generic P0xxx table (~40 codes) | done |
| `vin.py` | Mode 09 VIN retrieval + WMI → manufacturer decode | stub |
| `mock_adapter.py` | `MockELM327Adapter` — canned AT/PID responses (`default` + `no_adapter` scenarios) for dev without hardware | done |

## Profiles (`cypher_dds.profiles`) — brand-specific

| Profile | Coverage target | Status |
|---|---|---|
| `base.py` | `VehicleProfile` interface + registry | stub |
| `gm.py` | GM, 2008+, CAN 11-bit | stub, priority 1 |
| `ford.py` | Ford, 2008+, CAN. **Only standard OBD2 CAN is reachable via a basic ELM327 — MS-CAN (body/comfort systems) is out of scope for v1.** | stub, priority 2 |
| `dodge_chrysler.py` | Dodge/Chrysler, 2008+, CAN. Pre-2008 SCI vehicles are out of scope for v1. | stub, priority 3 |
| `toyota_lexus.py` | Toyota/Lexus, 2008+, CAN | empty stub — proves plugin architecture is brand-agnostic |
| `honda_acura.py` | Honda/Acura, 2008+, CAN | empty stub — proves plugin architecture is brand-agnostic |

Explicitly out of scope for this phase: VAG, BMW, Mercedes (require UDS/ISO
14229 session handling — architecturally different), and anything
pre-2008 or non-CAN (ISO9141, KWP2000, J1850).

## TUI (`cypher_dds.tui`)

| Module | Purpose | Status |
|---|---|---|
| `theme.py` | Brand accent colors (Royal Blue = connected/live + focus, Cherry Red = DTC alert), reserved for status meaning only | done |
| `app.py` | Textual app: connection status badge + DTC alert badge are real (styled, keyboard-toggleable via demo bindings `c`/`x`); live PID readout, real serial/DTC wiring | stub |

## Tests (`tests/`)

`test_pids.py`, `test_elm327.py`, `test_serial_conn.py`, and `test_dtc.py`
exercise real logic now — PID decode math, the full ELM327
init/command/protocol-detection flow, DTC byte decoding (all four
letter-prefix cases, padding, error paths), and `DTCReader` against
`MockELM327Adapter`. VIN is still scaffolded pending `vin.py`.

## Next steps (not yet started)

1. Implement Mode 09 VIN retrieval/decoding + WMI table for the five target
   brands.
2. Flesh out GM/Ford/Dodge profiles with real DTC and enhanced-PID tables
   where public documentation supports it.
3. Wire up the Textual dashboard against `core` (or the mock adapter).
