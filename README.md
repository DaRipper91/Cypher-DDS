<div align="center">

# Cypher-DDS

**A terminal-first diagnostic tool for talking to your car over a USB ELM327 adapter.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](#license)
[![Status](https://img.shields.io/badge/status-core%20layer%20implemented-yellow)](PROJECT_STATUS.md)

Live PID data. Diagnostic trouble codes. VIN decoding. No cloud, no app store, no subscription — just your laptop, a cable, and the OBD2 port under your dash.

</div>

---

## What it does

Plug a USB ELM327 (or ELM327-clone / STN11xx) adapter into your car's OBD2 port and into your machine, and Cypher-DDS will:

- Auto-detect and connect over serial, initialize the ELM327 chip, and auto-detect the vehicle's protocol
- Stream **live data** — RPM, speed, coolant temp, throttle position, and more — into a live-updating terminal dashboard
- Read and clear **diagnostic trouble codes (DTCs)**, with brand-aware descriptions where available
- Pull and decode the **VIN**, using it to auto-select the right vehicle profile

It works on any standard CAN-bus OBD2 vehicle out of the box, and gets smarter about specific brands through a plugin system — see [Architecture](#architecture) below.

## Why

Every OBD2 app on the market either wants a subscription, phones data home, or hides basic PID access behind a paywall. Cypher-DDS is local-only: it talks directly to the adapter over serial, decodes everything itself, and answers to nobody. It's also meant to be a tool you can actually read — small, brand-agnostic core, inspectable decoding logic, no black boxes.

## Architecture

Two layers, deliberately kept apart:

```
┌────────────────────────────────────────────────────────────┐
│  cypher_dds.tui                                             │
│  Textual dashboard — connection status, live PIDs, DTC panel│
└───────────────────────────┬───────────────────────────────-┘
                             │  talks only to public interfaces
┌───────────────────────────▼──────────────────────────────-─┐
│  cypher_dds.core            (brand-agnostic)                │
│  serial transport → ELM327 AT layer → Mode 01/03/04/09      │
│  Works on any CAN-bus OBD2 vehicle with zero brand code.     │
└───────────────────────────┬──────────────────────────────-─┘
                             │  optionally consulted for
                             │  DTC descriptions / enhanced PIDs
┌───────────────────────────▼──────────────────────────────-─┐
│  cypher_dds.profiles        (brand-specific plugins)        │
│  GM · Ford · Dodge/Chrysler · Toyota/Lexus · Honda/Acura     │
│  Each is a self-contained module. New brand = new module,    │
│  zero changes to core.                                       │
└───────────────────────────────────────────────────────────-┘
```

**Core never imports from profiles or the TUI.** A profile can be selected manually or picked automatically from the decoded VIN's WMI. The TUI only talks to core's public interfaces, so a GUI could sit next to it later without touching any protocol logic.

## Supported vehicles

| Brand | Years | Bus | Status |
|---|---|---|---|
| GM | 2008+ | CAN, 11-bit | 🚧 in progress |
| Ford | 2008+ | CAN | 🚧 in progress — see note below |
| Dodge / Chrysler | 2008+ | CAN | 🚧 in progress |
| Toyota / Lexus | 2008+ | CAN | 🌱 stub (proves the plugin interface) |
| Honda / Acura | 2008+ | CAN | 🌱 stub (proves the plugin interface) |

> **Ford note:** Ford splits data across the standard diagnostic CAN bus and a proprietary MS-CAN (body/comfort systems). A basic ELM327 only has visibility into standard CAN — Cypher-DDS does not attempt to bridge MS-CAN in v1.

**Explicitly out of scope for now:** VAG, BMW, Mercedes (require UDS/ISO 14229 session handling — a different architecture), and anything pre-2008 or non-CAN (ISO9141, KWP2000, J1850).

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

Launch the TUI:

```bash
cypher-dds
```

### Developing without a car

You don't need to be plugged into a vehicle to work on this. `cypher_dds.core.mock_adapter.MockELM327Adapter` implements the same interface as a real serial connection, so the whole stack — serial layer, ELM327 commands, PID/DTC/VIN decoding, the TUI — is developable and testable against canned responses alone.

### Connecting real hardware

On Linux, USB ELM327 adapters typically enumerate as:

- `/dev/ttyUSB*` — CH340-based clones
- `/dev/ttyACM*` — FTDI / native USB-serial

## Project layout

```
Cypher-DDS/
├── pyproject.toml
├── PROJECT_STATUS.md        # what's implemented vs. stubbed, updated as work lands
├── src/cypher_dds/
│   ├── core/                # brand-agnostic: serial, ELM327, PIDs, DTCs, VIN
│   ├── profiles/            # brand plugins: GM, Ford, Dodge/Chrysler, Toyota/Lexus, Honda/Acura
│   └── tui/                 # Textual dashboard
└── tests/                   # decode-logic tests — no hardware needed
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

The Toyota/Lexus and Honda/Acura profiles are intentionally empty stubs today, included specifically to prove this interface holds up before their tables get filled in.

## Roadmap

Tracked in detail in [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Done: serial transport, ELM327 command framing, Mode 01 PID decode math, Mode 03/04 DTC decode. Next: Mode 09 VIN decode, then filling in GM/Ford/Dodge DTC and enhanced-PID tables, then wiring the Textual dashboard up to live data.

## Safety

Reading data is inert. Clearing DTCs (Mode 04) resets your vehicle's readiness monitors, which can affect emissions testing until they recomplete a drive cycle — know what you're doing before you clear codes on a car you need inspected soon.

## License

MIT
