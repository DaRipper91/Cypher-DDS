"""Cypher-DDS Textual dashboard: connection status, live PID readout, DTC panel.

TODO once core is implemented:
  - ConnectionStatusWidget: port, baudrate, adapter state, detected protocol
  - LiveDataWidget: scrolling/updating table of subscribed PIDs
  - DTCPanelWidget: list of stored DTCs with brand-resolved descriptions,
    a "clear codes" action
  - App-level: connect (real port or --mock scenario), profile selection
    (manual or auto via decoded VIN)
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static


class CypherDDSApp(App):
    """Root Textual application."""

    TITLE = "Cypher-DDS"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Cypher-DDS TUI — scaffolding in place, dashboard not yet implemented.")
        yield Footer()


def main() -> None:
    CypherDDSApp().run()


if __name__ == "__main__":
    main()
