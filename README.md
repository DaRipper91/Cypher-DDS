<div align="center">

# Cypher-DDS

**Local-first vehicle diagnostics over ELM327.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)
[![Status](https://img.shields.io/badge/status-diagnostics%20core%20implemented-yellow)](PROJECT_STATUS.md)

Live PID data. DTC reads. VIN decoding. Early bi-directional action support. No cloud, no subscription, no black box.

</div>

> **Noticeable project update — July 17, 2026:** Cypher-DDS now has a working desktop Tkinter GUI and a significantly expanded Android Kivy GUI surface. The desktop GUI now includes a structured DTC table, clear-DTC confirmation flow, action-category filtering, richer action detail, and shared session-driven behavior with the TUI. The Android GUI now mirrors more of that workflow in code, including DTC detail rendering, clear-DTC confirmation, and action filtering. Real packaged runtime validation on Windows/Linux and real-device Android validation are still pending.

## What Cypher-DDS is

Cypher-DDS is a Python-based OBD-II diagnostic project built around a shared diagnostic core and multiple operator surfaces:

- Textual desktop TUI
- Tkinter desktop GUI MVP
- Kivy Android app

It talks to vehicles through ELM327-compatible adapters and is designed so the transport, protocol, session, profile, and UI layers stay separate.

## What it currently does

Implemented today:

- USB serial ELM327 communication
- desktop Linux Bluetooth RFCOMM communication
- Android Bluetooth transport path in code
- ELM327 initialization and protocol detection
- standard OBD-II live data
- standard OBD-II DTC reads
- standard OBD-II DTC clearing
- VIN retrieval and WMI-based make selection
- cross-make action catalog with confirmation-gated mutating actions
- first OEM-specific enhanced-data actions for GM and Ford
- desktop GUI workflow with:
  - structured DTC detail table
  - clear-DTC confirmation flow
  - action category filtering
  - richer action descriptions/danger notes
- Android GUI workflow in code with:
  - DTC detail rendering
  - clear-DTC confirmation flow
  - action category filtering

Not implemented as broad production support:

- general OEM coding
- broad active-test coverage
- module programming / flashing

## Supported make coverage

Current built-in profiles:

- GM
- Ford
- Dodge / Chrysler
- Toyota / Lexus
- Honda / Acura
- Kia

Current depth varies by make:

- GM and Ford have the deepest enhanced-data support today
- Dodge / Chrysler, Toyota / Lexus, and Honda / Acura currently focus on DTC/profile coverage
- Kia currently has routing/profile support and can grow from there

## Architecture

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

Design rules:

- protocol logic stays out of the UI
- make-specific logic stays out of the core transport/protocol layer
- all presentation layers drive the same `DiagnosticSession`

## Bi-directional support

Cypher-DDS now has a real action framework, but support is staged.

Implemented across makes:

- clear emissions DTCs
- tester present
- enter extended diagnostic session

Implemented OEM-specific enhanced reads:

- GM transmission fluid temperature
- Ford transmission fluid temperature
- Ford engine oil temperature

Planned but not broadly implemented:

- powertrain output control
- body control coding
- transmission adaptation reset
- ABS bleed
- EPB service mode

Blocked by design:

- module programming / flashing

## Platform status

### Linux desktop

Best-supported runtime target today.

- TUI works here
- desktop Bluetooth works here
- desktop GUI exists here and is now materially beyond MVP shell status

### Windows desktop

Packaging is configured for both TUI and GUI, but packaged runtime validation on a real Windows machine is still pending.

### Android

The Kivy app exists, and the Android Bluetooth transport path now exists in code through `pyjnius` and `android.bluetooth.BluetoothSocket`.

That is still not the same thing as validated field support.

Current Android caveat:

- packaging path exists
- Bluetooth code path exists
- real-device validation is still pending

### macOS

Not a current target.

## Getting started

```bash
git clone https://github.com/DaRipper91/Cypher-DDS.git
cd Cypher-DDS
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the TUI:

```bash
cypher-dds
```

Run the desktop GUI:

```bash
cypher-dds-gui
```

Current desktop GUI highlights:

- mock, USB, and Linux Bluetooth connection modes
- VIN and resolved make display
- structured DTC table with descriptions
- clear-DTC button with confirmation
- live data summary
- action list with category filtering and support/danger details

By default, the project uses the mock adapter when no real transport is selected.

## Real hardware use

### USB

Typical Linux device paths:

- `/dev/ttyUSB*`
- `/dev/ttyACM*`

TUI example:

```bash
cypher-dds --port /dev/ttyUSB0
```

### Bluetooth

Desktop Linux:

```bash
cypher-dds --bluetooth AA:BB:CC:DD:EE:FF
```

The desktop GUI exposes the same transport choice through its UI.

Android:

- transport backend exists in code
- physical-device validation is still pending

## Documentation

Key docs in this repo:

- [Cypher-DDS_MASTER.md](Cypher-DDS_MASTER.md)
- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [PRODUCTION_REVIEW_2026-07-17.md](PRODUCTION_REVIEW_2026-07-17.md)
- [plans/00-ROADMAP.md](plans/00-ROADMAP.md)
- [plans/01-GUI-PLAN.md](plans/01-GUI-PLAN.md)
- [plans/02-ANDROID-VALIDATION.md](plans/02-ANDROID-VALIDATION.md)
- [plans/03-DESKTOP-GUI-VALIDATION.md](plans/03-DESKTOP-GUI-VALIDATION.md)

## Safety

Reading is low-risk. Writing is not.

Important safety boundaries:

- clearing DTCs resets readiness monitors
- actuator movement and adaptation resets are safety-sensitive
- programming remains blocked until the transport, security, recovery, and validation story is much stronger

## License

MIT
