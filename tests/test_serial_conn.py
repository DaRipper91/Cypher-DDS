"""Tests for the serial transport layer that don't need real hardware."""

import pytest

from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.serial_conn import discover_ports, SerialConnection


def test_discover_ports_returns_a_list_without_erroring():
    # Can't assert real devices are present on the test machine — just that
    # the glob-based lookup runs cleanly and returns a list.
    assert isinstance(discover_ports(), list)


def test_is_connected_reflects_injected_transport_state():
    connection = SerialConnection(transport=MockELM327Adapter())
    assert connection.is_connected() is True


def test_disconnect_closes_transport_and_clears_it():
    transport = MockELM327Adapter()
    connection = SerialConnection(transport=transport)
    connection.disconnect()
    assert transport.is_open is False
    assert connection.is_connected() is False


def test_send_raw_without_connection_raises():
    connection = SerialConnection()
    with pytest.raises(ConnectionError):
        connection.send_raw(b"ATZ\r")
