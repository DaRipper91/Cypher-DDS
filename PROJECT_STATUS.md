# Cypher-DDS — Project Status

The core layer (serial, ELM327, PIDs, DTC, VIN) is fully implemented and
tested against a mock adapter, all five v1 brands carry real DTC data, and
the connect/VIN/DTC/PID orchestration logic lives in one framework-agnostic
place (`cypher_dds.session`) that both the TUI and the new mobile app drive.
Remaining work is enhanced PIDs, B/C/U codes, real-hardware validation, and
UI polish across both presentation layers. Update this file as pieces land.

## Core (`cypher_dds.core`) — brand-agnostic

| Module | Purpose | Status |
|---|---|---|
| `serial_conn.py` | Port discovery (`/dev/ttyUSB*`/`/dev/ttyACM*`), USB connect/disconnect, byte-level read-until-prompt framing, `connect_bluetooth()` | done |
| `bluetooth_adapter.py` | `BluetoothSerialAdapter` — RFCOMM/SPP transport via stdlib `socket.AF_BLUETOOTH`. **Linux-only** (that socket family isn't exposed by CPython on macOS/Windows); raises a clear `RuntimeError` there instead of failing obscurely. No SDP auto-discovery — connects to an already-OS-paired device by MAC. Untested against real Bluetooth ELM327 hardware (mocked at the socket layer in tests; no BT OBD2 adapter available in this dev environment — see `PROJECT_STATUS.md` history for what *was* checked). | done (socket-layer tests only) |
| `elm327.py` | AT init sequence, command/response framing, error detection, `ATDPN` protocol name lookup | done |
| `pids.py` | Mode 01 PID table + decode math (RPM, speed, coolant temp, intake temp, MAF, throttle position, fuel level); `read_pid()` issues a request through ELM327 and returns the decoded value | done |
| `dtc.py` | Mode 03/04 DTC read/clear, SAE J2012 byte decode, generic P0xxx table (~40 codes) | done |
| `vin.py` | Mode 09 VIN retrieval, WMI → manufacturer decode | done — `WMI_TABLE` has 353 entries across all 5 brands, sourced from NHTSA's public vPIC database |
| `mock_adapter.py` | `MockELM327Adapter` — canned AT/PID/DTC/VIN responses (`default`, `no_adapter`, `malformed_vin` scenarios) for dev without hardware | done |

## Session layer (`cypher_dds.session`)

`DiagnosticSession` owns connect (USB, Bluetooth, or mock) + VIN/profile
resolution + DTC reads (with brand-fallback descriptions) + live PID reads,
as plain framework-agnostic Python. Both `cypher_dds.tui` and
`cypher_dds.mobile` drive the exact same class rather than each
re-implementing this orchestration — extracted specifically so a second
(and now third) presentation layer wouldn't duplicate it. Fully unit
tested (`test_session.py`) independent of either UI framework. `done`

## Profiles (`cypher_dds.profiles`) — brand-specific

| Profile | Coverage target | Status |
|---|---|---|
| `base.py` | `VehicleProfile` interface + registry | stub |
| `gm.py` | GM, 1996+ (J1850 VPW pre-2008, CAN 2008+) | DTC_TABLE populated (402 P1xxx codes); 1 enhanced PID (trans fluid temp) |
| `ford.py` | Ford, 1996+ (J1850 PWM pre-2008, CAN 2008+). **Only the standard OBD2 bus is reachable via a basic ELM327 — MS-CAN (body/comfort systems) is out of scope for v1.** | DTC_TABLE populated (410 P1xxx codes, incl. Power Stroke diesel); 2 enhanced PIDs (trans fluid temp, engine oil temp) |
| `dodge_chrysler.py` | Dodge/Chrysler, 1996+ (ISO 9141-2/KWP2000 pre-2008, CAN 2008+). The proprietary SCI/CCD body bus is out of scope for v1 (same category as Ford's MS-CAN). | DTC_TABLE populated (97 P1xxx codes, incl. diesel/CNG variants); enhanced PIDs still stub |
| `toyota_lexus.py` | Toyota/Lexus, 1996+ (ISO 9141-2/KWP2000 pre-2008, CAN 2008+) | DTC_TABLE populated (44 P1xxx codes); enhanced PIDs still stub |
| `honda_acura.py` | Honda/Acura, 1996+ (ISO 9141-2/KWP2000 pre-2008, CAN 2008+) | DTC_TABLE populated (94 P1xxx codes); enhanced PIDs still stub |

Protocol selection is fully handled by the ELM327's auto-detect (`ATSP0`) —
`cypher_dds.core` already decodes Mode 01/03/09 identically regardless of
whether the transport is J1850, ISO 9141-2, KWP2000, or CAN, so widening
coverage from 2008+ to 1996+ needed no core changes, only updated scope
docs/profile metadata.

Explicitly out of scope for this phase: VAG, BMW, Mercedes (require UDS/ISO
14229 session handling — architecturally different), and anything
pre-1996 (before the US OBD-II mandate).

**Why DTC tables are large but enhanced-PID tables are small:** SAE J2012
means DTC codes and their meanings show up in consolidated public reference
sites (obd-codes.com, engine-light-help.com, etc.) — hundreds of entries per
brand. SAE J2190 (Mode 22) only standardizes the *mechanism* for enhanced
PIDs, not the PID assignments themselves, so those are scattered across
aftermarket-scanner community forums rather than published anywhere
consolidated. GM/Ford's enhanced-PID lists above are cross-referenced from
multiple independent community sources and kept intentionally small rather
than padded with unverified/conflicting hex codes.

## TUI (`cypher_dds.tui`) — desktop terminal

| Module | Purpose | Status |
|---|---|---|
| `app.py` | Textual app wired to `DiagnosticSession`: connects (real `--port`, `--bluetooth <MAC>`, or mock adapter) in a worker thread so serial I/O never blocks the UI, then runs connect → VIN → profile-resolution → DTC-read → live-PID-read. `r` re-reads DTCs + live data on demand. | done — no continuous auto-polling loop yet (manual refresh only); see planned features |

`cypher_dds.theme` (brand accent colors — Royal Blue = connected/live +
focus, Cherry Red = DTC alert) moved out of `cypher_dds.tui` to the top
level, since `cypher_dds.mobile` needs the same constants and neither
presentation layer should own the other's shared branding.

## Mobile (`cypher_dds.mobile`) — Android, new

| Module | Purpose | Status |
|---|---|---|
| `app.py` | Kivy app wired to the same `DiagnosticSession` as the TUI: connect/VIN/DTC/live-data flow on a background thread, results posted to the main thread via `Clock.schedule_once`. Mock adapter only — see caveats below. | done, **CI packaging confirmed green**, unverified beyond that |

**Real caveats, not hedging:**
- **Never run on a physical Android device or emulator.** This dev
  environment has no Android SDK/toolchain. What's actually verified is
  that `.github/workflows/build-android.yml` successfully *packages* the
  app into a real 21.4MB APK via Buildozer on a GitHub Actions runner
  (confirmed by pushing and watching the run — not assumed). A green CI
  build means "it built," not "it runs correctly on a phone."
- **Android Bluetooth is not implemented.** `BluetoothSerialAdapter` uses
  desktop Linux's `socket.AF_BLUETOOTH` (BlueZ), which Android doesn't
  expose to Python the same way. A real backend needs a `pyjnius` bridge to
  `android.bluetooth.BluetoothSocket` — flagged as a TODO, since it can't
  be verified without a physical device. Since most people don't run a USB
  ELM327 off an Android phone (few support USB-OTG to a car's OBD2 port
  practically), Bluetooth is the *only* connectivity path that will matter
  for a real Android release — this is the actual blocker before the APK
  is more than a demo shell.
- Local headless testing of the Kivy widget tree hit an environment limit
  in this sandbox (no SDL2 window provider on this aarch64 box, only
  `x11`/`pygame` providers attempted and neither available) — confirmed
  `DiagnosticSession`'s logic independently via `test_session.py` instead,
  and left real widget-tree verification to the CI build.

## Packaging / distribution

| Target | Tooling | Workflow | Status |
|---|---|---|---|
| Windows `.exe` | PyInstaller (`cypher-dds.spec`, repo root) — bundles the *existing* TUI app as-is, no new UI code | `.github/workflows/build-windows.yml`, `windows-latest` runner | **CI build confirmed green** (1m17s) — `dist/cypher-dds.exe`, 14.7MB artifact |
| Android `.apk` | Buildozer (`buildozer.spec` + `main.py`, repo root) — packages the new Kivy mobile app; runs the official `ghcr.io/kivy/buildozer` Docker image directly, not the `ArtemSBulgakov/buildozer-action` GitHub Action (see below) | `.github/workflows/build-android.yml`, `ubuntu-latest` runner | **CI build confirmed green** (13m53s cold), 21.4MB debug APK artifact |
| Linux `.AppImage` | PyInstaller (same `cypher-dds.spec` as Windows, same TUI binary) wrapped into a single-file AppImage via `appimagetool`, so it runs unmodified on the major distro families (Ubuntu, Fedora, Arch, Debian, openSUSE, …) with no `.deb`/`.rpm`/pacman packages to maintain separately | `.github/workflows/build-linux.yml`, `ubuntu-22.04` runner (deliberately not `ubuntu-latest` — older glibc runs on more distros) | **CI build confirmed green** (49s) — `dist/cypher-dds-x86_64.AppImage`, 23.7MB artifact |

All three were actually pushed and watched through CI to green, not just
written and assumed to work. The Windows/Android builds hit three real
failures along the way, all external/upstream, not app bugs; the Linux
AppImage build went green on the first push:
1. `ArtemSBulgakov/buildozer-action`'s own Dockerfile layers extra apt
   packages onto the `kivy/buildozer` base image and pulls in
   `ppa:openjdk-r/ppa`, which doesn't have a Release file for that image's
   Ubuntu "resolute" yet — every build failed before even checking out this
   repo. Fixed by driving `ghcr.io/kivy/buildozer` directly (Kivy's own
   documented Docker usage) instead of going through that action.
2. `sdkmanager`'s Android SDK license prompt is interactive; a plain
   `docker run` left it unanswered and build-tools install got skipped.
   Fixed with `yes | docker run --interactive ...`.
3. `python-for-android`'s CPython 3.14 recipe calls `preadv`/`pwritev`
   (`Python/remote_debugging.c`, a 3.13+ remote-debugging feature); Android's
   bionic libc doesn't expose those before API 24. Fixed by bumping
   `android.minapi` from 23 to 24 in `buildozer.spec`.

Windows and Android are CI-built by necessity: PyInstaller must run on the
target OS (no cross-compiling a `.exe` from Linux), and Buildozer needs a
full Android SDK/NDK toolchain this dev environment doesn't have. The Linux
AppImage *could* be built locally (this dev environment is Linux), but runs
in CI too for a clean, reproducible ubuntu-22.04 build rather than whatever
glibc this sandbox happens to have. **What CI green does NOT prove:** none
of the three artifacts has been run on real end-user hardware — the `.exe`
has never been launched on an actual Windows machine, the `.apk` has never
been installed on a physical Android device or emulator, and the AppImage
has never been run outside this CI job (not even locally in this sandbox).
That's the real next verification step for all three — the AppImage is the
cheapest of the three to actually check, since it just needs a Linux
machine with FUSE (or `--appimage-extract-and-run`), not a second OS or
physical device.

## Tests (`tests/`)

65 tests, 0 skipped. `test_pids.py`, `test_elm327.py`, `test_serial_conn.py`,
`test_dtc.py`, `test_vin.py`, and `test_bluetooth_adapter.py` all exercise
real logic against `MockELM327Adapter` (or a mocked socket layer for
Bluetooth): PID decode math (including `read_pid()`), the full ELM327
init/command/protocol-detection flow, DTC byte decoding (all four
letter-prefix cases, padding, error paths), `DTCReader`, WMI decoding
(including non-US manufacturing plants and the Mercedes/DaimlerChrysler
exclusion), `request_vin` (including the malformed-VIN length-validation
path), and the Bluetooth RFCOMM socket wiring (address/channel routing,
timeout handling, the unsupported-platform error path).
`test_profiles.py` locks in real P1xxx lookups for all five brands plus the
GM/Ford enhanced-PID entries. `test_session.py` exercises the full
connect → VIN → DTC → live-data flow as plain Python, independent of
either UI framework. `test_tui_app.py` runs Textual's headless harness
end to end (successful connect + resolution, manual refresh, two
connection-failure paths), awaiting the worker thread via
`app.workers.wait_for_complete()` before asserting UI state. The Kivy
mobile app has no equivalent headless UI test yet (see Mobile caveats).

## Next steps (not yet started)

1. **Real Android Bluetooth backend** (`pyjnius` → `android.bluetooth.BluetoothSocket`)
   — the actual blocker for the Android app being more than a mock-adapter demo.
2. **Install and run both packaged artifacts on real hardware** — the
   `.exe` on an actual Windows machine, the `.apk` on a physical
   Android device. Nothing beyond CI packaging has been verified for either.
3. Add enhanced PIDs and B/C/U-series codes for all five brands where
   documented; keep expanding GM/Ford's existing enhanced-PID entries as
   more are independently confirmed.
4. See "Planned features" below for TUI/GUI feature work once the above
   is solid.

## Planned features (TUI + mobile/GUI)

Not started — a backlog, not commitments. Roughly ordered by how directly
they build on what already exists:

- **Continuous live-data polling** in both UIs (currently manual refresh
  only in both) — needs real hardware to validate a sane polling interval
  against actual ELM327/bus response latency first.
- **Richer DTC view**: full descriptions (not just codes) in a scrollable
  list, plus a "clear codes" (Mode 04) action — gated behind an explicit
  confirmation step given the README's existing Safety note about
  readiness-monitor resets.
- **Freeze frame data** (Mode 02) — same PID table `pids.py` already has,
  different mode; a natural `cypher_dds.core` extension before it's a UI
  feature.
- **Readiness monitor / I|M status** (Mode 01 PID 0x01) — "is this vehicle
  ready for an emissions test" is a very common real-world ask.
- **Manual profile override** in both UIs, for when VIN decode fails or a
  user wants to force a specific brand's DTC table.
- **Export a scan report** (Markdown/JSON) of the current session's
  VIN/DTCs/live data — built from Cypher-DDS's own real data only, unlike
  the ThinkCar-derived report earlier in this project's history.

### Desktop GUI (planned — framework decided, not started)

**Framework: Tkinter**, stdlib — no new dependency (unlike mobile's `kivy`
extra), no LGPL/GPL licensing question (PySide/PyQt), and it packages with
the same PyInstaller toolchain `cypher-dds.spec` already uses for the
Windows `.exe`. Module name: `cypher_dds.gui`, matching the placeholder
already referenced in `session.py`'s and `tui/app.py`'s docstrings.

Plan, in order:

1. **`cypher_dds/gui/app.py`** — a root Tk window driving `DiagnosticSession`
   directly, same architectural role as `tui.app.CypherDDSApp` and
   `mobile.app.CypherDDSMobileApp`: presentation only, zero protocol logic
   duplicated a third time.
2. **Threading**: blocking serial I/O on a plain background thread (same
   pattern as `mobile/app.py`, since Tkinter has no worker abstraction like
   Textual's `run_worker`), posting results back to the UI thread via
   `Tk.after()` — the same role `App.call_from_thread()` and
   `Clock.schedule_once()` play in the other two UIs.
3. **Reuse, don't reinvent**: `DEFAULT_LIVE_PIDS` for the live-data row and
   the `ROYAL_BLUE`/`CHERRY_RED` constants from `cypher_dds.theme` for the
   same connected/DTC-alert status coloring the TUI and mobile app already
   use.
4. **Feature parity first**: connect (USB/Bluetooth/mock), VIN resolve, DTC
   read, manual live-data refresh — matching what TUI/mobile already do —
   before picking up any of the other backlog items above (continuous
   polling, richer DTC view, freeze frame, etc.); those land in all
   presentation layers together, not desktop-first.
5. **Bluetooth comes free on Linux**: unlike `cypher_dds.mobile` (which
   needs an unwritten pyjnius bridge to `android.bluetooth.BluetoothSocket`),
   the desktop GUI can call `core.bluetooth_adapter.BluetoothSerialAdapter`
   directly — it's already implemented for desktop Linux, just unused by
   any UI yet.
6. **Packaging**: extend `cypher-dds.spec` (or add a sibling spec) with a
   second `EXE` entry point at `src/cypher_dds/gui/app.py`,
   `console=False` since it's a real window, and a matching
   `[project.scripts]` entry once the module exists.
7. **CI**: `.github/workflows/build-windows.yml` currently builds and
   uploads only `cypher-dds.exe` (TUI) from `cypher-dds.spec`'s single
   hardcoded `Analysis` entry point — it won't pick up the GUI build for
   free. Once step 6 lands, add a second `pyinstaller`/`upload-artifact`
   step (or a new spec + step) to that workflow so the GUI `.exe` is
   actually built and verified in CI too, same as the TUI one already is.

### Bluetooth beyond Linux (planned — not started)

Today Bluetooth works on exactly one platform: desktop Linux, via
`core.bluetooth_adapter.BluetoothSerialAdapter`'s stdlib
`socket.AF_BLUETOOTH` RFCOMM sockets — already wired into the TUI's
`--bluetooth` flag and (per this file's Desktop GUI section) free for the
planned Tkinter GUI too. Every other platform+UI combination is either
unimplemented or raises `BLUETOOTH_SUPPORTED`'s clear "use USB instead"
`RuntimeError`. Two separate gaps, not one:

1. **Windows/macOS desktop** — `socket.AF_BLUETOOTH` doesn't exist there;
   the docstring in `bluetooth_adapter.py` already flags PyBluez as the
   candidate. That's a real dependency decision to make later, not a clean
   stdlib swap like the GUI framework was: PyBluez's Windows RFCOMM support
   is usable but the project is effectively unmaintained upstream, and its
   macOS backend has been broken for years — so macOS may end up staying
   USB-only (documented, same clear-error pattern already in place) even
   after Windows gets a real backend. Whatever backend lands, it only needs
   to implement `BluetoothSerialAdapter`'s existing `SerialLike` surface
   (`write`/`read`/`readline`/`close`/`in_waiting`/`is_open`) — `SerialConnection`
   and everything above it stays unchanged, same as this file's Desktop GUI
   section describes for the Tkinter work.
2. **Android (`cypher_dds.mobile`)** — needs the pyjnius bridge to
   `android.bluetooth.BluetoothSocket` that `mobile/app.py`'s docstring
   already calls out as unwritten. Same deal: implement the `SerialLike`
   surface once, and `DiagnosticSession`/`SerialConnection` need no changes
   to use it. Can't be verified without a physical Android device, same
   caveat as the rest of `cypher_dds.mobile`.

Neither gap blocks the Desktop GUI plan above — that one ships Linux
Bluetooth on day one and picks up Windows/macOS whenever gap 1 closes,
with no GUI-layer changes required either time.
