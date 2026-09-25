# Cypher-DDS Engineering Manual

Date: July 17, 2026

## Table of contents

- [1. Purpose](#1-purpose)
- [2. Current system state](#2-current-system-state)
- [3. Repository structure](#3-repository-structure)
- [4. Architecture](#4-architecture)
- [5. Transport and protocol layers](#5-transport-and-protocol-layers)
- [6. Session layer](#6-session-layer)
- [7. Profile system](#7-profile-system)
- [8. Bi-directional action system](#8-bi-directional-action-system)
- [9. Presentation layers](#9-presentation-layers)
- [10. Packaging and CI](#10-packaging-and-ci)
- [11. Testing strategy](#11-testing-strategy)
- [12. Validation workflows](#12-validation-workflows)
- [13. Engineering rules](#13-engineering-rules)
- [14. Known limits and risk boundaries](#14-known-limits-and-risk-boundaries)
- [15. Documentation map](#15-documentation-map)
- [16. Recommended next engineering steps](#16-recommended-next-engineering-steps)

## 1. Purpose

This manual is the engineering reference for Cypher-DDS.

It exists to answer:

- how the repo is structured
- what is implemented today
- where each responsibility belongs
- how to add new diagnostic capability safely
- what should remain out of scope until the transport/runtime story is stronger

This is not a user README. It is the working handbook for development.

## 2. Current system state

As of July 17, 2026:

- generic OBD-II read-oriented diagnostics are implemented
- a shared session layer is implemented
- six make profiles are registered:
  - GM
  - Ford
  - Dodge / Chrysler
  - Toyota / Lexus
  - Honda / Acura
  - Kia
- a cross-make bi-directional action framework is implemented
- the first OEM-specific read-only action pack is implemented for GM and Ford enhanced reads
- desktop TUI is implemented
- desktop Tkinter GUI MVP is implemented
- Android Kivy GUI exists and now has an Android Bluetooth code path
- Android Bluetooth is not real-device validated
- programming / flashing remains deliberately blocked

## 3. Repository structure

Primary code layout:

```text
src/cypher_dds/
├── core/        transport, framing, protocol helpers, actions
├── profiles/    make-specific metadata, DTCs, enhanced PIDs, action overrides, ECU catalogs
├── session.py   framework-agnostic orchestration layer
├── tui/         Textual desktop TUI
├── gui/         Tkinter desktop GUI
├── mobile/      Kivy Android GUI
└── theme.py     shared status colors
```

Key supporting docs:

- [README.md](/home/daripper/Projects/Cypher-DDS/README.md)
- [PROJECT_STATUS.md](/home/daripper/Projects/Cypher-DDS/PROJECT_STATUS.md)
- [PRODUCTION_REVIEW_2026-07-17.md](/home/daripper/Projects/Cypher-DDS/PRODUCTION_REVIEW_2026-07-17.md)
- [CYPHER_DDS_TOOL_REFERENCE.md](/home/daripper/Projects/Cypher-DDS/CYPHER_DDS_TOOL_REFERENCE.md)
- [plans/00-ROADMAP.md](/home/daripper/Projects/Cypher-DDS/plans/00-ROADMAP.md)
- [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md)
- [plans/02-ANDROID-VALIDATION.md](/home/daripper/Projects/Cypher-DDS/plans/02-ANDROID-VALIDATION.md)

## 4. Architecture

Cypher-DDS is intentionally layered.

```text
UI layers
  ├─ cypher_dds.tui
  ├─ cypher_dds.gui
  └─ cypher_dds.mobile
        │
        ▼
  cypher_dds.session
        │
        ├─ cypher_dds.core
        └─ cypher_dds.profiles
```

Rules:

- `core` must not import from `profiles` or UI layers
- UI layers must not implement diagnostic logic
- `session.py` is the integration boundary between presentation and diagnostics
- profiles add make-specific knowledge without mutating core protocol behavior

Why this matters:

- new UIs can be added without rewriting protocol logic
- new makes can be added without rewriting transport logic
- tests can verify core/session behavior without a UI framework

## 5. Transport and protocol layers

### 5.1 `serial_conn.py`

Responsibility:

- own a `SerialLike` transport
- connect over USB or Bluetooth
- provide raw send/read-until-prompt framing

Current transport paths:

- pyserial over USB
- desktop Linux RFCOMM via `BluetoothSerialAdapter`
- Android Bluetooth via `AndroidBluetoothSerialAdapter`
- mock transport via `MockELM327Adapter`

### 5.2 `bluetooth_adapter.py`

Responsibility:

- Linux desktop RFCOMM/SPP transport via `socket.AF_BLUETOOTH`

Status:

- implemented
- tested at mocked socket layer
- Linux-only

### 5.3 `android_bluetooth_adapter.py`

Responsibility:

- Android Bluetooth transport using `pyjnius`
- bridge to `android.bluetooth.BluetoothSocket`
- satisfy the same `SerialLike` contract as desktop transports

Status:

- implemented in code
- not validated on a physical Android device

### 5.4 `elm327.py`

Responsibility:

- ELM327 init sequence
- command send/response cleanup
- ELM327 error detection
- protocol name lookup

Important boundary:

- this layer knows adapter framing
- it does not know about vehicle makes

### 5.5 `pids.py`, `dtc.py`, `vin.py`

Responsibilities:

- `pids.py`: standard Mode 01 PID requests and decoding
- `dtc.py`: Mode 03/04 trouble code flows and generic P0xxx mapping
- `vin.py`: Mode 09 VIN request and WMI decode

Important boundary:

- these are read-oriented generic OBD-II helpers
- manufacturer-specific meaning belongs in profiles, not here

## 6. Session layer

File:

- [src/cypher_dds/session.py](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/session.py)

Responsibilities:

- connect
- resolve VIN and profile
- read DTCs
- read live data
- enumerate actions
- execute actions

This is the only layer UI code should drive directly.

Current public behavior:

- `connect(...)`
- `resolve_vehicle()`
- `read_dtcs()`
- `read_live_data()`
- `available_actions()`
- `run_action(...)`

This layer is blocking by design.
Each UI is responsible for putting calls on a worker/background thread.

## 7. Profile system

Profiles live under:

- [src/cypher_dds/profiles](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/profiles)

Each profile can provide:

- make key
- display name
- WMI hints
- manufacturer-specific DTC descriptions
- enhanced PID declarations
- action overrides/extensions
- ECU-family metadata

### Registered makes

| Key | Display |
|---|---|
| `gm` | General Motors |
| `ford` | Ford |
| `dodge_chrysler` | Dodge / Chrysler |
| `toyota_lexus` | Toyota / Lexus |
| `honda_acura` | Honda / Acura |
| `kia` | Kia |

### ECU-family catalog

File:

- [src/cypher_dds/profiles/catalog.py](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/profiles/catalog.py)

Purpose:

- define the planning/support matrix for each make
- provide a future basis for topology mapping and richer ECU-specific UX

Important limitation:

- this is support metadata, not proof that all listed ECUs are fully implemented

## 8. Bi-directional action system

File:

- [src/cypher_dds/core/actions.py](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/core/actions.py)

### 8.1 Current model

`DiagnosticAction` currently describes:

- key
- title
- description
- category
- raw command strings
- expected response prefixes
- support level
- mutates vehicle state
- danger note

### 8.2 Current action categories

- `SERVICE`
- `ACTIVE_TEST`
- `CODING`
- `PROGRAMMING`

### 8.3 Current support model

- `IMPLEMENTED`
- `MOCK_ONLY`
- `PLANNED`
- `BLOCKED`
- `OUT_OF_SCOPE`

### 8.4 Current implemented cross-make seed actions

- clear emissions DTCs
- tester present
- enter extended diagnostic session

### 8.5 Current implemented OEM-specific read-only actions

- GM:
  - transmission fluid temperature
- Ford:
  - transmission fluid temperature
  - engine oil temperature

### 8.6 Current design limit

The current action model is still too stringly-typed for serious OEM work.

It uses raw hex commands such as:

- `1003`
- `3E00`

That is acceptable for scaffolding, but not as a long-term UDS architecture.

### 8.7 Required next refactor

The next major action-system improvement should be:

- named UDS services
- typed parameters
- negative-response decoding
- action prerequisites
- a second action-control axis, for example:
  - fixed
  - toggle
  - variable
  - routine

This recommendation is reinforced by:

- [CYPHER_DDS_TOOL_REFERENCE.md](/home/daripper/Projects/Cypher-DDS/CYPHER_DDS_TOOL_REFERENCE.md)

## 9. Presentation layers

### 9.1 Textual TUI

Files:

- [src/cypher_dds/tui/app.py](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/tui/app.py)

Purpose:

- primary desktop operator interface
- connect
- show VIN
- show DTCs
- show live data
- manual refresh

Status:

- implemented
- currently the most mature runtime surface

### 9.2 Tkinter desktop GUI

Files:

- [src/cypher_dds/gui/app.py](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/gui/app.py)

Purpose:

- desktop GUI over the same session layer

Current scope:

- mock / USB / Bluetooth connect
- protocol state
- VIN
- DTCs
- live data
- action list
- action confirmation
- result log

Status:

- MVP implemented
- packaging paths configured
- packaged runtime still needs validation on real systems

### 9.3 Android Kivy app

Files:

- [src/cypher_dds/mobile/app.py](/home/daripper/Projects/Cypher-DDS/src/cypher_dds/mobile/app.py)

Current scope:

- mock / Bluetooth mode selection
- VIN
- DTCs
- live data
- action list
- confirmation popup
- result log

Status:

- UI path implemented
- Android Bluetooth path implemented in code
- physical-device validation still required

### 9.4 Shared UI rules

All UI layers should:

- call `DiagnosticSession`
- never parse protocol bytes directly
- move blocking work off the UI thread
- honor action confirmation for mutating operations
- display support level and danger note honestly

## 10. Packaging and CI

### Desktop packaging

Specs:

- [cypher-dds.spec](/home/daripper/Projects/Cypher-DDS/cypher-dds.spec)
- [cypher-dds-gui.spec](/home/daripper/Projects/Cypher-DDS/cypher-dds-gui.spec)

### Workflows

- [build-windows.yml](/home/daripper/Projects/Cypher-DDS/.github/workflows/build-windows.yml)
- [build-linux.yml](/home/daripper/Projects/Cypher-DDS/.github/workflows/build-linux.yml)
- [build-android.yml](/home/daripper/Projects/Cypher-DDS/.github/workflows/build-android.yml)

Current reality:

- TUI packaging paths were previously observed green in CI
- GUI packaging paths are now configured but still need fresh CI confirmation
- Android packaging path exists and was previously observed green
- Android runtime validation is still open

## 11. Testing strategy

The repo is built around fast local verification without vehicle hardware.

Current strength:

- core/session tests
- transport tests
- profile tests
- action tests
- desktop TUI widget/app-dispatch tests

### Important testing rule

Mock transport is valid for:

- framing logic
- decode math
- session orchestration
- action dispatch behavior

Mock transport is not proof of:

- real ECU compatibility
- timing behavior on a real bus
- gateway/authentication/session-lock behavior
- Android Bluetooth runtime behavior

## 12. Validation workflows

### Android

Use:

- [plans/02-ANDROID-VALIDATION.md](/home/daripper/Projects/Cypher-DDS/plans/02-ANDROID-VALIDATION.md)

### Desktop

Minimum runtime validation for GUI artifacts:

- launch GUI on Linux
- launch GUI on Windows
- connect using mock mode
- connect using a real adapter if available
- verify VIN / DTC / live-data path
- verify action list rendering
- verify confirmation flow for mutating actions

## 13. Engineering rules

### 13.1 Layer rules

- do not move make-specific logic into `core`
- do not move protocol logic into UI modules
- do not bypass `session.py` from UI code

### 13.2 Safety rules

- any mutating action must declare its danger clearly
- any mutating action must require explicit confirmation
- programming remains blocked until transport, validation, recovery, and power-management stories are explicit

### 13.3 Documentation rules

- user-facing claims must follow verified behavior, not planned behavior
- CI packaging is not runtime validation
- physical-device testing must be documented separately from mock/CI confidence

### 13.4 OEM-extension rules

Before adding a new OEM write routine:

- identify target ECU family
- identify transport/session requirements
- identify whether security access is required
- document the source/validation quality of the identifier or routine
- add mock fixtures
- add tests
- expose support level honestly

## 14. Known limits and risk boundaries

### 14.1 Programming

Blocked by design.

Reason:

- no first-class UDS stack
- no security access workflow
- no recovery design
- no J2534-equivalent transport story

### 14.2 Android

Implemented in code, but not validated in the field.

### 14.3 Commercial reference material

Commercial tools are useful for:

- naming
- UX patterns
- capability boundaries

They are not a valid source for proprietary ECU payloads.

## 15. Documentation map

Use these documents for their intended roles:

- [README.md](/home/daripper/Projects/Cypher-DDS/README.md)
  - user/project overview
- [PROJECT_STATUS.md](/home/daripper/Projects/Cypher-DDS/PROJECT_STATUS.md)
  - implementation status snapshot
- [PRODUCTION_REVIEW_2026-07-17.md](/home/daripper/Projects/Cypher-DDS/PRODUCTION_REVIEW_2026-07-17.md)
  - audit/review snapshot
- [CYPHER_DDS_TOOL_REFERENCE.md](/home/daripper/Projects/Cypher-DDS/CYPHER_DDS_TOOL_REFERENCE.md)
  - vocabulary and external architecture reference
- [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md)
  - GUI program plan
- [plans/02-ANDROID-VALIDATION.md](/home/daripper/Projects/Cypher-DDS/plans/02-ANDROID-VALIDATION.md)
  - physical Android validation checklist

## 16. Recommended next engineering steps

Priority order:

1. Refactor actions from raw UDS hex to named service models
2. Add a first-class UDS/transport layer below the action system
3. Validate desktop GUI packaging paths in CI and on real systems
4. Validate Android Bluetooth on a physical device
5. Expand OEM-specific action packs carefully:
   - service routines first
   - active tests second
   - coding only with validated identifiers
   - no programming until the transport/security story is mature

> Note
>
> The engineering direction is now clear enough to write an operational handbook later, but the operational handbook should be written only after more runtime validation exists for desktop GUI packaging, Android Bluetooth, and at least one deeper OEM write workflow.
