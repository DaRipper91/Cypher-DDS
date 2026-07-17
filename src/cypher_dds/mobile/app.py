"""Cypher-DDS mobile (Android) app — Kivy front-end over DiagnosticSession.

Same architectural role as cypher_dds.tui.app.CypherDDSApp: presentation
only, driving cypher_dds.session.DiagnosticSession for every bit of
connect/VIN/DTC/PID logic, so this and the TUI never duplicate that logic.
Background I/O runs on a plain Python thread, posting results back to the
main Kivy thread via Clock.schedule_once() — Kivy's equivalent of Textual's
App.call_from_thread().

IMPORTANT CAVEATS (read before assuming this "just works" on a phone):
  - This has never been run on a physical Android device or emulator —
    there's no Android SDK/toolchain in this repo's dev environment. The
    only verification that exists is packaging plus local mocked tests.
    A green build means "it built," not "it runs correctly on a phone."
  - Android Bluetooth transport now exists in the core layer via
    AndroidBluetoothSerialAdapter and is selected when this UI requests a
    Bluetooth connection on Android. That code path is still not validated
    on a physical device with a real adapter, so support remains
    implementation-level rather than field-proven.
"""

from __future__ import annotations

import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

import cypher_dds.profiles  # noqa: F401 — importing this registers all built-in vehicle profiles
from cypher_dds.core.actions import DiagnosticAction
from cypher_dds.core.dtc import DTC
from cypher_dds.ui_format import (
    action_category_labels,
    action_display_label,
    format_dtc_detail_lines,
    format_dtc_summary,
    format_live_summary,
)
from cypher_dds.core.vin import VINInfo
from cypher_dds.session import DEFAULT_LIVE_PIDS, DiagnosticSession
from cypher_dds.theme import CHERRY_RED, ROYAL_BLUE

_MUTED_RGBA = (0.6, 0.6, 0.6, 1.0)


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return (r, g, b, alpha)


_ROYAL_BLUE_RGBA = _hex_to_rgba(ROYAL_BLUE)
_CHERRY_RED_RGBA = _hex_to_rgba(CHERRY_RED)


