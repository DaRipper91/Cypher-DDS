# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python package laid out under `src/cypher_dds/`. The core OBD2/ELM327 logic lives in `src/cypher_dds/core/`, brand-specific vehicle profiles are in `src/cypher_dds/profiles/`, the shared session orchestration is in `src/cypher_dds/session.py`, and the desktop TUI is in `src/cypher_dds/tui/`. Android/Kivy code lives in `src/cypher_dds/mobile/`. Tests are in `tests/`, and packaging files such as `pyproject.toml`, `cypher-dds.spec`, and `buildozer.spec` sit at the repo root.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local environment.
- `pip install -e ".[dev]"`: install the package with test and lint tooling.
- `pytest`: run the test suite. Tests are designed to run without vehicle hardware.
- `cypher-dds`: launch the terminal UI using the default mock adapter.
- `cypher-dds --port /dev/ttyUSB0`: connect to a real USB adapter on Linux.
- `cypher-dds --bluetooth AA:BB:CC:DD:EE:FF`: connect over Bluetooth RFCOMM on Linux.

## Coding Style & Naming Conventions
Use Python 3.10+ syntax, 4-space indentation, and `snake_case` for functions, modules, and test names. Keep classes in `PascalCase`. Follow the existing style: small focused modules, explicit imports, and short docstrings only where they add clarity. `ruff` is the configured linting target; keep code compatible with it before submitting changes.

## Testing Guidelines
Place tests in `tests/` and name them `test_*.py`. Prefer deterministic tests that use the mock adapter or canned decode data instead of hardware. When adding protocol, profile, or session logic, add or update unit tests alongside the code path you changed. Run `pytest` before opening a pull request.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit messages such as `Fix Android APK build` or `Add Bluetooth support`. Keep commits focused and descriptive. Pull requests should explain what changed, why it changed, and how it was verified. Include screenshots or terminal output when UI behavior changes, and link any related issue or release note when relevant.

## Security & Configuration Tips
Do not commit real VINs, adapter identifiers, or other vehicle-specific data unless it is synthetic test data. Clearing DTCs can affect readiness monitors, so treat any Mode 04 behavior as safety-sensitive.
