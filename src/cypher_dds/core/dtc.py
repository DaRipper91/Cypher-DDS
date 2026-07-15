"""Mode 03/04 diagnostic trouble code (DTC) read/clear + generic P0xxx decoding.

Manufacturer-specific P1xxx tables live in cypher_dds.profiles, not here — this
module only knows the generic SAE-defined P0xxx/P2xxx/P3xxx/Uxxxx space plus
the DTC byte-pair -> code string math, which is brand-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DTC:
    code: str  # e.g. "P0301"
    description: str | None = None  # filled by a vehicle profile if brand-specific


# Generic SAE-defined P0xxx descriptions (a small seed set; expand as needed).
# TODO: fill in from SAE J2012 / ISO 15031-6 generic code list.
GENERIC_DTC_TABLE: dict[str, str] = {
    # "P0301": "Cylinder 1 Misfire Detected",
}


def decode_dtc_bytes(data: bytes) -> list[str]:
    """Decode raw Mode 03/04 response bytes into DTC code strings (e.g. 'P0301').

    Each DTC is 2 bytes: first two bits select the letter (P/C/B/U), the rest
    is digits. TODO: implement per SAE J2012.
    """
    raise NotImplementedError


class DTCReader:
    """Reads (Mode 03) and clears (Mode 04) DTCs via an ELM327 connection.

    TODO: read_stored() -> list[DTC], clear() -> None.
    """

    def read_stored(self) -> list[DTC]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
