# GPT-6 to GPT-4 Handoff

## Runtime baseline
- Core repository: `dehghoon/linkoteq-structural-core`
- Confirmed Core contract: `0.5`
- Drawing repository: `dehghoon/linkoteq-drawing-reconstruction`

## Verified baseline
- Core contract/mapper fixtures are present.
 - Deterministic source normalization and transform tracking is implemented.
- Grid geometry extraction is complete with vector-PDF and raster pipeline evidence.
 - OCR/grid labeling remains in progress.
 - Explicit-evidence scale calibration is implemented and tested; unresolved or conflicting scale blocks canonical physical-geometry writeback.
 - Column detection association is implemented as importer-private evidence; a plan detection does not establish vertical member extent.
- Beam centerline/endpoint reconstruction is implemented with distance-threshold review and a distinct-endpoint-node guard.

## Latest verification evidence
- User confirmed green GitHub Actions after `test: cover same-node beam endpoint review` (commit `7dd6838`).
- User confirmed green GitHub Actions after `docs: synchronize reconstruction stage status` (commit `fe6f405`).
- Project status is aligned to the current implementation layers; it does not claim production verification.

## Current owned stage
B`eam-reconstruction-and-connectivity` is in progress. The next boundary is safe mapping of only reviewed/resolved reconstruction evidence to Core-compatible model data.

## Boundary conditions
- YoLO/OCR/detector bounding boxes are evidence, not canonical engineering geometry.
 - Do not write raw pixel or normalized-drawing coordinates into Core.
- Canonical geometry must use global coordinates, explicit project units, and stable IDs and must validate against Core v0.5.
- Unresolved scale blocks canonical physical-geometry writeback.
- A column plan detection alone must not create a canonical vertical Member.
 - A beam must have two resolved, distinct structural nodes before canonical Member creation.
- Do not call PyNite directly; analysis belongs behind the Core-defined PyNite Analysis Adapter.

## Remaining cross-product blockers
1. Core v0.5 fixture validation is not yet wired to the Core TypeScript validator/CI.
2. Canonical physica-geometry writeback requires reliable resolved scale evidence for each relevant source page.
3. Production reconstruction verification has not been claimed.
