# Cypher-DDS Production Review

Date: July 17, 2026

## Table of contents

- [Executive summary](#executive-summary)
- [Verification performed](#verification-performed)
- [Section-by-section implementation status](#section-by-section-implementation-status)
- [Feature inventory](#feature-inventory)
- [Bi-directional architecture status](#bi-directional-architecture-status)
- [OEM and ECU-family coverage matrix](#oem-and-ecu-family-coverage-matrix)
- [Gaps, blockers, and production risks](#gaps-blockers-and-production-risks)
- [Recommended next production steps](#recommended-next-production-steps)

## Executive summary

Cypher-DDS currently has a solid read-oriented diagnostic core and a new first-pass bi-directional framework, but it is not yet a production-grade cross-OEM bi-directional scan tool.

Current state, in concrete terms:

- Core diagnostics are implemented for standard OBD-II flows:
  - serial transport
  - ELM327 command framing
  - VIN decode
  - Mode 01 live data
  - Mode 03 DTC read
  - Mode 04 DTC clear
- Session orchestration is implemented and shared cleanly across front ends.
- Six make profiles are now present:
  - GM
  - Ford
  - Dodge / Chrysler
  - Toyota / Lexus
  - Honda / Acura
  - Kia
- The repository now has an explicit OEM/ECU-family catalog covering 42 targeted ECU-family entries across those six makes.
- A bi-directional action manifest now exists for every make:
  - 9 declared actions per make
  - 54 declared actions total
  - 18 executable today
  - 30 planned but not executable
  - 6 intentionally blocked programming entries
- Desktop TUI is the most mature UI.
- Android/Kivy app is still a packaging/demo target, not a validated field-ready client.

Bottom line:

- Desktop diagnostics: usable development alpha
- Cross-make bi-directional architecture: implemented as a framework
- Real OEM-specific active tests/coding/programming: not implemented yet
- Mobile production readiness: not ready

## Verification performed

Verified on July 17, 2026 against the local repository state.

Commands run:

- `pytest tests/test_actions.py tests/test_profiles.py tests/test_vin.py tests/test_session.py`
- `python -m compileall src/cypher_dds`
- `pytest -k 'not tui_app'`
- `pytest` was also started for the full suite

Observed results:

| Verification item | Result | Notes |
|---|---|---|
| Targeted new/changed suites | Pass | 32 tests passed |
| Non-TUI full suite | Pass | 69 passed, 4 deselected |
| Full suite including TUI | Incomplete | 73 collected; run stalled during `tests/test_tui_app.py` in this environment |
| Bytecode compilation | Pass | `compileall` completed successfully |

Interpretation:

- Core/session/profile/transport logic is currently green.
- TUI integration still has an environment-specific verification gap.
- The new bi-directional framework is tested at the manifest/session level, not yet against real OEM write paths.

## Section-by-section implementation status

### 1. Core layer: `src/cypher_dds/core`

Status: implemented for generic OBD-II diagnostics, partially implemented for bi-directional scaffolding.

Implemented modules:

- `serial_conn.py`
- `bluetooth_adapter.py`
- `elm327.py`
- `pids.py`
- `dtc.py`
- `vin.py`
- `mock_adapter.py`
- `actions.py`

What is production-useful today:

- USB serial connectivity
- Linux Bluetooth RFCOMM support
- ELM327 initialization and protocol detection
- Standard OBD-II PID requests
- DTC decode
- VIN retrieval and WMI routing
- Mock adapter development path

What is not yet production-grade:

- Raw ISO-TP transport abstraction
- UDS session/security stack beyond seed commands
- ECU addressing/gateway management
- robust negative-response handling beyond current response-prefix checks
- retry/session timeout strategy for long-running write routines

### 2. Session layer: `src/cypher_dds/session.py`

Status: implemented and structurally sound.

Implemented responsibilities:

- connect/disconnect ownership
- VIN resolution
- make-profile selection
- DTC read and description enrichment
- live-data reads
- action discovery
- action execution with explicit confirmation for mutating operations

Assessment:

- This is the correct place for tool-facing orchestration.
- The new `available_actions()` and `run_action()` APIs are the correct boundary for future UI integration.
- The layer is still single-session, blocking I/O, and thread-offloaded by UIs rather than internally asynchronous.

### 3. Profile layer: `src/cypher_dds/profiles`

Status: implemented for make registration and DTC metadata; now extended with ECU-family coverage metadata.

Profiles currently registered:

| Key | Display name | Status |
|---|---|---|
| `gm` | General Motors | active |
| `ford` | Ford | active |
| `dodge_chrysler` | Dodge / Chrysler | active |
| `toyota_lexus` | Toyota / Lexus | active |
| `honda_acura` | Honda / Acura | active |
| `kia` | Kia | active |

Current profile capabilities:

- make registration
- WMI-based auto-selection
- manufacturer-specific DTC lookup
- enhanced PID exposure
- per-make action catalog exposure
- per-make ECU-family catalog exposure

Limitations:

- Only GM and Ford currently expose populated enhanced PID samples.
- Kia currently provides routing and framework integration, not Kia-specific DTC/action depth.
- No profile currently implements real OEM-specific write routines beyond shared seed service actions.

### 4. Desktop TUI: `src/cypher_dds/tui`

Status: functionally implemented, verification gap remains in full-suite headless testing in this environment.

Implemented:

- connect flow
- VIN display
- DTC panel
- live PID display
- refresh binding
- worker-thread offload for blocking I/O

Assessment:

- This remains the most production-relevant front end in the repo.
- It is still diagnostics-oriented only; no action browser or bi-directional workflow UI exists yet.
- Before calling this production-ready, the TUI test hang needs root-cause analysis.

### 5. Mobile app: `src/cypher_dds/mobile`

Status: pre-production demo.

Implemented:

- Kivy shell app
- mock-adapter connect flow
- VIN/DTC/live-data display
- refresh action

Known hard limits from the code itself:

- not validated on real device or emulator
- no Android Bluetooth backend
- no real-hardware diagnostic path

Assessment:

- This is a packaging milestone, not a shipped mobile product.

### 6. Packaging and distribution

Status: packaging infrastructure exists; runtime validation is incomplete.

Present in repo:

- `pyproject.toml`
- `cypher-dds.spec`
- `buildozer.spec`
- GitHub Actions workflows referenced in `README.md`

Assessment:

- Distribution plumbing exists for desktop and Android artifacts.
- Packaging success should not be confused with field validation.
- Android remains especially immature because transport is not implemented there.

### 7. Tests

Status: strong for core logic, incomplete for end-to-end UI confidence.

Test areas covered:

- action manifests
- Bluetooth adapter
- DTC logic
- ELM327 framing
- PID decoding
- profiles
- serial connection behavior
- session orchestration
- TUI integration
- VIN decoding

Assessment:

- The repository has good unit/integration coverage for a project at this stage.
- The main current testing weakness is real write-path behavior against actual vehicle/ECU traces.

## Feature inventory

| Feature area | Status | Notes |
|---|---|---|
| USB serial transport | Implemented | Core desktop path |
| Linux Bluetooth RFCOMM | Implemented | Desktop Linux only |
| Android Bluetooth | Not implemented | Explicitly called out in mobile code |
| ELM327 init/protocol detect | Implemented | Generic adapter layer works |
| Mock adapter | Implemented | Main non-hardware dev path |
| VIN read/decode | Implemented | WMI routing now includes Kia |
| Live data (Mode 01) | Implemented | Standard PID reads |
| DTC read (Mode 03) | Implemented | Generic + profile enrichment |
| DTC clear (Mode 04) | Implemented | Also exposed as action manifest |
| Enhanced PIDs | Partial | GM/Ford only in current repo |
| Make auto-detection | Implemented | Six profiles |
| TUI dashboard | Implemented | Most mature UI |
| Mobile app shell | Partial | Demo only |
| Bi-directional action catalog | Implemented | Framework exists across all makes |
| Action confirmation gate | Implemented | Required for mutating actions |
| Tester present | Implemented | Seed UDS keepalive |
| Enter extended diagnostic session | Implemented | Seed UDS session control |
| OEM actuator tests | Planned | Manifested, not executable |
| OEM coding/feature toggles | Planned | Manifested, not executable |
| Transmission relearn/adaptation flows | Planned | Manifested, not executable |
| ABS bleed service | Planned | Manifested, not executable |
| EPB service mode | Planned | Manifested, not executable |
| Module programming/flashing | Blocked | Deliberately not implemented |

## Bi-directional architecture status

### Implemented now

For every make, the code now declares:

- `clear_emissions_dtcs`
- `tester_present`
- `enter_extended_session`
- `powertrain_output_control`
- `body_control_coding`
- `transmission_adaptation_reset`
- `abs_bleed_service`
- `epb_service_mode`
- `module_programming`

Execution status:

| Action status | Count | Meaning |
|---|---:|---|
| Implemented | 18 | 3 executable actions across 6 makes |
| Planned | 30 | 5 non-executable but concretely declared actions across 6 makes |
| Blocked | 6 | programming entries across 6 makes |

### What “implemented” means here

Implemented does not mean “full OEM support.” It means:

- the action exists in a stable API
- the session layer can enumerate it
- mutating actions require explicit confirmation
- the mock transport can execute seed actions
- response validation exists at a basic positive-prefix level

### What is still missing for serious OEM write support

- raw request/response routing by ECU address
- ISO-TP handling as a first-class transport concern
- real UDS negative response classification
- security access workflows
- gateway/authentication handling
- per-ECU identifiers and routine-control mappings
- precondition checks such as battery voltage, ignition state, and vehicle state
- execution logging suitable for recovery/audit

## OEM and ECU-family coverage matrix

Important scope note:

The ECU-family entries below are the repo's current target catalog for implementation planning and review. They are not a claim that the project already supports all of those ECUs in the field.

### GM

| ECU family | Diagnostics | Bi-directional | Programming | Notes |
|---|---|---|---|---|
| PCM / ECM | implemented | mock_only | blocked | Current GM support is centered here |
| TCM | planned | planned | blocked | adaptation resets/relearns targeted |
| BCM | planned | planned | blocked | likely home for feature coding |
| ABS / ESC | planned | planned | blocked | brake bleed target |
| EPB | planned | planned | blocked | brake service mode target |
| SRS / Airbag | planned | blocked | blocked | safety-critical area |
| HVAC / Comfort | planned | planned | blocked | actuator/coding candidate |

### Ford

| ECU family | Diagnostics | Bi-directional | Programming | Notes |
|---|---|---|---|---|
| PCM | implemented | mock_only | blocked | current repo coverage is emissions-bus oriented |
| TCM | planned | planned | blocked | adaptation reset candidate |
| BCM | planned | blocked | blocked | MS-CAN limitation is the main obstacle |
| ABS / ESC | planned | planned | blocked | brake service candidate |
| EPB | planned | planned | blocked | likely routed through brake services |
| RCM / SRS | planned | blocked | blocked | safety-critical area |
| IPC / Cluster | planned | blocked | blocked | also affected by MS-CAN/gateway limits |

### Dodge / Chrysler

| ECU family | Diagnostics | Bi-directional | Programming | Notes |
|---|---|---|---|---|
| PCM / ECM | implemented | mock_only | blocked | current support is read-oriented |
| TCM | planned | planned | blocked | quick-learn/adaptation target |
| BCM / TIPM | planned | planned | blocked | feature coding candidate |
| ABS / ESC | planned | planned | blocked | brake service candidate |
| Secure Gateway | planned | blocked | blocked | likely blocker on newer platforms |
| EPB | planned | planned | blocked | service mode target |
| ORC / SRS | planned | blocked | blocked | safety-critical area |

### Toyota / Lexus

| ECU family | Diagnostics | Bi-directional | Programming | Notes |
|---|---|---|---|---|
| ECM | implemented | mock_only | blocked | current support is generic + profile metadata |
| TCM / ECT | planned | planned | blocked | adaptation reset target |
| Body ECU | planned | planned | blocked | likely home for hidden-feature coding |
| ABS / VSC | planned | planned | blocked | bleed and zero-point procedures targeted |
| EPB | planned | planned | blocked | pad service target |
| SRS | planned | blocked | blocked | safety-critical area |
| TPMS | planned | planned | blocked | ID registration/relearn candidate |

### Honda / Acura

| ECU family | Diagnostics | Bi-directional | Programming | Notes |
|---|---|---|---|---|
| PCM / ECM | implemented | mock_only | blocked | current support is generic + profile metadata |
| TCM | planned | planned | blocked | adaptation workflows targeted |
| MICU / Body Control | planned | planned | blocked | comfort-feature coding candidate |
| VSA / ABS | planned | planned | blocked | bleed/service candidate |
| EPB | planned | planned | blocked | brake service target |
| SRS | planned | blocked | blocked | safety-critical area |
| HVAC / Gauge / Convenience | planned | planned | blocked | actuator/coding candidate |

### Kia

| ECU family | Diagnostics | Bi-directional | Programming | Notes |
|---|---|---|---|---|
| ECM / PCM | implemented | mock_only | blocked | Kia routing exists; no Kia-specific write routines yet |
| TCM | planned | planned | blocked | likely early target for adaptation reset |
| BCM | planned | planned | blocked | primary hidden-feature coding target |
| ABS / ESC | planned | planned | blocked | brake service target |
| EPB | planned | planned | blocked | pad service mode target |
| SRS | planned | blocked | blocked | safety-critical area |
| TPMS | planned | planned | blocked | relearn candidate |

## Gaps, blockers, and production risks

### 1. Real OEM write support is not present yet

The framework exists. The actual OEM content does not.

Implication:

- the project can honestly say it has a bi-directional architecture
- it cannot honestly market full active-test/coding/programming support

### 2. Programming is still intentionally blocked

This is correct.

Reason:

- current transport and recovery architecture is not strong enough for module flashing

### 3. Desktop validation is not fully closed

The full suite stalled during TUI tests in this environment on July 17, 2026.

Implication:

- desktop runtime may still be fine
- but release confidence should treat the TUI harness as an open issue

### 4. Mobile is not field-ready

Current blockers:

- no Android Bluetooth backend
- no real-device verification
- no production transport path on phone

### 5. Documentation drift exists

As of this review:

- `README.md` still describes five brand profiles in several places
- the code now has six, including Kia
- the README and older status docs also do not yet reflect the new bi-directional framework

### 6. Adapter/transport limits remain fundamental

ELM327 is acceptable for generic diagnostics and limited seed actions.
It is not enough by itself to make this a serious cross-OEM programming tool.

## Recommended next production steps

Priority order:

1. Close the TUI verification gap
   - debug why `tests/test_tui_app.py` hangs in the full-suite run
   - decide whether the issue is test harness timing, worker lifecycle, or UI thread completion

2. Add one real OEM bi-directional pack end to end
   - choose one make and one ECU family
   - recommended starting points:
     - Kia BCM coding
     - Toyota ABS bleed
     - Ford PCM active test
   - include real request/response fixtures and explicit preconditions

3. Introduce a first-class UDS/transport layer
   - isolate request routing, session control, negative responses, and keepalive behavior from the generic ELM327 wrapper

4. Add action UI to the TUI
   - list available actions
   - show support level
   - require confirmation
   - log requests and responses

5. Update user-facing docs
   - add Kia to README/status docs
   - document current bi-directional support honestly
   - distinguish implemented, planned, blocked, and mock-only coverage

6. Keep programming blocked until architecture changes
   - no module flashing claims
   - no firmware write path until transport, security, logging, and recovery are designed explicitly
