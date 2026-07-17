"""Vehicle-tied coding function metadata.

These entries describe persistent configuration/write routines that are tied to
specific vehicle groups and ECU targets. They are intentionally separate from
the generic action catalog, which is broader and more protocol-oriented.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cypher_dds.core.actions import AdapterTier


class CodingFunctionStatus(StrEnum):
    RESEARCH = "research"
    CONFIRMED = "confirmed"
    IMPLEMENTED = "implemented"
    TESTED = "tested"


@dataclass(frozen=True)
class VehicleCodingFunction:
    key: str
    title: str
    profile_key: str
    brand: str
    model: str
    platform: str
    years: str
    target_function: str
    powertrain_notes: str | None = None
    module_name: str | None = None
    access_level: str | None = None
    adapter_tier: AdapterTier | None = None
    target_ecu_family: str | None = None
    required_session: int | None = None
    security_access_level: int | None = None
    procedure_summary: str | None = None
    write_identifier: int | None = None
    routine_identifier: int | None = None
    rollback_value: str | None = None
    verification_source: str | None = None
    status: CodingFunctionStatus = CodingFunctionStatus.RESEARCH
