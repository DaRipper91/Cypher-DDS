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


@dataclass(frozen=True)
class DiagnosticAction:
    key: str
    title: str
    description: str
    category: ActionCategory
    commands: tuple[str, ...] = ()
    expected_prefixes: tuple[str, ...] = ()
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


def default_profile_actions(profile_key: str, display_name: str) -> tuple[DiagnosticAction, ...]:
    """Baseline action catalog shown for every make until OEM-specific coverage grows."""
    prefix = f"{profile_key}."
    return (
        DiagnosticAction(
            key=f"{prefix}clear_emissions_dtcs",
            title="Clear emissions DTCs",
            description="Send OBD-II Mode 04 to clear stored emissions-related trouble codes.",
            category=ActionCategory.SERVICE,
            commands=("04",),
            expected_prefixes=("44",),
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
            commands=("3E00",),
            expected_prefixes=("7E00",),
        ),
        DiagnosticAction(
            key=f"{prefix}enter_extended_session",
            title="Enter extended diagnostic session",
            description=(
                f"Request UDS extended diagnostic session on {display_name}. This is a prerequisite "
                "for many active tests and coding flows on modern ECUs."
            ),
            category=ActionCategory.SERVICE,
            commands=("1003",),
            expected_prefixes=("5003",),
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
    if not action.supported or not action.commands:
        raise UnsupportedActionError(f"Action {action.key!r} is declared but not executable yet")
    if action.mutates_vehicle_state and not confirm_write:
        raise ActionConfirmationRequiredError(
            f"Action {action.key!r} mutates vehicle state and requires confirm_write=True"
        )

    responses: list[str] = []
    for index, command in enumerate(action.commands):
        response = elm327.send_command(command)
        responses.append(response)

        if index < len(action.expected_prefixes):
            expected = _compact_hex(action.expected_prefixes[index])
            actual = _compact_hex(response)
            if not actual.startswith(expected):
                raise ActionResponseError(
                    f"Action {action.key!r} expected response prefix {expected!r}, got {response!r}"
                )

    return ActionResult(action=action, responses=tuple(responses))
