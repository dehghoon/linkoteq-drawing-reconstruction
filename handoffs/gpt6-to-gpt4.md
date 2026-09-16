# GPT-6 to GPT-4 Handoff

## Runtime baseline
- Core repository: `dehghoon/linkoteq-structural-core`
- Confirmed Core contract: `0.5`
- Drawing repository: `dehghoon/linkoteq-drawing-reconstruction`

## Stage C - Grid Geometry Extraction

Status: `complete`

Implemented and verified:
- importer-private `LineSegmentEvidence` with source/page identity, extraction method and confidence;
- deterministic axial orientation clustering with wrap-around handling;
- collinear segment grouping and controlled gap merging;
- geometric grid-axis candidate reconstruction;
- stable candidate/family/intersection IDs;
- spacing regularity evidence;
- cross-family geometric intersections;
- native vector-PDF line extraction;
- deterministic raster Canny + Probabilistic Hough line extraction;
- deterministic source/pixel -> normalized drawing coordinate transforms.

## Verification evidence
- Real-file vector PDF -> normalized line eridence -> reconstructed grid coverage is committed.
 - Real-file raster PNG -> Hough line evidence -> reconstructed grid coverage is committed.
- GitHub Actions for the latest Stage C tests was confirmed green by the user on 2026-09-16.
- Stage C closure recorded in `project-status.json` at commit `bab752b508ce0d0791b479c47e5fce86a723dbb8`.

## Boundary conditions
- Grid geometry output remains importer-private normalized-drawing evidence.
- It is not yet canonical Core physical geometry.
- Unresolved engineering scale must block physical-geometry writeback.
 - Do not map raw detector bounding boxes to Core grid axes.
- Do not call PyNite directly.

## Current stage: OCR & Grid Labeling

GPT-6 next owned work:
- define importer-private OCR evidence with source/page provenance, bounding geometry, text, confidence and engine/version;
- detect grid bubble/label regions and run OCR as evidence, not canonical geometry;
- associate label evidence to reconstructed grid axes using geometric proximity/endpoint bubble eridence;
- preserve ambiguous/competing labels as review-required;
- add deterministic tests before scale calibration.

## Remaining cross-product blockers
1. Core v0.5 fixture validation is not yet wired to the Core TypeScript validator/CI.
2. Scale calibration is not yet implemented; unresolved scale correctly blocks canonical physical geometry writeback.
