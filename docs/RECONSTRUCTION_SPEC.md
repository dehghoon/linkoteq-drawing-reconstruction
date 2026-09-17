# GPT-6 Drawiing Reconstruction Specification

## Objective
Convert structural drawing evidence into reviewed, Core-compatible structural geometry. GPT-6 owns engineering reconstruction; GPT-7 owns structural object detection ML.

## Core baseline
Authoritative source: `dehghoon/linkoteq-structural-core`.
Target schema: `0.5`.

Canonical geometry crossing Core is global, uses explicit project units and stable IDs and validates against current Core. Never call PyNite directly.

## Pipeline
```text
PDF/Image
-> source classification
-> preprocessing + transform tracking
-> grid geometry extraction
-> bubble/OCR grid labeling
-> GPT-7 StructuralDetectionEvidence handoff
-> geometry-semantic fusion
-> scale calibration
-> topology reconstruction
-> validation/human review
-> Core mapper
-> StructuralModel
```

## GPT-7 detection boundary
Initial semantic classes are `column` and `beam`. Dataset lifecycle, annotation, detector selection/benchmark, training/fine-tuning, evaluation, active learning, model registry/artifact approval, and framework-specific inference belong to GPT-7 in `deghoon/linkoteq-structural-detection`.

GPT-6 consumes detector-agnostic `StructuralDetectionEvidence` with stable identity, source/page provenance, semantic class, confidence, source-space geometry, model name/version, and review state.

Detector output is evidence only. GPT-7 must not emit canonical `GridLine`, `Node`, `Member`, `Surface`, engineering scale, topology, or 3D geometry.

## Coordinates
Maintain deterministic source -> normalized drawing -> calibrated engineering -> global model coordinates, with explicit per-source/page transforms such as `T_source_to_model`. Never write raw source/pixel coordinates to Core.

## Grid and OCR
Reconstruct grid axes geometrically. Grid geometry is not detector box geometry. OCR labels grid candidates but does not define axis geometry by text alone.

## Scale
Never guess physical dimensions. Use reliable explicit evidence. Unresolved scale blocks canonical physical geometry.

## Geometry-semantic fusion
Fusion belongs to GPT-6.

Column evidence establishes a candidate horizontal location only. Associate using transformed geometry, grid/topology context, thresholds, and review state. Preserve intentional off-grid/eccentric columns. Do not invent vertical extent.

Beam evidence identifies semantic/region evidence only. Reconstruct centerline and endpoints independently of bbox corners, associate stable structural nodes, and validate connectivity.

## Topology
Topology owns connectivity. Resolve near-coincident nodes deterministically with engineering tolerances. Ambiguity triggers review.

## Review
Use `auto-accepted`, `review-required`, `rejected`, and `preserved-off-grid`. Block or narrow writeback for unresolved scale, ambiguous OCR, competing associations, excessive snap distance, unresolved endpoints, conflicting duplicates, low-confidence evidence, or topology inconsistency.

## Core mapping
Only reviewed/resolved engineering facts cross the Core boundary. Never call PyNite directly.

## Acceptance tests
Controlled fixtures should verify grids/OCR, scale gates, GPT-7 evidence contract, off-grid preservation, column association, beam centerline/endpoints/connectivity, no unintended duplicate nodes, stable IDs, Core validation, and no direct PyNite dependency.

## Implementation continuation
1. maintain Core mapper/contract tests;
2. complete OCR/grid labeling and scale gates;
3. validate GPT-7 handoff fixtures;
4. complete column/beam fusion;
5. complete topology/levels;
6. complete review/writeback gates;
7. verify StructuralModel/3D integration.

Detector training and dataset lifecycle are not GPT-6 tasks.
