"""Tests for DiagnosticSession — the framework-agnostic layer any
presentation front-end (TUI today, a future GUI eventually) drives.

Pure Python, no Textual needed — this is exactly why the orchestration
logic was extracted out of tui/app.py in the first place.
"""

from unittest.mock import patch

import pytest

import cypher_dds.profiles  # noqa: F401 — registers all built-in vehicle profiles
from cypher_dds.core.dtc import DTC
from cypher_dds.session import DiagnosticSession, NotConnectedError


def test_read_dtcs_before_connect_raises():
    session = DiagnosticSession()
    with pytest.raises(NotConnectedError):
        session.read_dtcs()


def test_resolve_vehicle_before_connect_raises():
    session = DiagnosticSession()
    with pytest.raises(NotConnectedError):
        session.resolve_vehicle()


def test_read_live_data_before_connect_raises():
    session = DiagnosticSession()
    with pytest.raises(NotConnectedError):
        session.read_live_data()


def test_full_session_flow_against_mock_adapter():
    session = DiagnosticSession()
    assert session.connected is False

    protocol = session.connect()  # no port => mock adapter, "default" scenario
    assert protocol == "ISO 15765-4 CAN (11 bit ID, 500 kbaud)"
    assert session.connected is True

    vin_info = session.resolve_vehicle()
    assert vin_info.vin == "1G1ZE5ST9JF123456"
    assert vin_info.manufacturer == "gm"
    assert session.profile is not None
    assert session.profile.display_name == "General Motors"

    dtcs = session.read_dtcs()
    assert dtcs == [
        DTC(code="P0301", description="Cylinder 1 Misfire Detected"),
        # P0104 isn't a real SAE code and isn't in GM's brand table either,
        # so it should come back with no description at all.
        DTC(code="P0104", description=None),
    ]

    values = session.read_live_data()
    assert values[0x0C] == 1726.0  # RPM
    assert values[0x0D] == 90.0  # speed
    assert values[0x05] == 83.0  # coolant temp


def test_connect_failure_raises_and_leaves_session_disconnected():
    session = DiagnosticSession()
    with pytest.raises(Exception):
        session.connect(mock_scenario="no_adapter")
    assert session.connected is False


def test_resolve_vehicle_returns_none_on_malformed_vin_without_raising():
    session = DiagnosticSession()
    session.connect(mock_scenario="malformed_vin")
    assert session.resolve_vehicle() is None
    assert session.profile is None


def test_connect_routes_bluetooth_address_to_connect_bluetooth():
    # No real adapter here — just confirming DiagnosticSession picks the
    # Bluetooth path and passes the right args through, not that RFCOMM
    # actually works (see test_bluetooth_adapter.py for that).
    with patch(
        "cypher_dds.core.serial_conn.SerialConnection.connect_bluetooth"
    ) as mock_connect_bt, patch(
        "cypher_dds.core.serial_conn.SerialConnection.connect"
    ) as mock_connect_usb:
        session = DiagnosticSession()
        with pytest.raises(Exception):
            # ELM327.initialize() will fail against the (unmocked) transport
            # returned by the patched connect_bluetooth — that's fine, we
            # only care that connect_bluetooth was called with our args.
            session.connect(bluetooth_address="AA:BB:CC:DD:EE:FF", bluetooth_channel=5)

        mock_connect_bt.assert_called_once_with("AA:BB:CC:DD:EE:FF", 5)
        mock_connect_usb.assert_not_called()
