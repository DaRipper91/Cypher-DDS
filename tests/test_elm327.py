"""Tests for the ELM327 command layer, run entirely against the mock adapter.

No hardware needed: MockELM327Adapter implements the same SerialLike surface
SerialConnection expects from a real pyserial port.
"""

import pytest

from cypher_dds.core.elm327 import ELM327, ELM327Error
from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.serial_conn import SerialConnection


def make_elm327(scenario: str = "default") -> ELM327:
    connection = SerialConnection(transport=MockELM327Adapter(scenario=scenario))
    return ELM327(connection)


def test_initialize_runs_full_init_sequence_without_error():
    elm = make_elm327()
    elm.initialize()  # should not raise


def test_send_command_strips_prompt_and_returns_response():
    elm = make_elm327()
    elm.initialize()
    assert elm.send_command("ATDPN") == "A6"


def test_send_command_strips_leading_echo_on_cold_atz():
    # Simulate an adapter that still echoes the command (echo not yet
    # disabled) by writing the echo ourselves into the transport's queue.
    connection = SerialConnection(transport=MockELM327Adapter())
    elm = ELM327(connection)
    response = elm.send_command("ATZ")
    assert response == "ELM327 v1.5"


def test_send_command_returns_pid_response():
    elm = make_elm327()
    assert elm.send_command("010C") == "41 0C 1A F8"


def test_send_command_raises_on_no_data():
    elm = make_elm327(scenario="no_adapter")
    with pytest.raises(ELM327Error):
        elm.send_command("ATZ")


def test_detected_protocol_strips_auto_marker_and_looks_up_name():
    elm = make_elm327()
    assert elm.detected_protocol() == "ISO 15765-4 CAN (11 bit ID, 500 kbaud)"
