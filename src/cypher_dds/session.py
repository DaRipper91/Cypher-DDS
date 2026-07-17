"""Framework-agnostic diagnostic session: connect, VIN/profile resolution,
DTC reads (with brand-fallback descriptions), and live PID reads.

Owns no UI. This is the layer any presentation front-end sits on top of —
cypher_dds.tui already drives it, and a future cypher_dds.gui would drive
the exact same DiagnosticSession rather than re-implementing this
orchestration logic a second time.
"""

from __future__ import annotations

from dataclasses import replace

from cypher_dds.core.actions import (
    ActionNotFoundError,
    ActionResult,
    DiagnosticAction,
    execute_action,
)
from cypher_dds.core.dtc import DTC, DTCReader
from cypher_dds.core.elm327 import ELM327
from cypher_dds.core.mock_adapter import MockELM327Adapter
from cypher_dds.core.pids import read_pid
from cypher_dds.core.serial_conn import SerialConnection
from cypher_dds.core.vin import VINInfo, request_vin
from cypher_dds.profiles.base import VehicleProfile, get_profile

# Standard live-data row: (Mode 01 PID, display label, unit). Presentation
# layers can pass a different subset to read_live_data().
DEFAULT_LIVE_PIDS: tuple[tuple[int, str, str], ...] = (
    (0x0C, "RPM", "rpm"),
    (0x0D, "Speed", "km/h"),
    (0x05, "Coolant", "°C"),
)


class NotConnectedError(RuntimeError):
    """Raised when a session method needs a connection that isn't there yet."""


class DiagnosticSession:
    """Owns one ELM327 connection plus the VIN-resolved brand profile.

    All I/O here is blocking (real pyserial timeouts included) — callers
    running inside a UI event loop are responsible for offloading these
    calls to a worker thread, same as cypher_dds.tui.app already does.
    """

    def __init__(self) -> None:
        self.elm327: ELM327 | None = None
        self.profile: VehicleProfile | None = None
        self.vin_info: VINInfo | None = None

    @property
    def connected(self) -> bool:
        return self.elm327 is not None

    def connect(
        self,
        port: str | None = None,
        mock_scenario: str = "default",
        bluetooth_address: str | None = None,
        bluetooth_channel: int | None = None,
    ) -> str:
        """Open a connection and run the ELM327 init sequence.

        Exactly one of `port` (real pyserial device, e.g. "/dev/ttyUSB0")
        or `bluetooth_address` (a paired ELM327's MAC, Linux-only — see
        core.bluetooth_adapter) selects real hardware; passing neither uses
        MockELM327Adapter. Returns the detected protocol name. Raises on
        any connection/init failure — callers decide how to surface that
        (the TUI shows it in the intro line).
        """
        connection = SerialConnection()
        if bluetooth_address:
            connection.connect_bluetooth(bluetooth_address, bluetooth_channel)
        elif port:
            connection.connect(port)
        else:
            connection = SerialConnection(transport=MockELM327Adapter(scenario=mock_scenario))

        elm = ELM327(connection)
        elm.initialize()
        self.elm327 = elm
        return elm.detected_protocol()

    def resolve_vehicle(self) -> VINInfo | None:
        """Read the VIN and select a brand profile from its WMI, if possible.

        Returns None (rather than raising) when the VIN isn't available —
        not every ECU supports Mode 09, and that's not fatal to the rest
        of the session.
        """
        if self.elm327 is None:
            raise NotConnectedError("connect() must succeed before resolve_vehicle()")

        try:
            vin_info = request_vin(self.elm327)
        except Exception:  # noqa: BLE001 — VIN isn't guaranteed on every ECU; non-fatal
            return None

        self.vin_info = vin_info
        self.profile = get_profile(vin_info.manufacturer) if vin_info.manufacturer else None
        return vin_info

    def read_dtcs(self) -> list[DTC]:
        """Read stored DTCs, filling in a brand-specific description where
        the generic table (SAE J2012 P0xxx) doesn't have one."""
        if self.elm327 is None:
            raise NotConnectedError("connect() must succeed before read_dtcs()")

        dtcs = DTCReader(self.elm327).read_stored()
        return [self._resolve_description(d) for d in dtcs]

    def _resolve_description(self, dtc: DTC) -> DTC:
        if dtc.description is not None or self.profile is None:
            return dtc
        brand_description = self.profile.get_dtc_description(dtc.code)
        return replace(dtc, description=brand_description) if brand_description else dtc

    def read_live_data(
        self, pids: tuple[tuple[int, str, str], ...] = DEFAULT_LIVE_PIDS
    ) -> dict[int, float | None]:
        """Read each requested Mode 01 PID; an unsupported PID comes back as
        None for that entry rather than aborting the whole batch."""
        if self.elm327 is None:
            raise NotConnectedError("connect() must succeed before read_live_data()")

        values: dict[int, float | None] = {}
        for pid, _label, _unit in pids:
            try:
                values[pid] = read_pid(self.elm327, pid)
            except Exception:  # noqa: BLE001 — an unsupported PID shouldn't abort the batch
                values[pid] = None
        return values

    def available_actions(self) -> tuple[DiagnosticAction, ...]:
        """Return the current make's declared bi-directional action catalog."""
        if self.profile is None:
            return ()
        return self.profile.supported_actions()

    def run_action(self, key: str, *, confirm_write: bool = False) -> ActionResult:
        """Execute one declared bi-directional action by manifest key."""
        if self.elm327 is None:
            raise NotConnectedError("connect() must succeed before run_action()")

        for action in self.available_actions():
            if action.key == key:
                return execute_action(self.elm327, action, confirm_write=confirm_write)
        raise ActionNotFoundError(f"Unknown action key: {key}")
