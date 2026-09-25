# Cypher-DDS — Reference Tools & Documentation

Research pass on high-end commercial scan tools and open technical references, for agents (`agy`, Claude Code, etc.) to consult when scoping bi-directional/coding/programming features. This is feature-terminology and architecture reference, not a spec to copy verbatim — none of these vendors publish their actual ECU command tables publicly.

## Flagship commercial tools (feature vocabulary + UX patterns)

**Autel MaxiSys Ultra / Ultra S2 / Elite II Pro**
https://www.autel.us/inside-autels-ultra-s2/

- Splits functionality into clean tiers worth mirroring in our own support-level model: "Active Test" (bi-directional), "Guided Functions," "40–48 Service Resets," "ECU Coding," "ECU Programming" (new blank ECU flash).
- Topology Mapping — a live network diagram of ECUs on the vehicle's bus, built before running tests. Good target for our `catalog.py` ECU-family metadata to eventually render as a diagram in the TUI.
- Explicit vehicle-count/model-count marketing (15,000+ models) — a pattern we should avoid copying rhetorically per your no-hardcoded-counts preference, but useful as a sense of scale for "real" coverage.

**Snap-on TRITON-D10 / ZEUS / APOLLO-D9**
https://www.manualslib.com/manual/2166518/Snap-On-Triton-D10.html

- Most useful single find: Snap-on's manual draws a clean line between **Toggle Tests** (binary state change — relay/solenoid/switch on↔off) and **Variable Control Tests** (commanding a value along a range — spark timing in 1° steps, EGR duty cycle in 10% steps). That's a concrete second axis worth adding to our `DiagnosticAction` model beyond category/support_level — right now every action is implicitly "send command(s), check prefix," with no notion of a parameterized/ranged command.
- "Functional Tests & Bi-Directional Controls" and "Relearns/Adaptations" are treated as separate menu tiers, matching our `ACTIVE_TEST` vs `SERVICE` category split.

**XTOOL D8S / D9S, Topdon Phoenix/ArtiDiag/UltraDiag line**
https://obdadvisor.com/professional-automotive-scanners/

- Mid-tier tools increasingly market "Topology Mapping" and "CAN FD support" as the differentiator from basic bi-directional, at well under flagship pricing — signals these are becoming baseline-expected features, not premium-only.
- Consistent naming across this tier for reset services: oil, EPB, SAS (steering angle sensor), DPF regen, throttle adaptation, ABS bleed, injector coding, BMS (battery management reset) — this list is a good cross-check against our `ecu_families`/`actions` planned-action names to make sure naming matches what a technician would search for.

## Open-source / protocol-level references (actually inspectable code & specs)

**python-udsoncan** (MIT license) — full UDS (ISO 14229) client implementation in Python
https://github.com/pylessard/python-udsoncan
https://udsoncan.readthedocs.io/en/latest/

- Directly relevant prior art for the gaps our own `PRODUCTION_REVIEW` flagged: real negative-response classification, `change_session`, `unlock_security_access`, routine control. This is the single best reference for building the "first-class UDS/transport layer" the review recommends — its `services` module shows how to structure request/response classes per UDS service ID.

**python-can-isotp** (companion library, ISO-TP / ISO 15765-2 transport)

- Pairs with udsoncan above; relevant for the "raw ISO-TP transport abstraction" gap called out in the review as not yet production-grade in Cypher-DDS.

**FORScan** — Ford/Lincoln/Mazda bi-directional tool, closed-source but well documented by its community
https://forscan.org/modules_list.html

- Not open-source, but its module list and forum threads describe real-world command/coding patterns (As-Built Data editing, module programming via a separate licensed add-on) that map well onto our `body_control_coding` / `module_programming` action categories — useful as a naming/scope reference for what a Ford profile would eventually need, without using any of their actual proprietary payloads.

## Standards (the actual normative documents, not vendor marketing)

- **ISO 14229 (UDS)** — the request/response service framework udsoncan implements. Worth the team having a summarized service-ID table (0x10 DiagnosticSessionControl, 0x11 ECUReset, 0x22 ReadDataByIdentifier, 0x2E WriteDataByIdentifier, 0x31 RoutineControl, 0x27 SecurityAccess, etc.) since `actions.py` currently hardcodes only two UDS commands (`1003`, `3E00`) as raw hex strings rather than named services.
- **ISO 15765-2 (ISO-TP)** — transport segmentation over CAN, the layer below UDS.
- **SAE J2534 (pass-thru)** — the standard flagship tools use for OEM-level reflashing; relevant context for why `module_programming` is correctly blocked until Cypher-DDS has an equivalent transport story.

## Suggested use for your agents

The clearest actionable gap across all of this: Cypher-DDS's `actions.py` treats UDS commands as opaque hex strings (`"1003"`, `"3E00"`). Every serious reference above (Snap-on's toggle/variable split, udsoncan's service classes) models this as **named services with typed parameters**, not raw command strings. That's probably the single highest-leverage refactor before adding real OEM write routines — it would make the `PLANNED` actions in the current catalog much closer to actually implementable.
