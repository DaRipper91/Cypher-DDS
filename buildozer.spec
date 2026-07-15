[app]

# Buildozer config for the Cypher-DDS Android app.
# Built by .github/workflows/build-android.yml via ArtemSBulgakov/buildozer-action
# on a GitHub Actions ubuntu-latest runner — there's no Android SDK/NDK in
# this repo's dev environment, so that CI run is the real build step.
# See src/cypher_dds/mobile/app.py's module docstring for what's NOT yet
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
requirements = python3,kivy,pyserial

orientation = portrait
fullscreen = 0

# Bluetooth permissions are declared for when a real Android Bluetooth
# backend lands (see app.py docstring) — not used by anything yet.
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN

android.api = 34
android.minapi = 23
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
