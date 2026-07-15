"""Mode 03/04 diagnostic trouble code (DTC) read/clear + generic P0xxx decoding.

Manufacturer-specific P1xxx tables live in cypher_dds.profiles, not here — this
module only knows the generic SAE-defined P0xxx/P2xxx/P3xxx/Uxxxx space plus
the DTC byte-pair -> code string math, which is brand-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass

from cypher_dds.core.elm327 import ELM327

_LETTER_BY_PREFIX = {0b00: "P", 0b01: "C", 0b10: "B", 0b11: "U"}


@dataclass(frozen=True)
class DTC:
    code: str  # e.g. "P0301"
    description: str | None = None  # filled by a vehicle profile if brand-specific


# Generic SAE J2012 / ISO 15031-6 definitions — standardized, public-domain
# code meanings (not manufacturer-specific). Seed set of commonly seen
# codes; expand as needed. Manufacturer P1xxx/B/C/U ranges belong in
# cypher_dds.profiles, not here.
GENERIC_DTC_TABLE: dict[str, str] = {
    "P0100": "Mass or Volume Air Flow Circuit Malfunction",
    "P0101": "Mass or Volume Air Flow Circuit Range/Performance Problem",
    "P0102": "Mass or Volume Air Flow Circuit Low Input",
    "P0103": "Mass or Volume Air Flow Circuit High Input",
    "P0110": "Intake Air Temperature Circuit Malfunction",
    "P0115": "Engine Coolant Temperature Circuit Malfunction",
    "P0117": "Engine Coolant Temperature Circuit Low Input",
    "P0118": "Engine Coolant Temperature Circuit High Input",
    "P0120": "Throttle/Pedal Position Sensor/Switch A Circuit Malfunction",
    "P0125": "Insufficient Coolant Temperature for Closed Loop Fuel Control",
    "P0128": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
    "P0130": "O2 Sensor Circuit Malfunction (Bank 1 Sensor 1)",
    "P0133": "O2 Sensor Circuit Slow Response (Bank 1 Sensor 1)",
    "P0135": "O2 Sensor Heater Circuit Malfunction (Bank 1 Sensor 1)",
    "P0141": "O2 Sensor Heater Circuit Malfunction (Bank 1 Sensor 2)",
    "P0171": "System Too Lean (Bank 1)",
    "P0172": "System Too Rich (Bank 1)",
    "P0174": "System Too Lean (Bank 2)",
    "P0175": "System Too Rich (Bank 2)",
    "P0217": "Engine Coolant Overtemperature Condition",
    "P0300": "Random/Multiple Cylinder Misfire Detected",
    "P0301": "Cylinder 1 Misfire Detected",
    "P0302": "Cylinder 2 Misfire Detected",
    "P0303": "Cylinder 3 Misfire Detected",
    "P0304": "Cylinder 4 Misfire Detected",
    "P0325": "Knock Sensor 1 Circuit Malfunction (Bank 1)",
    "P0335": "Crankshaft Position Sensor A Circuit Malfunction",
    "P0340": "Camshaft Position Sensor A Circuit Malfunction",
    "P0401": "Exhaust Gas Recirculation Flow Insufficient Detected",
    "P0420": "Catalyst System Efficiency Below Threshold (Bank 1)",
    "P0430": "Catalyst System Efficiency Below Threshold (Bank 2)",
    "P0440": "Evaporative Emission Control System Malfunction",
    "P0442": "Evaporative Emission Control System Leak Detected (Small Leak)",
    "P0446": "Evaporative Emission Control System Vent Control Circuit Malfunction",
    "P0455": "Evaporative Emission Control System Leak Detected (Large Leak)",
    "P0456": "Evaporative Emission Control System Leak Detected (Very Small Leak)",
    "P0460": "Fuel Level Sensor Circuit Malfunction",
    "P0500": "Vehicle Speed Sensor Malfunction",
    "P0505": "Idle Control System Malfunction",
    "P0562": "System Voltage Low",
    "P0563": "System Voltage High",
    "P0601": "Internal Control Module Memory Check Sum Error",
    "P0606": "ECM/PCM Processor Fault",
    "P0700": "Transmission Control System Malfunction",
    "P0705": "Transmission Range Sensor Circuit Malfunction",
    "P0715": "Input/Turbine Speed Sensor Circuit Malfunction",
    "P0720": "Output Speed Sensor Circuit Malfunction",
}


def decode_dtc_bytes(data: bytes) -> list[str]:
    """Decode raw DTC payload bytes into code strings (e.g. 'P0301').

    `data` is the pure sequence of 2-byte DTC pairs — no mode echo (e.g. the
    leading '43'), no CAN/ISO-TP framing. Stripping that is the caller's job
    (see DTCReader). Per SAE J2012: byte 1's top 2 bits select the letter
    (00=P, 01=C, 10=B, 11=U), its next 2 bits are the first digit (0-3), and
    the remaining 12 bits (low nibble of byte 1 + all of byte 2) are the
    next three hex digits. A 0x0000 pair means "no code" / padding and is
    skipped.
    """
    if len(data) % 2 != 0:
        raise ValueError(f"DTC payload must be an even number of bytes, got {len(data)}")

    codes: list[str] = []
    for i in range(0, len(data), 2):
        high, low = data[i], data[i + 1]
        if high == 0 and low == 0:
            continue
        letter = _LETTER_BY_PREFIX[(high & 0b11000000) >> 6]
        digit1 = (high & 0b00110000) >> 4
        digit2 = high & 0b00001111
        digit3 = (low & 0b11110000) >> 4
        digit4 = low & 0b00001111
        codes.append(f"{letter}{digit1}{digit2:X}{digit3:X}{digit4:X}")
    return codes


def _hex_tokens_to_bytes(text: str) -> bytes:
    """Parse ELM327 space/newline-separated hex byte tokens into bytes."""
    tokens = text.split()
    return bytes(int(token, 16) for token in tokens)


class DTCReader:
    """Reads (Mode 03) and clears (Mode 04) DTCs via an ELM327 connection."""

    def __init__(self, elm327: ELM327) -> None:
        self._elm327 = elm327

    def read_stored(self) -> list[DTC]:
        response = self._elm327.send_command("03")
        tokens = response.split()
        if tokens and tokens[0].upper() == "43":
            tokens = tokens[1:]
        payload = _hex_tokens_to_bytes(" ".join(tokens))
        return [
            DTC(code=code, description=GENERIC_DTC_TABLE.get(code))
            for code in decode_dtc_bytes(payload)
        ]

    def clear(self) -> None:
        self._elm327.send_command("04")
