"""Mode 09 VIN retrieval and decoding.

Decodes only as far as manufacturer (WMI, first 3 chars) — enough to drive
automatic profile selection in cypher_dds.profiles. Full VIN decode (model year,
plant, sequence) is out of scope unless a later need justifies it.
"""

from __future__ import annotations

from dataclasses import dataclass

from cypher_dds.core.elm327 import ELM327


@dataclass(frozen=True)
class VINInfo:
    vin: str
    wmi: str  # first 3 characters
    manufacturer: str | None  # resolved profile key, or None if unrecognized


# World Manufacturer Identifier prefixes for the v1 target brands.
# TODO: this is a non-exhaustive seed; each brand has multiple WMIs across
# plants/regions and this needs to be filled in against a real WMI reference.
#
# NOTE: this must be kept in sync with each profile's `wmi_codes` in
# cypher_dds.profiles (gm.py, ford.py, dodge_chrysler.py, toyota_lexus.py,
# honda_acura.py). Core can't import profiles (see cypher_dds.core's
# package docstring), so this table is necessarily a separate copy, not a
# derived one — adding a WMI to a profile does nothing here unless it's
# added here too.
WMI_TABLE: dict[str, str] = {
    "1G1": "gm",
    "1GC": "gm",
    "1GT": "gm",
    "3GN": "gm",
    "1FA": "ford",
    "1FT": "ford",
    "1FM": "ford",
    "3FA": "ford",
    "1C3": "dodge_chrysler",
    "1C4": "dodge_chrysler",
    "1C6": "dodge_chrysler",
    "2C3": "dodge_chrysler",
    "4T1": "toyota_lexus",
    "4T3": "toyota_lexus",
    "JTD": "toyota_lexus",
    "JTH": "toyota_lexus",
    "1HG": "honda_acura",
    "19U": "honda_acura",
    "JHM": "honda_acura",
    "2HG": "honda_acura",
}


def decode_wmi(vin: str) -> str | None:
    """Return the registered profile key for a VIN's WMI, or None if unknown."""
    return WMI_TABLE.get(vin[:3].upper())


def request_vin(elm327: ELM327) -> VINInfo:
    """Send Mode 09 PID 02 and parse the (possibly multi-frame) VIN response.

    Response format is `49 02 01 <ASCII VIN bytes...>`: `49` is the Mode 09
    positive-response SID, `02` echoes the requested PID, `01` is a
    message-count byte, and the remainder is the 17-character VIN as ASCII,
    sometimes left-padded with null bytes to round out the CAN frame count.
    ELM327 reassembles the underlying multi-frame ISO-TP transport for us,
    so this only has to handle the application-layer bytes.
    """
    response = elm327.send_command("0902")
    tokens = response.split()

    if len(tokens) >= 2 and tokens[0].upper() == "49" and tokens[1].upper() == "02":
        tokens = tokens[2:]
    if tokens and tokens[0].upper() == "01":
        tokens = tokens[1:]

    raw = bytes(int(token, 16) for token in tokens)
    # Some vehicles left-pad the VIN with nulls; CAN vehicles commonly
    # right-pad it too (the last ISO-TP frame is zero-filled out to the
    # frame size). str.strip() won't remove embedded NUL characters, so
    # this has to happen on the raw bytes before decoding.
    raw = raw.strip(b"\x00")
    vin = raw.decode("ascii", errors="replace").strip()

    if len(vin) != 17:
        raise ValueError(f"Expected a 17-character VIN, got {len(vin)!r}: {vin!r}")

    return VINInfo(vin=vin, wmi=vin[:3], manufacturer=decode_wmi(vin))
