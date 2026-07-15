"""Toyota/Lexus (1996+; ISO 9141-2/KWP2000 pre-2008, CAN 2008+) vehicle profile.

Deliberately an empty stub for this phase. Its job right now is to prove the
plugin architecture is truly brand-agnostic: this file follows the exact
same VehicleProfile interface as gm.py/ford.py/dodge_chrysler.py with empty
tables, and registers itself the same way. Filling in DTC_TABLE and
ENHANCED_PIDS later should require no changes anywhere else in the codebase.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

DTC_TABLE: dict[str, str] = {}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = ()


class ToyotaLexusProfile(VehicleProfile):
    key = "toyota_lexus"
    display_name = "Toyota / Lexus"
    wmi_codes = ("4T1", "4T3", "JTD", "JTH")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(ToyotaLexusProfile())
