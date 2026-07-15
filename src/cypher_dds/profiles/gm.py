"""GM (2008+, CAN 11-bit) vehicle profile.

Priority 1 target — standard-heavy, well-documented enhanced PIDs available
in the aftermarket scanner community. Tables below are seeds; expand as
documentation is gathered.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

# TODO: expand — this is a seed set to prove the shape.
DTC_TABLE: dict[str, str] = {
    # "P0446": "Evaporative Emission Control System Vent Control Circuit",
}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = (
    # EnhancedPID(pid="221E37", name="TRANS_FLUID_TEMP", description="Transmission fluid temperature", unit="°C"),
)


class GMProfile(VehicleProfile):
    key = "gm"
    display_name = "General Motors"
    wmi_codes = ("1G1", "1GC", "1GT", "3GN")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(GMProfile())
