"""Toyota/Lexus (1996+; ISO 9141-2/KWP2000 pre-2008, CAN 2008+) vehicle profile.

Its stub-proving job is done — see toyota_lexus.py's history for how the
plugin architecture was validated with this file empty before any brand
documentation existed. Now carries real DTC data, following the exact same
VehicleProfile interface as gm.py/ford.py/dodge_chrysler.py.
"""

from __future__ import annotations

from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

# Toyota/Lexus manufacturer-specific (P1xxx) DTC definitions, sourced from
# public OBD-II reference documentation. Covers 1996+ Toyota/Lexus
# platforms.
# TODO: expand with B/C/U-series codes and enhanced (Mode 22) PIDs.
DTC_TABLE: dict[str, str] = {
    # Sensors: BARO, accelerator pedal, throttle, air/fuel
    "P1100": "BARO Sensor Circuit",
    "P1120": "Accelerator Pedal Position Sensor Circuit",
    "P1121": "Accelerator Pedal Position Sensor Range/Performance Problem",
    "P1125": "Throttle Control Motor Circuit",
    "P1126": "Magnetic Clutch Circuit",
    "P1127": "ETCS Actuator Power Source Circuit",
    "P1128": "Throttle Control Motor Lock",
    "P1129": "Electric Throttle Control System",
    "P1130": "Air/Fuel Sensor Circuit Range/Performance (Bank 1 Sensor 1)",
    "P1133": "Air/Fuel Sensor Circuit Response (Bank 1 Sensor 1)",
    "P1135": "Air/Fuel Sensor Heater Circuit Response (Bank 1 Sensor 1)",
    "P1150": "Air/Fuel Sensor Circuit Range/Performance (Bank 1 Sensor 2)",
    "P1153": "Air/Fuel Sensor Circuit Response (Bank 1 Sensor 2)",
    "P1155": "Air/Fuel Sensor Heater Circuit (Bank 1 Sensor 2)",
    "P1400": "Sub-Throttle Position Sensor",
    "P1401": "Sub-Throttle Position Sensor Range/Performance Problem",
    "P1405": "Turbo Pressure Sensor Circuit",
    "P1406": "Turbo Pressure Sensor Range/Performance Problem",
    # Fuel / ignition
    "P1200": "Fuel Pump Relay Circuit",
    "P1300": "Igniter Circuit Malfunction - No. 1",
    "P1305": "Igniter Circuit Malfunction - No. 2",
    "P1335": "No Crankshaft Position Sensor Signal - Engine Running",
    "P1349": "VVT System",
    "P1605": "Knock Control CPU",
    # EGR / boost / EVAP-adjacent
    "P1410": "EGR Valve Position Sensor Circuit Malfunction",
    "P1411": "EGR Valve Position Sensor Circuit Range/Performance",
    "P1510": "Boost Pressure Control Circuit",
    "P1511": "Boost Pressure Low",
    "P1512": "Boost Pressure High",
    "P1658": "Wastegate Valve Control Circuit",
    "P1661": "EGR Circuit",
    "P1662": "EGR Bypass Valve Control Circuit",
    # Idle / cruise / body
    "P1500": "Starter Signal Circuit",
    "P1520": "Stop Lamp Switch Signal Malfunction",
    "P1565": "Cruise Control Main Switch Circuit",
    "P1652": "Idle Air Control Valve Control Circuit",
    "P1656": "OCV Circuit",
    # Module / control system
    "P1600": "ECM BATT Malfunction",
    "P1630": "Traction Control System",
    "P1633": "ECM",
    # Transmission
    "P1700": "Vehicle Speed Sensor '2' Circuit Fault",
    "P1705": "Direct Clutch Speed Circuit Fault",
    "P1765": "Linear Shift Solenoid Circuit Fault",
    "P1780": "Park/Neutral Position Switch Malfunction (Only For A/T)",
}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = ()


class ToyotaLexusProfile(VehicleProfile):
    key = "toyota_lexus"
    display_name = "Toyota / Lexus"
    wmi_codes = ("4T1", "4T3", "JTD", "JTH")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS


register_profile(ToyotaLexusProfile())
