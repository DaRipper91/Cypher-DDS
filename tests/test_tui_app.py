"""Unit-level tests for the Textual dashboard components.

These tests avoid Textual's headless app harness, which is currently not
shutting down cleanly under this Python/Textual combination. The end-to-end
diagnostic flow remains covered in `tests/test_session.py`; here we keep
coverage on widget rendering and app-level dispatch/helpers.
"""

from __future__ import annotations

from unittest.mock import Mock

from cypher_dds.tui.app import ConnectionStatusWidget, CypherDDSApp, DTCPanelWidget
from cypher_dds.theme import ROYAL_BLUE


def test_connection_status_widget_renders_connected_protocol():
    widget = ConnectionStatusWidget()
    widget.connected = True
    widget.protocol = "ISO 15765-4 CAN (11 bit ID, 500 kbaud)"
    widget.watch_connected(True)
    widget.watch_protocol(widget.protocol)

    assert "ISO 15765-4 CAN" in str(widget.render())


def test_connection_status_widget_renders_disconnected_state():
    widget = ConnectionStatusWidget()
    widget.connected = False
    widget.watch_connected(False)

    assert str(widget.render()) == "○ NO ADAPTER"


def test_dtc_panel_widget_renders_alert_state():
    widget = DTCPanelWidget()
    widget.codes = ("P0301", "P0104")
    widget.watch_codes(widget.codes)

    rendered = str(widget.render())
    assert "P0301" in rendered
    assert "P0104" in rendered


def test_dtc_panel_widget_renders_clear_state():
    widget = DTCPanelWidget()
    widget.codes = ()
    widget.watch_codes(())

    assert str(widget.render()) == "✓ NO CODES STORED"


def test_action_refresh_dispatches_worker_only_when_connected():
    app = CypherDDSApp()
    app.run_worker = Mock()

    app.action_refresh()
    app.run_worker.assert_not_called()

    app._session.elm327 = Mock()
    app.action_refresh()

    app.run_worker.assert_called_once_with(app._refresh_dtcs_and_pids, thread=True, group="refresh")


def test_connecting_message_reflects_selected_transport():
    usb = CypherDDSApp(port="/dev/ttyUSB0")
    bt = CypherDDSApp(bluetooth_address="AA:BB:CC:DD:EE:FF")
    mock = CypherDDSApp()

    assert usb._connecting_message() == "Connecting to /dev/ttyUSB0…"
    assert bt._connecting_message() == "Connecting to AA:BB:CC:DD:EE:FF over Bluetooth…"
    assert mock._connecting_message() == "Connecting to mock adapter…"


def test_live_data_placeholder_contains_default_labels():
    placeholder = CypherDDSApp._live_data_placeholder()

    assert "RPM: —" in placeholder
    assert "Speed: —" in placeholder
    assert "Coolant: —" in placeholder


def test_tui_uses_shared_status_accent_color():
    assert ROYAL_BLUE in CypherDDSApp.CSS
