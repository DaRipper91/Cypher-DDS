"""Tests that the profile plugin architecture is actually brand-agnostic.

The Toyota/Lexus and Honda/Acura stubs exist specifically to prove new
brands slot in via the same interface with zero core changes — these tests
check that registration and lookup work uniformly across full and stub
profiles alike.
"""

from cypher_dds.profiles import base  # noqa: F401 (triggers registration)
from cypher_dds.profiles.base import all_profiles, get_profile

EXPECTED_KEYS = {"gm", "ford", "dodge_chrysler", "toyota_lexus", "honda_acura"}


def test_all_five_v1_profiles_are_registered():
    assert EXPECTED_KEYS.issubset(all_profiles().keys())


def test_stub_profiles_follow_same_interface_as_full_profiles():
    for key in EXPECTED_KEYS:
        profile = get_profile(key)
        assert profile is not None
        assert profile.get_dtc_description("P0000") is None
        assert profile.enhanced_pids() == () or isinstance(profile.enhanced_pids(), tuple)


def test_unknown_profile_key_returns_none():
    assert get_profile("bmw") is None
