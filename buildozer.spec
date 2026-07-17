[app]

# Buildozer config for the Cypher-DDS Android app.
# Built by .github/workflows/build-android.yml, which runs the official
# ghcr.io/kivy/buildozer Docker image directly on a GitHub Actions
# ubuntu-latest runner — there's no Android SDK/NDK in this repo's dev
# environment, so that CI run is the real build step. See
# src/cypher_dds/mobile/app.py's module docstring for what's NOT yet
# verified (never run on a physical device/emulator; no Android Bluetooth
# backend).

title = Cypher-DDS
package.name = cypherdds
package.domain = org.cypherdds

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
# main.py at the repo root pulls in src/ — see that file for why.

version = 0.1.0

# pyserial is imported at module level by cypher_dds.core.serial_conn even
# when only the mock adapter is in use, so it has to be bundled too.
# pyjnius is required for the Android Bluetooth transport bridge.
requirements = python3,kivy,pyserial,pyjnius

orientation = portrait
fullscreen = 0

# Bluetooth permissions are declared for when a real Android Bluetooth
# backend lands (see app.py docstring) — not used by anything yet.
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN

android.api = 34
# 24 (not 23) because python-for-android's CPython 3.14 recipe calls
# preadv/pwritev (Python/remote_debugging.c), which Android's bionic libc
# doesn't expose before API 24 — confirmed via a real CI build failure
# (clang: "call to undeclared function 'preadv'") at minapi 23.
android.minapi = 24
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
