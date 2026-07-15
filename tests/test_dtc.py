"""Tests for Mode 03/04 DTC byte decoding (pure logic, no hardware)."""

import pytest

from cypher_dds.core.dtc import decode_dtc_bytes


@pytest.mark.skip(reason="decode_dtc_bytes not implemented yet")
def test_decode_single_powertrain_dtc():
    # 0x03 0x01 -> "P0301" (Cylinder 1 Misfire Detected)
    assert decode_dtc_bytes(bytes([0x03, 0x01])) == ["P0301"]
