"""Serial transport: port discovery, connect/disconnect, byte-level framing.

Anything that speaks bytes in/out the way pyserial's ``Serial`` does can be
used here, including ``cypher_dds.core.mock_adapter.MockELM327Adapter``. Code
above this layer (elm327.py and up) should depend on ``SerialLike``, never on
``serial.Serial`` directly, so a mock can always be swapped in.
"""

from __future__ import annotations

import glob
from typing import Protocol, runtime_checkable

import serial as pyserial

# Typical Linux enumeration for USB ELM327 adapters:
#   /dev/ttyUSB*  — CH340-based clones
#   /dev/ttyACM*  — FTDI / native USB-serial
CANDIDATE_PORT_GLOBS = ("/dev/ttyUSB*", "/dev/ttyACM*")

DEFAULT_BAUDRATE = 38400

# ELM327 responses can be slow (ATZ resets the chip; some PID requests wait
# on a stalled bus before timing out), so this is generous on purpose.
DEFAULT_TIMEOUT = 2.0  # seconds

PROMPT = b">"


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
    """Return candidate serial device paths present on this machine."""
    ports: list[str] = []
    for pattern in CANDIDATE_PORT_GLOBS:
        ports.extend(sorted(glob.glob(pattern)))
    return ports


class SerialConnection:
    """Owns a SerialLike transport; handles connect/disconnect and framing.

    A transport can be injected directly (e.g. MockELM327Adapter for
    hardware-free development); otherwise connect() opens a real pyserial
    port.
    """

    def __init__(self, transport: SerialLike | None = None) -> None:
        self._transport = transport

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE) -> None:
        self._transport = pyserial.Serial(
            port=port, baudrate=baudrate, timeout=DEFAULT_TIMEOUT
        )

    def disconnect(self) -> None:
        if self._transport is not None:
            self._transport.close()
        self._transport = None

    def is_connected(self) -> bool:
        return self._transport is not None and self._transport.is_open

    def send_raw(self, data: bytes) -> None:
        if self._transport is None:
            raise ConnectionError("not connected")
        self._transport.write(data)

    def read_until_prompt(self, prompt: bytes = PROMPT) -> bytes:
        """Read until the ELM327's '>' prompt, or until a read times out."""
        if self._transport is None:
            raise ConnectionError("not connected")
        buffer = bytearray()
        while True:
            chunk = self._transport.read(1)
            if not chunk:
                break  # transport timed out with no more data
            buffer += chunk
            if buffer.endswith(prompt):
                break
        return bytes(buffer)
