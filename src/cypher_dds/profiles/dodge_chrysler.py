"""Dodge/Chrysler (2008+, CAN) vehicle profile.

Priority 3 target.

Scope note: pre-2008 Chrysler group vehicles used SCI (Serial Communications
Interface), not CAN, and are out of scope for v1 — this profile assumes a
2008+ CAN-bus vehicle.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

# TODO: expand — this is a seed set to prove the shape.
DTC_TABLE: dict[str, str] = {
    # "P1494": "Leak Detection Pump Pressure Switch or Mechanical Fault",
}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = (
    # EnhancedPID(pid="22F440", name="TIPM_STATUS", description="Totally Integrated Power Module status", unit=""),
)


class DodgeChryslerProfile(VehicleProfile):
    key = "dodge_chrysler"
    display_name = "Dodge / Chrysler"
    wmi_codes = ("1C3", "1C4", "1C6", "2C3")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(DodgeChryslerProfile())
