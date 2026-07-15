"""Ford (1996+) vehicle profile.

J1850 PWM pre-2008, CAN 2008+ — the ELM327's protocol auto-detect handles
the difference transparently, so this profile (and cypher_dds.core) applies
unchanged across the whole range. Priority 2 target.

IMPORTANT — MS-CAN limitation (2008+ vehicles): Ford splits vehicle data
across the standard diagnostic CAN bus and a proprietary MS-CAN
(medium-speed CAN, typically body and comfort systems). A basic ELM327
adapter only has visibility into the standard OBD2 bus. Cypher-DDS v1 does
NOT attempt to bridge or access MS-CAN — anything living there (many body
control / comfort PIDs) is simply unreachable through this tool for now.
Do not treat missing Ford data as a bug without checking whether it's an
MS-CAN-only parameter first.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

# TODO: expand — standard-CAN-reachable P1xxx codes only (see module docstring).
DTC_TABLE: dict[str, str] = {
    # "P1000": "OBD System Readiness Test Not Complete",
}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = (
    # Only PIDs confirmed reachable on the standard OBD2 CAN bus belong here.
)


class FordProfile(VehicleProfile):
    key = "ford"
    display_name = "Ford"
    wmi_codes = ("1FA", "1FT", "1FM", "3FA")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(FordProfile())
