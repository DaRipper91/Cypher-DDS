# Cypher-DDS Project Roadmap

## Current Status Overview
The core communication layer (ELM327 framing, standard PIDs, DTC decoding, VIN retrieval) is fully implemented, unit-tested via `MockELM327Adapter`, and wrapped in a framework-agnostic session manager (`DiagnosticSession`).
Current presentation layers:
- **TUI (`cypher_dds.tui`)**: Terminal interface with manual refresh.
- **Desktop GUI (`cypher_dds.gui`)**: Tkinter MVP implemented, not yet runtime-validated on packaged desktop artifacts.
- **Mobile (`cypher_dds.mobile`)**: Kivy app, Android Bluetooth path implemented in code, still untested on real hardware.

The repo also now has a staged OEM-write foundation:
- typed UDS request helpers
- action prerequisite metadata and negative-response handling
- a separate vehicle-tied coding manifest for persistent feature-write research

See [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md) for the current desktop + Android GUI implementation plan.

---

## Roadmap Milestones

### Milestone 1: Desktop GUI (Tkinter)
- **Status:** Proposed
- **Goal:** Build a thread-isolated Tkinter desktop application (`cypher_dds.gui`) that mirrors existing TUI functionality without adding new dependencies or licensing complications.
- **Plan:** [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md#desktop-gui-plan)

### Milestone 2: Android Bluetooth Backend
- **Status:** Proposed
- **Goal:** Implement a `pyjnius` bridge interfacing with `android.bluetooth.BluetoothSocket` to enable functional OBD2 communication on Android devices.
- **Plan:** [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md#android-gui-plan)

### Milestone 3: Real Hardware Validation & Testing
- **Status:** Proposed
- **Goal:** Execute manual testing of Windows/Linux/Android artifacts on physical OBD2 hardware, bypassing the virtualized socket mocks.
- **Plan:** [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md#cross-platform-gui-milestones)

### Milestone 4: Enhanced PIDs & DTC Tables Expansion
- **Status:** Proposed
- **Goal:** Expand brand-specific PIDs (GM/Ford/Dodge/Toyota/Honda) and integrate B (Body), C (Chassis), and U (Network) series trouble codes.
- **Plan:** Tracked in `PROJECT_STATUS.md` and future OEM implementation specs.

### Milestone 5: Continuous Polling & UI Polish
- **Status:** Proposed
- **Goal:** Transition UIs from manual refresh to continuous live-data polling, add confirmation-gated DTC clearing (Mode 04), and polish UI layouts.
- **Plan:** [plans/01-GUI-PLAN.md](/home/daripper/Projects/Cypher-DDS/plans/01-GUI-PLAN.md#cross-platform-gui-milestones)

### Milestone 6: Vehicle-Tied Coding Execution
- **Status:** In Progress
- **Goal:** Move from generic planned coding actions to verified per-vehicle persistent coding workflows with explicit ECU/session/security requirements.
- **Plan:** [VEHICLE_TIED_CODING_FUNCTIONS_ROADMAP.md](/home/daripper/Projects/Cypher-DDS/VEHICLE_TIED_CODING_FUNCTIONS_ROADMAP.md)

---

## Completed Milestones
- TUI baseline and shared session architecture
- Desktop GUI MVP scaffold
- Android Bluetooth transport code path
- Typed UDS action foundation
- Vehicle-tied coding manifest foundation
