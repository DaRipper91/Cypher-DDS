"""Bi-directional diagnostic action framework.

This layer is intentionally narrower than "programming a car." It provides a
manufacturer-agnostic way to declare executable diagnostic actions, enforce
write confirmations, and validate expected positive responses. OEM-specific
profiles can override or extend these manifests with real ECU-level routines
as documentation is gathered.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cypher_dds.core.elm327 import ELM327
from cypher_dds.core.uds import (
    UDSRequest,
    diagnostic_session_control,
    parse_negative_response,
    tester_present,
)


class ActionCategory(StrEnum):
    SERVICE = "service"
    ACTIVE_TEST = "active_test"
    CODING = "coding"
    PROGRAMMING = "programming"


class SupportLevel(StrEnum):
    IMPLEMENTED = "implemented"
    MOCK_ONLY = "mock_only"
    PLANNED = "planned"
    BLOCKED = "blocked"
    OUT_OF_SCOPE = "out_of_scope"


class ActionError(RuntimeError):
    """Base exception for bi-directional action failures."""


class ActionNotFoundError(ActionError):
    """Raised when a requested action key is not defined."""


class UnsupportedActionError(ActionError):
    """Raised when an action is declared but not yet executable."""


class ActionConfirmationRequiredError(ActionError):
    """Raised when a mutating action is requested without explicit confirmation."""


class ActionResponseError(ActionError):
    """Raised when an ECU response does not match the manifest expectation."""


class UDSNegativeResponseError(ActionResponseError):
    """Raised when a UDS service returns an explicit negative response."""


class AdapterTier(StrEnum):
    BASIC_ELM327 = "basic_elm327"
    CAN_UDS = "can_uds"
    CAN_UDS_SECURITY = "can_uds_security"


@dataclass(frozen=True)
class DiagnosticAction:
    key: str
    title: str
    description: str
    category: ActionCategory
    uds_requests: tuple[UDSRequest, ...] = ()
    commands: tuple[str, ...] = ()
    expected_prefixes: tuple[str, ...] = ()
    target_ecu_family: str | None = None
    required_session: int | None = None
    security_access_level: int | None = None
    adapter_tier: AdapterTier = AdapterTier.BASIC_ELM327
    supported: bool = True
    support_level: SupportLevel = SupportLevel.IMPLEMENTED
    mutates_vehicle_state: bool = False
    danger_note: str | None = None


@dataclass(frozen=True)
class ActionResult:
    action: DiagnosticAction
    responses: tuple[str, ...]


def _compact_hex(value: str) -> str:
    return "".join(value.upper().split())


def _default_ecu_targets(profile_key: str) -> dict[str, str]:
    explicit_targets = {
        "gm": {
            "pcm": "gm_pcm",
            "tcm": "gm_tcm",
            "bcm": "gm_bcm",
            "abs": "gm_abs",
            "epb": "gm_epb",
        },
        "ford": {
            "pcm": "ford_pcm",
            "tcm": "ford_tcm",
            "bcm": "ford_bcm",
            "abs": "ford_abs",
            "epb": "ford_epb",
        },
        "dodge_chrysler": {
            "pcm": "mopar_pcm",
            "tcm": "mopar_tcm",
            "bcm": "mopar_bcm",
            "abs": "mopar_abs",
            "epb": "mopar_epb",
        },
        "toyota_lexus": {
            "pcm": "toyota_ecm",
            "tcm": "toyota_tcm",
            "bcm": "toyota_bcm",
            "abs": "toyota_abs",
            "epb": "toyota_epb",
        },
        "honda_acura": {
            "pcm": "honda_pcm",
            "tcm": "honda_tcm",
            "bcm": "honda_micu",
            "abs": "honda_abs",
            "epb": "honda_epb",
        },
        "kia": {
            "pcm": "kia_ecm",
            "tcm": "kia_tcm",
            "bcm": "kia_bcm",
            "abs": "kia_abs",
            "epb": "kia_epb",
        },
    }
    return explicit_targets[profile_key]


def default_profile_actions(profile_key: str, display_name: str) -> tuple[DiagnosticAction, ...]:
    """Baseline action catalog shown for every make until OEM-specific coverage grows."""
    prefix = f"{profile_key}."
    ecu_targets = _default_ecu_targets(profile_key)
    return (
        DiagnosticAction(
            key=f"{prefix}clear_emissions_dtcs",
            title="Clear emissions DTCs",
            description="Send OBD-II Mode 04 to clear stored emissions-related trouble codes.",
            category=ActionCategory.SERVICE,
            commands=("04",),
            expected_prefixes=("44",),
            target_ecu_family=ecu_targets["pcm"],
            mutates_vehicle_state=True,
            danger_note="Clearing DTCs can reset readiness monitors.",
        ),
        DiagnosticAction(
            key=f"{prefix}tester_present",
            title="Tester present keepalive",
            description=(
                f"Send a UDS tester-present keepalive on {display_name} so a diagnostic session "
                "does not time out during deeper workflows."
            ),
            category=ActionCategory.SERVICE,
            uds_requests=(tester_present(),),
            target_ecu_family=ecu_targets["pcm"],
            adapter_tier=AdapterTier.CAN_UDS,
        ),
        DiagnosticAction(
            key=f"{prefix}enter_extended_session",
            title="Enter extended diagnostic session",
            description=(
                f"Request UDS extended diagnostic session on {display_name}. This is a prerequisite "
                "for many active tests and coding flows on modern ECUs."
            ),
            category=ActionCategory.SERVICE,
            uds_requests=(diagnostic_session_control(0x03),),
            target_ecu_family=ecu_targets["pcm"],
            required_session=0x03,
            adapter_tier=AdapterTier.CAN_UDS,
        ),
        DiagnosticAction(
            key=f"{prefix}powertrain_output_control",
            title="Powertrain output control",
            description=(
                f"Planned actuator/output tests for {display_name} powertrain ECUs. This covers "
                "functions such as fan relays, purge valves, injector cut, and throttle routines "
                "once ECU-specific identifiers and preconditions are validated."
            ),
            category=ActionCategory.ACTIVE_TEST,
            target_ecu_family=ecu_targets["pcm"],
            required_session=0x03,
            adapter_tier=AdapterTier.CAN_UDS,
            supported=False,
            support_level=SupportLevel.PLANNED,
            mutates_vehicle_state=True,
            danger_note="Output controls can start actuators unexpectedly if preconditions are wrong.",
        ),
        DiagnosticAction(
            key=f"{prefix}body_control_coding",
            title="Body control coding",
            description=(
                f"Planned coding/adaptation entry point for {display_name} body control modules. "
                "Target scope includes feature flags, option bytes, and adaptation resets after "
                "OEM-specific identifiers are validated."
            ),
            category=ActionCategory.CODING,
            target_ecu_family=ecu_targets["bcm"],
            required_session=0x03,
            security_access_level=1,
            adapter_tier=AdapterTier.CAN_UDS_SECURITY,
            supported=False,
            support_level=SupportLevel.PLANNED,
            mutates_vehicle_state=True,
            danger_note="Coding changes can alter configuration and disable features if written incorrectly.",
        ),
        DiagnosticAction(
            key=f"{prefix}transmission_adaptation_reset",
            title="Transmission adaptation reset",
            description=(
                f"Planned service routine for {display_name} transmission control modules. This "
                "would cover adaptation reset and clutch/shift relearn entry points where the OEM "
                "documents a routine control path."
            ),
            category=ActionCategory.SERVICE,
            target_ecu_family=ecu_targets["tcm"],
            required_session=0x03,
            adapter_tier=AdapterTier.CAN_UDS,
            supported=False,
            support_level=SupportLevel.PLANNED,
            mutates_vehicle_state=True,
            danger_note="Resetting transmission adaptations can degrade drivability until relearn completes.",
        ),
        DiagnosticAction(
            key=f"{prefix}abs_bleed_service",
            title="ABS bleed service mode",
            description=(
                f"Planned brake service routine for {display_name} ABS/ESC modules. Requires "
                "OEM-specific routine identifiers and strict hydraulic service procedures."
            ),
            category=ActionCategory.SERVICE,
            target_ecu_family=ecu_targets["abs"],
            required_session=0x03,
            adapter_tier=AdapterTier.CAN_UDS,
            supported=False,
            support_level=SupportLevel.PLANNED,
            mutates_vehicle_state=True,
            danger_note="Brake service routines are safety-critical and must only run during controlled service work.",
        ),
        DiagnosticAction(
            key=f"{prefix}epb_service_mode",
            title="EPB service mode",
            description=(
                f"Planned electronic parking brake service routine for {display_name}. Intended "
                "for pad replacement/service mode once the ECU path is validated."
            ),
            category=ActionCategory.SERVICE,
            target_ecu_family=ecu_targets["epb"],
            required_session=0x03,
            adapter_tier=AdapterTier.CAN_UDS,
            supported=False,
            support_level=SupportLevel.PLANNED,
            mutates_vehicle_state=True,
            danger_note="EPB service routines physically move brake actuators.",
        ),
        DiagnosticAction(
            key=f"{prefix}module_programming",
            title="Module programming",
            description=(
                f"Reserved for future {display_name} firmware/calibration workflows. Flash "
                "programming is deliberately blocked until transport, security access, power "
                "management, file validation, and recovery support exist."
            ),
            category=ActionCategory.PROGRAMMING,
            target_ecu_family=ecu_targets["pcm"],
            required_session=0x02,
            security_access_level=1,
            adapter_tier=AdapterTier.CAN_UDS_SECURITY,
            supported=False,
            support_level=SupportLevel.BLOCKED,
            mutates_vehicle_state=True,
            danger_note="Programming can brick modules if transport, power, or files are wrong.",
        ),
    )


def execute_action(
    elm327: ELM327, action: DiagnosticAction, *, confirm_write: bool = False
) -> ActionResult:
    """Execute one declared action and verify expected positive responses."""
    commands = action.commands
    expected_prefixes = action.expected_prefixes
    if action.uds_requests:
        commands = tuple(request.command_hex() for request in action.uds_requests)
        if not expected_prefixes:
            expected_prefixes = tuple(
                request.positive_response_prefix() for request in action.uds_requests
            )

    if not action.supported or not commands:
        raise UnsupportedActionError(f"Action {action.key!r} is declared but not executable yet")
    if action.mutates_vehicle_state and not confirm_write:
        raise ActionConfirmationRequiredError(
            f"Action {action.key!r} mutates vehicle state and requires confirm_write=True"
        )

    responses: list[str] = []
    for index, command in enumerate(commands):
        response = elm327.send_command(command)
        responses.append(response)

        negative_response = parse_negative_response(response)
        if negative_response is not None:
            raise UDSNegativeResponseError(
                f"Action {action.key!r} failed: {negative_response.summary()}"
            )

        if index < len(expected_prefixes):
            expected = _compact_hex(expected_prefixes[index])
            actual = _compact_hex(response)
            if not actual.startswith(expected):
                raise ActionResponseError(
                    f"Action {action.key!r} expected response prefix {expected!r}, got {response!r}"
                )

    return ActionResult(action=action, responses=tuple(responses))
