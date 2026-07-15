"""Dodge/Chrysler (1996+) vehicle profile.

ISO 9141-2 / ISO 14230-4 KWP2000 pre-2008, CAN 2008+ — the ELM327's
protocol auto-detect handles the difference transparently, so this profile
(and cypher_dds.core) applies unchanged across the whole range. Priority 3
target.

Scope note: some Chrysler-group vehicles also run a proprietary SCI/CCD bus
for body and instrument-cluster diagnostics, separate from the standard
OBD2 pins a basic ELM327 talks to. Like Ford's MS-CAN, that bus is out of
scope for v1 — this profile only covers what's reachable on the standard,
federally-mandated OBD2 protocol.
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
