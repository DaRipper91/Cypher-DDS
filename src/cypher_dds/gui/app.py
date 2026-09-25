"""Desktop Tkinter GUI for Cypher-DDS.

This is a presentation layer over DiagnosticSession, matching the same
architectural role as the Textual and Kivy front ends. All blocking I/O
runs on background threads and posts results back to the Tk main loop via
`after()`.
"""

from __future__ import annotations

import argparse
import threading
import tkinter as tk
from tkinter import messagebox, ttk

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


def connection_field_states(mode: str) -> dict[str, str]:
    if mode == "usb":
        return {"port": "normal", "bluetooth": "disabled", "channel": "disabled"}
    if mode == "bluetooth":
        return {"port": "disabled", "bluetooth": "normal", "channel": "normal"}
    return {"port": "disabled", "bluetooth": "disabled", "channel": "disabled"}


def action_filter_summary(visible_count: int, total_count: int, category: str) -> str:
    if total_count == 0:
        return "Showing 0 actions"
    if category == "all":
        return f"Showing {visible_count} of {total_count} actions"
    return f"Showing {visible_count} of {total_count} actions in {category}"


class CypherDDSGUI(tk.Tk):
    """Root desktop GUI window."""

    def __init__(
        self,
        port: str | None = None,
        mock_scenario: str = "default",
        bluetooth_address: str | None = None,
        bluetooth_channel: int | None = None,
    ) -> None:
        super().__init__()
        self.title("Cypher-DDS")
        self.geometry("980x720")

        self._session = DiagnosticSession()
        self._mock_scenario = mock_scenario

        self._connect_mode = tk.StringVar(
            value="bluetooth" if bluetooth_address else ("usb" if port else "mock")
        )
        self._port_var = tk.StringVar(value=port or "")
        self._bluetooth_var = tk.StringVar(value=bluetooth_address or "")
        self._bluetooth_channel_var = tk.StringVar(value=str(bluetooth_channel or 1))
        self._status_var = tk.StringVar(value="○ NO ADAPTER")
        self._vehicle_var = tk.StringVar(value="VIN: —")
        self._dtc_var = tk.StringVar(value="✓ NO CODES STORED")
        self._live_var = tk.StringVar(value=self._live_placeholder())
        self._selected_action_key = tk.StringVar(value="")
        self._action_category_filter = tk.StringVar(value="all")
        self._action_filter_summary = tk.StringVar(value="Showing 0 actions")
        self._selected_action_description = tk.StringVar(value="Description: —")
        self._selected_action_support = tk.StringVar(value="Support: —")
        self._selected_action_danger = tk.StringVar(value="Danger: —")

        self._action_index: dict[str, DiagnosticAction] = {}
        self._visible_action_keys: list[str] = []
        self._busy = False

        self._build_layout()
        self._connect_mode.trace_add("write", self._on_connect_mode_changed)
        self._update_connection_field_states()

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)
        root.rowconfigure(5, weight=1)

        connection = ttk.LabelFrame(root, text="Connection", padding=10)
        connection.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for column in range(6):
            connection.columnconfigure(column, weight=1 if column in {1, 3, 5} else 0)

        ttk.Radiobutton(connection, text="Mock", variable=self._connect_mode, value="mock").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Radiobutton(connection, text="USB", variable=self._connect_mode, value="usb").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Radiobutton(
            connection, text="Bluetooth", variable=self._connect_mode, value="bluetooth"
        ).grid(row=0, column=2, sticky="w")

        ttk.Label(connection, text="Port").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self._port_entry = ttk.Entry(connection, textvariable=self._port_var)
        self._port_entry.grid(
            row=1, column=1, sticky="ew", padx=(4, 12), pady=(8, 0)
        )
        ttk.Label(connection, text="Bluetooth MAC").grid(row=1, column=2, sticky="w", pady=(8, 0))
        self._bluetooth_entry = ttk.Entry(connection, textvariable=self._bluetooth_var)
        self._bluetooth_entry.grid(
            row=1, column=3, sticky="ew", padx=(4, 12), pady=(8, 0)
        )
        ttk.Label(connection, text="RFCOMM").grid(row=1, column=4, sticky="w", pady=(8, 0))
        self._bluetooth_channel_entry = ttk.Entry(
            connection, textvariable=self._bluetooth_channel_var, width=6
        )
        self._bluetooth_channel_entry.grid(
            row=1, column=5, sticky="w", padx=(4, 0), pady=(8, 0)
        )

        self._connect_button = ttk.Button(connection, text="Connect", command=self._start_connect)
        self._connect_button.grid(
            row=0, column=5, sticky="e"
        )
        self._refresh_button = ttk.Button(
            connection, text="Refresh", command=self._start_refresh, state="disabled"
        )
        self._refresh_button.grid(row=0, column=4, sticky="e", padx=(0, 8))

        status = ttk.LabelFrame(root, text="Status", padding=10)
        status.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        status.columnconfigure(0, weight=1)
        status.columnconfigure(1, weight=1)

        self._status_label = tk.Label(
            status, textvariable=self._status_var, fg=CHERRY_RED, anchor="w"
        )
        self._status_label.grid(row=0, column=0, sticky="ew")
        ttk.Label(status, textvariable=self._vehicle_var).grid(row=0, column=1, sticky="ew")

        diagnostics = ttk.LabelFrame(root, text="Diagnostics", padding=10)
        diagnostics.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        diagnostics.columnconfigure(0, weight=1)
        diagnostics.rowconfigure(1, weight=1)
        ttk.Label(diagnostics, textvariable=self._dtc_var).grid(row=0, column=0, sticky="w")
        dtc_columns = ("code", "description")
        self._dtc_tree = ttk.Treeview(diagnostics, columns=dtc_columns, show="headings", height=5)
        self._dtc_tree.heading("code", text="Code")
        self._dtc_tree.heading("description", text="Description")
        self._dtc_tree.column("code", width=110, anchor="w")
        self._dtc_tree.column("description", width=560, anchor="w")
        dtc_scroll = ttk.Scrollbar(diagnostics, orient="vertical", command=self._dtc_tree.yview)
        self._dtc_tree.configure(yscrollcommand=dtc_scroll.set)
        self._dtc_tree.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        dtc_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 8))
        ttk.Label(diagnostics, textvariable=self._live_var).grid(row=2, column=0, sticky="w", pady=(0, 8))
        self._clear_dtcs_button = ttk.Button(
            diagnostics, text="Clear DTCs", command=self._start_clear_dtcs, state="disabled"
        )
        self._clear_dtcs_button.grid(row=3, column=0, sticky="e")

        main_panes = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
        main_panes.grid(row=4, column=0, sticky="nsew", pady=(0, 8))

        actions = ttk.LabelFrame(main_panes, text="Actions", padding=10)
        actions.columnconfigure(0, weight=1)
        actions.rowconfigure(1, weight=1)
        main_panes.add(actions, weight=3)

        header_row = ttk.Frame(actions)
        header_row.grid(row=0, column=0, sticky="ew")
        header_row.columnconfigure(1, weight=1)
        ttk.Label(header_row, text="Available actions").grid(row=0, column=0, sticky="w")
        ttk.Label(header_row, text="Category").grid(row=0, column=1, sticky="e", padx=(8, 4))
        self._category_filter_combo = ttk.Combobox(
            header_row,
            textvariable=self._action_category_filter,
            state="readonly",
            values=("all",),
            width=16,
        )
        self._category_filter_combo.grid(row=0, column=2, sticky="e")
        self._category_filter_combo.bind("<<ComboboxSelected>>", self._on_action_filter_changed)
        ttk.Label(actions, textvariable=self._action_filter_summary).grid(row=1, column=0, sticky="w")
        self._actions_listbox = tk.Listbox(actions, exportselection=False, height=14)
        action_list_frame = ttk.Frame(actions)
        action_list_frame.grid(row=2, column=0, sticky="nsew", pady=(6, 8))
        action_list_frame.columnconfigure(0, weight=1)
        action_list_frame.rowconfigure(0, weight=1)
        self._actions_listbox.grid(in_=action_list_frame, row=0, column=0, sticky="nsew")
        action_scroll = ttk.Scrollbar(
            action_list_frame, orient="vertical", command=self._actions_listbox.yview
        )
        self._actions_listbox.configure(yscrollcommand=action_scroll.set)
        action_scroll.grid(row=0, column=1, sticky="ns")
        self._actions_listbox.bind("<<ListboxSelect>>", self._on_action_selected)
        ttk.Label(actions, textvariable=self._selected_action_description, wraplength=320).grid(
            row=3, column=0, sticky="w"
        )
        ttk.Label(actions, textvariable=self._selected_action_support).grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Label(actions, textvariable=self._selected_action_danger, wraplength=320).grid(
            row=5, column=0, sticky="w", pady=(6, 6)
        )
        self._run_action_button = ttk.Button(
            actions, text="Run action", command=self._start_run_action, state="disabled"
        )
        self._run_action_button.grid(row=6, column=0, sticky="e")

        logs = ttk.LabelFrame(main_panes, text="Logs", padding=10)
        logs.columnconfigure(0, weight=1)
        logs.rowconfigure(1, weight=1)
        main_panes.add(logs, weight=2)

        logs_header = ttk.Frame(logs)
        logs_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        logs_header.columnconfigure(0, weight=1)
        ttk.Label(logs_header, text="Event log").grid(row=0, column=0, sticky="w")
        ttk.Button(logs_header, text="Clear log", command=self._clear_log).grid(row=0, column=1, sticky="e")

        self._log_text = tk.Text(logs, wrap="word", height=18, state="disabled")
        self._log_text.grid(row=1, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(logs, orient="vertical", command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.grid(row=1, column=1, sticky="ns")

    @staticmethod
    def _live_placeholder() -> str:
        return "   ".join(f"{label}: —" for _pid, label, _unit in DEFAULT_LIVE_PIDS)

    def _append_log(self, message: str) -> None:
        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"{message}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    def _set_busy(self, busy: bool, *, connect_label: str | None = None) -> None:
        self._busy = busy
        self._connect_button.configure(
            state="disabled" if busy else "normal",
            text=connect_label if busy and connect_label else "Connect",
        )
        if busy:
            self._refresh_button.configure(state="disabled")
            self._clear_dtcs_button.configure(state="disabled")
            self._run_action_button.configure(state="disabled")
            self._category_filter_combo.configure(state="disabled")
        else:
            self._refresh_button.configure(state="normal" if self._session.connected else "disabled")
            self._clear_dtcs_button.configure(state="normal" if self._session.connected else "disabled")
            self._category_filter_combo.configure(
                state="readonly" if self._action_index else "disabled"
            )
            action = self._selected_action()
            self._run_action_button.configure(
                state="normal" if action is not None and action.supported and action.commands else "disabled"
            )
        self._update_connection_field_states()

    def _update_connection_field_states(self) -> None:
        states = connection_field_states(self._connect_mode.get())
        if self._busy:
            states = {"port": "disabled", "bluetooth": "disabled", "channel": "disabled"}
        self._port_entry.configure(state=states["port"])
        self._bluetooth_entry.configure(state=states["bluetooth"])
        self._bluetooth_channel_entry.configure(state=states["channel"])

    def _on_connect_mode_changed(self, *_args) -> None:
        self._update_connection_field_states()

    def _validate_connection_inputs(self) -> str | None:
        mode = self._connect_mode.get()
        if mode == "usb" and not self._port_var.get().strip():
            return "Enter a USB serial port before connecting."
        if mode == "bluetooth":
            if not self._bluetooth_var.get().strip():
                return "Enter a Bluetooth MAC address before connecting."
            try:
                int(self._bluetooth_channel_var.get())
            except ValueError:
                return "RFCOMM channel must be a whole number."
        return None

    def _start_connect(self) -> None:
        if self._busy:
            return
        validation_error = self._validate_connection_inputs()
        if validation_error:
            self._on_connect_failed(validation_error)
            return
        self._set_busy(True, connect_label="Connecting…")
        threading.Thread(target=self._connect, daemon=True).start()

    def _start_refresh(self) -> None:
        if self._session.connected and not self._busy:
            self._set_busy(True)
            threading.Thread(target=self._refresh, daemon=True).start()

    def _start_clear_dtcs(self) -> None:
        if not self._session.connected or self._busy:
            return
        if not messagebox.askyesno(
            "Confirm DTC clear",
            "Clearing DTCs resets readiness monitors. Continue?",
            parent=self,
        ):
            self._append_log("Cancelled DTC clear")
            return
        threading.Thread(target=self._clear_dtcs, daemon=True).start()

    def _start_run_action(self) -> None:
        if self._busy:
            return
        action = self._selected_action()
        if action is None:
            return
        if action.mutates_vehicle_state:
            if not messagebox.askyesno(
                "Confirm vehicle state change",
                action.danger_note or "This action changes vehicle state. Continue?",
                parent=self,
            ):
                self._append_log(f"Cancelled action: {action.title}")
                return

        self._set_busy(True)
        threading.Thread(target=self._run_action, args=(action,), daemon=True).start()

    def _selected_action(self) -> DiagnosticAction | None:
        key = self._selected_action_key.get()
        return self._action_index.get(key)

    def _connect(self) -> None:
        try:
            mode = self._connect_mode.get()
            if mode == "usb":
                protocol = self._session.connect(port=self._port_var.get())
            elif mode == "bluetooth":
                protocol = self._session.connect(
                    bluetooth_address=self._bluetooth_var.get(),
                    bluetooth_channel=int(self._bluetooth_channel_var.get()),
                )
            else:
                protocol = self._session.connect(mock_scenario=self._mock_scenario)
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._finish_connect_failed, str(exc))
            return

        self.after(0, self._on_connected, protocol)
        vin_info = self._session.resolve_vehicle()
        self.after(0, self._on_vin_resolved, vin_info)
        self._refresh()
        self.after(0, self._load_actions)
        self.after(0, self._set_busy, False)

    def _refresh(self) -> None:
        dtcs: tuple[DTC, ...] = ()
        try:
            dtcs = tuple(self._session.read_dtcs())
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._append_log, f"DTC read failed: {exc}")
        self.after(0, self._on_dtcs_resolved, dtcs)

        try:
            values = self._session.read_live_data()
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._append_log, f"PID read failed: {exc}")
            self.after(0, self._set_busy, False)
            return
        self.after(0, self._on_pid_values, values)
        self.after(0, self._set_busy, False)

    def _clear_dtcs(self) -> None:
        try:
            self._session.clear_dtcs()
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._append_log, f"DTC clear failed: {exc}")
            self.after(0, self._set_busy, False)
            return

        self.after(0, self._append_log, "DTC clear succeeded")
        self._refresh()

    def _run_action(self, action: DiagnosticAction) -> None:
        try:
            result = self._session.run_action(action.key, confirm_write=action.mutates_vehicle_state)
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._append_log, f"Action failed: {action.title}: {exc}")
            self.after(0, self._set_busy, False)
            return

        self.after(0, self._append_log, f"Action succeeded: {action.title}")
        for response in result.responses:
            self.after(0, self._append_log, f"  {response}")
        self.after(0, self._set_busy, False)

    def _on_connect_failed(self, error: str) -> None:
        self._status_var.set(f"Connection failed: {error}")
        self._status_label.configure(fg=CHERRY_RED)
        self._append_log(f"Connection failed: {error}")

    def _finish_connect_failed(self, error: str) -> None:
        self._on_connect_failed(error)
        self._set_busy(False)

    def _on_connected(self, protocol: str) -> None:
        self._status_var.set(f"● LIVE — {protocol}")
        self._status_label.configure(fg=ROYAL_BLUE)
        self._refresh_button.configure(state="normal")
        self._clear_dtcs_button.configure(state="normal")
        self._append_log(f"Connected: {protocol}")

    def _on_vin_resolved(self, vin_info: VINInfo | None) -> None:
        if vin_info is None:
            self._vehicle_var.set("VIN: unavailable")
            self._append_log("VIN unavailable")
        elif self._session.profile is not None:
            self._vehicle_var.set(f"VIN: {vin_info.vin} → {self._session.profile.display_name}")
            self._append_log(f"Vehicle resolved: {vin_info.vin} → {self._session.profile.display_name}")
        else:
            self._vehicle_var.set(
                f"VIN: {vin_info.vin} → unrecognized manufacturer (WMI {vin_info.wmi})"
            )
            self._append_log(f"Vehicle resolved with unknown profile: {vin_info.vin}")

    def _on_dtcs_resolved(self, dtcs: tuple[DTC, ...]) -> None:
        self._dtc_var.set(format_dtc_summary(dtcs))
        for item in self._dtc_tree.get_children():
            self._dtc_tree.delete(item)
        if dtcs:
            for dtc in dtcs:
                self._dtc_tree.insert(
                    "",
                    "end",
                    values=(dtc.code, dtc.description or "No description available"),
                )
        else:
            self._dtc_tree.insert("", "end", values=("—", "No stored DTC details."))

    def _on_pid_values(self, values: dict[int, float | None]) -> None:
        self._live_var.set(format_live_summary(values))

    def _load_actions(self) -> None:
        actions = self._session.available_actions()
        self._action_index = {action.key: action for action in actions}
        self._category_filter_combo.configure(values=action_category_labels(actions))
        self._action_category_filter.set("all")
        self._apply_action_filter()

    def _apply_action_filter(self) -> None:
        selected_category = self._action_category_filter.get()
        self._actions_listbox.delete(0, "end")
        self._visible_action_keys = []
        for key, action in self._action_index.items():
            if selected_category != "all" and action.category.value != selected_category:
                continue
            self._actions_listbox.insert("end", action_display_label(action))
            self._visible_action_keys.append(key)
        self._action_filter_summary.set(
            action_filter_summary(
                len(self._visible_action_keys), len(self._action_index), selected_category
            )
        )

        if self._visible_action_keys:
            first_key = self._visible_action_keys[0]
            self._selected_action_key.set(first_key)
            self._actions_listbox.selection_set(0)
            self._update_selected_action_details(self._action_index[first_key])
        else:
            self._selected_action_key.set("")
            self._selected_action_description.set("Description: —")
            self._selected_action_support.set("Support: —")
            self._selected_action_danger.set("Danger: —")
            self._run_action_button.configure(state="disabled")

    def _on_action_filter_changed(self, _event=None) -> None:
        self._apply_action_filter()

    def _on_action_selected(self, _event=None) -> None:
        selection = self._actions_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        key = self._visible_action_keys[index]
        action = self._action_index[key]
        self._selected_action_key.set(key)
        self._update_selected_action_details(action)

    def _update_selected_action_details(self, action: DiagnosticAction) -> None:
        self._selected_action_description.set(f"Description: {action.description}")
        self._selected_action_support.set(
            f"Support: {action.support_level.value} | Mutates state: {'yes' if action.mutates_vehicle_state else 'no'}"
        )
        self._selected_action_danger.set(f"Danger: {action.danger_note or '—'}")
        self._run_action_button.configure(
            state="normal" if not self._busy and action.supported and action.commands else "disabled"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Cypher-DDS desktop GUI")
    parser.add_argument("--port", help="Serial port to connect to (e.g. /dev/ttyUSB0).")
    parser.add_argument("--bluetooth", metavar="MAC", help="Bluetooth MAC address for RFCOMM/SPP.")
    parser.add_argument("--bluetooth-channel", type=int, default=None, help="RFCOMM channel.")
    parser.add_argument(
        "--mock-scenario",
        default="default",
        help="Mock adapter scenario when neither --port nor --bluetooth is provided.",
    )
    args = parser.parse_args()
    if args.port and args.bluetooth:
        parser.error("--port and --bluetooth are mutually exclusive")

    app = CypherDDSGUI(
        port=args.port,
        mock_scenario=args.mock_scenario,
        bluetooth_address=args.bluetooth,
        bluetooth_channel=args.bluetooth_channel,
    )
    app.mainloop()


if __name__ == "__main__":
    main()
