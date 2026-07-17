"""Cypher-DDS Textual dashboard: connection status, live PID readout, DTC panel.

Presentation-only — all connect/VIN/DTC/PID orchestration lives in
cypher_dds.session.DiagnosticSession, so a future cypher_dds.gui can drive
the exact same logic without re-implementing it. Blocking serial I/O still
runs in a worker thread via App.run_worker(thread=True) — Textual's UI
thread must never block on a 2-second pyserial read timeout. Workers
report back to the UI thread with App.call_from_thread().
"""

from __future__ import annotations

import argparse

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

import cypher_dds.profiles  # noqa: F401 — importing this registers all built-in vehicle profiles
from cypher_dds.profiles.base import VehicleProfile
from cypher_dds.session import DEFAULT_LIVE_PIDS, DiagnosticSession
from cypher_dds.core.vin import VINInfo
from cypher_dds.theme import CHERRY_RED, ROYAL_BLUE


class ConnectionStatusWidget(Static, can_focus=True):
    """Connection status badge — Royal Blue means connected/live."""

    connected: reactive[bool] = reactive(False)
    protocol: reactive[str | None] = reactive(None)

    def watch_connected(self, connected: bool) -> None:
        self.set_class(connected, "-connected")
        self.set_class(not connected, "-disconnected")
        self._refresh_label()

    def watch_protocol(self, _protocol: str | None) -> None:
        self._refresh_label()

    def _refresh_label(self) -> None:
        if not self.connected:
            self.update("○ NO ADAPTER")
        elif self.protocol:
            self.update(f"● LIVE — {self.protocol}")
        else:
            self.update("● LIVE")


class DTCPanelWidget(Static, can_focus=True):
    """DTC alert badge — Cherry Red means one or more codes are stored."""

    codes: reactive[tuple[str, ...]] = reactive(())

    def watch_codes(self, codes: tuple[str, ...]) -> None:
        self.set_class(len(codes) > 0, "-alert")
        if codes:
            self.update(f"⚠ {len(codes)} DTC(S): {', '.join(codes)}")
        else:
            self.update("✓ NO CODES STORED")


