"""Tests for Mode 03/04 DTC byte decoding (pure logic) and DTCReader (mock)."""

import pytest

from cypher_dds.core.dtc import DTC, GENERIC_DTC_TABLE, DTCReader, decode_dtc_bytes
from cypher_dds.core.elm327 import ELM327
from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.serial_conn import SerialConnection


def test_decode_single_powertrain_dtc():
    # 0x03 0x01 -> "P0301" (Cylinder 1 Misfire Detected)
    assert decode_dtc_bytes(bytes([0x03, 0x01])) == ["P0301"]


def test_decode_multiple_dtcs():
    assert decode_dtc_bytes(bytes([0x03, 0x01, 0x01, 0x04])) == ["P0301", "P0104"]


def test_decode_all_four_letter_prefixes():
    # top 2 bits of the high byte select P/C/B/U
    assert decode_dtc_bytes(bytes([0x00, 0x01]))[0].startswith("P")
    assert decode_dtc_bytes(bytes([0x41, 0x01]))[0].startswith("C")
    assert decode_dtc_bytes(bytes([0x81, 0x01]))[0].startswith("B")
    assert decode_dtc_bytes(bytes([0xC1, 0x01]))[0].startswith("U")


def test_decode_skips_zero_padding_pair():
    assert decode_dtc_bytes(bytes([0x03, 0x01, 0x00, 0x00])) == ["P0301"]


def test_decode_odd_length_raises_value_error():
    with pytest.raises(ValueError):
        decode_dtc_bytes(bytes([0x03]))


def test_generic_dtc_table_has_seed_entries():
    assert GENERIC_DTC_TABLE["P0301"] == "Cylinder 1 Misfire Detected"
    assert "P0420" in GENERIC_DTC_TABLE  # catalyst efficiency, a common one


def test_dtc_reader_read_stored_against_mock_adapter():
    connection = SerialConnection(transport=MockELM327Adapter())
    reader = DTCReader(ELM327(connection))
    codes = reader.read_stored()
    assert codes == [
        DTC(code="P0301", description="Cylinder 1 Misfire Detected"),
        DTC(code="P0104", description=None),  # not in the generic seed table
    ]


def test_dtc_reader_clear_sends_mode_04():
    connection = SerialConnection(transport=MockELM327Adapter())
    reader = DTCReader(ELM327(connection))
    reader.clear()  # should not raise
