"""Honda/Acura (2008+, CAN) vehicle profile.

Deliberately an empty stub for this phase — see toyota_lexus.py docstring
for why. Same interface, empty tables, proves the plugin architecture scales
to a new brand with zero core changes.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

DTC_TABLE: dict[str, str] = {}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = ()


class HondaAcuraProfile(VehicleProfile):
    key = "honda_acura"
    display_name = "Honda / Acura"
    wmi_codes = ("1HG", "19U", "JHM", "2HG")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(HondaAcuraProfile())
