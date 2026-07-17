# Cypher-DDS GUI Plan

Date: July 17, 2026

## Purpose

Define a practical GUI plan for both desktop and Android that reuses the existing diagnostic stack:

- `cypher_dds.core`
- `cypher_dds.session`
- `cypher_dds.profiles`

The goal is to add GUI surfaces without duplicating protocol, VIN, DTC, PID, or action logic.

## Current baseline

Already implemented:

- generic OBD-II core
- shared `DiagnosticSession`
- desktop TUI in `cypher_dds.tui`
- Android Kivy app in `cypher_dds.mobile`
- bi-directional action framework at the session/profile layer

Current GUI reality:

- Desktop GUI: implemented as an MVP, not yet runtime-validated on packaged targets
- Android GUI: implemented in code, with Android Bluetooth transport path present but not yet real-device validated

## Product direction

Two GUI surfaces will be maintained:

1. Desktop GUI
   - module: `cypher_dds.gui`
   - framework: `Tkinter`
   - target platforms:
     - Linux: primary
     - Windows: supported for packaging and runtime validation
     - macOS: not a current target

2. Android GUI
   - module: `cypher_dds.mobile`
   - framework: `Kivy`
   - target platform:
     - Android only

The session/core stack remains shared across both.

## Non-goals

The GUI plan does not include:

- module programming/flashing
- platform-specific protocol forks in UI code
- re-implementing diagnostic logic inside GUI modules
- claiming full OEM coding/active-test coverage before ECU-specific work exists

## Shared architecture rules

Every GUI surface must follow these rules:

1. Presentation-only UI layer
   - GUI modules call `DiagnosticSession`
   - no PID/DTC/VIN parsing in UI code

2. Background I/O
   - serial/Bluetooth operations stay off the UI thread
   - each GUI posts results back to its own main thread mechanism

3. Shared visual semantics
   - reuse `DEFAULT_LIVE_PIDS`
   - reuse `cypher_dds.theme` colors
   - keep status vocabulary consistent:
     - no adapter
     - live
     - VIN unavailable
     - DTC present

4. Shared action model
   - use `available_actions()`
   - use `run_action()`
   - expose `danger_note`
   - require explicit confirmation before mutating operations

## Desktop GUI plan

### Framework decision

Use `Tkinter`.

Reason:

- standard library
- no extra dependency surface
- compatible with existing PyInstaller flow
- sufficient for the first desktop GUI scope

### Desktop GUI scope: phase 1

Feature parity with the current TUI:

- connect over:
  - mock adapter
  - USB serial
  - Linux Bluetooth RFCOMM
- show connection/protocol state
- show VIN + resolved make
- show stored DTCs
- show live PID summary
- manual refresh

### Desktop GUI scope: phase 2

Action-aware workflow:

- list supported actions by category
- show support level:
  - implemented
  - mock_only
  - planned
  - blocked
- confirmation dialog for mutating actions
- request/response log view

### Desktop GUI scope: phase 3

Diagnostic quality-of-life features:

- richer DTC view with descriptions
- clear-DTC button with confirmation
- readiness status
- freeze-frame data
- export session report

### Desktop GUI implementation structure

Planned files:

- `src/cypher_dds/gui/__init__.py`
- `src/cypher_dds/gui/app.py`
- `src/cypher_dds/gui/widgets.py` if widget decomposition becomes useful

### Desktop GUI threading model

- worker thread for connect/refresh/action execution
- `Tk.after()` to marshal results back to the main thread

### Desktop GUI layout proposal

Main window sections:

- connection bar
  - adapter mode
  - port/Bluetooth selector
  - connect button
  - protocol badge
- vehicle summary
  - VIN
  - detected make/profile
- DTC panel
  - count
  - codes
  - clear-codes action later
- live data panel
  - `DEFAULT_LIVE_PIDS`
  - manual refresh button
- actions panel
  - category list
  - support level
  - execute button
  - danger note
- log panel
  - info/errors/action responses

### Desktop GUI packaging

Required follow-up:

- add GUI entry point to packaging
- either:
  - extend `cypher-dds.spec`, or
  - add sibling GUI-specific PyInstaller spec
