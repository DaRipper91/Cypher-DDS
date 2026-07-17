"""Dodge/Chrysler (1996+) vehicle profile.

ISO 9141-2 / ISO 14230-4 KWP2000 pre-2008, CAN 2008+ — the ELM327's
protocol auto-detect handles the difference transparently, so this profile
(and cypher_dds.core) applies unchanged across the whole range. Priority 3
target.

Scope note: some Chrysler-group vehicles also run a proprietary SCI/CCD bus
for body and instrument-cluster diagnostics, separate from the standard
OBD2 pins a basic ELM327 talks to. Like Ford's MS-CAN, that bus is out of
scope for v1 — this profile only covers what's reachable on the standard,
federally-mandated OBD2 protocol.
"""

from __future__ import annotations

from cypher_dds.core.vehicle_coding import CodingFunctionStatus, VehicleCodingFunction
from cypher_dds.profiles.base import EnhancedPID, VehicleProfile, register_profile

# Dodge/Chrysler manufacturer-specific (P1xxx) DTC definitions, sourced from
# public OBD-II reference documentation. Covers 1996+ Chrysler-group
# platforms (includes diesel/CNG-variant codes alongside gas engine codes).
# TODO: expand with B/C/U-series Chrysler codes and enhanced (Mode 22) PIDs.
DTC_TABLE: dict[str, str] = {
    # Sensors: BARO, IAT, TP, MAP, radiator temp, EGR
    "P1105": "Open Or Shorted Condition Detected In The Baro Read Solenoid Control Circuit",
    "P1192": "Inlet Air Temp. Circuit Low",
    "P1193": "Inlet Air Temp. Circuit High",
    "P1194": "Incorrect Or Irrational Performance Has Been Detected For The PWM",
    "P1198": "Radiator Temperature Sensor Voltage Too High",
    "P1199": "Radiator Temperature Sensor Voltage Too Low",
    "P1295": "Loss Of 5 Volts To TP Sensor",
    "P1296": "Loss Of 5 Volts To MAP Sensor",
    "P1297": "No Change In MAP From Start To Run",
    "P1403": "Loss Of 5 Volts To EGR Sensor",
    # O2 sensor / catalyst monitor
    "P1195": "O2 Sensor 1/1 (Bank 1, Sensor 1) Slow During Catalyst Monitor",
    "P1196": "O2 Sensor 2/1 (Bank 2, Sensor 1) Slow During Catalyst Monitor",
    "P1197": "O2 Sensor 1/2 (Bank 1, Sensor 2) Slow During Catalyst Monitor",
    "P1482": "Catalyst Temperature Sensor Circuit Shorted Low",
    "P1483": "Catalyst Temperature Sensor Circuit Shorted High",
    "P1484": "Catalytic Converter Overheat Detected",
    # Fuel system / turbo / CNG / idle
    "P1243": "Open Or Shorted Condition Detected In The Turbocharger Surge Valve Solenoid Control",
    "P1280": "Open Or Shorted Condition Detected In The Fuel System Relay Control Circuit",
    "P1281": "Engine Operating Temp Below Acceptable Range",
    "P1282": "Fuel Pump Relay Control Circuit Open Or Shorted",
    "P1283": "Idle Select Signal Invalid",
    "P1284": "Fuel Injection Pump Battery Voltage Out Of Range",
    "P1285": "Fuel Injection Pump Controller Always On",
    "P1286": "Accelerator Pedal Position Sensor Supply Voltage Too High",
    "P1287": "Fuel Injection Pump Controller Supply Voltage Low",
    "P1288": "Intake Manifold Short Runner Solenoid Circuit Open Or Shorted",
    "P1289": "Manifold Tune Valve Solenoid Circuit Open Or Shorted",
    "P1290": "CNG Fuel Pressure Too High",
    "P1291": "No Temp Rise Seen From Fuel Heaters",
    "P1292": "CNG Pressure Sensor Voltage Too High",
    "P1293": "CNG Pressure Sensor Voltage Too Low",
    "P1294": "Target Idle Not Reached",
    "P1298": "Lean Operation At Wide Open Throttle",
    "P1299": "Vacuum Leak Found (IAC Fully Seated)",
    "P1688": "Internal Fuel Injection Pump Controller Failure",
    "P1689": "No Communication Between ECM & Injection Pump Module",
    "P1690": "Fuel Injection Pump CKP Sensor Does Not Agree With ECM CKP Sensor",
    "P1691": "Fuel Injection Pump Controller Calibration Failure",
    # ASD relay / crank-cam sync
    "P1388": "Auto Shutdown (ASD) Relay Control Circuit Open Or Shorted",
    "P1389": "No Auto Shutdown (ASD) Relay Output Voltage At PCM",
    "P1390": "Timing Belt Skipped One Tooth Or More",
    "P1391": "Intermittent Loss of CMP Or CKP",
    "P1398": "PCM Is Unable To Learn The Crankshaft Position Sensor's Signal",
    "P1399": "Wait To Start Lamp Circuit Open Or Shorted",
    # Secondary air / cooling fan / A/C
    "P1475": "Auxiliary 5 Volt Output Too High",
    "P1476": "Too Little Secondary Air",
    "P1477": "Too Much Secondary Air",
    "P1478": "Battery Temp Sensor Voltage Out Of Limit",
    "P1479": "Transmission Fan Relay Circuit Open Or Shorted",
    "P1480": "PCV Solenoid Valve Open Or Shorted",
    "P1481": "EATX RPM Pulse Generator Signal For Misfire Detection",
    "P1485": "Air Injection Solenoid Circuit Open Or Shorted",
    "P1486": "Evap Leak Monitor Pinched Hose",
    "P1487": "Hi Speed Rad Fan Control Relay Circuit Open Or Shorted",
    "P1488": "Auxiliary 5 Volt Supply Output Too Low",
    "P1489": "High Speed Fan Control Relay Circuit Open Or Shorted",
    "P1490": "Low Speed Fan Control Relay Circuit Open Or Shorted",
    "P1491": "Radiator Fan Control Relay Circuit Open Or Shorted",
    "P1492": "Battery Temperature Sensor Voltage Too High",
    "P1493": "Battery Temperature Sensor Voltage Too Low",
    "P1494": "Leak Detection Pump Switch or Mechanical Fault",
    "P1495": "Leak Detection Pump Solenoid Circuit Open Or Shorted",
    "P1496": "5 Volt Supply Output Too Low",
    "P1498": "High Speed Rad Fan Ground Control Relay Circuit",
    "P1499": "Open Or Shorted Condition Detected In The Hydraulic Cooling Fan Solenoid Control",
    "P1598": "A/C Pressure Sensor Voltage Too High",
    "P1599": "A/C Pressure Sensor Voltage Too Low",
    # Charging / speed control / PCM
    "P1594": "Charging System Voltage Too High",
    "P1595": "Speed Control Solenoid Circuit Open Or Shorted",
    "P1596": "Speed Control Switch Always High",
    "P1597": "Speed Control Switch Always Low",
    "P1602": "PCM Not Programmed",
    "P1682": "Charging System Voltage Too Low",
    "P1683": "Speed Control Power Relay Or Speed Control 12 Volt Driver Circuit Open Or Shorted",
    "P1684": "Battery Disconnected Within Last 50 Starts",
    "P1696": "PCM Failure EEPROM Write Denied",
    "P1697": "PCM Failure SRI Mile Not Stored",
    # Body / module communication (CCD/J1850, SKIM, cluster)
    "P1680": "Clutch Released Switch Circuit Open Or Shorted",
    "P1681": "No Instrument Panel Cluster CCD/J1850 Messages Received",
    "P1685": "SKIM Invalid Key",
    "P1686": "No SKIM Bus Message Received",
    "P1687": "No Cluster Bus Message",
    "P1693": "DTC Detected In ECM Or PCM",
    "P1694": "No CCD Messages Received From ECM",
    "P1695": "No CCD/J1850 Message From BCM",
    "P1698": "No CCD Messages Received From PCM",
    "P1699": "No CCD/J1850 Messages Received From The Climate Control Module (CCM)",
    # Transmission
    "P1719": "Skip Shift Solenoid Circuit Open Or Shorted",
    "P1740": "TCC Or OD Solenoid Performance",
    "P1756": "Governor Pressure Not Equal To Target At 15-20 PSI",
    "P1757": "Governor Pressure Above 3 PSI When Request Is 0 PSI",
    "P1762": "Governor Pressure Sensor Offset Improper Voltage",
    "P1763": "Governor Pressure Sensor Voltage Too High",
    "P1764": "Governor Pressure Sensor Voltage Too Low",
    "P1765": "Trans 12 Volt Supply Relay Control Circuit Open Or Shorted",
    "P1830": "Open Or Shorted Condition Detected In The Clutch Pedal Switch Over-Ride Relay Control",
    "P1899": "Park/Neutral Position Switch Stuck In Park or In Gear",
}

