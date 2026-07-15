"""Cypher-DDS Textual dashboard: connection status, live PID readout, DTC panel.

TODO once core is implemented:
  - ConnectionStatusWidget: wire `connected` to cypher_dds.core.serial_conn
    instead of the demo binding below
  - LiveDataWidget: scrolling/updating table of subscribed PIDs
  - DTCPanelWidget: wire `dtc_count` to cypher_dds.core.dtc instead of the
    demo binding below; list of stored DTCs with brand-resolved
    descriptions, a "clear codes" action
  - App-level: connect (real port or --mock scenario), profile selection
    (manual or auto via decoded VIN)
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from cypher_dds.tui.theme import CHERRY_RED, ROYAL_BLUE


class ConnectionStatusWidget(Static, can_focus=True):
    """Connection status badge — Royal Blue means connected/live.

    `connected` is a plain reactive flag for now; real wiring to
    cypher_dds.core.serial_conn lands with the core work.
    """

    connected: reactive[bool] = reactive(False)

    def watch_connected(self, connected: bool) -> None:
        self.set_class(connected, "-connected")
        self.set_class(not connected, "-disconnected")
        self.update("● LIVE" if connected else "○ NO ADAPTER")


class DTCPanelWidget(Static, can_focus=True):
    """DTC alert badge — Cherry Red means one or more codes are stored.

    `dtc_count` is a plain reactive flag for now; real wiring to
    cypher_dds.core.dtc lands with the core work.
    """

    dtc_count: reactive[int] = reactive(0)

    def watch_dtc_count(self, count: int) -> None:
        self.set_class(count > 0, "-alert")
        self.update(f"⚠ {count} DTC(S)" if count else "✓ NO CODES STORED")


class CypherDDSApp(App):
    """Root Textual application."""

    TITLE = "Cypher-DDS"

    BINDINGS = [
        Binding("c", "toggle_connection", "Toggle connection (demo)"),
        Binding("x", "toggle_dtc", "Toggle DTC alert (demo)"),
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
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Cypher-DDS TUI — scaffolding in place, live dashboard not yet "
            "implemented.\nPress 'c' / 'x' to preview the status accent colors."
        )
        with Horizontal(id="status-row"):
            yield ConnectionStatusWidget(
                "○ NO ADAPTER", id="connection-status", classes="-disconnected"
            )
            yield DTCPanelWidget("✓ NO CODES STORED", id="dtc-panel")
        yield Footer()

    def action_toggle_connection(self) -> None:
        status = self.query_one("#connection-status", ConnectionStatusWidget)
        status.connected = not status.connected

    def action_toggle_dtc(self) -> None:
        panel = self.query_one("#dtc-panel", DTCPanelWidget)
        panel.dtc_count = 0 if panel.dtc_count else 3


def main() -> None:
    CypherDDSApp().run()


if __name__ == "__main__":
    main()
