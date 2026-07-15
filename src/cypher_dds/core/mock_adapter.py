"""Mock ELM327 serial adapter for development without a car or hardware.

Implements the same SerialLike surface as a real pyserial connection, so it
can be handed to SerialConnection/ELM327 unchanged. Everything above this
layer should be unable to tell the difference between a real adapter and
this one.
"""

from __future__ import annotations

# Canned command -> response tables, keyed by scenario name. Responses are
# the ASCII text ELM327 would send back (without the trailing '\r>' framing
# — write() adds that). Values mirror the public ELM327 AT command set and
# the SAE J1979 Mode 01 positive-response format (41 <PID> <data bytes...>).
_SCENARIOS: dict[str, dict[str, str]] = {
    "default": {
        "ATZ": "ELM327 v1.5",
        "ATE0": "OK",
        "ATL0": "OK",
        "ATH0": "OK",
        "ATSP0": "OK",
        "ATDPN": "A6",  # auto-detected protocol 6: ISO 15765-4 CAN 11bit/500k
        "010C": "41 0C 1A F8",  # RPM = 1726
        "0105": "41 05 7B",  # coolant temp = 83 C
        "0D": "41 0D 5A",  # speed = 90 km/h (mode 01 without leading '01' too)
        "010D": "41 0D 5A",
        "03": "43 03 01 01 04",  # two stored DTCs: P0301, P0104
        "04": "44",  # clear DTCs: positive response, no data
        # VIN "1G1ZE5ST9JF123456" (WMI 1G1 -> gm), as Mode 09 PID 02 ASCII bytes
        "0902": "49 02 01 31 47 31 5A 45 35 53 54 39 4A 46 31 32 33 34 35 36",
    },
    "no_adapter": {},  # every command times out — simulates nothing connected
    "malformed_vin": {
        # A truncated VIN response ("1G1" only) to exercise request_vin's
        # length-validation path.
        "0902": "49 02 01 31 47 31",
    },
    "padded_vin": {
        # Same VIN as "default", but with trailing 0x00 padding bytes, as
        # real CAN vehicles commonly send (the last ISO-TP frame is
        # zero-filled out to the frame size).
        "0902": (
            "49 02 01 31 47 31 5A 45 35 53 54 39 4A 46 31 32 33 34 35 36 00 00 00"
        ),
    },
}


class MockELM327Adapter:
    """In-memory stand-in for a pyserial ``Serial`` talking to a real ELM327."""

    def __init__(self, scenario: str = "default") -> None:
        self.scenario = scenario
        self._is_open = True
        self._out_buffer = bytearray()
        self._responses = _SCENARIOS.get(scenario, _SCENARIOS["default"])

    def write(self, data: bytes) -> int:
        if not self._is_open:
            raise OSError("adapter is closed")
        command = data.decode("ascii", errors="replace").strip().upper()
        response = self._responses.get(command)
        if response is not None:
            self._out_buffer += response.encode("ascii") + b"\r>"
        # Unknown command or "no_adapter" scenario: no bytes queued, so the
        # next read() times out exactly like a real disconnected adapter.
        return len(data)

    def read(self, size: int = 1) -> bytes:
        if not self._out_buffer:
            return b""
        chunk = bytes(self._out_buffer[:size])
        del self._out_buffer[:size]
        return chunk

    def readline(self) -> bytes:
        if b"\r" not in self._out_buffer:
            line = bytes(self._out_buffer)
            self._out_buffer.clear()
            return line
        idx = self._out_buffer.index(b"\r") + 1
        line = bytes(self._out_buffer[:idx])
        del self._out_buffer[:idx]
        return line

    def close(self) -> None:
        self._is_open = False

    @property
    def in_waiting(self) -> int:
        return len(self._out_buffer)

    @property
    def is_open(self) -> bool:
        return self._is_open
