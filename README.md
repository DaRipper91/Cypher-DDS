<div align="center">

# Cypher-DDS

**A terminal-first diagnostic tool for talking to your car over a USB or Bluetooth ELM327 adapter.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)
[![Status](https://img.shields.io/badge/status-core%20layer%20implemented-yellow)](PROJECT_STATUS.md)

Live PID data. Diagnostic trouble codes. VIN decoding. No cloud, no app store, no subscription — just your laptop, a cable, and the OBD2 port under your dash.

</div>

---

## What it does

Plug a USB ELM327 (or ELM327-clone / STN11xx) adapter into your car's OBD2 port — or pair one over Bluetooth on Linux — and Cypher-DDS will:

- Connect over serial (USB or Bluetooth RFCOMM), initialize the ELM327 chip, and auto-detect the vehicle's protocol
- Stream **live data** — RPM, speed, coolant temp, throttle position, and more
- Read **diagnostic trouble codes (DTCs)**, with brand-aware descriptions where available
- Pull and decode the **VIN**, using it to auto-select the right vehicle profile

It works on any standard OBD2 vehicle (1996+, any protocol — J1850, ISO 9141-2, KWP2000, or CAN) out of the box, and gets smarter about specific brands through a plugin system — see [Architecture](#architecture) below. The terminal UI is the primary, most-tested interface; an Android app exists as an early demo (mock-adapter only for now — see [Other platforms](#other-platforms)).

## Why

Every OBD2 app on the market either wants a subscription, phones data home, or hides basic PID access behind a paywall. Cypher-DDS is local-only: it talks directly to the adapter over serial, decodes everything itself, and answers to nobody. It's also meant to be a tool you can actually read — small, brand-agnostic core, inspectable decoding logic, no black boxes.

## Architecture

Four layers, deliberately kept apart:

```
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  cypher_dds.tui               │  │  cypher_dds.mobile            │
│  Textual dashboard (desktop)  │  │  Kivy app (Android)           │
└───────────────┬──────────────┘  └───────────────┬──────────────┘
                 │        both drive the same session layer        │
                 └───────────────────────┬──────────────────────---┘
                             ┌───────────▼────────────┐
                             │  cypher_dds.session      │
                             │  connect → VIN/profile → │
                             │  DTC-read → live-PID-read│
                             │  Framework-agnostic — no │
                             │  UI code of its own.      │
                             └───────────┬────────────-─┘
                             │  optionally consulted for
                             │  DTC descriptions / enhanced PIDs
┌───────────────────────────▼──────────────────────────────-─┐
│  cypher_dds.profiles        (brand-specific plugins)        │
│  GM · Ford · Dodge/Chrysler · Toyota/Lexus · Honda/Acura     │
│  Each is a self-contained module. New brand = new module,    │
│  zero changes to core.                                       │
└───────────────────────────┬──────────────────────────────-─┘
                             │  talks only to public interfaces
┌───────────────────────────▼──────────────────────────────-─┐
│  cypher_dds.core            (brand-agnostic)                │
│  USB/Bluetooth serial transport → ELM327 AT layer →          │
│  Mode 01/03/04/09. Works on any OBD2 vehicle, any protocol,  │
│  with zero brand code.                                        │
└───────────────────────────────────────────────────────────-┘
```

**Core never imports from profiles or a presentation layer.** A profile can be selected manually or picked automatically from the decoded VIN's WMI. Both the TUI and the mobile app talk only to `cypher_dds.session`'s public interface — neither re-implements connect/VIN/DTC/PID logic, and a future desktop GUI would slot in the exact same way, no protocol logic duplicated a third time.

## Supported vehicles

1996 is the year the US OBD-II mandate took effect, so it's Cypher-DDS's floor:

| Brand | Years | Bus | Status |
|---|---|---|---|
| GM | 1996+ | J1850 VPW (1996–2007ish) → CAN (2008+) | 🚧 DTC table done (402 P1xxx codes) + 1 enhanced PID |
| Ford | 1996+ | J1850 PWM (1996–2007ish) → CAN (2008+) | 🚧 DTC table done (410 P1xxx codes, incl. Power Stroke diesel) + 2 enhanced PIDs — see note below |
| Dodge / Chrysler | 1996+ | ISO 9141-2 / ISO 14230-4 KWP (1996–2007ish) → CAN (2008+) | 🚧 DTC table done (97 P1xxx codes, incl. diesel/CNG); enhanced PIDs pending — see note below |
| Toyota / Lexus | 1996+ | ISO 9141-2 / ISO 14230-4 KWP → CAN | 🚧 DTC table done (44 P1xxx codes); enhanced PIDs pending |
| Honda / Acura | 1996+ | ISO 9141-2 / ISO 14230-4 KWP → CAN | 🚧 DTC table done (94 P1xxx codes); enhanced PIDs pending |

Cypher-DDS never hardcodes a protocol — the ELM327's `ATSP0` auto-detect handles J1850 PWM/VPW, ISO 9141-2, ISO 14230-4 KWP2000, and CAN transparently, and Mode 01/03/09 decoding is identical at the application layer regardless of which one a vehicle actually uses. Widening coverage from 2008+ to 1996+ was a documentation/scope change, not a core code change.

> **Ford note:** Ford splits data across the standard diagnostic bus and a proprietary MS-CAN (body/comfort systems). A basic ELM327 only has visibility into the standard bus — Cypher-DDS does not attempt to bridge MS-CAN in v1.

> **Dodge/Chrysler note:** Some Chrysler-group vehicles also run a proprietary SCI/CCD bus for body and instrument-cluster diagnostics, separate from the standard OBD2 pins a basic ELM327 talks to. Like Ford's MS-CAN, that's out of scope for v1 — Cypher-DDS only reaches what's on the standard, federally-mandated OBD2 protocol.

**Explicitly out of scope for now:** VAG, BMW, Mercedes (require UDS/ISO 14229 session handling — a different architecture), and anything pre-1996 (before the OBD-II mandate).

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for a module-by-module implemented-vs-stubbed breakdown.

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

- **Windows `.exe`** — [`.github/workflows/build-windows.yml`](.github/workflows/build-windows.yml) packages the exact same Textual TUI with PyInstaller on a `windows-latest` runner. No separate Windows codebase; it's the identical app. Build confirmed green (14.7MB artifact) — **not yet launched on a real Windows machine**.
- **Linux `.AppImage`** — [`.github/workflows/build-linux.yml`](.github/workflows/build-linux.yml) wraps the same PyInstaller TUI binary as the Windows build into a single-file AppImage on `ubuntu-22.04` (older glibc, so it runs on more distros than a `ubuntu-latest` build would), covering the major distro families — Ubuntu, Fedora, Arch, Debian, openSUSE, etc. — without maintaining separate `.deb`/`.rpm`/pacman packages. No macOS build; not a currently supported target. Build confirmed green (23.7MB artifact) — **not yet run outside CI**, not even locally in this dev environment.
- **Android `.apk`** — [`.github/workflows/build-android.yml`](.github/workflows/build-android.yml) packages `cypher_dds.mobile`, a separate minimal Kivy app (Textual can't run inside an Android app the way it can in a real terminal), via the official `kivy/buildozer` Docker image. Build confirmed green (21.4MB debug APK) after fixing three real upstream issues along the way (a broken third-party build action, an unattended SDK license prompt, and a CPython-3.14-vs-old-Android bionic incompatibility — see `PROJECT_STATUS.md` for details). **This is still an early demo, not a finished mobile app**: CI packaging succeeding means it built, not that it runs correctly on a phone — it's never been installed on a real device or emulator, and it has no working Bluetooth backend yet (Android needs a `pyjnius`-based backend that isn't written), which matters a lot since Bluetooth is realistically the only way a phone talks to a car's OBD2 port.

All three artifacts are uploaded as workflow run artifacts on every push to `main`; grab them from the [Actions tab](../../actions).

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
│   ├── core/                # brand-agnostic: serial (USB + Bluetooth), ELM327, PIDs, DTCs, VIN
│   ├── session.py           # framework-agnostic orchestration both UIs drive
│   ├── theme.py             # shared brand accent colors (Royal Blue / Cherry Red)
│   ├── profiles/            # brand plugins: GM, Ford, Dodge/Chrysler, Toyota/Lexus, Honda/Acura
│   ├── tui/                 # Textual dashboard (desktop)
│   └── mobile/               # Kivy app (Android)
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

Toyota/Lexus and Honda/Acura started as intentionally empty stubs, included specifically to prove this interface holds up before their tables got filled in — all five brands now carry real DTC data, validating that the plugin architecture scales without any core changes.

## Roadmap

Tracked in detail in [`PROJECT_STATUS.md`](PROJECT_STATUS.md), including a full planned-features backlog for both UIs. Done: the whole core layer (USB + Bluetooth serial transport, ELM327 command framing, Mode 01/03/04/09 decode), DTC tables for all five brands (GM 402, Ford 410, Dodge/Chrysler 97, Toyota/Lexus 44, Honda/Acura 94 P1xxx codes), a small verified set of GM/Ford enhanced PIDs, a 353-entry `WMI_TABLE` from NHTSA's public vPIC database, the Textual dashboard wired end to end to real core state via the new `cypher_dds.session` layer, and CI-built Windows/Android packages. Next: a real Android Bluetooth backend, installing both packaged artifacts on actual hardware to verify them beyond CI, and enhanced PIDs/B/C/U codes across all five brands.

## Safety

Reading data is inert. Clearing DTCs (Mode 04) resets your vehicle's readiness monitors, which can affect emissions testing until they recomplete a drive cycle — know what you're doing before you clear codes on a car you need inspected soon.

## License

MIT