ENHANCED_PIDS: tuple[EnhancedPID, ...] = (
    # EnhancedPID(pid="22F440", name="TIPM_STATUS", description="Totally Integrated Power Module status", unit=""),
)

CODING_FUNCTIONS: tuple[VehicleCodingFunction, ...] = (
    VehicleCodingFunction("dodge_chrysler.ram_1500_dt.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Ram", "Ram 1500", "DT", "2019+", "disable_auto_stop_start_persistent", powertrain_notes="eTorque and supported newer powertrains", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.ram_1500_classic_ds.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Ram", "Ram 1500 Classic", "DS", "-", "disable_auto_stop_start_persistent", powertrain_notes="Do not inherit DT ASS support automatically", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.durango_wd.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Dodge", "Durango", "WD", "2016-2025", "disable_auto_stop_start_persistent", powertrain_notes="Primarily 3.6L Pentastar V6", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.pacifica_ru.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Chrysler", "Pacifica", "RU", "2018+", "disable_auto_stop_start_persistent", powertrain_notes="Exclude Pacifica Hybrid from conventional ASS logic", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.voyager_ru.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Chrysler", "Voyager", "RU", "2020+", "disable_auto_stop_start_persistent", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.grand_cherokee_wk2.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Jeep", "Grand Cherokee", "WK2", "2016-2021", "disable_auto_stop_start_persistent", powertrain_notes="Primarily 3.6L Pentastar V6", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.grand_cherokee_wl.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Jeep", "Grand Cherokee", "WL", "2021+", "disable_auto_stop_start_persistent", powertrain_notes="Exclude 4xe from conventional ASS logic", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
    VehicleCodingFunction("dodge_chrysler.grand_cherokee_l_wl.disable_auto_stop_start_persistent", "Disable auto stop-start (persistent)", "dodge_chrysler", "Jeep", "Grand Cherokee L", "WL", "2021+", "disable_auto_stop_start_persistent", powertrain_notes="Exclude hybrid configurations from conventional ASS logic", target_ecu_family="mopar_bcm", status=CodingFunctionStatus.RESEARCH),
)


class DodgeChryslerProfile(VehicleProfile):
    key = "dodge_chrysler"
    display_name = "Dodge / Chrysler"
    wmi_codes = ("1C3", "1C4", "1C6", "2C3")

    def get_dtc_description(self, code: str) -> str | None:
        return DTC_TABLE.get(code)

    def enhanced_pids(self) -> tuple[EnhancedPID, ...]:
        return ENHANCED_PIDS

    def coding_functions(self) -> tuple[VehicleCodingFunction, ...]:
        return CODING_FUNCTIONS


register_profile(DodgeChryslerProfile())