- GUI binary should use `console=False`

### Desktop GUI CI

Required follow-up:

- extend `.github/workflows/build-windows.yml`
- build GUI artifact separately from TUI artifact
- upload both artifacts

## Android GUI plan

### Framework decision

Keep `Kivy`.

Reason:

- Android app already exists
- Android-specific packaging path already exists
- replacing the framework now would create churn without solving the transport problem

### Android GUI reality

The current Android app is already the GUI plan’s base implementation.

It is not production-ready because:

- no real-device validation exists
- Android Bluetooth path has not been verified on a physical device
- packaged runtime behavior is still unverified

### Android scope: phase 1

Stabilize the existing Kivy app:

- preserve mock/demo path
- clean up layout and state handling
- align feature labels and status wording with desktop

### Android scope: phase 2

Make real hardware possible:

- implement Android Bluetooth transport using `pyjnius`
- bridge to `android.bluetooth.BluetoothSocket`
- adapt it to the existing `SerialLike` surface used by `SerialConnection`

### Android scope: phase 3

Match desktop diagnostic parity:

- real adapter connect
- VIN resolve
- DTC read
- manual live data refresh
- safe action discovery

### Android scope: phase 4

Action-aware mobile workflow:

- action list by category
- confirmation modal
- action status/danger labels
- result log

### Android UI layout proposal

Primary screens:

1. connection screen
   - mock vs Bluetooth
   - connect state
2. vehicle screen
   - VIN
   - make/profile
   - protocol
3. diagnostics screen
   - DTCs
   - live data
4. actions screen
   - service
   - active tests
   - coding
5. logs/settings screen
   - results
   - warnings
   - adapter preferences

### Android packaging

Current base:

- `buildozer.spec`
- `.github/workflows/build-android.yml`

Required follow-up:

- add `pyjnius` when Bluetooth backend work starts
- confirm Android permissions remain accurate
- validate on physical device before changing README support claims

## Cross-platform GUI milestones

### Milestone A: shared GUI contract

Goal:

- freeze the session/action APIs the GUIs rely on

Deliverables:

- documented GUI-facing session contract
- stable action presentation rules

### Milestone B: desktop GUI MVP

Goal:

- first working Tkinter GUI with TUI parity

Deliverables:

- `cypher_dds.gui`
- mock/USB/Bluetooth desktop connect
- VIN/DTC/live-data/refresh

### Milestone C: Android transport enablement

Goal:

- real Bluetooth communication on Android

Deliverables:

- Android Bluetooth adapter implementation
- device-level smoke validation

### Milestone D: action-aware GUIs

Goal:

- surface shared bi-directional action support in both GUIs

Deliverables:

- action list
- support status
- confirmation flow
- result log

### Milestone E: parity and polish

Goal:

- align desktop and Android UX around the same operator flows

Deliverables:

- richer DTC view
- readiness
- freeze frame
- export

## Dependencies and blockers

### Desktop blockers

- TUI test hang should be investigated before using TUI behavior as the sole UI baseline
- Windows GUI runtime still needs real validation even if packaging succeeds

### Android blockers

- no Bluetooth transport
- no real-device test coverage
- pyjnius integration work not started

### Shared blockers

- OEM-specific bi-directional routines are still mostly planned
- action UIs will initially reflect framework state, not broad real-vehicle support

## Recommended order of work

1. close the TUI verification gap
2. build desktop Tkinter GUI MVP
3. stabilize Android Kivy UI states and layouts
4. implement Android Bluetooth transport
5. add action-aware UX to both GUIs
6. expand richer diagnostic views

## Acceptance criteria

### Desktop GUI MVP is done when

- launches locally
- connects to mock adapter
- connects to USB adapter
- can use Linux Bluetooth path
- shows protocol, VIN, DTCs, and live data
- refresh works without blocking UI

### Android real-device milestone is done when

- APK installs on a real device
- Bluetooth adapter connects to a real OBD2 dongle
- VIN/DTC/live-data path works without mock transport

### Shared action GUI milestone is done when

- both GUIs can enumerate actions
- both GUIs show support level and danger note
- both GUIs require explicit confirmation for mutating actions
