# GPT-6 to GPT-4 Handoff

## Runtime baseline
- Core repository: `dehghoon/linkoteq-structural-core`
- Confirmed Core schema: `0.5`
- Drawing repository: `dehghoon/linkoteq-drawing-reconstruction`

## Stage B implementation
Implemented and locally verified:
- explicit `vector` / `raster` / `mixed` source classification;
- stable source/page identity, dimensions, optional DPI and media-type metadata;
- mixed-page policy preserving native vector geometry as the normalization source space;
- deterministic ordered preprocessing transform accumulation;
- affine transforms plus projective transform tracking for perspective correction;
- normalized page dimensions and immutable preprocessing evidence;
- bridge from normalized page evidence to unresolved `T_source_to_model`;
- unresolved engineering scale/units/global placement continue to block Core writeback.

Not implemented:
- concrete PDF/image parser adapters that extract the page metadata from real files;
- grid geometry extraction;
- OCR/grid labels;
- engineering scale calibration;
- YOLO/object detection;
- beam/column reconstruction;
- PyNite/solver calls.

## Verification evidence
Focused implementation test executed locally before GitHub write:
- `python -m pytest -q tests/test_source_normalization.py`
- result: `7 passed`

Regression reconstruction of current foundation suite plus Stage B tests:
- `python -m pytest -q`
- result: `14 passed`
- note: this regression run used the GitHub-read foundation modules plus the exact Stage B content written in this handoff; repository CI was not available/triggered here.

## Current blockers
1. Concrete real-file PDF/image parser adapters are not implemented; source normalization currently begins from explicit extracted page metadata.
2. Core v0.5 fixture validation is not wired to the Core TypeScript validator/CI.
3. Scale calibration from drawing evidence remains unimplemented; unresolved scale intentionally blocks canonical physical geometry.

## Exact next action
Begin Stage C grid geometry extraction on normalized geometry: define importer-private line-segment/grid-candidate evidence, deterministic orientation/collinearity clustering and controlled fixtures. Keep grid axes geometric, do not use detector bounding boxes, and do not start YOLO.

## Forbidden changes
- Do not map raw pixels directly to Core geometry.
- Do not infer or invent engineering scale.
- Do not merge importer-private evidence into canonical Core types.
- Do not call PyNite directly.
- Do not modify `linkoteq-structural-core` for importer convenience.
