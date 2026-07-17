<div align="center">

# Cypher-DDS

**A terminal-first diagnostic tool for talking to your car over a USB or Bluetooth ELM327 adapter.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)
[![Status](https://img.shields.io/badge/status-core%20layer%20implemented-yellow)](PROJECT_STATUS.md)

Live PID data. Diagnostic trouble codes. VIN decoding. Early bi-directional service scaffolding. No cloud, no app store, no subscription — just your laptop, a cable, and the OBD2 port under your dash.

**[⬇ Download the latest release](../../releases/latest)** — pick the file for your device:

| Device | File | Notes |
|---|---|---|
| Windows | `cypher-dds.exe` | Double-click to run. Not yet tested on a real Windows machine. |
| Linux (Ubuntu, Fedora, Arch, Debian, openSUSE, etc.) | `cypher-dds-x86_64.AppImage` | `chmod +x` it, then run it — no install needed. |
| Android | `cypherdds-*-arm64-v8a-debug.apk` | Early demo — Android Bluetooth path is now coded, but not validated on a physical device yet. |
| macOS | — | Not built yet, not currently a supported target. |

</div>

---

## What it does

Plug a USB ELM327 (or ELM327-clone / STN11xx) adapter into your car's OBD2 port — or pair one over Bluetooth on Linux — and Cypher-DDS will:

- Connect over serial (USB or Bluetooth RFCOMM), initialize the ELM327 chip, and auto-detect the vehicle's protocol
- Stream **live data** — RPM, speed, coolant temp, throttle position, and more
- Read **diagnostic trouble codes (DTCs)**, with brand-aware descriptions where available
- Pull and decode the **VIN**, using it to auto-select the right vehicle profile
- Expose a **bi-directional action catalog** for supported makes, with explicit confirmation gates for mutating operations

It works on any standard OBD2 vehicle (1996+, any protocol — J1850, ISO 9141-2, KWP2000, or CAN) out of the box, and gets smarter about specific brands through a plugin system — see [Architecture](#architecture) below. The terminal UI is the primary, most-tested interface; a desktop GUI now exists as a Tkinter MVP, and the Android app is still an early demo pending real-device validation.

The current bi-directional layer is a framework, not a finished OEM write tool. Today it can execute a small seed set of generic service actions and declare planned active-test/coding/service targets per make. Real hidden-feature toggles, actuator tests, and module programming still require ECU-specific implementations.

## Why

Every OBD2 app on the market either wants a subscription, phones data home, or hides basic PID access behind a paywall. Cypher-DDS is local-only: it talks directly to the adapter over serial, decodes everything itself, and answers to nobody. It's also meant to be a tool you can actually read — small, brand-agnostic core, inspectable decoding logic, no black boxes.

## Architecture

Four layers, deliberately kept apart:

```
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  cypher_dds.tui               │  │  cypher_dds.mobile            │
│  Textual dashboard (desktop)  │  │  Kivy app (Android)           │
│  Tkinter GUI also drives the  │  │  same shared session layer    │
│  same shared session layer    │  │                               │
└───────────────┬──────────────┘  └───────────────┬──────────────┘
                 │        both drive the same session layer        │
                 └───────────────────────┬──────────────────────---┘
                             ┌───────────▼────────────┐
                             │  cypher_dds.session      │
                             │  connect → VIN/profile → │
                             │  DTC-read → live-PID-read│
                             │  → action execution      │
                             │  Framework-agnostic — no │
                             │  UI code of its own.      │
                             └───────────┬────────────-─┘
                             │  optionally consulted for
                             │  DTC descriptions / enhanced PIDs /
                             │  ECU/action catalogs
┌───────────────────────────▼──────────────────────────────-─┐
│  cypher_dds.profiles        (brand-specific plugins)        │
│  GM · Ford · Dodge/Chrysler · Toyota/Lexus · Honda/Acura ·   │
│  Kia                                                         │
│  Each is a self-contained module. New brand = new module,    │
│  zero changes to core.                                       │
└───────────────────────────┬──────────────────────────────-─┘
                             │  talks only to public interfaces
┌───────────────────────────▼──────────────────────────────-─┐
│  cypher_dds.core            (brand-agnostic)                │
│  USB/Bluetooth serial transport → ELM327 AT layer →          │
│  Mode 01/03/04/09 + seed action execution. Works on any OBD2 │
│  vehicle for read-oriented diagnostics, with zero brand code.│
└───────────────────────────────────────────────────────────-┘
```

**Core never imports from profiles or a presentation layer.** A profile can be selected manually or picked automatically from the decoded VIN's WMI. The TUI, Tkinter desktop GUI, and mobile app all talk only to `cypher_dds.session`'s public interface — no protocol logic duplicated across UI layers.

## Supported vehicles

1996 is the year the US OBD-II mandate took effect, so it's Cypher-DDS's floor:

| Brand | Years | Bus | Status |
|---|---|---|---|
| GM | 1996+ | J1850 VPW (1996–2007ish) → CAN (2008+) | 🚧 DTC table done (402 P1xxx codes) + 1 enhanced PID |
| Ford | 1996+ | J1850 PWM (1996–2007ish) → CAN (2008+) | 🚧 DTC table done (410 P1xxx codes, incl. Power Stroke diesel) + 2 enhanced PIDs — see note below |
| Dodge / Chrysler | 1996+ | ISO 9141-2 / ISO 14230-4 KWP (1996–2007ish) → CAN (2008+) | 🚧 DTC table done (97 P1xxx codes, incl. diesel/CNG); enhanced PIDs pending — see note below |
| Toyota / Lexus | 1996+ | ISO 9141-2 / ISO 14230-4 KWP → CAN | 🚧 DTC table done (44 P1xxx codes); enhanced PIDs pending |
| Honda / Acura | 1996+ | ISO 9141-2 / ISO 14230-4 KWP → CAN | 🚧 DTC table done (94 P1xxx codes); enhanced PIDs pending |
| Kia | 1996+ | ISO 9141-2 / ISO 14230-4 KWP → CAN | 🚧 VIN/WMI routing + profile registration done; Kia-specific DTC/enhanced PID depth pending |

Cypher-DDS never hardcodes a protocol — the ELM327's `ATSP0` auto-detect handles J1850 PWM/VPW, ISO 9141-2, ISO 14230-4 KWP2000, and CAN transparently, and Mode 01/03/09 decoding is identical at the application layer regardless of which one a vehicle actually uses. Widening coverage from 2008+ to 1996+ was a documentation/scope change, not a core code change.

> **Ford note:** Ford splits data across the standard diagnostic bus and a proprietary MS-CAN (body/comfort systems). A basic ELM327 only has visibility into the standard bus — Cypher-DDS does not attempt to bridge MS-CAN in v1.

> **Dodge/Chrysler note:** Some Chrysler-group vehicles also run a proprietary SCI/CCD bus for body and instrument-cluster diagnostics, separate from the standard OBD2 pins a basic ELM327 talks to. Like Ford's MS-CAN, that's out of scope for v1 — Cypher-DDS only reaches what's on the standard, federally-mandated OBD2 protocol.

**Explicitly out of scope for now:** VAG, BMW, Mercedes (require UDS/ISO 14229 session handling — a different architecture), and anything pre-1996 (before the OBD-II mandate).

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for a module-by-module implemented-vs-stubbed breakdown.

## Bi-directional support

Cypher-DDS now has a cross-make bi-directional framework, but support is intentionally staged.

Implemented across all current makes:

- action discovery through the session/profile layer
- explicit confirmation for mutating actions
- seed executable service actions:
  - clear emissions DTCs
  - tester present
  - enter extended diagnostic session
- first OEM-specific enhanced-data actions:
  - GM transmission fluid temperature read (`221940`)
  - Ford transmission fluid temperature read (`221E1C`)
  - Ford engine oil temperature read (`221310`)

Declared but not yet executable across all current makes:

- powertrain output control
- body control coding
- transmission adaptation reset
- ABS bleed service
- EPB service mode

Explicitly blocked:

- module programming / firmware flashing

This split is deliberate. Generic OBD-II plus ELM327 is enough for the current diagnostic feature set and seed service actions. It is not enough to honestly claim full cross-OEM coding, active tests, or programming without make/ECU-specific implementations, transport upgrades, and safety controls.

## Getting started

```bash
git clone https://github.com/DaRipper91/Cypher-DDS.git
cd Cypher-DDS
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite (pure decode-logic tests, no hardware required):

```bash
pytest
```

Launch the TUI — with no flags it connects to the mock adapter automatically:

```bash
cypher-dds
```

Once connected (mock or real), the dashboard runs the full init → VIN → profile-resolution → DTC-read → live-PID-read flow automatically; press `r` to re-read DTCs and live data on demand.

### Developing without a car

You don't need to be plugged into a vehicle to work on this. `cypher_dds.core.mock_adapter.MockELM327Adapter` implements the same interface as a real serial connection, so the whole stack — serial layer, ELM327 commands, PID/DTC/VIN decoding, the TUI — is developable and testable against canned responses alone. `cypher-dds` uses it by default; pass `--mock-scenario no_adapter` to preview the disconnected state, or `--mock-scenario malformed_vin` for a bad-VIN response.

### Connecting real hardware

On Linux, USB ELM327 adapters typically enumerate as:

- `/dev/ttyUSB*` — CH340-based clones
- `/dev/ttyACM*` — FTDI / native USB-serial

Point the TUI at one directly:

```bash
cypher-dds --port /dev/ttyUSB0
```

Or connect over Bluetooth (Linux only — pair the adapter via your OS's Bluetooth settings first, this doesn't do pairing itself):

```bash
cypher-dds --bluetooth AA:BB:CC:DD:EE:FF
```

## Other platforms

Cypher-DDS is developed and tested as a Linux terminal app first. Three other build targets exist, all produced by GitHub Actions rather than locally (PyInstaller has to run on the target OS, and Buildozer needs a full Android SDK/NDK toolchain — neither is available in this project's dev environment). All three workflows have been pushed and watched through to a **confirmed green CI build**, not just written and assumed to work:

- **Windows `.exe`** — [`.github/workflows/build-windows.yml`](.github/workflows/build-windows.yml) now builds both the Textual TUI and the Tkinter desktop GUI with PyInstaller on a `windows-latest` runner. Build artifacts exist, but **neither Windows binary has been launched on a real Windows machine yet**.
- **Linux `.AppImage`** — [`.github/workflows/build-linux.yml`](.github/workflows/build-linux.yml) now builds AppImages for both the TUI and the Tkinter desktop GUI on `ubuntu-22.04`. No macOS build; not a currently supported target. Runtime validation of the GUI AppImage is still pending on a real desktop environment.
- **Android `.apk`** — [`.github/workflows/build-android.yml`](.github/workflows/build-android.yml) packages `cypher_dds.mobile`, the Kivy Android app, via the official `kivy/buildozer` Docker image. The app now has an Android Bluetooth transport path in code (`pyjnius` → `android.bluetooth.BluetoothSocket`), but **this is still not real-device validated**: CI packaging succeeding means it built, not that it runs correctly on a phone or talks successfully to a real adapter.

All three artifacts are uploaded as workflow run artifacts on every push to `main` (grab those from the [Actions tab](../../actions) if you want a build off an untagged commit), but for a normal download, use the [Releases page](../../releases) — see the download table at the top of this README.

## Project layout

```
Cypher-DDS/
├── pyproject.toml
├── PROJECT_STATUS.md        # what's implemented vs. stubbed, updated as work lands
├── main.py                  # Buildozer/Android entry point (delegates to src/)
├── buildozer.spec           # Android (Kivy) packaging config
├── cypher-dds.spec          # PyInstaller (Windows/desktop) packaging config
├── .github/workflows/       # CI: build-windows.yml, build-linux.yml, build-android.yml
├── src/cypher_dds/
│   ├── core/                # brand-agnostic: serial (USB + Bluetooth), ELM327, PIDs, DTCs, VIN, actions
│   ├── session.py           # framework-agnostic orchestration both UIs drive
│   ├── theme.py             # shared brand accent colors (Royal Blue / Cherry Red)
│   ├── profiles/            # brand plugins + ECU-family catalogs: GM, Ford, Dodge/Chrysler, Toyota/Lexus, Honda/Acura, Kia
│   ├── gui/                 # Tkinter desktop GUI
│   ├── tui/                 # Textual dashboard (desktop)
│   └── mobile/              # Kivy app (Android)
└── tests/                   # decode-logic + session + UI tests — no hardware needed
```

## Adding a new brand

A profile is a small subclass plus a registration call — nothing else in the codebase changes:

```python
from cypher_dds.profiles.base import VehicleProfile, EnhancedPID, register_profile

class MyBrandProfile(VehicleProfile):
    key = "my_brand"
    display_name = "My Brand"
    wmi_codes = ("1MB",)  # VIN prefixes used for auto-detection

    def get_dtc_description(self, code: str) -> str | None:
        return {"P1234": "Something manufacturer-specific"}.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ()

register_profile(MyBrandProfile())
```

Profiles can also expose bi-directional action catalogs and ECU-family metadata through the base interface. The current built-in set is GM, Ford, Dodge/Chrysler, Toyota/Lexus, Honda/Acura, and Kia.

## Roadmap

Tracked in detail in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Done: the whole core read-oriented layer (USB + Bluetooth serial transport, ELM327 command framing, Mode 01/03/04/09 decode), DTC tables for GM/Ford/Dodge-Chrysler/Toyota-Lexus/Honda-Acura, Kia profile and VIN/WMI routing, a small verified set of GM/Ford enhanced PIDs, a NHTSA-derived `WMI_TABLE`, the Textual dashboard wired end to end to real core state via `cypher_dds.session`, a Tkinter desktop GUI MVP, an Android Bluetooth transport path in code, and the first cross-make bi-directional action framework with the first OEM-specific enhanced-data action pack. Next: validate the desktop GUI artifacts on real machines, validate Android Bluetooth on a physical device, build a stronger UDS/transport layer, and expand OEM-specific action coverage beyond enhanced reads.

## Safety

Reading data is inert. Clearing DTCs (Mode 04) resets your vehicle's readiness monitors, which can affect emissions testing until they recomplete a drive cycle — know what you're doing before you clear codes on a car you need inspected soon.

Any future bi-directional functions that move actuators, reset adaptations, or alter coding are safety-sensitive by default. Cypher-DDS now enforces explicit confirmation for mutating actions at the session layer, and module programming remains deliberately blocked.

## License

MIT
