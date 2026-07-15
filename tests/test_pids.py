"""Tests for Mode 01 PID decoding math.

Pure logic, no hardware needed. Fill these in as pids.py decode formulas
land — this is the highest-value test target in the project since it's
testable in full without a physical adapter.
"""

import pytest

from cypher_dds.core.pids import STANDARD_PIDS, decode_pid


def test_standard_pids_table_has_expected_entries():
    assert 0x0C in STANDARD_PIDS  # RPM
    assert 0x0D in STANDARD_PIDS  # speed
    assert STANDARD_PIDS[0x0C].name == "RPM"


@pytest.mark.skip(reason="decode formulas not implemented yet")
def test_decode_rpm():
    # RPM = ((A * 256) + B) / 4
    assert decode_pid(0x0C, bytes([0x1A, 0xF8])) == 1726.0


@pytest.mark.skip(reason="decode formulas not implemented yet")
def test_decode_coolant_temp():
    # Coolant temp = A - 40
    assert decode_pid(0x05, bytes([0x7B])) == 83.0
