# StructuralLayoutProposal Contract v0.1

## Purpose
`StructuralLayoutProposal` is a GPT-6-owned, non-canonical reconstruction artifact for drawings where structural layout is incomplete, ambiguous, or not explicitly drawn. It formalizes proposed/inferred grids and structural elements without misrepresenting them as GPT-7 source observations or Core geometry.

This contract complements, and does not replace, `StructuralDetectionEvidence v0.2`.

## Ownership
- GPT-7 owns source-page visual detection and `StructuralDetectionEvidence`.
- GPT-6 owns engineering fusion, reconstruction, proposal generation, review routing, and Core writeback decisions.
- GPT-4 owns cross-repository orchestration and contract reconciliation.
- Core remains the canonical engineering integration boundary.

## Parallel evidence architecture
The original source drawing is supplied independently to the detection and reconstruction/context paths. GPT-7 is not required to receive a GPT-6-modified drawing.

A drawing with no explicit grid or no visible column symbols remains a valid input. Zero detector observations for a class do not prove engineering absence.

## Evidence origin
Every proposed object MUST declare exactly one `origin`: `observed`, `reconstructed`, or `proposed`.

`observed` is directly supported by traceable source evidence. When derived from detector output, it MUST reference the corresponding `StructuralDetectionEvidence` record.

`reconstructed` is deterministically reconstructed from sufficient traceable drawing evidence such as dimensions, transforms, explicit grid geometry, related drawings, or reviewed cross-level evidence.

`proposed` is an engineering hypothesis produced from multiple contextual signals and requiring review before canonical writeback.

`proposed` MUST NOT be serialized as `StructuralDetectionEvidence` and MUST NOT be represented as observed source content.

## Minimum proposal record
A proposal record MUST contain `proposal_id`, `source_id`, `page_id`, `object_type`, `origin`, `coordinate_space`, `geometry`, `basis[]`, `provenance[]`, `confidence`, `review_state`, `core_writeback_eligible`, and `contract_version`.

`contract_version` MUST be `0.1`. Initial `object_type` values are `grid_axis`, `column`, `beam`, and `wall`.

## Coordinate and provenance rules
Proposal geometry MUST remain traceable to the original source coordinate system through explicit transforms. `source-page` SHOULD be retained whenever possible. Derived spaces MUST include a deterministic transform chain back to `source-page`. Synthetic/rendered overlays are presentation artifacts only and MUST NOT become source observations by being passed through GPT-7.

## Grid proposal rules
GPT-6 MAY create a proposed structural reference grid when the source drawing has no explicit grid, provided the grid is marked `origin=proposed`, its basis/provenance are retained, regular spacing alone is not sufficient for canonical promotion, it remains reviewable, and it does not overwrite or fabricate source evidence.

An inferred/proposed grid is not a claim that a grid was present in the source drawing.

## Column proposal rules
GPT-6 MAY propose a column location when visible detector evidence is absent, but MUST NOT do so solely because a grid intersection, beam intersection, regular spacing pattern, or typical-building convention exists.

A proposed column MUST retain supporting evidence, confidence, and review state. Missing GPT-7 column evidence MUST NOT become either automatic absence or automatic presence.

## Detector boundary
`StructuralDetectionEvidence v0.2` remains source-observation evidence. GPT-6 proposals MUST NOT be fed back to GPT-7 and then relabeled as observed detector evidence.

GPT-7 training/annotation datasets MUST NOT treat GPT-6 proposed objects as observed ground truth unless an independent source-evidence/adjudication process establishes that status under the GPT-7 dataset contract.

## Lifecycle
Allowed `review_state` : `proposed`, `review-required`, `approved`, `rejected`.

New proposals default to `proposed` or `review-required`. `approved` means the applicable GPT-6 engineering/review gate passed; it does not bz itself guarantee Core schema validity.

## Core writeback gate
`core_writeback_eligible` MUST default to `false` for proposed records. Eligibility requires review/approval, resolved scale/transforms where physical geometry is needed, applicable topology/geometry checks, traceable provenance, compatibility with the current Core Contract, and successful Core validation.

Only GPT-6 reconstruction/Core mapping may promote eligible engineering geometry into the canonical `StructuralModel`.

## Safety invariants
Forbidden: claiming a proposed grid existed in the source; claiming a proposed column was visually detected by GPT-7; automatic columns at every grid intersection; treating missing detector evidence as proof of absence; promoting architectural partitions to structural walls from graphics alone; using synthetic overlays to manufacture detector provenance; direct PyNite integration across the platform boundary; bypassing Core validation.

## Core and PyNite boundary
This is an intermediate reconstruction contract and does not redefine Core entities. Canonical geometry MUST use the current Core Contract. PyNite MUST be reached through the Core analysis adapter; proposal generation has no direct PyNite dependency.

## Required regression coverage
GPT-6 implementation MUST demonstrate:
1. no-grid/no-visible-column input remains valid;
2. zero-column detector evidence is not engineering absence;
3. proposed grid is distinguishable from observed grid;
4. proposed column is distinguishable from observed/detected column;
5. grid intersections do not automatically create columns;
6. provenance and source transform chain are preserved;
7. synthetic overlays cannot become `StructuralDetectionEvidence through detector re-processing;
8. unapproved proposals cannot write canonical Core geometry;
9. approved proposals still require Core mapping/validation;
10. existing `StructuralDetectionEvidence v0.2` regressions remain passing;
11. legacy v0.1 column/beam compatibility and v0.1 wall rejection remain passing;
12. no direct PyNite dependency is introduced.

## Activation status
This v0.1 document defines the orchestration-approved contract boundary. Runtime implementation is NOT considered complete until GPT-6 implements the proposal model/gates, adds the required regressions, and records successful CI evidence.
