# GPT-6 to GPT-4 Handoff

## Status
Foundation initialized.

## Core
Target schema: `0.5`.
Authoritative source: `dehghoon/linkoteq-structural-core`.

## Deliverables
- `docs/RECONSTRUCTION_SPEC.md`
- `docs/CORE_MAPPING.md`
- `project-status.json`
- `models/model_manifest.json`
- `pyproject.toml`

## Next actions
1. Add Core v0.5 mapper contract fixtures.
2. Add deterministic transform schema and tests for `T_source_to_model`.
3. Add first grid-only fixture.
4. Implement grid extraction before YOLO integration.

## Forbidden changes
- Do not bypass Core with a competing cross-product schema.
- Do not map raw detector boxes directly to canonical geometry.
- Do not call PyNite directly from this importer.
- Do not invent vertical column extent from a single plan.
