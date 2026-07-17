"""Profile metadata catalog for ECU-family targeting and support reporting."""

from __future__ import annotations

from dataclasses import dataclass

from cypher_dds.core.actions import SupportLevel


@dataclass(frozen=True)
class ECUFamily:
    key: str
    name: str
    bus: str
    diagnostics_support: SupportLevel
    bidirectional_support: SupportLevel
    programming_support: SupportLevel
    notes: str


_COMMON_BUS_NOTE = "Standard OBD-II CAN / legacy emissions bus via ELM327 unless noted otherwise."

_ECU_FAMILY_TABLE: dict[str, tuple[ECUFamily, ...]] = {
    "gm": (
        ECUFamily("gm_pcm", "Powertrain Control Module (PCM/ECM)", _COMMON_BUS_NOTE, SupportLevel.IMPLEMENTED, SupportLevel.MOCK_ONLY, SupportLevel.BLOCKED, "Current repo coverage is centered here: VIN, Mode 01, Mode 03/04, and GM-specific DTC metadata."),
        ECUFamily("gm_tcm", "Transmission Control Module (TCM)", _COMMON_BUS_NOTE, SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for adaptation resets and temperature/shift routines after OEM command validation."),
        ECUFamily("gm_bcm", "Body Control Module (BCM)", "Body/chassis bus; reachability depends on gateway behavior and adapter limits.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for hidden-feature coding and option-byte changes."),
        ECUFamily("gm_abs", "ABS / ESC Module (EBCM)", "Chassis bus; often gateway-mediated on newer vehicles.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for automated bleed and service mode routines."),
        ECUFamily("gm_epb", "Electronic Parking Brake (EPB)", "Chassis bus; often integrated with ABS/ESC.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Planned brake service mode workflows."),
        ECUFamily("gm_srs", "SRS / Airbag Module", "Safety bus or gateway-protected diagnostics path.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Safety-critical area; read/reset work requires careful gating."),
        ECUFamily("gm_hvac", "HVAC / Comfort Control", "Body bus or gateway path.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Potential target for actuator tests and feature configuration."),
    ),
    "ford": (
        ECUFamily("ford_pcm", "Powertrain Control Module (PCM)", _COMMON_BUS_NOTE, SupportLevel.IMPLEMENTED, SupportLevel.MOCK_ONLY, SupportLevel.BLOCKED, "Current repo coverage is limited to emissions-bus-visible Ford diagnostics."),
        ECUFamily("ford_tcm", "Transmission Control Module (TCM)", _COMMON_BUS_NOTE, SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Candidate for relearn and adaptive reset routines."),
        ECUFamily("ford_bcm", "Body Control Module (BCM)", "Mostly MS-CAN on many 2008+ vehicles.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Ford body functions are constrained by the repo's documented MS-CAN limitation."),
        ECUFamily("ford_abs", "ABS / ESC Module", "Often HS-CAN reachable, but service routing varies by platform.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for brake bleed and chassis service routines."),
        ECUFamily("ford_epb", "Electronic Parking Brake", "Usually behind ABS/ESC or BCM service routing.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Planned service mode entry after ECU mapping."),
        ECUFamily("ford_srs", "Restraints Control Module (RCM)", "Safety bus / protected diagnostics path.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "No active SRS write support planned until safety gates mature."),
        ECUFamily("ford_cluster", "IPC / Instrument Cluster", "Often MS-CAN or gateway mediated.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Potential coding target if transport expands beyond current ELM327 assumptions."),
    ),
    "dodge_chrysler": (
        ECUFamily("mopar_pcm", "Powertrain Control Module (PCM/ECM)", _COMMON_BUS_NOTE, SupportLevel.IMPLEMENTED, SupportLevel.MOCK_ONLY, SupportLevel.BLOCKED, "Current repo support is read-oriented plus seed service actions."),
        ECUFamily("mopar_tcm", "Transmission Control Module (TCM)", _COMMON_BUS_NOTE, SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for quick-learn/adaptation workflows once command sets are validated."),
        ECUFamily("mopar_bcm", "Body Control Module (BCM/TIPM)", "Body/gateway path varies by platform.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for feature coding and body service routines."),
        ECUFamily("mopar_abs", "ABS / ESC Module", "Chassis network via gateway on newer platforms.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Brake bleed and calibration routines are planned."),
        ECUFamily("mopar_sgw", "Secure Gateway / Central Gateway", "Gateway path; authentication may be required on newer vehicles.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Gateway restrictions are a likely blocker for late-model bi-directional work."),
        ECUFamily("mopar_epb", "Electronic Parking Brake", "Typically routed through ABS/ESC or BCM.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Planned service mode support."),
        ECUFamily("mopar_srs", "Occupant Restraint Controller (ORC)", "Safety/protected diagnostics path.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Safety-critical; no write support until stronger protections exist."),
    ),
    "toyota_lexus": (
        ECUFamily("toyota_ecm", "Engine Control Module (ECM)", _COMMON_BUS_NOTE, SupportLevel.IMPLEMENTED, SupportLevel.MOCK_ONLY, SupportLevel.BLOCKED, "Current coverage is emissions-bus diagnostics plus Toyota/Lexus DTC metadata."),
        ECUFamily("toyota_tcm", "Transmission / ECT Control", _COMMON_BUS_NOTE, SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for adaptation resets and temperature-based service routines."),
        ECUFamily("toyota_bcm", "Body ECU / Main Body Control", "Body CAN / gateway path varies by platform.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Likely home for hidden-feature toggles and convenience coding."),
        ECUFamily("toyota_abs", "ABS / VSC Module", "Chassis network, often reachable through gatewayed diagnostics.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for brake bleed and yaw/zero-point procedures."),
        ECUFamily("toyota_epb", "Electronic Parking Brake", "Often integrated with brake control ECU.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Planned pad-service mode."),
        ECUFamily("toyota_srs", "Airbag / Occupant Restraint ECU", "Safety/protected path.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Read and clear workflows require additional safeguards."),
        ECUFamily("toyota_tpms", "Tire Pressure Monitoring System", "Body/chassis gateway path.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Candidate for ID registration and relearn support."),
    ),
    "honda_acura": (
        ECUFamily("honda_pcm", "Powertrain Control Module (PCM/ECM)", _COMMON_BUS_NOTE, SupportLevel.IMPLEMENTED, SupportLevel.MOCK_ONLY, SupportLevel.BLOCKED, "Current coverage is generic diagnostics plus Honda/Acura DTC metadata."),
        ECUFamily("honda_tcm", "Transmission Control Module (TCM)", _COMMON_BUS_NOTE, SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for clutch/shift adaptation routines."),
        ECUFamily("honda_micu", "MICU / Body Control", "Body multiplex network or gatewayed CAN path.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Candidate for comfort-feature coding and body actuator tests."),
        ECUFamily("honda_abs", "VSA / ABS Module", "Chassis path; OEM routing varies by generation.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for bleed and steering-angle related service routines."),
        ECUFamily("honda_epb", "Electronic Parking Brake", "Usually tied to VSA/ABS service functions.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Planned brake service mode."),
        ECUFamily("honda_srs", "SRS Unit", "Safety/protected diagnostics path.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Safety-critical; no write support in the current architecture."),
        ECUFamily("honda_hvac", "HVAC / Gauge / Convenience ECUs", "Body network or gateway path.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Potential target for actuator tests and feature toggles."),
    ),
    "kia": (
        ECUFamily("kia_ecm", "Engine Control Module (ECM/PCM)", _COMMON_BUS_NOTE, SupportLevel.IMPLEMENTED, SupportLevel.MOCK_ONLY, SupportLevel.BLOCKED, "Kia profile currently supports VIN routing and generic diagnostics; no Kia-specific write routines yet."),
        ECUFamily("kia_tcm", "Transmission Control Module (TCM)", _COMMON_BUS_NOTE, SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Likely early target for adaptation reset once a platform is chosen."),
        ECUFamily("kia_bcm", "Body Control Module (BCM)", "Body CAN / gateway path varies by platform.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Primary target for hidden-feature coding and convenience settings."),
        ECUFamily("kia_abs", "ABS / ESC Module", "Chassis network via gatewayed diagnostics.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Target for brake bleed and chassis service routines."),
        ECUFamily("kia_epb", "Electronic Parking Brake", "Often surfaced through brake controller routines.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Planned pad service mode and retract/extend routines."),
        ECUFamily("kia_srs", "SRS / Airbag Module", "Safety/protected diagnostics path.", SupportLevel.PLANNED, SupportLevel.BLOCKED, SupportLevel.BLOCKED, "Safety-critical; no write support in the current build."),
        ECUFamily("kia_tpms", "TPMS / Receiver Module", "Body/chassis network.", SupportLevel.PLANNED, SupportLevel.PLANNED, SupportLevel.BLOCKED, "Candidate for ID registration and relearn workflows."),
    ),
}


def profile_ecu_families(profile_key: str) -> tuple[ECUFamily, ...]:
    return _ECU_FAMILY_TABLE.get(profile_key, ())
