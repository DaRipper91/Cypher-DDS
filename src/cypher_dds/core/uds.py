"""Minimal typed UDS request and response models used by the action framework.

This is intentionally small: enough structure to stop treating UDS traffic as
opaque hex strings, while preserving the current repo behavior and mock-based
tests. As real OEM workflows are added, this module can grow into a fuller
service/request/response layer.
"""

from __future__ import annotations

from dataclasses import dataclass

_NEGATIVE_RESPONSE_CODES: dict[int, str] = {
    0x10: "General reject",
    0x11: "Service not supported",
    0x12: "Sub-function not supported",
    0x13: "Incorrect message length or invalid format",
    0x21: "Busy repeat request",
    0x22: "Conditions not correct",
    0x24: "Request sequence error",
    0x31: "Request out of range",
    0x33: "Security access denied",
    0x35: "Invalid key",
    0x36: "Exceeded number of attempts",
    0x37: "Required time delay not expired",
    0x72: "General programming failure",
    0x78: "Response pending",
}


def _hex_bytes(data: bytes) -> str:
    return data.hex().upper()


@dataclass(frozen=True)
class UDSRequest:
    """One UDS request with enough metadata to build the expected positive response."""

    service_id: int
    subfunction: int | None = None
    data_identifier: int | None = None
    payload: bytes = b""

    def command_hex(self) -> str:
        parts = [f"{self.service_id:02X}"]
        if self.subfunction is not None:
            parts.append(f"{self.subfunction:02X}")
        if self.data_identifier is not None:
            parts.append(f"{self.data_identifier:04X}")
        if self.payload:
            parts.append(_hex_bytes(self.payload))
        return "".join(parts)

    def positive_response_prefix(self) -> str:
        parts = [f"{self.service_id + 0x40:02X}"]
        if self.subfunction is not None:
            parts.append(f"{self.subfunction:02X}")
        if self.data_identifier is not None:
            parts.append(f"{self.data_identifier:04X}")
        return "".join(parts)


@dataclass(frozen=True)
class UDSNegativeResponse:
    service_id: int
    response_code: int

    @property
    def code_name(self) -> str:
        return _NEGATIVE_RESPONSE_CODES.get(self.response_code, "Unknown negative response")

    def summary(self) -> str:
        return (
            f"UDS negative response for service 0x{self.service_id:02X}: "
            f"0x{self.response_code:02X} ({self.code_name})"
        )


def diagnostic_session_control(session_type: int) -> UDSRequest:
    return UDSRequest(service_id=0x10, subfunction=session_type)


def tester_present(*, suppress_response: bool = False) -> UDSRequest:
    return UDSRequest(service_id=0x3E, subfunction=0x80 if suppress_response else 0x00)


def read_data_by_identifier(data_identifier: int) -> UDSRequest:
    return UDSRequest(service_id=0x22, data_identifier=data_identifier)


def parse_negative_response(response: str) -> UDSNegativeResponse | None:
    compact = "".join(response.upper().split())
    if len(compact) < 6 or not compact.startswith("7F"):
        return None
    return UDSNegativeResponse(
        service_id=int(compact[2:4], 16),
        response_code=int(compact[4:6], 16),
    )
