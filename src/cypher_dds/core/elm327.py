"""ELM327 AT command layer: init sequence and command/response framing.

Sits directly on top of SerialConnection. Knows nothing about PIDs, DTCs, or
vehicle brands — just how to talk to the ELM327 chip itself. Command set and
response conventions are the public ELM327 AT command reference (Elm
Electronics' own datasheet) plus SAE J1979 positive-response framing.
"""

from __future__ import annotations

from cypher_dds.core.serial_conn import SerialConnection

# Standard init sequence for a cold ELM327 connection.
INIT_SEQUENCE = (
    "ATZ",  # reset
    "ATE0",  # echo off
    "ATL0",  # linefeeds off
    "ATH0",  # headers off (can be toggled on later if needed for CAN ID info)
    "ATSP0",  # protocol: auto-detect
)

# Substrings that mark an ELM327-level failure rather than vehicle data.
# ("?" is handled separately since it's an exact-match token, not a phrase.)
_ERROR_PHRASES = (
    "NO DATA",
    "UNABLE TO CONNECT",
    "ERROR",
    "STOPPED",
    "BUS INIT",
    "BUFFER FULL",
)

# ATDPN protocol numbers, per the ELM327 datasheet. ATDPN prefixes "A" when
# the protocol was auto-detected rather than manually forced (ATSPn).
PROTOCOL_NAMES: dict[str, str] = {
    "0": "Automatic",
    "1": "SAE J1850 PWM",
    "2": "SAE J1850 VPW",
    "3": "ISO 9141-2",
    "4": "ISO 14230-4 KWP (5-baud init)",
    "5": "ISO 14230-4 KWP (fast init)",
    "6": "ISO 15765-4 CAN (11 bit ID, 500 kbaud)",
    "7": "ISO 15765-4 CAN (29 bit ID, 500 kbaud)",
    "8": "ISO 15765-4 CAN (11 bit ID, 250 kbaud)",
    "9": "ISO 15765-4 CAN (29 bit ID, 250 kbaud)",
    "A": "SAE J1939 CAN (29 bit ID, 250 kbaud)",
    "B": "USER1 CAN",
    "C": "USER2 CAN",
}


class ELM327Error(Exception):
    """Raised on ELM327-level failures (NO DATA, UNABLE TO CONNECT, ERROR, ...)."""


def _is_error_line(line: str) -> bool:
    upper = line.strip().upper()
    if upper == "?":  # unrecognized command
        return True
    return any(phrase in upper for phrase in _ERROR_PHRASES)


class ELM327:
    """Talks AT/PID commands to an ELM327 over a SerialConnection."""

    def __init__(self, connection: SerialConnection) -> None:
        self._connection = connection

    def initialize(self) -> None:
        """Run INIT_SEQUENCE, raising ELM327Error if any step fails."""
        for command in INIT_SEQUENCE:
            self.send_command(command)

    def send_command(self, command: str) -> str:
        """Send an AT or PID command and return its cleaned response text.

        Strips the echoed command line (in case ATE0 hasn't taken effect
        yet, e.g. during the very first ATZ of a cold init), the trailing
        '>' prompt, and blank lines. Raises ELM327Error on adapter-level
        failure responses. Multi-line responses (e.g. multi-frame VIN or
        DTC data) are preserved, newline-joined.
        """
        self._connection.send_raw(command.encode("ascii") + b"\r")
        raw = self._connection.read_until_prompt()
        text = raw.decode("ascii", errors="replace").replace(">", "")
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        if lines and lines[0].upper() == command.upper():
            lines = lines[1:]

        if not lines:
            raise ELM327Error(f"No response to {command!r}")

        for line in lines:
            if _is_error_line(line):
                raise ELM327Error(f"{command!r} -> {line}")

        return "\n".join(lines)

    def detected_protocol(self) -> str:
        """Human-readable protocol name, from ATDPN (describe protocol by number)."""
        code = self.send_command("ATDPN").strip().upper()
        if len(code) > 1 and code.startswith("A"):
            code = code[1:]  # strip the "auto-detected" marker
        return PROTOCOL_NAMES.get(code, f"Unknown protocol ({code})")
