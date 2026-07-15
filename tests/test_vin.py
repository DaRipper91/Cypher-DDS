"""Tests for VIN WMI decoding (pure logic) and request_vin (mock adapter)."""

import pytest

from cypher_dds.core.elm327 import ELM327
from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.serial_conn import SerialConnection
from cypher_dds.core.vin import WMI_TABLE, VINInfo, decode_wmi, request_vin


def test_wmi_table_has_seed_entries_for_target_brands():
    assert WMI_TABLE["1G1"] == "gm"
    assert WMI_TABLE["1FA"] == "ford"
    assert WMI_TABLE["1C3"] == "dodge_chrysler"


def test_decode_wmi_known_gm_vin():
    assert decode_wmi("1G1ZE5ST9JF123456") == "gm"


def test_decode_wmi_unknown_prefix_returns_none():
    assert decode_wmi("XXXZE5ST9JF123456") is None


def test_decode_wmi_is_case_insensitive():
    assert decode_wmi("1g1ze5st9jf123456") == "gm"


def test_request_vin_against_mock_adapter():
    connection = SerialConnection(transport=MockELM327Adapter())
    elm = ELM327(connection)
    info = request_vin(elm)
    assert info == VINInfo(vin="1G1ZE5ST9JF123456", wmi="1G1", manufacturer="gm")


def test_request_vin_wrong_length_raises_value_error():
    connection = SerialConnection(transport=MockELM327Adapter(scenario="malformed_vin"))
    elm = ELM327(connection)
    with pytest.raises(ValueError):
        request_vin(elm)


def test_request_vin_strips_trailing_null_padding():
    # Real CAN vehicles commonly zero-pad the last ISO-TP frame, so the VIN
    # payload can have trailing 0x00 bytes after the 17 ASCII characters.
    connection = SerialConnection(transport=MockELM327Adapter(scenario="padded_vin"))
    elm = ELM327(connection)
    info = request_vin(elm)
    assert info == VINInfo(vin="1G1ZE5ST9JF123456", wmi="1G1", manufacturer="gm")


def test_wmi_table_matches_every_registered_profiles_wmi_codes():
    # WMI_TABLE is a hand-maintained copy of each profile's wmi_codes
    # (cypher_dds.core can't import cypher_dds.profiles), so it's prone to
    # silently drifting out of sync — guard against that here.
    import cypher_dds.profiles  # noqa: F401 (registers all profiles)
    from cypher_dds.profiles.base import all_profiles

    for key, profile in all_profiles().items():
        for wmi in profile.wmi_codes:
            assert WMI_TABLE.get(wmi) == key, (
                f"{profile.display_name} declares wmi_codes {wmi!r} but "
                f"vin.WMI_TABLE maps it to {WMI_TABLE.get(wmi)!r}"
            )
