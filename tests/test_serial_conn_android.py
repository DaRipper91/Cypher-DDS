from unittest.mock import patch

from cypher_dds.core.serial_conn import DEFAULT_TIMEOUT, SerialConnection


def test_connect_bluetooth_uses_android_adapter_on_android():
    connection = SerialConnection()

    with patch("cypher_dds.core.serial_conn.sys.platform", "android"), patch(
        "cypher_dds.core.android_bluetooth_adapter.AndroidBluetoothSerialAdapter"
    ) as mock_android_adapter:
        connection.connect_bluetooth("AA:BB:CC:DD:EE:FF", 7)

    mock_android_adapter.assert_called_once_with(
        "AA:BB:CC:DD:EE:FF",
        7,
        timeout=DEFAULT_TIMEOUT,
    )


def test_connect_bluetooth_uses_default_android_channel_when_unspecified():
    connection = SerialConnection()

    with patch("cypher_dds.core.serial_conn.sys.platform", "android"), patch(
        "cypher_dds.core.android_bluetooth_adapter.AndroidBluetoothSerialAdapter"
    ) as mock_android_adapter:
        connection.connect_bluetooth("AA:BB:CC:DD:EE:FF")

    mock_android_adapter.assert_called_once_with(
        "AA:BB:CC:DD:EE:FF",
        1,
        timeout=DEFAULT_TIMEOUT,
    )
