"""Bluetooth (RFCOMM/SPP) transport for ELM327 adapters that use classic
Bluetooth rather than USB.

Linux-only for now: uses Python's stdlib `socket.AF_BLUETOOTH` RFCOMM
sockets, so there's no extra dependency to install — a good fit for the
project's stated dev machines (CachyOS, Asahi Linux). macOS/Windows would
need a different backend (e.g. PyBluez) since CPython's socket module
doesn't expose AF_BLUETOOTH there; not implemented — BluetoothSerialAdapter
raises a clear error on unsupported platforms rather than failing obscurely.

Pairing is still the OS's job (bluetoothctl, GNOME/KDE Bluetooth settings,
etc.) — this only opens an RFCOMM connection to an already-paired device
by MAC address, the same way most ELM327 tools (including python-OBD) work.
No SDP-based auto-discovery here; that's a reasonable future addition, not
a requirement to open a connection.
"""

from __future__ import annotations

import socket

# Standard RFCOMM/SPP channel most ELM327 Bluetooth adapters listen on.
DEFAULT_RFCOMM_CHANNEL = 1

try:
    _AF_BLUETOOTH = socket.AF_BLUETOOTH
    _BTPROTO_RFCOMM = socket.BTPROTO_RFCOMM
    BLUETOOTH_SUPPORTED = True
except AttributeError:
    _AF_BLUETOOTH = None
    _BTPROTO_RFCOMM = None
    BLUETOOTH_SUPPORTED = False


class BluetoothSerialAdapter:
    """SerialLike wrapper around a Bluetooth RFCOMM socket.

    Implements the same surface as pyserial's Serial / MockELM327Adapter,
    so it plugs into SerialConnection unchanged.
    """

    def __init__(
        self,
        address: str,
        channel: int = DEFAULT_RFCOMM_CHANNEL,
        timeout: float = 2.0,
    ) -> None:
        if not BLUETOOTH_SUPPORTED:
            raise RuntimeError(
                "Bluetooth RFCOMM sockets aren't available on this platform "
                "(Python's socket.AF_BLUETOOTH is Linux-only). macOS/Windows "
                "Bluetooth support isn't implemented yet — use a USB ELM327 "
                "adapter there instead."
            )
        self._socket = socket.socket(_AF_BLUETOOTH, socket.SOCK_STREAM, _BTPROTO_RFCOMM)
        self._socket.settimeout(timeout)
        self._socket.connect((address, channel))
        self._is_open = True

    def write(self, data: bytes) -> int:
        return self._socket.send(data)

    def read(self, size: int = 1) -> bytes:
        try:
            return self._socket.recv(size)
        except socket.timeout:
            return b""

    def readline(self) -> bytes:
        # A raw socket doesn't buffer lines the way pyserial does; read
        # byte-by-byte until '\r' (ELM327's line terminator) or a timeout.
        line = bytearray()
        while True:
            chunk = self.read(1)
            if not chunk:
                break
            line += chunk
            if chunk == b"\r":
                break
        return bytes(line)

    def close(self) -> None:
        self._socket.close()
        self._is_open = False

    @property
    def in_waiting(self) -> int:
        # Not queryable on a raw socket. SerialConnection.read_until_prompt()
        # only ever calls read(1) in a loop, so nothing in this codebase
        # actually depends on an accurate count here.
        return 0

    @property
    def is_open(self) -> bool:
        return self._is_open
