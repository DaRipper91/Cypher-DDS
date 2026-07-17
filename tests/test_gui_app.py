from cypher_dds.core.actions import ActionCategory, DiagnosticAction, SupportLevel
from cypher_dds.core.dtc import DTC
from cypher_dds.ui_format import (
    action_category_labels,
    action_display_label,
    format_dtc_detail_lines,
    format_dtc_summary,
    format_live_summary,
)


def test_format_live_summary_renders_default_pid_labels():
    summary = format_live_summary({0x0C: 1726.0, 0x0D: 90.0, 0x05: 83.0})

    assert "RPM: 1726 rpm" in summary
    assert "Speed: 90 km/h" in summary
    assert "Coolant: 83 °C" in summary


def test_format_dtc_summary_and_detail_lines_include_descriptions():
    dtcs = (
        DTC(code="P0301", description="Cylinder 1 Misfire Detected"),
        DTC(code="P0104", description=None),
    )

    assert format_dtc_summary(dtcs) == "⚠ 2 DTC(S): P0301, P0104"

    detail_lines = format_dtc_detail_lines(dtcs)
    assert "P0301 — Cylinder 1 Misfire Detected" in detail_lines
    assert "P0104 — No description available" in detail_lines


def test_format_dtc_helpers_render_empty_state():
    assert format_dtc_summary(()) == "✓ NO CODES STORED"
    assert format_dtc_detail_lines(()) == "No stored DTC details."


def test_action_display_label_uses_category_and_support_level():
    action = DiagnosticAction(
        key="gm.clear_emissions_dtcs",
        title="Clear emissions DTCs",
        description="Clear stored emissions codes.",
        category=ActionCategory.SERVICE,
        support_level=SupportLevel.IMPLEMENTED,
    )

    assert action_display_label(action) == "[service] Clear emissions DTCs (implemented)"


def test_action_category_labels_returns_all_plus_sorted_categories():
    actions = (
        DiagnosticAction(
            key="gm.clear_emissions_dtcs",
            title="Clear emissions DTCs",
            description="Clear stored emissions codes.",
            category=ActionCategory.SERVICE,
            support_level=SupportLevel.IMPLEMENTED,
        ),
        DiagnosticAction(
            key="gm.body_control_coding",
            title="Body control coding",
            description="Body control routines.",
            category=ActionCategory.CODING,
            support_level=SupportLevel.PLANNED,
        ),
    )

    assert action_category_labels(actions) == ("all", "coding", "service")
