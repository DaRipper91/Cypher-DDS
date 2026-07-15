"""Tests for VIN WMI -> manufacturer decoding (pure logic, no hardware)."""

import pytest

from cypher_dds.core.vin import WMI_TABLE, decode_wmi


def test_wmi_table_has_seed_entries_for_target_brands():
    assert WMI_TABLE["1G1"] == "gm"
    assert WMI_TABLE["1FA"] == "ford"
    assert WMI_TABLE["1C3"] == "dodge_chrysler"


@pytest.mark.skip(reason="decode_wmi not implemented yet")
def test_decode_wmi_known_gm_vin():
    assert decode_wmi("1G1ZE5ST9JF123456") == "gm"


@pytest.mark.skip(reason="decode_wmi not implemented yet")
def test_decode_wmi_unknown_prefix_returns_none():
    assert decode_wmi("XXXZE5ST9JF123456") is None
