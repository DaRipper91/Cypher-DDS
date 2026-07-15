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


def test_wmi_table_covers_non_us_manufacturing_plants():
    # Sampled from NHTSA vPIC data across each brand's non-US entities, to
    # catch a regression that only tests the handful of original US codes.
    assert WMI_TABLE["2FT"] == "ford"  # Ford Motor Company of Canada
    assert WMI_TABLE["3C4"] == "dodge_chrysler"  # Chrysler de Mexico
    assert WMI_TABLE["2C3"] == "dodge_chrysler"  # FCA Canada
    assert WMI_TABLE["KL1"] == "gm"  # GM Korea
    assert WMI_TABLE["JTH"] == "toyota_lexus"  # Toyota Motor Corporation (Lexus badge)
    assert WMI_TABLE["JHM"] == "honda_acura"  # Honda Motor Co.
    assert WMI_TABLE["2HG"] == "honda_acura"  # Honda of Canada Mfg.


def test_wmi_table_excludes_mercedes_daimlerchrysler_era_codes():
    # WD*/WC* prefixes belong to Mercedes-Benz (1998-2007 DaimlerChrysler
    # merger), not Dodge/Jeep/Chrysler — must not be present.
    assert "WDY" not in WMI_TABLE
    assert "WD2" not in WMI_TABLE


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
