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


# World Manufacturer Identifier prefixes for the v1 target brands, pulled
# from NHTSA's public vPIC database (vpic.nhtsa.dot.gov) — the official
# US government VIN-decoding reference, not any single vendor's data.
# Corporate-entity mapping notes:
#   - Lexus and Acura have no WMIs of their own in vPIC; their vehicles are
#     registered under Toyota Motor Corporation / Honda Motor Co., so they
#     share the toyota_lexus / honda_acura tables already.
#   - Dodge/Jeep/Ram/Chrysler's modern corporate entities are "FCA US LLC"
#     and "FCA Canada Inc." (plus Chrysler de Mexico's older plant codes);
#     DaimlerChrysler-era "WD*"/"WC*" prefixes are excluded — those are
#     Mercedes-Benz WMIs from the 1998-2007 DaimlerChrysler merger, not
#     Dodge/Jeep/Chrysler vehicles.
#   - Excludes motorcycle-only WMIs (e.g. Honda's Thai/Vietnamese/Montesa
#     entries) and joint-venture plants shared with an out-of-scope brand
#     (e.g. Mazda Toyota Manufacturing USA), since those would misroute a
#     different manufacturer's vehicle.
# Still not literally exhaustive of every WMI NHTSA has ever issued, but
# covers each brand's North American passenger-vehicle manufacturing
# entities plus major overseas plants.
WMI_TABLE: dict[str, str] = {
    # GM — General Motors LLC (USA/Canada/Mexico), plus GM Korea (Chevrolet/
    # Buick models built there and sold in the US) and GM Australia.
    **{wmi: "gm" for wmi in (
        "1G0", "1G1", "1G2", "1G3", "1G4", "1G6", "1G7", "1G8", "1GA", "1GB",
        "1GC", "1GD", "1GE", "1GJ", "1GK", "1GM", "1GN", "1GY",
        "2C1", "2C2", "2CG", "2CK", "2CN", "2CT",
        "2G0", "2G1", "2G2", "2G3", "2G4", "2G5", "2G6", "2G7", "2G8", "2GA",
        "2GB", "2GC", "2GD", "2GE", "2GH", "2GJ", "2GK", "2GN", "2GT",
        "3G0", "3G1", "3G2", "3G3", "3G4", "3G5", "3G7", "3GB", "3GC", "3GD",
        "3GG", "3GM", "3GN", "3GP", "3GS", "3GT", "3GY",
        "4G1", "4G2", "4G3", "4G5", "4GB", "4GD", "4GL", "4GT",
        "4KB", "4KD", "4KL", "4NS", "4NT", "4NU", "4W1", "4W5",
        "5G2", "5G3", "5G5", "5G8", "5GA", "5GD", "5GN", "5GR", "5GT", "5GZ",
        "J8C", "J8T", "JG1", "JG2", "JGC", "JGT",
        "6G1", "6G2", "6G3", "KL1", "KL2",
    )},
    # Ford — Ford Motor Company USA/Canada/Mexico (includes Lincoln/Mercury,
    # same corporate PCM lineage), plus Germany, Turkey, Australia, Brazil,
    # India, and New Zealand plants.
    **{wmi: "ford" for wmi in (
        "1F1", "1F7", "1FA", "1FB", "1FC", "1FD", "1FL", "1FM", "1FT",
        "1L1", "1LJ", "1LN", "1ME", "1MH", "1MR",
        "4F2", "4F3", "4F4", "4M2", "4M3", "4M4", "4N2", "4N3", "4N4",
        "5L1", "5LD", "5LM", "5LT",
        "2FA", "2FB", "2FC", "2FD", "2FM", "2FT",
        "2L1", "2LJ", "2LM", "2LN", "2ME", "2MH", "2MR",
        "3FA", "3FB", "3FC", "3FD", "3FE", "3FM", "3FT", "3MA", "3ME", "3LN",
        "WF0", "WF1", "NM0", "6MP", "9BF", "MAJ", "7A5",
    )},
    # Dodge / Jeep / Ram / Chrysler — FCA US LLC, FCA Canada Inc., and
    # Chrysler de Mexico's plant codes (modern Stellantis-era North
    # American entities).
    **{wmi: "dodge_chrysler" for wmi in (
        "1A2", "1A3", "1A4", "1A6", "1A7", "1A8",
        "1B2", "1B3", "1B4", "1B5", "1B6", "1B7", "1B8",
        "1C2", "1C3", "1C4", "1C6", "1C7", "1C8",
        "1D2", "1D3", "1D4", "1D5", "1D6", "1D7", "1D8",
        "1E3", "1J2", "1J3", "1J4", "1J5", "1J6", "1J7", "1J8", "1JC", "1JD", "1JT",
        "1P3", "1P4", "1P5", "1P6", "1P7", "1XM",
        "1Z2", "1Z3", "1Z4", "1Z6", "1Z7", "1Z8",
        "4B3", "4C3", "4E3", "JB3", "JE3", "MN3",
        "2A2", "2A3", "2A4", "2A6", "2A7", "2A8",
        "2B2", "2B3", "2B4", "2B5", "2B6", "2B7", "2B8",
        "2C3", "2C4", "2C6", "2C7", "2C8", "2CA",
        "2D2", "2D3", "2D4", "2D5", "2D6", "2D7", "2D8",
        "2E3", "2E4", "2J4", "2J5", "2J6", "2P3", "2P4", "2P5", "2P6", "2P7", "2V4",
        "3A2", "3A3", "3A4", "3A6", "3A7", "3B2", "3B3", "3B4", "3B5", "3B6", "3B7", "3B8",
        "3C2", "3C3", "3C4", "3C6", "3C7", "3C8", "3CA",
        "3D2", "3D3", "3D4", "3D5", "3D6", "3D7", "3D8",
        "3E3", "3E4", "3F6", "3J4", "3J5", "3J6", "3P3", "3P4", "3P5", "3P6", "3P7",
    )},
    # Toyota / Lexus — Toyota Motor Corporation and Toyota Motor North
    # America's manufacturing entities (Lexus has no WMI of its own; it's
    # registered under Toyota Motor Corporation).
    **{wmi: "toyota_lexus" for wmi in (
        "2T1", "2T2", "2T3", "3TM", "3TY",
        "4T1", "4T3", "4T4", "5TB", "5TD", "5TE", "5TF", "5YF", "58A",
        "7SV", "SB1", "NMT", "VNK",
        "JT2", "JT3", "JT4", "JT5", "JT6", "JT8",
        "JTD", "JTE", "JTH", "JTJ", "JTK", "JTL", "JTM", "JTN",
    )},
    # Honda / Acura — Honda Motor Co. and American Honda / Honda of Canada /
    # Honda de Mexico manufacturing entities (Acura has no WMI of its own).
    # Excludes motorcycle-only WMIs (Thai Honda, Honda Vietnam, Montesa
    # Honda, Moto Honda da Amazonia, Sundiro Honda).
    **{wmi: "honda_acura" for wmi in (
        "1HF", "1HG", "19U", "19V", "19X", "478",
        "5FN", "5FP", "5FR", "5FS", "5J6", "5J7", "5J8", "5KB", "5KC",
        "2HG", "2HH", "2HJ", "2HK", "2HN",
        "3CZ", "3DH", "3H1", "3HD", "3HG",
        "7FA", "JH1", "JH2", "JH3", "JH4", "JHL", "JHM", "JR2", "SHH", "SHS", "YC1", "ZDC",
    )},
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
    raw = raw.lstrip(b"\x00")  # some vehicles left-pad the VIN with nulls
    vin = raw.decode("ascii", errors="replace").strip()

    if len(vin) != 17:
        raise ValueError(f"Expected a 17-character VIN, got {len(vin)!r}: {vin!r}")

    return VINInfo(vin=vin, wmi=vin[:3], manufacturer=decode_wmi(vin))
