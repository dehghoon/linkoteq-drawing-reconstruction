# GPT-6 to GPT-4 Handoff

## Runtime baseline
- Core repository: `dehghoon/linkoteq-structural-core`
- Confirmed Core schema: `0.5`
- Drawing repository: `dehghoon/linkoteq-drawing-reconstruction`

## Stage C geometry foundation
Implemented:
- importer-private `LineSegmentEvidence` with source/page identity, extraction method, and confidence;
- deterministic axial orientation clustering with wrap-around handling;
- collinear segment grouping and controlled gap merging;
- geometric grid-axis candidate reconstruction from segment endpoints;
- stable deterministic candidate/family/intersection IDs;
- spacing regularity evidence;
- cross-family geometric intersections;
- short-line noise filtering and source-page integrity gates.

The output remains in normalized drawing coordinates as importer-private evidence. It is not a Core `GridLine` and carries no engineering scale/units/model Z.

## Explicitly not implemented
- YOLO or object detection;
- OCR/grid labeling;
- raster line detector execution (Hough/LSD/EDLines);
- real PDF vector-path extraction adapter;
- engineering scale calibration;
- canonical Core GridLine writeback from these candidates.

## Verification evidence
- Focused Stage C tests executed locally before GitHub write: `python -m pytest -q` => `8 passed`.
- The committed grid module and test file were read back from GitHub after write.
- Full repository suite/CI was not executed after the GitHub write; do not treat the 8-test focused run as full regression evidence.

## Current blockers
1. Stage C does not yet have a real-file line-extraction adapter; it currently consumes explicit `LineSegmentEvidence`.
2. Real PDF/image parser adapters remain unimplemented.
3. Core v0.5 fixture validation is not wired to the Core TypeScript validator/CI.
4. Scale calibration from drawing evidence remains unimplemented; unresolved scale continues to block canonical physical geometry.

## Exact next action
Complete Stage C by wiring concrete line-extraction adapters to produce normalized `LineSegmentEvidence` from real vector/raster page content. Prefer native vector paths on vector/mixed pages; for raster pages, wire a deterministic line detector adapter. Keep OCR and YOLO out of this task.

## Forbidden changes
- Do not map normalized drawing coordinates to Core while engineering scale/units/global placement are unresolved.
- Do not treat detector bounding boxes as grid axes.
- Do not start YOLO during grid extraction.
