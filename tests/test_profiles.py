"""Tests that the profile plugin architecture is actually brand-agnostic.

All five v1 profiles now carry real DTC data (Toyota/Lexus and Honda/Acura
were originally empty stubs specifically to prove new brands slot in via
the same interface with zero core changes — that architectural point still
holds, it's just that all five profiles are "full" now). Enhanced PIDs
remain a stub for Dodge/Chrysler/Toyota/Lexus/Honda/Acura; only GM and Ford
have any so far.
"""

from cypher_dds.profiles import base  # noqa: F401 (triggers registration)
from cypher_dds.profiles.base import all_profiles, get_profile

EXPECTED_KEYS = {"gm", "ford", "dodge_chrysler", "toyota_lexus", "honda_acura"}


def test_all_five_v1_profiles_are_registered():
    assert EXPECTED_KEYS.issubset(all_profiles().keys())


def test_all_profiles_follow_the_same_interface():
    for key in EXPECTED_KEYS:
        profile = get_profile(key)
        assert profile is not None
        assert profile.get_dtc_description("P0000") is None
        assert profile.enhanced_pids() == () or isinstance(profile.enhanced_pids(), tuple)


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


def test_gm_and_ford_enhanced_pids_are_populated():
    gm_pids = {p.name: p for p in get_profile("gm").enhanced_pids()}
    assert gm_pids["TRANS_FLUID_TEMP"].pid == "221940"

    ford_pids = {p.name: p for p in get_profile("ford").enhanced_pids()}
    assert ford_pids["TRANS_FLUID_TEMP"].pid == "221E1C"
    assert ford_pids["ENGINE_OIL_TEMP"].pid == "221310"
