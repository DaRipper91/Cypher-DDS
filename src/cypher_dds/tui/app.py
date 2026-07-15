"""Cypher-DDS Textual dashboard: connection status, live PID readout, DTC panel.

All blocking serial I/O (connect, initialize, VIN, DTCs, PIDs) runs in a
worker thread via App.run_worker(thread=True) — Textual's UI thread must
never block on a 2-second pyserial read timeout. Workers report back to the
UI thread with App.call_from_thread().
"""

from __future__ import annotations

import argparse
from dataclasses import replace

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

import cypher_dds.profiles  # noqa: F401 — importing this registers all five vehicle profiles
from cypher_dds.core.dtc import DTC, DTCReader
from cypher_dds.core.elm327 import ELM327
from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.pids import read_pid
from cypher_dds.core.serial_conn import SerialConnection
from cypher_dds.core.vin import VINInfo, request_vin
from cypher_dds.profiles.base import VehicleProfile, get_profile
from cypher_dds.tui.theme import CHERRY_RED, ROYAL_BLUE

# Live PID row: (Mode 01 PID, display label, unit)
LIVE_PIDS: tuple[tuple[int, str, str], ...] = (
    (0x0C, "RPM", "rpm"),
    (0x0D, "Speed", "km/h"),
    (0x05, "Coolant", "°C"),
)


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
    # (see cypher_dds.tui.theme) — everything else stays on Textual's
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

    def __init__(self, port: str | None = None, mock_scenario: str = "default") -> None:
        super().__init__()
        self._port = port
        self._mock_scenario = mock_scenario
        self._elm: ELM327 | None = None
        self._profile: VehicleProfile | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Connecting…" if self._port else "Connecting to mock adapter…",
            id="intro",
        )
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
        if self._elm is not None:
            self.run_worker(self._refresh_dtcs_and_pids, thread=True, group="refresh")

    # ── worker-thread methods (blocking serial I/O only, no UI access) ──────

    def _connect(self) -> None:
        try:
            if self._port:
                connection = SerialConnection()
                connection.connect(self._port)
            else:
                connection = SerialConnection(
                    transport=MockELM327Adapter(scenario=self._mock_scenario)
                )
            elm = ELM327(connection)
            elm.initialize()
        except Exception as exc:  # noqa: BLE001 — top-level I/O boundary; report, don't crash
            self.call_from_thread(self._on_connect_failed, str(exc))
            return

        self._elm = elm
        protocol = elm.detected_protocol()
        self.call_from_thread(self._on_connected, protocol)

        vin_info: VINInfo | None = None
        try:
            vin_info = request_vin(elm)
        except Exception:  # noqa: BLE001 — VIN isn't guaranteed on every ECU; non-fatal
            pass
        profile = get_profile(vin_info.manufacturer) if vin_info and vin_info.manufacturer else None
        self._profile = profile
        self.call_from_thread(self._on_vin_resolved, vin_info, profile)

        self._refresh_dtcs_and_pids()

    def _refresh_dtcs_and_pids(self) -> None:
        if self._elm is None:
            return

        codes: tuple[str, ...] = ()
        try:
            dtcs = DTCReader(self._elm).read_stored()
            dtcs = [self._resolve_description(d) for d in dtcs]
            codes = tuple(d.code for d in dtcs)
        except Exception:  # noqa: BLE001 — a bad DTC read shouldn't crash the dashboard
            pass
        self.call_from_thread(self._on_dtcs_resolved, codes)

        values: dict[int, float | None] = {}
        for pid, _label, _unit in LIVE_PIDS:
            try:
                values[pid] = read_pid(self._elm, pid)
            except Exception:  # noqa: BLE001 — an unsupported PID shouldn't crash the poll
                values[pid] = None
        self.call_from_thread(self._on_pid_values, values)

    def _resolve_description(self, dtc: DTC) -> DTC:
        """Fall back to the selected brand profile when the generic table misses."""
        if dtc.description is not None or self._profile is None:
            return dtc
        brand_description = self._profile.get_dtc_description(dtc.code)
        return replace(dtc, description=brand_description) if brand_description else dtc

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
        for pid, label, unit in LIVE_PIDS:
            value = values.get(pid)
            parts.append(f"{label}: {value:.0f} {unit}" if value is not None else f"{label}: —")
        self.query_one("#live-data", Static).update("   ".join(parts))

    @staticmethod
    def _live_data_placeholder() -> str:
        return "   ".join(f"{label}: —" for _pid, label, _unit in LIVE_PIDS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cypher-DDS OBD2 diagnostic TUI")
    parser.add_argument(
        "--port",
        help="Serial port to connect to (e.g. /dev/ttyUSB0). Omit to use the mock adapter.",
    )
    parser.add_argument(
        "--mock-scenario",
        default="default",
        help="Mock adapter scenario to use when --port is omitted (see mock_adapter.py).",
    )
    args = parser.parse_args()
    CypherDDSApp(port=args.port, mock_scenario=args.mock_scenario).run()


if __name__ == "__main__":
    main()
