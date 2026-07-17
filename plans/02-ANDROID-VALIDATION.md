# Android Bluetooth Validation Checklist

Date: July 17, 2026

## Purpose

This checklist is the required real-device validation path for the Android
Bluetooth implementation in `cypher_dds.core.android_bluetooth_adapter`.

It exists because this repository cannot prove Android Bluetooth behavior in
CI or in the current local environment.

## Test prerequisites

- Android device running API 24+
- Built APK from `.github/workflows/build-android.yml` or local Buildozer run
- Paired ELM327-compatible Bluetooth adapter
- Vehicle or powered bench ECU

## Validation sequence

### 1. Install and launch

- install APK
- launch app
- confirm no startup crash
- confirm connection mode UI renders

### 2. Permissions

- grant Bluetooth permissions when prompted
- verify app behavior when permissions are denied
- verify permission failure is reported clearly in UI/logs

### 3. Adapter connection

- enter paired adapter MAC address
- keep RFCOMM/SPP default channel at `1`
- connect to adapter
- confirm:
  - no UI freeze
  - connection state changes to live
  - protocol string renders

### 4. Diagnostic flow

- resolve VIN
- confirm profile selection matches the VIN WMI
- read DTCs
- read live data
- refresh twice to confirm repeated polling path remains stable

### 5. Action flow

- open action list
- verify actions are populated for the resolved make
- run one non-mutating action
- verify response log updates
- run one mutating action only if safe in the current environment
- verify confirmation prompt appears before execution

### 6. Failure handling

- test with invalid MAC address
- test with adapter powered off
- test with adapter paired but vehicle ignition off
- confirm:
  - app does not crash
  - failure is logged
  - refresh/action buttons remain consistent with connection state

## Pass criteria

Android Bluetooth is considered validated only when:

- the app connects to a real adapter
- VIN/DTC/live-data path completes
- action list renders
- at least one action executes and logs a response
- failure modes are handled without app crash
