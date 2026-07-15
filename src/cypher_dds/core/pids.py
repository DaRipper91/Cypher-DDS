"""Mode 01 (live data) PID request/response handling and decoding.

This is pure math over bytes — no serial I/O — so it's the most testable
piece of core without hardware. Formulas are the standard SAE J1979 /
ISO 15031-5 definitions, valid on any compliant OBD2 vehicle.
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


# Standard Mode 01 PIDs (SAE J1979 / ISO 15031-5). Response bytes are named
# A, B, ... per the spec's convention, A being the first payload byte.
STANDARD_PIDS: dict[int, PIDDefinition] = {
    0x05: PIDDefinition(
        0x05, "COOLANT_TEMP", "Engine coolant temperature", 1, "°C",
        lambda b: b[0] - 40,
    ),
    0x0C: PIDDefinition(
        0x0C, "RPM", "Engine RPM", 2, "rpm",
        lambda b: ((b[0] * 256) + b[1]) / 4,
    ),
    0x0D: PIDDefinition(
        0x0D, "SPEED", "Vehicle speed", 1, "km/h",
        lambda b: float(b[0]),
    ),
    0x0F: PIDDefinition(
        0x0F, "INTAKE_TEMP", "Intake air temperature", 1, "°C",
        lambda b: b[0] - 40,
    ),
    0x10: PIDDefinition(
        0x10, "MAF", "MAF air flow rate", 2, "g/s",
        lambda b: ((b[0] * 256) + b[1]) / 100,
    ),
    0x11: PIDDefinition(
        0x11, "THROTTLE_POS", "Throttle position", 1, "%",
        lambda b: (100 / 255) * b[0],
    ),
    0x2F: PIDDefinition(
        0x2F, "FUEL_LEVEL", "Fuel tank level input", 1, "%",
        lambda b: (100 / 255) * b[0],
    ),
}


def decode_pid(pid: int, response: bytes) -> float:
    """Decode a Mode 01 PID response payload using STANDARD_PIDS.

    `response` is just the data bytes (A, B, ...) — no mode/PID echo, no
    ELM327 framing. Stripping that framing is the caller's job.
    """
    try:
        definition = STANDARD_PIDS[pid]
    except KeyError:
        raise KeyError(f"Unknown or unsupported PID: {pid:#04x}") from None

    if len(response) != definition.bytes_expected:
        raise ValueError(
            f"{definition.name} (PID {pid:#04x}) expects "
            f"{definition.bytes_expected} byte(s), got {len(response)}"
        )

    return definition.decode(response)


def build_request(pid: int) -> str:
    """Build the ELM327 command string for a Mode 01 PID request, e.g. '010C'."""
    if pid not in STANDARD_PIDS:
        raise KeyError(f"Unknown or unsupported PID: {pid:#04x}")
    return f"01{pid:02X}"
