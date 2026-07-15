"""Mode 01 (live data) PID request/response handling and decoding.

This is pure math over bytes — no serial I/O — so it's the most testable
piece of core without hardware. Decode formulas are intentionally left as
TODOs pending the protocol-logic pass; the shape (PID table + decode
function signature) is what's being sanity-checked here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PIDDefinition:
    pid: int  # e.g. 0x0C for RPM
    name: str
    description: str
    bytes_expected: int
    unit: str
    decode: Callable[[bytes], float]


def _not_implemented(_: bytes) -> float:
    raise NotImplementedError


# Standard Mode 01 PIDs. Formulas TODO — see SAE J1979 / ISO 15031-5 for the
# reference math (e.g. RPM = ((A*256)+B)/4, speed = A km/h, coolant temp =
# A-40, etc.). Left unfilled deliberately for this scaffolding pass.
STANDARD_PIDS: dict[int, PIDDefinition] = {
    0x05: PIDDefinition(0x05, "COOLANT_TEMP", "Engine coolant temperature", 1, "°C", _not_implemented),
    0x0C: PIDDefinition(0x0C, "RPM", "Engine RPM", 2, "rpm", _not_implemented),
    0x0D: PIDDefinition(0x0D, "SPEED", "Vehicle speed", 1, "km/h", _not_implemented),
    0x0F: PIDDefinition(0x0F, "INTAKE_TEMP", "Intake air temperature", 1, "°C", _not_implemented),
    0x10: PIDDefinition(0x10, "MAF", "MAF air flow rate", 2, "g/s", _not_implemented),
    0x11: PIDDefinition(0x11, "THROTTLE_POS", "Throttle position", 1, "%", _not_implemented),
    0x2F: PIDDefinition(0x2F, "FUEL_LEVEL", "Fuel tank level input", 1, "%", _not_implemented),
}


def decode_pid(pid: int, response: bytes) -> float:
    """Decode a Mode 01 PID response payload using STANDARD_PIDS.

    TODO: look up PIDDefinition, validate len(response) == bytes_expected,
    call definition.decode(response).
    """
    raise NotImplementedError


def build_request(pid: int) -> str:
    """Build the ELM327 command string for a Mode 01 PID request, e.g. '010C'.

    TODO.
    """
    raise NotImplementedError
