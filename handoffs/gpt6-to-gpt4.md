# GPT-6 to GPT-4 Handoff

## Runtime baseline
- Core repository: `dehghoon/linkoteq-structural-core`
- Confirmed Core schema: `0.5`
- Drawing repository: `dehghoon/linkoteq-drawing-reconstruction`

## Foundation implementation
Implemented:
- deterministic per-source/page affine transform tracking;
- explicit source -> normalized -> calibrated/global model transform chain;
- unresolved scale/unit/global-placement writeback gate;
- importer-private calibration evidence;
- initial Core v0.5 minimal mapper fixture;
- mapper boundary checks for stable IDs, level references, and exclusion of source pixel evidence;
- deterministic transform and mapper tests.

Not implemented:
- YOLO/object detection;
- grid extraction algorithms;
- OCR;
- scale inference/calibration algorithms;
- beam/column reconstruction;
- PyNite/solver calls.

## Verification evidence
Local test execution against the committed implementation content:
- command: `python -m pytest -q`
- result: `10 passed in 0.11s`
- no repository CI workflow was available/triggered by GPT-6 in this handoff.

## Current blockers
1. Real vector/raster/mixed source normalization is not implemented.
2. Core v0.5 fixture validation is not yet wired to the Core TypeScript validator/CI.
3. Scale calibration from drawing evidence is not implemented; unresolved scale intentionally blocks canonical physical geometry.

## Exact next action
Implement Stage B source normalization: source classification, deterministic page/source metadata, preprocessing transform accumulation, and tests that preserve page identity and source geometry. Do not start YOLO or grid detection in that task.

## Forbidden changes
- Do not bypass unresolved scale/global-placement gates.
- Do not map raw pixels to Core geometry.
- Do not merge importer-private evidence into canonical Core types.
- Do not call PyNite directly.
- Do not modify `linkoteq-structural-core` for importer convenience.