class CypherDDSMobileApp(App):
    """Root Kivy application."""

    title = "Cypher-DDS"

    def build(self):
        self._session = DiagnosticSession()
        self._actions_by_label: dict[str, DiagnosticAction] = {}
        self._actions_by_key: dict[str, DiagnosticAction] = {}

        root = BoxLayout(orientation="vertical", padding=16, spacing=8)
        controls = BoxLayout(orientation="vertical", size_hint_y=None, height=236, spacing=6)
        mode_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=8)
        address_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=8)
        actions_row = BoxLayout(orientation="vertical", size_hint_y=None, height=252, spacing=8)

        self.mode_spinner = Spinner(
            text="Mock adapter",
            values=("Mock adapter", "Bluetooth adapter"),
            size_hint=(1, None),
            height=40,
        )
        self.bluetooth_input = TextInput(
            hint_text="Bluetooth MAC address",
            multiline=False,
            size_hint=(1, None),
            height=40,
        )
        self.channel_input = TextInput(
            text="1",
            multiline=False,
            size_hint=(None, None),
            width=80,
            height=40,
        )
        mode_row.add_widget(self.mode_spinner)
        address_row.add_widget(self.bluetooth_input)
        address_row.add_widget(self.channel_input)

        self.status_label = Label(text="○ NO ADAPTER", color=_MUTED_RGBA, size_hint_y=None, height=40)
        self.vehicle_label = Label(text="VIN: —", size_hint_y=None, height=32)
        self.dtc_label = Label(text="✓ NO CODES STORED", color=_MUTED_RGBA, size_hint_y=None, height=40)
        self.dtc_detail_label = Label(
            text="No stored DTC details.",
            size_hint_y=None,
            height=88,
            halign="left",
            valign="top",
            text_size=(None, None),
        )
        self.live_label = Label(text=self._live_placeholder(), size_hint_y=None, height=48)
        button_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=48, spacing=8)
        self.refresh_button = Button(text="Refresh", size_hint=(0.5, None), height=48, disabled=True)
        self.refresh_button.bind(on_press=lambda _btn: self._start_refresh())
        self.clear_dtcs_button = Button(text="Clear DTCs", size_hint=(0.5, None), height=48, disabled=True)
        self.clear_dtcs_button.bind(on_press=lambda _btn: self._confirm_clear_dtcs())
        button_row.add_widget(self.refresh_button)
        button_row.add_widget(self.clear_dtcs_button)
        self.action_category_spinner = Spinner(
            text="all",
            values=("all",),
            size_hint=(1, None),
            height=40,
            disabled=True,
        )
        self.action_spinner = Spinner(
            text="No actions available",
            values=(),
            size_hint=(1, None),
            height=40,
            disabled=True,
        )
        self.action_description_label = Label(text="Description: —", size_hint_y=None, height=64)
        self.action_support_label = Label(text="Support: —", size_hint_y=None, height=32)
        self.action_danger_label = Label(text="Danger: —", size_hint_y=None, height=64)
        self.action_button = Button(text="Run Action", size_hint_y=None, height=48, disabled=True)
        self.action_button.bind(on_press=lambda _btn: self._confirm_action())
        self.log_label = Label(text="Log: waiting for connection", valign="top")

        actions_row.add_widget(self.action_category_spinner)
        actions_row.add_widget(self.action_spinner)
        actions_row.add_widget(self.action_description_label)
        actions_row.add_widget(self.action_support_label)
        actions_row.add_widget(self.action_danger_label)
        actions_row.add_widget(self.action_button)

        controls.add_widget(mode_row)
        controls.add_widget(address_row)
        controls.add_widget(button_row)

        for widget in (
            controls,
            self.status_label,
            self.vehicle_label,
            self.dtc_label,
            self.dtc_detail_label,
            self.live_label,
            actions_row,
        ):
            root.add_widget(widget)
        log_anchor = AnchorLayout(anchor_x="left", anchor_y="top")
        log_anchor.add_widget(self.log_label)
        root.add_widget(log_anchor)

        Clock.schedule_once(lambda _dt: self._start_connect(), 0)
        return root

    @staticmethod
    def _live_placeholder() -> str:
        return "   ".join(f"{label}: —" for _pid, label, _unit in DEFAULT_LIVE_PIDS)

    def _selected_filtered_actions(self) -> tuple[DiagnosticAction, ...]:
        selected_category = self.action_category_spinner.text
        actions = tuple(self._actions_by_key.values())
        if selected_category == "all":
            return actions
        return tuple(action for action in actions if action.category.value == selected_category)

    # ── background-thread work (blocking serial I/O only, no UI access) ────

    def _start_connect(self) -> None:
        threading.Thread(target=self._connect, daemon=True).start()

    def _start_refresh(self) -> None:
        if self._session.connected:
            threading.Thread(target=self._refresh, daemon=True).start()

    def _start_clear_dtcs(self) -> None:
        if self._session.connected:
            threading.Thread(target=self._clear_dtcs, daemon=True).start()

    def _connect(self) -> None:
        try:
            if self.mode_spinner.text == "Bluetooth adapter":
                protocol = self._session.connect(
                    bluetooth_address=self.bluetooth_input.text.strip(),
                    bluetooth_channel=int(self.channel_input.text or "1"),
                )
            else:
                protocol = self._session.connect()  # mock adapter — see module docstring
        except Exception as exc:  # noqa: BLE001 — top-level I/O boundary; report, don't crash
            Clock.schedule_once(lambda _dt: self._on_connect_failed(str(exc)), 0)
            return

        Clock.schedule_once(lambda _dt: self._on_connected(protocol), 0)

        vin_info = self._session.resolve_vehicle()
        Clock.schedule_once(lambda _dt: self._on_vin_resolved(vin_info), 0)
        Clock.schedule_once(lambda _dt: self._load_actions(), 0)

        self._refresh()

    def _refresh(self) -> None:
        dtcs: tuple[DTC, ...] = ()
        try:
            dtcs = tuple(self._session.read_dtcs())
        except Exception:  # noqa: BLE001 — a bad DTC read shouldn't crash the app
            pass
        Clock.schedule_once(lambda _dt: self._on_dtcs_resolved(dtcs), 0)

        values = self._session.read_live_data()
        Clock.schedule_once(lambda _dt: self._on_pid_values(values), 0)

    def _clear_dtcs(self) -> None:
        try:
            self._session.clear_dtcs()
        except Exception as exc:  # noqa: BLE001
            Clock.schedule_once(
                lambda _dt: setattr(self.log_label, "text", f"Log: DTC clear failed — {exc}"),
                0,
            )
            return

        Clock.schedule_once(lambda _dt: setattr(self.log_label, "text", "Log: DTC clear succeeded"), 0)
        self._refresh()

    # ── main-thread UI updates ──────────────────────────────────────────────

    def _on_connect_failed(self, error: str) -> None:
        self.status_label.text = f"Connection failed: {error}"
        self.status_label.color = _CHERRY_RED_RGBA
        self.log_label.text = f"Log: connection failed — {error}"

    def _on_connected(self, protocol: str) -> None:
        self.status_label.text = f"● LIVE — {protocol}"
        self.status_label.color = _ROYAL_BLUE_RGBA
        self.refresh_button.disabled = False
        self.clear_dtcs_button.disabled = False
        self.log_label.text = f"Log: connected — {protocol}"

    def _on_vin_resolved(self, vin_info: VINInfo | None) -> None:
        if vin_info is None:
            self.vehicle_label.text = "VIN: unavailable"
        elif self._session.profile is not None:
            self.vehicle_label.text = f"VIN: {vin_info.vin} → {self._session.profile.display_name}"
        else:
            self.vehicle_label.text = (
                f"VIN: {vin_info.vin} → unrecognized manufacturer (WMI {vin_info.wmi})"
            )

    def _on_dtcs_resolved(self, dtcs: tuple[DTC, ...]) -> None:
        self.dtc_label.text = format_dtc_summary(dtcs)
        self.dtc_detail_label.text = format_dtc_detail_lines(dtcs)
        if dtcs:
            self.dtc_label.color = _CHERRY_RED_RGBA
        else:
            self.dtc_label.color = _MUTED_RGBA

    def _on_pid_values(self, values: dict[int, float | None]) -> None:
        self.live_label.text = format_live_summary(values)

    def _load_actions(self) -> None:
        actions = self._session.available_actions()
        self._actions_by_key = {action.key: action for action in actions}
        if not self._actions_by_key:
            self.action_category_spinner.text = "all"
            self.action_category_spinner.values = ("all",)
            self.action_category_spinner.disabled = True
            self.action_spinner.text = "No actions available"
            self.action_spinner.values = ()
            self.action_spinner.disabled = True
            self.action_button.disabled = True
            return

        categories = action_category_labels(actions)
        self.action_category_spinner.values = categories
        self.action_category_spinner.text = "all"
        self.action_category_spinner.disabled = False
        self.action_category_spinner.bind(
            text=lambda _spinner, value: self._on_action_category_selected(value)
        )
        self._apply_action_filter()
        self.action_spinner.bind(text=lambda _spinner, value: self._on_action_selected(value))

    def _apply_action_filter(self) -> None:
        filtered_actions = self._selected_filtered_actions()
        self._actions_by_label = {
            action_display_label(action): action for action in filtered_actions
        }
        if not self._actions_by_label:
            self.action_spinner.text = "No actions in category"
            self.action_spinner.values = ()
            self.action_spinner.disabled = True
            self.action_button.disabled = True
            self.action_description_label.text = "Description: —"
            self.action_support_label.text = "Support: —"
            self.action_danger_label.text = "Danger: —"
            return

        labels = tuple(self._actions_by_label.keys())
        self.action_spinner.values = labels
        self.action_spinner.text = labels[0]
        self.action_spinner.disabled = False
        self.action_button.disabled = False
        self._update_action_details(self._actions_by_label[labels[0]])

    def _on_action_category_selected(self, _label: str) -> None:
        self._apply_action_filter()

    def _on_action_selected(self, label: str) -> None:
        action = self._actions_by_label.get(label)
        if action is not None:
            self._update_action_details(action)

    def _update_action_details(self, action: DiagnosticAction) -> None:
        self.action_description_label.text = f"Description: {action.description}"
        self.action_support_label.text = (
            f"Support: {action.support_level.value} | Mutates state: {'yes' if action.mutates_vehicle_state else 'no'}"
        )
        self.action_danger_label.text = f"Danger: {action.danger_note or '—'}"
        self.action_button.disabled = not (action.supported and action.commands)

    def _confirm_clear_dtcs(self) -> None:
        layout = BoxLayout(orientation="vertical", padding=12, spacing=8)
        layout.add_widget(Label(text="Clearing DTCs resets readiness monitors. Continue?"))
        buttons = BoxLayout(size_hint_y=None, height=48, spacing=8)
        popup = Popup(title="Confirm DTC clear", content=layout, size_hint=(0.85, 0.45))
        buttons.add_widget(Button(text="Cancel", on_press=lambda _btn: popup.dismiss()))
        buttons.add_widget(
            Button(
                text="Clear",
                on_press=lambda _btn: (popup.dismiss(), self._start_clear_dtcs()),
            )
        )
        layout.add_widget(buttons)
        popup.open()

    def _confirm_action(self) -> None:
        action = self._actions_by_label.get(self.action_spinner.text)
        if action is None:
            return

        if not action.mutates_vehicle_state:
            threading.Thread(target=self._run_action, args=(action,), daemon=True).start()
            return

        layout = BoxLayout(orientation="vertical", padding=12, spacing=8)
        layout.add_widget(Label(text=action.danger_note or "This action changes vehicle state."))
        buttons = BoxLayout(size_hint_y=None, height=48, spacing=8)
        popup = Popup(title="Confirm vehicle state change", content=layout, size_hint=(0.85, 0.45))
        buttons.add_widget(Button(text="Cancel", on_press=lambda _btn: popup.dismiss()))
        buttons.add_widget(
            Button(
                text="Run",
                on_press=lambda _btn: (popup.dismiss(), threading.Thread(
                    target=self._run_action, args=(action,), daemon=True
                ).start()),
            )
        )
        layout.add_widget(buttons)
        popup.open()

    def _run_action(self, action: DiagnosticAction) -> None:
        try:
            result = self._session.run_action(action.key, confirm_write=action.mutates_vehicle_state)
        except Exception as exc:  # noqa: BLE001
            Clock.schedule_once(
                lambda _dt: setattr(self.log_label, "text", f"Log: action failed — {action.title}: {exc}"),
                0,
            )
            return

        responses = " | ".join(result.responses)
        Clock.schedule_once(
            lambda _dt: setattr(
                self.log_label, "text", f"Log: action succeeded — {action.title} → {responses}"
            ),
            0,
        )


def main() -> None:
    CypherDDSMobileApp().run()


if __name__ == "__main__":
    main()
