"""Integration tests for the TUI's connect/VIN/DTC/live-data wiring.

Runs Textual's headless test harness against the mock adapter — no real
hardware needed. The connect flow does its blocking serial I/O in a worker
thread (App.run_worker(thread=True)), so tests must await
app.workers.wait_for_complete() before asserting UI state. No pytest-asyncio
dependency: each test wraps its async body in asyncio.run().
"""

import asyncio

from cypher_dds.tui.app import ConnectionStatusWidget, CypherDDSApp, DTCPanelWidget
from cypher_dds.tui.theme import ROYAL_BLUE


def test_connects_and_wires_up_real_core_state():
    async def run() -> None:
        app = CypherDDSApp()  # no --port => mock adapter, "default" scenario
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            status = app.query_one("#connection-status", ConnectionStatusWidget)
            assert status.connected is True
            assert status.protocol == "ISO 15765-4 CAN (11 bit ID, 500 kbaud)"
            assert status.styles.color is not None
            assert status.styles.color.hex == ROYAL_BLUE.upper()

            vehicle_info = str(app.query_one("#vehicle-info").render())
            assert "1G1ZE5ST9JF123456" in vehicle_info
            assert "General Motors" in vehicle_info

            dtc_panel = app.query_one("#dtc-panel", DTCPanelWidget)
            assert dtc_panel.codes == ("P0301", "P0104")
            assert "-alert" in dtc_panel.classes

            live_data = str(app.query_one("#live-data").render())
            assert "RPM: 1726" in live_data
            assert "Speed: 90" in live_data
            assert "Coolant: 83" in live_data

    asyncio.run(run())


def test_refresh_binding_rereads_dtcs_and_pids():
    async def run() -> None:
        app = CypherDDSApp()
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("r")
            await app.workers.wait_for_complete()
            await pilot.pause()

            dtc_panel = app.query_one("#dtc-panel", DTCPanelWidget)
            assert dtc_panel.codes == ("P0301", "P0104")

    asyncio.run(run())


def test_mock_adapter_connection_failure_does_not_crash():
    async def run() -> None:
        app = CypherDDSApp(mock_scenario="no_adapter")
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            status = app.query_one("#connection-status", ConnectionStatusWidget)
            assert status.connected is False

            intro = str(app.query_one("#intro").render())
            assert "Connection failed" in intro

            # Refresh with no live connection should be a safe no-op, not a crash.
            await pilot.press("r")
            await app.workers.wait_for_complete()
            await pilot.pause()

    asyncio.run(run())


def test_invalid_real_port_fails_gracefully():
    async def run() -> None:
        app = CypherDDSApp(port="/dev/nonexistent-port-xyz")
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            status = app.query_one("#connection-status", ConnectionStatusWidget)
            assert status.connected is False

            intro = str(app.query_one("#intro").render())
            assert "Connection failed" in intro

    asyncio.run(run())
