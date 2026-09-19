# Structural Layout Context Consumer v0.1

## Authoritative shared contract
GPT-6 consumes `dehghoon/linkoteq-structural-detection/contracts/structural-layout-context-v0.1.md`.
Refresh that contract before changing reconstruction behavior. Do not fork or silently redefine its semantics.

## Reconstruction boundary
The shared contract supplies contextual priors, review triggers, and hard inference gates. GPT-6 owns engineering fusion and canonical reconstruction.

Required behavior:
- accept drawings with no explicit grid without inventing grids;
- do not create columns at every grid intersection;
- do not interpret a missing visible/detected column as proof of absence;
- preserve materially off-grid evidence for review rather than blindly snapping;
- treat `story_count` as context only; it cannot create levels, elevations, story heights, columns, or vertical extents;
- use cross-level column repetition only as supporting continuity evidence;
- route cross-level appearance/disappearance/relocation/offset/change to review for possible transfer, setback, termination/start, framing change, drawing inconsistency, or detection error;
- treat inside-column-grid-bay wall location only as a prior compatible with nonstructural partitioning, never proof;
- recognize internal shear/core walls as counterexamples;
- never promote architectural partitions to structural walls from graphics alone;
- fuse wall semantics with transforms, scale, drawing conventions, related geometry/semantics, cross-level evidence, and review before canonical wall reconstruction.

## Evidence compatibility
StructuralDetectionEvidence v0.1 remains exactly `column` and `beam`.
A `wall` record claiming v0.1 semantics must be rejected.
Detector boxes, masks, centers, and axes remain evidence only and must not automatically become Core geometry.

## Wall activation gate
Do not treat wall consumption as production-ready until the approved wall-capable ontology/annotation rules, StructuralDetectionEvidence contract, GPT-6 consumer regression, and coordinated approval exist in GitHub.

## Consumer regression requirements
Tests for the shared layout-context migration must demonstrate:
1. no-grid input does not invent grids;
2. grid intersections do not automatically create columns;
3. missing visible column evidence does not become an automatic absence conclusion;
4. story count does not create vertical geometry;
5. cross-level repetition remains contexual;
6. discontinuity/relocation routes to review;
7. inside-grid walls are not automatically structural or nonstructural;
8. partition-like graphics alone cannot create canonical structural walls;
9. unresolved wall semantics remain reviewable;
10. legacy StructuralDetectionEvidence v0.1 column/beam behavior remains passing;
11. v0.1 wall evidence is rejected;
12. provenance and review state are preserved through reconstruction.
