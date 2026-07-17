"""Cypher-DDS mobile (Android) app — Kivy front-end over DiagnosticSession.

Same architectural role as cypher_dds.tui.app.CypherDDSApp: presentation
only, driving cypher_dds.session.DiagnosticSession for every bit of
connect/VIN/DTC/PID logic, so this and the TUI never duplicate that logic.
Background I/O runs on a plain Python thread, posting results back to the
main Kivy thread via Clock.schedule_once() — Kivy's equivalent of Textual's
App.call_from_thread().

IMPORTANT CAVEATS (read before assuming this "just works" on a phone):
  - This has never been run on a physical Android device or emulator —
    there's no Android SDK/toolchain in this repo's dev environment. The
    only verification that exists is .github/workflows/build-android.yml
    successfully *packaging* it into an APK on a GitHub Actions runner.
    A green CI build means "it built," not "it runs correctly on a phone."
  - Bluetooth is NOT implemented here. cypher_dds.core.BluetoothSerialAdapter
    uses desktop Linux's socket.AF_BLUETOOTH (BlueZ), which Android doesn't
    expose to Python the same way — a real Android backend needs a pyjnius
    bridge to android.bluetooth.BluetoothSocket, which isn't written and
    can't be verified without a physical device. This app only connects to
    the mock adapter for now, so it's still fully demoable via CI.
"""

from __future__ import annotations

import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import cypher_dds.profiles  # noqa: F401 — importing this registers all built-in vehicle profiles
from cypher_dds.core.vin import VINInfo
from cypher_dds.session import DEFAULT_LIVE_PIDS, DiagnosticSession
from cypher_dds.theme import CHERRY_RED, ROYAL_BLUE

_MUTED_RGBA = (0.6, 0.6, 0.6, 1.0)


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b, alpha)


_ROYAL_BLUE_RGBA = _hex_to_rgba(ROYAL_BLUE)
_CHERRY_RED_RGBA = _hex_to_rgba(CHERRY_RED)


class CypherDDSMobileApp(App):
    """Root Kivy application."""

    title = "Cypher-DDS"

    def build(self):
        self._session = DiagnosticSession()

        root = BoxLayout(orientation="vertical", padding=16, spacing=8)

        self.status_label = Label(text="○ NO ADAPTER", color=_MUTED_RGBA, size_hint_y=None, height=40)
        self.vehicle_label = Label(text="VIN: —", size_hint_y=None, height=32)
        self.dtc_label = Label(text="✓ NO CODES STORED", color=_MUTED_RGBA, size_hint_y=None, height=40)
        self.live_label = Label(text=self._live_placeholder(), size_hint_y=None, height=32)
        self.refresh_button = Button(text="Refresh", size_hint_y=None, height=48, disabled=True)
        self.refresh_button.bind(on_press=lambda _btn: self._start_refresh())

        for widget in (
            self.status_label,
            self.vehicle_label,
            self.dtc_label,
            self.live_label,
            self.refresh_button,
        ):
            root.add_widget(widget)

        Clock.schedule_once(lambda _dt: self._start_connect(), 0)
        return root

    @staticmethod
    def _live_placeholder() -> str:
        return "   ".join(f"{label}: —" for _pid, label, _unit in DEFAULT_LIVE_PIDS)

    # ── background-thread work (blocking serial I/O only, no UI access) ────

    def _start_connect(self) -> None:
        threading.Thread(target=self._connect, daemon=True).start()

    def _start_refresh(self) -> None:
        if self._session.connected:
            threading.Thread(target=self._refresh, daemon=True).start()

    def _connect(self) -> None:
        try:
            protocol = self._session.connect()  # mock adapter — see module docstring
        except Exception as exc:  # noqa: BLE001 — top-level I/O boundary; report, don't crash
            Clock.schedule_once(lambda _dt: self._on_connect_failed(str(exc)), 0)
            return

        Clock.schedule_once(lambda _dt: self._on_connected(protocol), 0)

        vin_info = self._session.resolve_vehicle()
        Clock.schedule_once(lambda _dt: self._on_vin_resolved(vin_info), 0)

        self._refresh()

    def _refresh(self) -> None:
        codes: tuple[str, ...] = ()
        try:
            dtcs = self._session.read_dtcs()
            codes = tuple(d.code for d in dtcs)
        except Exception:  # noqa: BLE001 — a bad DTC read shouldn't crash the app
            pass
        Clock.schedule_once(lambda _dt: self._on_dtcs_resolved(codes), 0)

        values = self._session.read_live_data()
        Clock.schedule_once(lambda _dt: self._on_pid_values(values), 0)

    # ── main-thread UI updates ──────────────────────────────────────────────

    def _on_connect_failed(self, error: str) -> None:
        self.status_label.text = f"Connection failed: {error}"
        self.status_label.color = _CHERRY_RED_RGBA

    def _on_connected(self, protocol: str) -> None:
        self.status_label.text = f"● LIVE — {protocol}"
        self.status_label.color = _ROYAL_BLUE_RGBA
        self.refresh_button.disabled = False

    def _on_vin_resolved(self, vin_info: VINInfo | None) -> None:
        if vin_info is None:
            self.vehicle_label.text = "VIN: unavailable"
        elif self._session.profile is not None:
            self.vehicle_label.text = f"VIN: {vin_info.vin} → {self._session.profile.display_name}"
        else:
            self.vehicle_label.text = (
                f"VIN: {vin_info.vin} → unrecognized manufacturer (WMI {vin_info.wmi})"
            )

    def _on_dtcs_resolved(self, codes: tuple[str, ...]) -> None:
        if codes:
            self.dtc_label.text = f"⚠ {len(codes)} DTC(S): {', '.join(codes)}"
            self.dtc_label.color = _CHERRY_RED_RGBA
        else:
            self.dtc_label.text = "✓ NO CODES STORED"
            self.dtc_label.color = _MUTED_RGBA

    def _on_pid_values(self, values: dict[int, float | None]) -> None:
        parts = []
        for pid, label, unit in DEFAULT_LIVE_PIDS:
            value = values.get(pid)
            parts.append(f"{label}: {value:.0f} {unit}" if value is not None else f"{label}: —")
        self.live_label.text = "   ".join(parts)


def main() -> None:
    CypherDDSMobileApp().run()


if __name__ == "__main__":
    main()
