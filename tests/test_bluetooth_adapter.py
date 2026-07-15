"""Tests for the Bluetooth RFCOMM transport.

No real Bluetooth hardware here, so these mock the socket layer — what's
under test is that BluetoothSerialAdapter builds the right kind of socket,
connects to the right (address, channel), and implements SerialLike
correctly against a fake connection, not real over-the-air behavior.
"""

import socket
from unittest.mock import MagicMock, patch

import pytest

from cypher_dds.core.bluetooth_adapter import (
    DEFAULT_RFCOMM_CHANNEL,
    BluetoothSerialAdapter,
)


def test_connects_to_given_address_and_channel():
    with patch("cypher_dds.core.bluetooth_adapter.socket.socket") as mock_socket_cls:
        mock_socket = MagicMock()
        mock_socket_cls.return_value = mock_socket

        adapter = BluetoothSerialAdapter("AA:BB:CC:DD:EE:FF", channel=3)

        mock_socket.connect.assert_called_once_with(("AA:BB:CC:DD:EE:FF", 3))
        assert adapter.is_open is True


def test_default_channel_is_one():
    assert DEFAULT_RFCOMM_CHANNEL == 1
    with patch("cypher_dds.core.bluetooth_adapter.socket.socket") as mock_socket_cls:
        mock_socket = MagicMock()
        mock_socket_cls.return_value = mock_socket

        BluetoothSerialAdapter("AA:BB:CC:DD:EE:FF")

        mock_socket.connect.assert_called_once_with(("AA:BB:CC:DD:EE:FF", 1))


def test_write_delegates_to_socket_send():
    with patch("cypher_dds.core.bluetooth_adapter.socket.socket") as mock_socket_cls:
        mock_socket = MagicMock()
        mock_socket.send.return_value = 4
        mock_socket_cls.return_value = mock_socket

        adapter = BluetoothSerialAdapter("AA:BB:CC:DD:EE:FF")
        assert adapter.write(b"ATZ\r") == 4
        mock_socket.send.assert_called_once_with(b"ATZ\r")


def test_read_returns_empty_bytes_on_timeout():
    with patch("cypher_dds.core.bluetooth_adapter.socket.socket") as mock_socket_cls:
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = socket.timeout
        mock_socket_cls.return_value = mock_socket

        adapter = BluetoothSerialAdapter("AA:BB:CC:DD:EE:FF")
        assert adapter.read(1) == b""


def test_close_marks_adapter_as_not_open():
    with patch("cypher_dds.core.bluetooth_adapter.socket.socket") as mock_socket_cls:
        mock_socket = MagicMock()
        mock_socket_cls.return_value = mock_socket

        adapter = BluetoothSerialAdapter("AA:BB:CC:DD:EE:FF")
        adapter.close()

        mock_socket.close.assert_called_once()
        assert adapter.is_open is False


def test_raises_clearly_when_bluetooth_unsupported_on_platform():
    with patch("cypher_dds.core.bluetooth_adapter.BLUETOOTH_SUPPORTED", False):
        with pytest.raises(RuntimeError, match="Bluetooth"):
            BluetoothSerialAdapter("AA:BB:CC:DD:EE:FF")
