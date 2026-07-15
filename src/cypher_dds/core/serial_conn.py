"""Serial transport: port discovery, connect/disconnect/reconnect.

Anything that speaks bytes in/out the way pyserial's ``Serial`` does can be
used here, including ``cypher_dds.core.mock_adapter.MockELM327Adapter``. Code
above this layer (elm327.py and up) should depend on ``SerialLike``, never on
``serial.Serial`` directly, so a mock can always be swapped in.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

# Typical Linux enumeration for USB ELM327 adapters:
#   /dev/ttyUSB*  — CH340-based clones
#   /dev/ttyACM*  — FTDI / native USB-serial
CANDIDATE_PORT_GLOBS = ("/dev/ttyUSB*", "/dev/ttyACM*")

DEFAULT_BAUDRATE = 38400


@runtime_checkable
class SerialLike(Protocol):
    """Minimal surface SerialConnection needs from a transport.

    Both ``serial.Serial`` and ``MockELM327Adapter`` satisfy this.
    """

    def write(self, data: bytes) -> int: ...
    def read(self, size: int = 1) -> bytes: ...
    def readline(self) -> bytes: ...
    def close(self) -> None: ...
    @property
    def in_waiting(self) -> int: ...
    @property
    def is_open(self) -> bool: ...


def discover_ports() -> list[str]:
    """Return candidate serial device paths present on this machine.

    TODO: glob CANDIDATE_PORT_GLOBS (or use serial.tools.list_ports).
    """
    raise NotImplementedError


class SerialConnection:
    """Owns a SerialLike transport; handles connect/disconnect/reconnect.

    TODO: open(port, baudrate), close(), reconnect() with backoff,
    send_raw(bytes) -> None, read_response(terminator=b">") -> bytes.
    """

    def __init__(self, transport: SerialLike | None = None) -> None:
        self._transport = transport

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE) -> None:
        raise NotImplementedError

    def disconnect(self) -> None:
        raise NotImplementedError

    def is_connected(self) -> bool:
        raise NotImplementedError

    def send_raw(self, data: bytes) -> None:
        raise NotImplementedError

    def read_until_prompt(self, prompt: bytes = b">") -> bytes:
        """ELM327 terminates responses with a '>' prompt char."""
        raise NotImplementedError
