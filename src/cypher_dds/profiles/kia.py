"""Kia (1996+; ISO 9141-2/KWP2000 pre-CAN, CAN on later platforms) vehicle profile.

Initial support is intentionally narrow: VIN/WMI routing plus a dedicated
profile entry in the plugin registry. Manufacturer-specific DTC coverage can
be expanded once validated Kia-specific tables are curated for this project.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

# TODO: populate with validated Kia manufacturer-specific P1xxx/B/C/U code
# definitions sourced for the markets/platforms this project targets.
DTC_TABLE: dict[str, str] = {}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = ()


class KiaProfile(VehicleProfile):
    key = "kia"
    display_name = "Kia"
    wmi_codes = ("KNA", "KND", "5XX", "5XY", "3KP")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(KiaProfile())
