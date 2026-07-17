# Desktop GUI Runtime Validation Checklist

Date: July 17, 2026

## Purpose

This checklist is the required runtime validation path for packaged desktop GUI builds.

It exists because CI packaging proves artifact production, not usable runtime behavior on real target systems.

## Targets

- Linux AppImage produced by `.github/workflows/build-linux.yml`
- Windows `.exe` produced by `.github/workflows/build-windows.yml`

## Test prerequisites

- latest packaged GUI artifact
- one Linux desktop with GUI session
- one Windows desktop
- one ELM327-compatible adapter
- one vehicle or powered bench ECU

## Validation sequence

### 1. Launch and window behavior

- launch the packaged GUI
- confirm main window opens
- confirm no immediate crash
- confirm connect controls, diagnostics section, actions section, and logs render

### 2. Mock-mode baseline

- start in mock mode
- connect
- confirm:
  - connection state changes to live
  - VIN renders
  - DTC summary renders
  - DTC detail table renders
  - live data renders
  - action list populates
  - category filter works

### 3. Mock-mode actions

- run one non-mutating action
- confirm response log updates
- run one mutating action
- confirm confirmation prompt appears before execution
- clear DTCs
- confirm clear confirmation appears and UI refresh path remains stable

### 4. Real USB adapter

- connect via USB
- confirm:
  - no UI freeze
  - protocol renders
  - VIN resolves or fails cleanly
  - DTC read completes
  - live data refresh completes

### 5. Desktop Bluetooth path

Linux:

- connect using Bluetooth MAC and RFCOMM channel
- confirm stable connect and refresh behavior

Windows:

- confirm expected behavior for current transport limitation
- if unsupported, confirm failure is clear and non-crashing

### 6. Failure handling

- invalid USB path
- invalid Bluetooth MAC
- adapter disconnected during refresh
- ignition off / no ECU response

Confirm:

- no crash
- error appears in status or log
- buttons remain consistent with actual connection state

## Pass criteria

Desktop GUI runtime validation is considered complete only when:

- packaged GUI launches on real Linux and Windows systems
- mock-mode workflow is stable
- USB workflow is stable on at least one real target
- Linux Bluetooth workflow is stable on at least one real target
- mutating confirmations appear correctly
- failure paths do not crash the application
