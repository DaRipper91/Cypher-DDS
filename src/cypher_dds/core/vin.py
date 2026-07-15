"""Mode 09 VIN retrieval and decoding.

Decodes only as far as manufacturer (WMI, first 3 chars) — enough to drive
automatic profile selection in cypher_dds.profiles. Full VIN decode (model year,
plant, sequence) is out of scope unless a later need justifies it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VINInfo:
    vin: str
    wmi: str  # first 3 characters
    manufacturer: str | None  # resolved brand, or None if unrecognized


# World Manufacturer Identifier prefixes for the v1 target brands.
# TODO: this is a non-exhaustive seed; each brand has multiple WMIs across
# plants/regions and this needs to be filled in against a real WMI reference.
WMI_TABLE: dict[str, str] = {
    "1G1": "gm",
    "1GC": "gm",
    "1FA": "ford",
    "1FT": "ford",
    "1C3": "dodge_chrysler",
    "1C4": "dodge_chrysler",
    "4T1": "toyota_lexus",
    "JTD": "toyota_lexus",
    "1HG": "honda_acura",
    "19U": "honda_acura",
}


def decode_wmi(vin: str) -> str | None:
    """Return the registered profile key for a VIN's WMI, or None if unknown."""
    raise NotImplementedError


def request_vin() -> VINInfo:
    """Send Mode 09 PID 02 and parse the multi-frame VIN response.

    TODO: build request, reassemble multi-line ELM327 response, strip
    padding, decode ASCII, build VINInfo via decode_wmi().
    """
    raise NotImplementedError
