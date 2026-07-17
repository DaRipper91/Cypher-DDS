"""Tests that the profile plugin architecture is actually brand-agnostic.

Most built-in profiles now carry real DTC data. Kia support starts with
registry + VIN routing and can grow its manufacturer-specific DTC/enhanced PID
coverage later without requiring changes in core/session code.
"""

from cypher_dds.profiles import base  # noqa: F401 (triggers registration)
from cypher_dds.profiles.base import all_profiles, get_profile
from cypher_dds.core.vehicle_coding import CodingFunctionStatus

EXPECTED_KEYS = {"gm", "ford", "dodge_chrysler", "toyota_lexus", "honda_acura", "kia"}


def test_all_builtin_profiles_are_registered():
    assert EXPECTED_KEYS.issubset(all_profiles().keys())


def test_all_profiles_follow_the_same_interface():
    for key in EXPECTED_KEYS:
        profile = get_profile(key)
        assert profile is not None
        assert profile.get_dtc_description("P0000") is None
        assert profile.enhanced_pids() == () or isinstance(profile.enhanced_pids(), tuple)
        assert profile.supported_actions()
        assert profile.coding_functions() == () or isinstance(profile.coding_functions(), tuple)


def test_unknown_profile_key_returns_none():
    assert get_profile("bmw") is None


def test_gm_profile_resolves_known_manufacturer_codes():
    gm = get_profile("gm")
    assert gm.get_dtc_description("P1031") == (
        "HO2S Heater Current Monitor Control Circuit Banks 1 and 2 Sensor 1"
    )
    assert gm.get_dtc_description("P0301") is None  # generic code, not GM's table
    assert gm.get_dtc_description("P9999") is None  # not a real code


def test_ford_profile_resolves_known_manufacturer_codes():
    ford = get_profile("ford")
    assert ford.get_dtc_description("P1000") == "OBD System Readiness Test Not Complete"
    assert ford.get_dtc_description("P0420") is None  # generic code, not Ford's table
    assert ford.get_dtc_description("P9999") is None  # not a real code


def test_dodge_chrysler_profile_resolves_known_manufacturer_codes():
    mopar = get_profile("dodge_chrysler")
    assert mopar.get_dtc_description("P1494") == "Leak Detection Pump Switch or Mechanical Fault"
    assert mopar.get_dtc_description("P0301") is None  # generic code, not Chrysler's table
    assert mopar.get_dtc_description("P9999") is None  # not a real code


def test_toyota_lexus_profile_resolves_known_manufacturer_codes():
    toyota = get_profile("toyota_lexus")
    assert toyota.get_dtc_description("P1120") == "Accelerator Pedal Position Sensor Circuit"
    assert toyota.get_dtc_description("P0420") is None  # generic code, not Toyota's table
    assert toyota.get_dtc_description("P9999") is None  # not a real code


def test_honda_acura_profile_resolves_known_manufacturer_codes():
    honda = get_profile("honda_acura")
    assert honda.get_dtc_description("P1201") == "Cylinder 1 Misfire"
    assert honda.get_dtc_description("P0300") is None  # generic code, not Honda's table
    assert honda.get_dtc_description("P9999") is None  # not a real code


def test_kia_profile_registers_and_exposes_same_interface():
    kia = get_profile("kia")
    assert kia is not None
    assert kia.display_name == "Kia"
    assert kia.get_dtc_description("P0000") is None
    assert kia.enhanced_pids() == ()


def test_gm_and_ford_enhanced_pids_are_populated():
    gm_pids = {p.name: p for p in get_profile("gm").enhanced_pids()}
    assert gm_pids["TRANS_FLUID_TEMP"].pid == "221940"

    ford_pids = {p.name: p for p in get_profile("ford").enhanced_pids()}
    assert ford_pids["TRANS_FLUID_TEMP"].pid == "221E1C"
    assert ford_pids["ENGINE_OIL_TEMP"].pid == "221310"


def test_vehicle_tied_coding_functions_are_seeded_for_target_profiles():
    ford_functions = get_profile("ford").coding_functions()
    gm_functions = get_profile("gm").coding_functions()
    mopar_functions = get_profile("dodge_chrysler").coding_functions()

    assert len(ford_functions) == 6
    assert len(gm_functions) == 12
    assert len(mopar_functions) == 8
    assert all(function.status == CodingFunctionStatus.RESEARCH for function in ford_functions)
    assert all(function.target_function == "disable_auto_stop_start_persistent" for function in gm_functions)
    assert any(function.brand == "Jeep" for function in mopar_functions)
