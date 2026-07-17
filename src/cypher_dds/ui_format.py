"""Shared presentation formatting helpers for GUI/TUI surfaces."""

from __future__ import annotations

from cypher_dds.core.actions import DiagnosticAction
from cypher_dds.core.dtc import DTC
from cypher_dds.session import DEFAULT_LIVE_PIDS


def format_live_summary(values: dict[int, float | None]) -> str:
    parts = []
    for pid, label, unit in DEFAULT_LIVE_PIDS:
        value = values.get(pid)
        parts.append(f"{label}: {value:.0f} {unit}" if value is not None else f"{label}: —")
    return "   ".join(parts)


def format_dtc_summary(dtcs: tuple[DTC, ...]) -> str:
    if dtcs:
        codes = ", ".join(dtc.code for dtc in dtcs)
        return f"⚠ {len(dtcs)} DTC(S): {codes}"
    return "✓ NO CODES STORED"


def format_dtc_detail_lines(dtcs: tuple[DTC, ...]) -> str:
    if not dtcs:
        return "No stored DTC details."
    return "\n".join(
        f"{dtc.code} — {dtc.description}" if dtc.description else f"{dtc.code} — No description available"
        for dtc in dtcs
    )


def action_display_label(action: DiagnosticAction) -> str:
    return f"[{action.category.value}] {action.title} ({action.support_level.value})"


def action_category_labels(actions: tuple[DiagnosticAction, ...]) -> tuple[str, ...]:
    categories = sorted({action.category.value for action in actions})
    return ("all", *categories)

