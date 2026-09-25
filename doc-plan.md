# Doc Plan: Cypher-DDS master manual refresh and README rewrite

## Audience & Purpose

- **Primary audience (master manual):** maintainers, collaborators, and agents working inside the Cypher-DDS repo who need one canonical handbook that explains the product, engineering architecture, documentation set, validation posture, and roadmap in one place.
- **Primary audience (README):** developers, evaluators, and technically capable users landing on the repo who need a concise but accurate project overview, setup path, feature scope, and support boundaries.
- **Done looks like:**
  - `Cypher-DDS_MASTER.md` reads as a coherent handbook rather than a loose summary of adjacent docs.
  - `README.md` is shorter, clearer, and aligned with the current codebase and validation status.
  - claims about GUI packaging, Android Bluetooth, OEM actions, and support levels match current repo state.

## Source Material

- Available:
  - `README.md`
  - `Cypher-DDS_MASTER.md`
  - `ENGINEERING_MANUAL.md`
  - `PROJECT_STATUS.md`
  - `PRODUCTION_REVIEW_2026-07-17.md`
  - `CYPHER_DDS_TOOL_REFERENCE.md`
  - `plans/00-ROADMAP.md`
  - `plans/01-GUI-PLAN.md`
  - `plans/02-ANDROID-VALIDATION.md`
  - source under `src/cypher_dds/`
  - tests under `tests/`
  - workflow files under `.github/workflows/`
  - packaging files `buildozer.spec`, `cypher-dds.spec`, `cypher-dds-gui.spec`, `pyproject.toml`
- Missing (Draft stage must find or flag):
  - fresh CI confirmation for the newly added GUI packaging paths
  - physical-device/runtime validation for Android Bluetooth
  - real desktop runtime validation for packaged GUI artifacts

## Doc Type

Master manual + user-facing overview refresh | Depth: exhaustive for master manual, concise for README | Triggers Verify: yes

## Outline

1. **Master manual refresh** — make `Cypher-DDS_MASTER.md` read like a canonical handbook with clear part boundaries, explicit validation posture, and a stronger bridge between product, engineering, and operations.
2. **README rewrite** — tighten the project overview, preserve essential setup/use information, and align claims with current implementation and validation reality.
3. **Validation-sensitive sections** — verify every claim touching packaging, GUI state, Android Bluetooth, OEM action support, and current supported surfaces against code/tests/workflows.
4. **Documentation cross-links** — keep the master manual and README linked to the detailed supporting docs without duplicating every detail.
5. **Promotion readiness** — final drafts should be directly promotable into `Cypher-DDS_MASTER.md` and `README.md` with no silent unresolved verification markers.
