"""Tests for the bi-directional action manifest and execution layer."""

import cypher_dds.profiles  # noqa: F401 — registers all built-in vehicle profiles
from cypher_dds.core.actions import (
    ActionCategory,
    ActionConfirmationRequiredError,
    ActionNotFoundError,
    SupportLevel,
    UnsupportedActionError,
)
from cypher_dds.profiles.base import get_profile
from cypher_dds.session import DiagnosticSession


def test_all_current_profiles_expose_action_catalogs():
    for key in ("gm", "ford", "dodge_chrysler", "toyota_lexus", "honda_acura", "kia"):
        profile = get_profile(key)
        assert profile is not None

        actions = {action.key: action for action in profile.supported_actions()}
        assert f"{key}.clear_emissions_dtcs" in actions
        assert f"{key}.tester_present" in actions
        assert f"{key}.enter_extended_session" in actions
        assert f"{key}.powertrain_output_control" in actions
        assert f"{key}.body_control_coding" in actions
        assert f"{key}.module_programming" in actions

    gm_actions = {action.key: action for action in get_profile("gm").supported_actions()}
    assert "gm.read_trans_fluid_temp" in gm_actions

    ford_actions = {action.key: action for action in get_profile("ford").supported_actions()}
    assert "ford.read_trans_fluid_temp" in ford_actions
    assert "ford.read_engine_oil_temp" in ford_actions


def test_action_catalog_exposes_service_and_future_write_categories():
    profile = get_profile("kia")
    categories = {action.category for action in profile.supported_actions()}
    assert categories == {
        ActionCategory.SERVICE,
        ActionCategory.ACTIVE_TEST,
        ActionCategory.CODING,
        ActionCategory.PROGRAMMING,
    }
    actions = {action.key: action for action in profile.supported_actions()}
    assert actions["kia.clear_emissions_dtcs"].support_level == SupportLevel.IMPLEMENTED
    assert actions["kia.body_control_coding"].support_level == SupportLevel.PLANNED
    assert actions["kia.module_programming"].support_level == SupportLevel.BLOCKED


def test_run_action_requires_explicit_confirmation_for_mutating_commands():
    session = DiagnosticSession()
    session.connect()
    session.resolve_vehicle()

    try:
        session.run_action("gm.clear_emissions_dtcs")
    except ActionConfirmationRequiredError:
        pass
    else:
        raise AssertionError("expected ActionConfirmationRequiredError")


def test_run_action_executes_mock_supported_service_commands():
    session = DiagnosticSession()
    session.connect()
    session.resolve_vehicle()

    keepalive = session.run_action("gm.tester_present")
    assert keepalive.responses == ("7E 00",)

    extended = session.run_action("gm.enter_extended_session")
    assert extended.responses == ("50 03",)

    cleared = session.run_action("gm.clear_emissions_dtcs", confirm_write=True)
    assert cleared.responses == ("44",)

    gm_enhanced = session.run_action("gm.read_trans_fluid_temp")
    assert gm_enhanced.responses == ("62 19 40 5A",)


def test_run_action_executes_ford_oem_action_pack_against_ford_mock():
    session = DiagnosticSession()
    session.connect(mock_scenario="ford")
    vin_info = session.resolve_vehicle()

    assert vin_info is not None
    assert vin_info.manufacturer == "ford"

    trans_temp = session.run_action("ford.read_trans_fluid_temp")
    assert trans_temp.responses == ("62 1E 1C 13 88",)

    oil_temp = session.run_action("ford.read_engine_oil_temp")
    assert oil_temp.responses == ("62 13 10 13 88",)


def test_run_action_rejects_unknown_or_placeholder_actions():
    session = DiagnosticSession()
    session.connect()
    session.resolve_vehicle()

    try:
        session.run_action("gm.not_a_real_action")
    except ActionNotFoundError:
        pass
    else:
        raise AssertionError("expected ActionNotFoundError")

    try:
        session.run_action("gm.body_control_coding")
    except UnsupportedActionError:
        pass
    else:
        raise AssertionError("expected UnsupportedActionError")


def test_all_current_profiles_expose_ecu_family_catalogs():
    for key in ("gm", "ford", "dodge_chrysler", "toyota_lexus", "honda_acura", "kia"):
        profile = get_profile(key)
        families = profile.ecu_families()
        assert families
        assert all(family.key for family in families)
