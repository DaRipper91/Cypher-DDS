# Cypher-DDS - Vehicle-Tied Coding Functions Roadmap

This roadmap tracks **persistent coding/parameter-write functions** (e.g. permanently disabling auto stop-start, other "set it once and it stays off" ECU settings) separately from Cypher-DDS's core diagnostic feature set (PIDs, DTCs, VIN, live data).

Why separate: these functions are vehicle/module-specific rather than protocol-generic. Each entry needs its own research, its own module target, and its own write procedure - this list will grow per make/model/year rather than per brand family.

## How to use this doc

Add one row per confirmed function. Don't add a row until the parameter/procedure has been verified against a real source (community write-up, service manual reference, or your own tested confirmation) - this avoids the list filling up with unverified guesses.

## Status legend

- `research` - function is known to exist for this platform, procedure not yet confirmed
- `confirmed` - procedure verified against a documented source, not yet implemented in Cypher-DDS
- `implemented` - coded into the relevant brand profile module
- `tested` - implemented and confirmed working against real hardware

## Function tracker

Target function for all rows below: **disable auto stop-start (persistent)**.

| Brand | Model | Platform | Years | Powertrain / Notes | Module | Access Level | Adapter Type | Status |
|---|---|---|---|---|---|---|---|---|
| Ford | F-150 | P552 | 2017-2020 | EcoBoost | | | | research |
| Ford | F-150 | P702 | 2021+ | Gasoline EcoBoost / PowerBoost needs separate handling | | | | research |
| Ford | Explorer | U625 | 2020+ | | | | | research |
| Ford | Escape | CX482 | 2020+ | Exclude hybrid powertrains from conventional ASS logic | | | | research |
| Ford | Expedition | U553 | 2018+ | | | | | research |
| Ford | Bronco | - | 2021+ | ASS configuration requires further validation | | | | research |
| Chevrolet | Silverado 1500 | T1XX | 2019+ | | | | | research |
| Chevrolet | Equinox | D2XX | 2018-2024 | | | | | research |
| Chevrolet | Equinox | D2XX-2 | 2025+ | | | | | research |
| Chevrolet | Tahoe | T1XX | 2021+ | | | | | research |
| Chevrolet | Suburban | T1XX | 2021+ | | | | | research |
| Chevrolet | Traverse | C1XX | 2018-2023 | | | | | research |
| Chevrolet | Traverse | C1XX-2 | 2024+ | | | | | research |
| Chevrolet | Colorado | 31XX-2 | 2023+ | | | | | research |
| Chevrolet | Trax | - | - | ASS configuration requires further validation | | | | research |
| GMC | Sierra 1500 | T1XX | 2019+ | | | | | research |
| GMC | Yukon | T1XX | 2021+ | | | | | research |
| GMC | Canyon | 31XX-2 | 2023+ | | | | | research |
| Ram | Ram 1500 | DT | 2019+ | eTorque and supported newer powertrains | | | | research |
| Ram | Ram 1500 Classic | DS | - | Do not inherit DT ASS support automatically | | | | research |
| Dodge | Durango | WD | 2016-2025 | Primarily 3.6L Pentastar V6 | | | | research |
| Chrysler | Pacifica | RU | 2018+ | Exclude Pacifica Hybrid from conventional ASS logic | | | | research |
| Chrysler | Voyager | RU | 2020+ | | | | | research |
| Jeep | Grand Cherokee | WK2 | 2016-2021 | Primarily 3.6L Pentastar V6 | | | | research |
| Jeep | Grand Cherokee | WL | 2021+ | Exclude 4xe from conventional ASS logic | | | | research |
| Jeep | Grand Cherokee L | WL | 2021+ | Exclude hybrid configurations from conventional ASS logic | | | | research |

## Notes on auto stop-start specifically

- Typically lives as a coding bit in the BCM or a body-adjacent module - rarely the PCM/ECM itself
- Access level varies widely by manufacturer: some allow open coding writes over a basic ELM327/Bluetooth adapter, others gate the write behind security access (seed-key), which pushes the requirement toward a UDS-capable adapter for that specific brand
- Existing consumer coding apps (Carista, BimmerLink, OBDeleven, AlfaOBD, FORScan) already implement this for many platforms - worth checking their supported-vehicle lists per brand as a fast way to confirm whether a given model is a "basic adapter" case or a "needs security access" case before doing from-scratch research
- Once the vehicle groups are added below, each row should note which of Cypher-DDS's six existing brand profiles (GM, Ford, Dodge/Chrysler, Toyota/Lexus, Honda/Acura, Kia) it falls under, so the write procedure can live in the matching profile module
- Jeep isn't currently one of the six existing brand profiles - it shares Stellantis platforms with Dodge/Chrysler/Ram, so decide whether it lives inside the existing Dodge/Chrysler profile module or needs its own
- Several rows explicitly exclude hybrid/electrified variants (Escape Hybrid, Pacifica Hybrid, Grand Cherokee 4xe) from conventional ASS logic - these likely need a separate function entry later rather than being folded into the standard ICE procedure, since hybrid stop-start behavior is usually controlled differently

## Open questions to resolve per vehicle group

1. Which module holds the parameter?
2. Is security access required, and if so, is the algorithm publicly known/reverse-engineered for this platform?
3. What's the minimum adapter tier needed - basic ELM327/BLE, or CAN+UDS?
4. Is there a known byte/bit value and offset, or does it require a documented coding procedure (e.g. via a specific diagnostic session type)?

## Engineering phases

This tracker only becomes real product work if the transport/action stack underneath it is built in the right order.

### Current repo progress

- Phase 1 is started: the action layer now uses typed UDS request models for existing UDS-backed actions
- Phase 2 is started: UDS negative responses are now classified separately from generic response mismatches, and actions can declare ECU/session/security/adapter prerequisites
- No real persistent coding write routine is implemented yet; the next step is to add security-access and write-service helpers for one specific vehicle slice

### Phase 1 - UDS action foundation

- Replace raw UDS hex literals in action manifests with typed request models
- Introduce named helpers for common services such as:
  - Diagnostic Session Control (`0x10`)
  - Tester Present (`0x3E`)
  - Read Data By Identifier (`0x22`)
  - Write Data By Identifier (`0x2E`)
  - Routine Control (`0x31`)
  - Security Access (`0x27`)
- Keep current mock/test behavior stable while making room for richer request/response validation

### Phase 2 - Response and safety model

- Decode UDS negative responses explicitly instead of treating all failures as generic action errors
- Add action metadata for:
  - target ECU family
  - required diagnostic session
  - required security access level
  - adapter/network prerequisites
- Add stricter confirmation gates for coding writes versus read-only enhanced data actions

### Phase 3 - Vehicle-tied coding manifest

- Add a dedicated manifest structure for persistent coding functions, separate from generic service actions
- Each entry should capture:
  - make/profile target
  - vehicle/platform scope
  - ECU/module target
  - required session/security path
  - identifier/byte/bit procedure
  - rollback/default value if known
- Do not mark a function `implemented` until the manifest is backed by a verified source

### Phase 4 - First supported platform slice

- Pick one platform family with the best public documentation and the fewest transport blockers
- Implement read/validate/write flow in the matching profile module
- Add mock coverage for the request sequence and guardrails
- Promote only that specific vehicle group to `implemented`; leave the rest at `research` or `confirmed`

### Recommended first slice

- Start with GM or Ford only
- GM has the cleaner current path for standard-bus-visible enhanced actions in this repo
- Ford body functions are often constrained by the documented MS-CAN limitation in the current architecture
- Avoid late-model Stellantis first because gateway/security restrictions are likely to dominate early effort
