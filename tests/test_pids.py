"""Tests for Mode 01 PID decoding math.

Pure logic, no hardware needed.
"""

import pytest

from cypher_dds.core.elm327 import ELM327
from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.pids import STANDARD_PIDS, build_request, decode_pid, read_pid
from cypher_dds.core.serial_conn import SerialConnection


def test_standard_pids_table_has_expected_entries():
    assert 0x0C in STANDARD_PIDS  # RPM
    assert 0x0D in STANDARD_PIDS  # speed
    assert STANDARD_PIDS[0x0C].name == "RPM"


def test_decode_rpm():
    # RPM = ((A * 256) + B) / 4
    assert decode_pid(0x0C, bytes([0x1A, 0xF8])) == 1726.0


def test_decode_coolant_temp():
    # Coolant temp = A - 40
    assert decode_pid(0x05, bytes([0x7B])) == 83.0


def test_decode_intake_temp():
    assert decode_pid(0x0F, bytes([0x28])) == 0.0


def test_decode_speed():
    assert decode_pid(0x0D, bytes([0x5A])) == 90.0


def test_decode_maf():
    # MAF = ((A * 256) + B) / 100
    assert decode_pid(0x10, bytes([0x01, 0xF4])) == 5.0


def test_decode_throttle_position():
    assert decode_pid(0x11, bytes([0xFF])) == pytest.approx(100.0)
    assert decode_pid(0x11, bytes([0x00])) == 0.0


def test_decode_fuel_level():
    assert decode_pid(0x2F, bytes([0x80])) == pytest.approx(50.196, rel=1e-3)


def test_decode_unknown_pid_raises_key_error():
    with pytest.raises(KeyError):
        decode_pid(0x99, bytes([0x00]))


def test_decode_wrong_length_raises_value_error():
    with pytest.raises(ValueError):
        decode_pid(0x0C, bytes([0x1A]))  # RPM needs 2 bytes, not 1


def test_build_request():
    assert build_request(0x0C) == "010C"
    assert build_request(0x05) == "0105"


def test_build_request_unknown_pid_raises_key_error():
    with pytest.raises(KeyError):
        build_request(0x99)


def test_read_pid_against_mock_adapter():
    connection = SerialConnection(transport=MockELM327Adapter())
    elm = ELM327(connection)
    assert read_pid(elm, 0x0C) == 1726.0  # RPM
    assert read_pid(elm, 0x05) == 83.0  # coolant temp
