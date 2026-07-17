"""Android Bluetooth SPP/RFCOMM transport for ELM327 adapters.

This adapter is intentionally isolated behind the same SerialLike surface
used by pyserial, the Linux RFCOMM adapter, and the mock adapter. Higher
layers should not care whether the bytes come from USB, desktop Bluetooth,
or Android's Java Bluetooth stack.
"""

from __future__ import annotations

import sys

ANDROID_SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"


def android_bluetooth_supported() -> bool:
    return sys.platform == "android"


class AndroidBluetoothSerialAdapter:
    """SerialLike wrapper around android.bluetooth.BluetoothSocket.

    Uses pyjnius lazily so non-Android environments can import this module
    without carrying an Android runtime.
    """

    def __init__(self, address: str, channel: int = 1, timeout: float = 2.0) -> None:
        if not android_bluetooth_supported():
            raise RuntimeError("Android Bluetooth transport is only available on Android")

        try:
            from jnius import autoclass  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "pyjnius is required for Android Bluetooth support but is not available"
            ) from exc

        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        UUID = autoclass("java.util.UUID")

        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter is None:
            raise RuntimeError("No Android Bluetooth adapter is available on this device")

        remote_device = adapter.getRemoteDevice(address)
        uuid = UUID.fromString(ANDROID_SPP_UUID)
        socket = remote_device.createRfcommSocketToServiceRecord(uuid)

        if adapter.isDiscovering():
            adapter.cancelDiscovery()

        socket.connect()

        self._socket = socket
        self._input_stream = socket.getInputStream()
        self._output_stream = socket.getOutputStream()
        self._is_open = True
        self._timeout = timeout
        self._channel = channel  # retained for parity/debugging; SPP UUID is used for the actual connect

    def write(self, data: bytes) -> int:
        self._output_stream.write(data)
        self._output_stream.flush()
        return len(data)

    def read(self, size: int = 1) -> bytes:
        available = self._input_stream.available()
        if available <= 0:
            return b""

        limit = min(size, available)
        buffer = bytearray()
        for _ in range(limit):
            value = self._input_stream.read()
            if value < 0:
                break
            buffer.append(value & 0xFF)
        return bytes(buffer)

    def readline(self) -> bytes:
        line = bytearray()
        while True:
            chunk = self.read(1)
            if not chunk:
                break
            line += chunk
            if chunk == b"\r":
                break
        return bytes(line)

    def close(self) -> None:
        self._socket.close()
        self._is_open = False

    @property
    def in_waiting(self) -> int:
        try:
            return int(self._input_stream.available())
        except Exception:  # noqa: BLE001
            return 0

    @property
    def is_open(self) -> bool:
        return self._is_open
