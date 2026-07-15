"""Cypher-DDS mobile (Android) presentation layer — Kivy over DiagnosticSession.

Same architectural role as cypher_dds.tui: presentation-only, no protocol
logic of its own. Packaged into an APK by .github/workflows/build-android.yml
via Buildozer; see cypher_dds.mobile.app for the real caveats (Android
Bluetooth isn't implemented, and none of this has been run on a physical
device or emulator — only the CI packaging step is actually verified).
"""
