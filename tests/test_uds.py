"""Tests for the minimal typed UDS request helpers."""

from cypher_dds.core.uds import (
    UDSRequest,
    diagnostic_session_control,
    parse_negative_response,
    read_data_by_identifier,
    routine_control,
    security_access_request_seed,
    security_access_send_key,
    tester_present as build_tester_present,
    write_data_by_identifier,
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


def test_phase_three_uds_helpers_encode_write_security_and_routine_requests():
    assert write_data_by_identifier(0x1234, b"\xAA\x55").command_hex() == "2E1234AA55"
    assert write_data_by_identifier(0x1234, b"\xAA\x55").positive_response_prefix() == "6E1234"

    assert security_access_request_seed(0x01).command_hex() == "2701"
    assert security_access_request_seed(0x01).positive_response_prefix() == "6701"

    assert security_access_send_key(0x02, b"\x10\x20").command_hex() == "27021020"
    assert security_access_send_key(0x02, b"\x10\x20").positive_response_prefix() == "6702"

    assert routine_control(0x01, 0xFF00, b"\x99").command_hex() == "3101FF0099"
    assert routine_control(0x01, 0xFF00, b"\x99").positive_response_prefix() == "7101FF00"