class CypherDDSApp(App):
    """Root Textual application."""

    TITLE = "Cypher-DDS"

    BINDINGS = [
        Binding("r", "refresh", "Refresh DTCs + live data"),
    ]

    # Royal Blue and Cherry Red are the app's two reserved status accents
    # (see cypher_dds.theme) — everything else stays on Textual's
    # default theme so these two keep standing out.
    CSS = f"""
    #status-row {{
        height: auto;
        padding: 1 2;
    }}

    ConnectionStatusWidget, DTCPanelWidget {{
        width: auto;
        height: auto;
        padding: 0 2;
        margin-right: 2;
        text-style: bold;
        border: round $panel-lighten-1;
    }}

    ConnectionStatusWidget.-connected {{
        color: {ROYAL_BLUE};
        border: round {ROYAL_BLUE};
    }}
    ConnectionStatusWidget.-disconnected {{
        color: $text-muted;
    }}

    DTCPanelWidget.-alert {{
        color: {CHERRY_RED};
        border: round {CHERRY_RED};
    }}

    ConnectionStatusWidget:focus, DTCPanelWidget:focus {{
        border: round {ROYAL_BLUE};
    }}

    #vehicle-info, #live-data {{
        padding: 0 2;
    }}
    """

    def __init__(
        self,
        port: str | None = None,
        mock_scenario: str = "default",
        bluetooth_address: str | None = None,
        bluetooth_channel: int | None = None,
    ) -> None:
        super().__init__()
        self._port = port
        self._mock_scenario = mock_scenario
        self._bluetooth_address = bluetooth_address
        self._bluetooth_channel = bluetooth_channel
        self._session = DiagnosticSession()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._connecting_message(), id="intro")
        with Horizontal(id="status-row"):
            yield ConnectionStatusWidget(
                "○ NO ADAPTER", id="connection-status", classes="-disconnected"
            )
            yield DTCPanelWidget("✓ NO CODES STORED", id="dtc-panel")
        yield Static("VIN: —", id="vehicle-info")
        yield Static(self._live_data_placeholder(), id="live-data")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._connect, thread=True, exclusive=True, group="connect")

    def action_refresh(self) -> None:
        if self._session.connected:
            self.run_worker(self._refresh_dtcs_and_pids, thread=True, group="refresh")

    # ── worker-thread methods (blocking serial I/O only, no UI access) ──────

    def _connect(self) -> None:
        try:
            protocol = self._session.connect(
                port=self._port,
                mock_scenario=self._mock_scenario,
                bluetooth_address=self._bluetooth_address,
                bluetooth_channel=self._bluetooth_channel,
            )
        except Exception as exc:  # noqa: BLE001 — top-level I/O boundary; report, don't crash
            self.call_from_thread(self._on_connect_failed, str(exc))
            return

        self.call_from_thread(self._on_connected, protocol)

        vin_info = self._session.resolve_vehicle()
        self.call_from_thread(self._on_vin_resolved, vin_info, self._session.profile)

        self._refresh_dtcs_and_pids()

    def _refresh_dtcs_and_pids(self) -> None:
        codes: tuple[str, ...] = ()
        try:
            dtcs = self._session.read_dtcs()
            codes = tuple(d.code for d in dtcs)
        except Exception:  # noqa: BLE001 — a bad DTC read shouldn't crash the dashboard
            pass
        self.call_from_thread(self._on_dtcs_resolved, codes)

        values = self._session.read_live_data()
        self.call_from_thread(self._on_pid_values, values)

    # ── UI-thread callbacks (safe to touch widgets) ─────────────────────────

    def _on_connect_failed(self, error: str) -> None:
        self.query_one("#intro", Static).update(f"Connection failed: {error}")

    def _on_connected(self, protocol: str) -> None:
        status = self.query_one("#connection-status", ConnectionStatusWidget)
        status.connected = True
        status.protocol = protocol
        self.query_one("#intro", Static).update("Connected. Reading VIN and DTCs…")

    def _on_vin_resolved(self, vin_info: VINInfo | None, profile: VehicleProfile | None) -> None:
        if vin_info is None:
            text = "VIN: unavailable"
        elif profile is not None:
            text = f"VIN: {vin_info.vin} → {profile.display_name}"
        else:
            text = f"VIN: {vin_info.vin} → unrecognized manufacturer (WMI {vin_info.wmi})"
        self.query_one("#vehicle-info", Static).update(text)

    def _on_dtcs_resolved(self, codes: tuple[str, ...]) -> None:
        self.query_one("#dtc-panel", DTCPanelWidget).codes = codes
        self.query_one("#intro", Static).update("Live.")

    def _on_pid_values(self, values: dict[int, float | None]) -> None:
        parts = []
        for pid, label, unit in DEFAULT_LIVE_PIDS:
            value = values.get(pid)
            parts.append(f"{label}: {value:.0f} {unit}" if value is not None else f"{label}: —")
        self.query_one("#live-data", Static).update("   ".join(parts))

    @staticmethod
    def _live_data_placeholder() -> str:
        return "   ".join(f"{label}: —" for _pid, label, _unit in DEFAULT_LIVE_PIDS)

    def _connecting_message(self) -> str:
        if self._bluetooth_address:
            return f"Connecting to {self._bluetooth_address} over Bluetooth…"
        if self._port:
            return f"Connecting to {self._port}…"
        return "Connecting to mock adapter…"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cypher-DDS OBD2 diagnostic TUI")
    parser.add_argument(
        "--port",
        help="Serial port to connect to (e.g. /dev/ttyUSB0). Omit to use the mock adapter.",
    )
    parser.add_argument(
        "--bluetooth",
        metavar="MAC",
        help=(
            "Connect to a paired ELM327 over Bluetooth RFCOMM by MAC address "
            "instead of USB (Linux-only; pair the device via the OS first)."
        ),
    )
    parser.add_argument(
        "--bluetooth-channel",
        type=int,
        default=None,
        help="RFCOMM channel to use with --bluetooth (default: 1, the usual SPP channel).",
    )
    parser.add_argument(
        "--mock-scenario",
        default="default",
        help="Mock adapter scenario to use when --port/--bluetooth are omitted (see mock_adapter.py).",
    )
    args = parser.parse_args()
    if args.port and args.bluetooth:
        parser.error("--port and --bluetooth are mutually exclusive")
    CypherDDSApp(
        port=args.port,
        mock_scenario=args.mock_scenario,
        bluetooth_address=args.bluetooth,
        bluetooth_channel=args.bluetooth_channel,
    ).run()


if __name__ == "__main__":
    main()
