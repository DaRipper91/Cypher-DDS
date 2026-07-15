"""ELM327 AT command layer: init sequence and command/response framing.

Sits directly on top of SerialConnection. Knows nothing about PIDs, DTCs, or
vehicle brands — just how to talk to the ELM327 chip itself.
"""

from __future__ import annotations

from cypher_dds.core.serial_conn import SerialConnection

# Standard init sequence for a cold ELM327 connection.
# TODO: confirm exact ordering/timing against ELM327 datasheet.
INIT_SEQUENCE = (
    "ATZ",  # reset
    "ATE0",  # echo off
    "ATL0",  # linefeeds off
    "ATH0",  # headers off (can be toggled on later if needed for CAN ID info)
    "ATSP0",  # protocol: auto-detect
)


class ELM327Error(Exception):
    """Raised on ELM327-level failures (NO DATA, UNABLE TO CONNECT, ERROR, ...)."""


class ELM327:
    """Talks AT/PID commands to an ELM327 over a SerialConnection.

    TODO: initialize() running INIT_SEQUENCE and validating each response,
    send_command(cmd: str) -> str stripping echo/prompt/whitespace,
    detected_protocol() -> str (from ATDPN once connected).
    """

    def __init__(self, connection: SerialConnection) -> None:
        self._connection = connection

    def initialize(self) -> None:
        raise NotImplementedError

    def send_command(self, command: str) -> str:
        raise NotImplementedError

    def detected_protocol(self) -> str:
        raise NotImplementedError
