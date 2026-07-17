"""VehicleProfile interface + registry.

Core logic never needs to know a profile exists; it just decodes standard
Mode 01/03/04/09 data. Profiles layer manufacturer-specific meaning on top:
P1xxx DTC descriptions and enhanced (Mode 22 or equivalent) PID tables.

Adding a new brand = writing a new VehicleProfile subclass and calling
register_profile() — no changes to cypher_dds.core, and no changes to other
profiles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from cypher_dds.core.actions import DiagnosticAction, default_profile_actions
from cypher_dds.profiles.catalog import ECUFamily, profile_ecu_families


@dataclass(frozen=True)
class EnhancedPID:
    pid: str  # manufacturer-specific PID identifier (format varies by brand)
    name: str
    description: str
    unit: str


class VehicleProfile(ABC):
    """Base class every brand plugin implements.

    Subclasses are expected to be stateless / effectively singletons — one
    instance represents "this brand's knowledge", not a live vehicle
    session.
    """

    #: Registry key, e.g. "gm". Must be unique across profiles.
    key: str

    #: Human-readable brand name, e.g. "General Motors".
    display_name: str

    #: WMI (VIN prefix) codes that map to this profile. Used by
    #: cypher_dds.core.vin for automatic profile selection.
    wmi_codes: tuple[str, ...] = ()

    @abstractmethod
    def get_dtc_description(self, code: str) -> str | None:
        """Look up a manufacturer-specific (typically P1xxx) DTC description.

        Return None if this profile doesn't know the code — caller should
        fall back to cypher_dds.core.dtc.GENERIC_DTC_TABLE.
        """

    @abstractmethod
    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        """Return this brand's enhanced/manufacturer PID table, if any."""

    def supported_actions(self) -> tuple[DiagnosticAction, ...]:
        """Return the declared bi-directional action catalog for this make.

        Subclasses can override this to add real OEM-specific routines once
        validated identifiers and safety rules are available.
        """
        return default_profile_actions(self.key, self.display_name)

    def ecu_families(self) -> tuple[ECUFamily, ...]:
        """Return the targeted ECU-family catalog for this make."""
        return profile_ecu_families(self.key)


_REGISTRY: dict[str, VehicleProfile] = {}


def register_profile(profile: VehicleProfile) -> None:
    _REGISTRY[profile.key] = profile


def get_profile(key: str) -> VehicleProfile | None:
    return _REGISTRY.get(key)


def all_profiles() -> dict[str, VehicleProfile]:
    return dict(_REGISTRY)
