"""Tests for the minimal typed UDS request helpers."""

from cypher_dds.core.uds import (
    UDSRequest,
    diagnostic_session_control,
    parse_negative_response,
    read_data_by_identifier,
    tester_present as build_tester_present,
)


def test_uds_request_builds_command_hex_and_positive_prefix():
    request = UDSRequest(service_id=0x2E, data_identifier=0xF190, payload=b"\x01\x02")

    assert request.command_hex() == "2EF1900102"
    assert request.positive_response_prefix() == "6EF190"


def test_common_uds_helpers_encode_current_action_requests():
    assert build_tester_present().command_hex() == "3E00"
    assert build_tester_present().positive_response_prefix() == "7E00"

    assert diagnostic_session_control(0x03).command_hex() == "1003"
    assert diagnostic_session_control(0x03).positive_response_prefix() == "5003"

    assert read_data_by_identifier(0x1940).command_hex() == "221940"
    assert read_data_by_identifier(0x1940).positive_response_prefix() == "621940"


def test_parse_negative_response_extracts_service_and_code():
    negative = parse_negative_response("7F 10 22")

    assert negative is not None
    assert negative.service_id == 0x10
    assert negative.response_code == 0x22
    assert negative.code_name == "Conditions not correct"
