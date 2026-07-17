<!-- Promoted master document for repo-facing documentation on 2026-07-17 -->

# Cypher-DDS Master Document

Date: July 17, 2026

## Table of contents

- [Part I — Executive Overview](#part-i--executive-overview)
- [Part II — Product and Feature Scope](#part-ii--product-and-feature-scope)
- [Part III — Engineering Architecture](#part-iii--engineering-architecture)
- [Part IV — Platform and UI Surfaces](#part-iv--platform-and-ui-surfaces)
- [Part V — Bi-Directional Model and OEM Scope](#part-v--bi-directional-model-and-oem-scope)
- [Part VI — Packaging, CI, and Validation](#part-vi--packaging-ci-and-validation)
- [Part VII — Documentation and Workflow System](#part-vii--documentation-and-workflow-system)
- [Part VIII — Roadmap and Operational Direction](#part-viii--roadmap-and-operational-direction)
- [Part IX — Source Document Map](#part-ix--source-document-map)

---

# Part I — Executive Overview

## What Cypher-DDS is

Cypher-DDS is a local-first vehicle diagnostics project built around ELM327-compatible adapters and a shared Python diagnostic stack.

It is designed to keep:

- transport logic
- protocol logic
- make-specific logic
- session orchestration
- presentation layers

separate from one another.

That separation is the reason the same core can now support:

- a Textual desktop TUI
- a Tkinter desktop GUI
- a Kivy Android app

without duplicating diagnostic logic.

## Current maturity

Current maturity should be described honestly as:

- strong generic diagnostic core
- credible multi-surface architecture
- staged bi-directional framework
- early OEM-specific extension path
- incomplete runtime validation on packaged desktop GUI and Android surfaces

Cypher-DDS is not yet a production-grade cross-OEM coding/programming tool.

## Current top-level capabilities

Implemented:

- USB serial ELM327 transport
- desktop Linux Bluetooth RFCOMM transport
- Android Bluetooth transport path in code
- ELM327 initialization and protocol detection
- standard OBD-II Mode 01, 03, 04, and 09 workflows
- VIN/WMI profile selection
- make-aware DTC enrichment
- action catalog and action execution model
- desktop and mobile presentation surfaces

Blocked or intentionally limited:

- broad OEM active tests
- broad OEM coding
- programming / flashing

---

# Part II — Product and Feature Scope

## Generic diagnostic feature set

Cypher-DDS currently supports:

- live PID reads
- DTC reads
- DTC clearing
- VIN retrieval
- profile selection

These are the stable, low-risk, most mature parts of the system.

## Supported makes

Registered profiles:

- GM
- Ford
- Dodge / Chrysler
- Toyota / Lexus
- Honda / Acura
- Kia

## Depth by make

### GM

- profile present
- DTC table populated
- enhanced PID declarations present
- OEM enhanced read action implemented

### Ford

- profile present
- DTC table populated
- enhanced PID declarations present
- OEM enhanced read actions implemented

### Dodge / Chrysler

- profile present
- DTC table populated
- enhanced actions not yet implemented

### Toyota / Lexus

- profile present
- DTC table populated
- enhanced actions not yet implemented

### Honda / Acura

- profile present
- DTC table populated
- enhanced actions not yet implemented

### Kia

- profile present
- VIN/WMI routing present
- make-specific depth still shallow compared with GM/Ford

## Scope boundary

Cypher-DDS should currently be described as:

- a local diagnostic platform
- an engineering base for future OEM action growth

It should not currently be described as:

- a broad coding platform
- a module programming/flashing tool
- a validated cross-OEM service tool

---

# Part III — Engineering Architecture

## Layer model

Cypher-DDS is intentionally layered:

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

## Repository structure

```text
src/cypher_dds/
├── core/
├── profiles/
├── session.py
├── tui/
├── gui/
├── mobile/
└── theme.py
```

## Core responsibilities

### `core`

Owns:

- serial transports
- Bluetooth transports
- ELM327 framing
- standard PID helpers
- generic DTC helpers
- VIN decoding
- action model

### `profiles`

Owns:

- make metadata
- DTC enrichment
- enhanced PID declarations
- ECU-family metadata
- OEM action extensions

### `session.py`

Owns:

- connect
- VIN/profile resolution
- DTC reads
- live-data reads
- action enumeration
- action execution

### UI layers

Own:

- operator interaction
- display/state transitions
- threading around blocking calls

UI layers must not own:

- protocol decoding
- transport logic
- manufacturer-specific logic

## Engineering rules

1. `core` does not import from `profiles` or UI code.
2. UI layers do not decode protocol payloads directly.
3. `session.py` remains the single integration boundary.
4. Profiles extend behavior without mutating core transport design.

---

# Part IV — Platform and UI Surfaces

## Textual desktop TUI

Current role:

- primary operator surface
- most mature practical runtime path

Current functions:

- connect
- VIN display
- DTC display
- live data display
- refresh

## Tkinter desktop GUI

Current role:

- graphical desktop surface over the same shared session layer

Current functions:

- mock / USB / Bluetooth connect
- VIN display
- DTC display
- live data display
- action list
- confirmation for mutating actions
- result log

Current status:

- implemented as MVP
- packaging configured
- packaged runtime validation still pending

## Android Kivy app

Current role:

- mobile diagnostic surface

Current functions:

- mock / Bluetooth mode selection
- VIN display
- DTC display
- live data display
- action list
- confirmation popup
- result log

Current status:

- implemented in code
- Android Bluetooth transport path exists in code
- physical-device validation still pending

## Shared UI principles

Every surface should:

- use `DiagnosticSession`
- keep I/O off the UI thread
- show support levels honestly
- require confirmation for mutating actions

---

# Part V — Bi-Directional Model and OEM Scope

## Current action framework

Cypher-DDS has a shared cross-make action framework.

Current action categories:

- service
- active test
- coding
- programming

Current support levels:

- implemented
- mock_only
- planned
- blocked
- out_of_scope

## Implemented cross-make actions

- clear emissions DTCs
- tester present
- enter extended diagnostic session

## Implemented OEM-specific actions

### GM

- read transmission fluid temperature

### Ford

- read transmission fluid temperature
- read engine oil temperature

## Planned action classes

- powertrain output control
- body control coding
- transmission adaptation reset
- ABS bleed
- EPB service mode

These exist today as declared actions and support metadata, not as broad real-OEM implementations.

## Current ECU-family coverage model

Cypher-DDS now carries ECU-family support metadata per make.

The purpose of this layer is to make support reporting explicit instead of vague. It separates:

- generic diagnostics support
- bi-directional support
- programming support

That makes it possible to say, for example, that an ECM may be implemented for diagnostics while a BCM remains planned for coding and blocked for programming.

## Cross-make ECU-family pattern

Across the current makes, the common families represented are:

- engine / powertrain controller
- transmission controller
- body controller
- ABS / ESC
- electronic parking brake
- SRS / restraint controller
- one or more convenience or gateway modules depending on OEM

## OEM ECU-family detail

### GM

- PCM/ECM: diagnostics implemented; bidirectional mock-only; programming blocked
- TCM: diagnostics planned; bidirectional planned; programming blocked
- BCM: diagnostics planned; bidirectional planned; programming blocked
- ABS/EBCM: diagnostics planned; bidirectional planned; programming blocked
- EPB: diagnostics planned; bidirectional planned; programming blocked
- SRS: diagnostics planned; bidirectional blocked; programming blocked
- HVAC/comfort: diagnostics planned; bidirectional planned; programming blocked

### Ford

- PCM: diagnostics implemented; bidirectional mock-only; programming blocked
- TCM: diagnostics planned; bidirectional planned; programming blocked
- BCM: diagnostics planned; bidirectional blocked; programming blocked
- ABS/ESC: diagnostics planned; bidirectional planned; programming blocked
- EPB: diagnostics planned; bidirectional planned; programming blocked
- RCM/SRS: diagnostics planned; bidirectional blocked; programming blocked
- IPC/cluster: diagnostics planned; bidirectional blocked; programming blocked

### Dodge / Chrysler

- PCM/ECM: diagnostics implemented; bidirectional mock-only; programming blocked
- TCM: diagnostics planned; bidirectional planned; programming blocked
- BCM/TIPM: diagnostics planned; bidirectional planned; programming blocked
- ABS/ESC: diagnostics planned; bidirectional planned; programming blocked
- SGW/gateway: diagnostics planned; bidirectional blocked; programming blocked
- EPB: diagnostics planned; bidirectional planned; programming blocked
- ORC/SRS: diagnostics planned; bidirectional blocked; programming blocked

### Toyota / Lexus

- ECM: diagnostics implemented; bidirectional mock-only; programming blocked
- TCM/ECT: diagnostics planned; bidirectional planned; programming blocked
- Body ECU: diagnostics planned; bidirectional planned; programming blocked
- ABS/VSC: diagnostics planned; bidirectional planned; programming blocked
- EPB: diagnostics planned; bidirectional planned; programming blocked
- SRS: diagnostics planned; bidirectional blocked; programming blocked
- TPMS: diagnostics planned; bidirectional planned; programming blocked

### Honda / Acura

- PCM/ECM: diagnostics implemented; bidirectional mock-only; programming blocked
- TCM: diagnostics planned; bidirectional planned; programming blocked
- MICU/body control: diagnostics planned; bidirectional planned; programming blocked
- VSA/ABS: diagnostics planned; bidirectional planned; programming blocked
- EPB: diagnostics planned; bidirectional planned; programming blocked
- SRS: diagnostics planned; bidirectional blocked; programming blocked
- HVAC/gauge/convenience: diagnostics planned; bidirectional planned; programming blocked

### Kia

- ECM/PCM: diagnostics implemented; bidirectional mock-only; programming blocked
- TCM: diagnostics planned; bidirectional planned; programming blocked
- BCM: diagnostics planned; bidirectional planned; programming blocked
- ABS/ESC: diagnostics planned; bidirectional planned; programming blocked
- EPB: diagnostics planned; bidirectional planned; programming blocked
- SRS: diagnostics planned; bidirectional blocked; programming blocked
- TPMS: diagnostics planned; bidirectional planned; programming blocked

## Design limitation in the current action model

The current action layer still models executable requests as raw command strings plus expected response prefixes.

That is adequate for:

- simple service actions
- seed UDS requests
- enhanced read prototypes

It is not yet a production-grade model for:

- typed UDS services
- parameterized variable-control tests
- security access
- routine-control orchestration
- flashing/programming workflows

---

# Part VI — Packaging, CI, and Validation

## Packaging surfaces

The repository currently contains packaging/configuration for:

- Python package install via `pyproject.toml`
- desktop PyInstaller packaging
- Android Buildozer packaging

## Desktop packaging

Current desktop entry points:

- `cypher-dds` → Textual TUI
- `cypher-dds-gui` → Tkinter GUI

## Android packaging

Android packaging exists through the Kivy app structure and `buildozer.spec`.

The transport path for Android Bluetooth now exists in code through `AndroidBluetoothSerialAdapter`, selected by `SerialConnection.connect_bluetooth()` when `sys.platform == "android"`.

## Validation status

Validation is not uniform across surfaces.

### Verified locally

- Python package structure
- unit/integration tests against mock and patched transports
- session orchestration
- desktop GUI logic under test

### Verified in code/tests but not on target hardware

- Android Bluetooth backend selection
- Android Bluetooth adapter import and construction path

### Pending runtime validation

- packaged desktop GUI on real Windows
- packaged desktop GUI AppImage on real Linux desktop environments
- Android APK on a physical device
- Android Bluetooth connection to a real ELM327 adapter

## Why this distinction matters

A green build or passing mocked test is not the same thing as field validation.

Cypher-DDS documentation should continue to distinguish between:

- implemented in code
- tested in automation
- validated on target runtime

---

# Part VII — Documentation and Workflow System

## Documentation hierarchy

The cleanest hierarchy for the repo at this point is:

1. `README.md` for repo landing and operator/developer orientation
2. `Cypher-DDS_MASTER.md` for the consolidated engineering/master view
3. `PROJECT_STATUS.md` for implemented-vs-planned tracking
4. production review and plan documents for point-in-time analysis

## Documentation standard

Project docs should:

- avoid hardcoded marketing-style coverage claims
- separate implemented from planned from blocked
- distinguish packaging success from runtime validation
- describe OEM support by make and ECU family, not just by brand name

## Workflow notes

The current documentation pass was produced through a staged workflow:

- plan
- draft
- verify against code
- promote final repo-facing docs

That method is worth keeping for future documentation changes because this repo now has enough moving parts that casual README edits will drift from the code.

---

# Part VIII — Roadmap and Operational Direction

## Near-term engineering priorities

The next practical priorities remain:

1. validate desktop GUI runtime on real packaged targets
2. validate Android runtime and Bluetooth on physical hardware
3. refactor the action layer toward named/typed UDS services
4. expand OEM-specific enhanced reads and service routines
5. improve support reporting and topology/ECU visibility

## Medium-term direction

Medium-term, the repo should move toward:

- a first-class UDS/ISO-TP service layer
- OEM routine abstractions beyond raw hex strings
- stronger write gating and recovery boundaries
- more precise per-ECU support declarations

## Long-term constraint

Programming/flashing should remain blocked until the repo has a coherent story for:

- transport reliability
- power-loss handling
- security access
- file/package validation
- recovery/fallback
- OEM-specific programming flow control

---

# Part IX — Source Document Map

This master document should be treated as the top-level consolidated reference.

Primary linked source documents in the repo:

- `README.md`
- `PROJECT_STATUS.md`
- `PRODUCTION_REVIEW_2026-07-17.md`
- `plans/00-ROADMAP.md`
- `plans/01-GUI-PLAN.md`
- `plans/02-ANDROID-VALIDATION.md`

Local working references may exist outside the pushed document set, but repo-facing docs should avoid depending on unpublished files.
