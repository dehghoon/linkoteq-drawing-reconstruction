# Upload to 3D Reconstruction Contract v0.1

## Purpose

Define the website runtime boundary from a user-uploaded structural PDF/image to a reviewed Linkoteq Core v0.5 `StructuralModel` and web 3D visualization.

## Web upload inputs

The upload flow MUST collect:
- the structural PDF or image;
- `story_count`: user-provided positive integer for the number of stories to reconstruct.

The web UI SHOULD ask the user "How many stories does this structural model have?" during upload, before reconstruction starts.

`story_count` is user-provided restruction evidence. It MUST NOT be used to invent story heights, level elevations, or column vertical extents. Those require drawing evidence or explicit user calibration/confirmation.

## Runtime ownership

General orchestration/request routing belongs to GPT-4. GPT-6 is the drawing-reconstruction entry point and owns source classification, preprocessing, normalization, deterministic transform tracking, grid/OCR/scale, fusion, engineering geometry, topology, review, Core mapping, and 3D reconstruction output.

GPT-7 owns structural detection inference for the approved semantic classes. Initial classes are `column` and `beam`.

## GPT-6 -> GPT-7 inference input

GPT-6 MUST preserve the original source as read-only provenance and produce a deterministic detector input for each source page. The GPT-7 inference request MUST include:
- `source_id`;
- `page_id`;
- an immutable source-page image reference or bytes decived from the upload;
- `coordinate_space = "source-page"`;
- source pixel width and height;
- detection contract version;
- label ontology version;
- preprocessing provenance if a detector-specific derivative is used.

If GPT-7 runs inference on a resized, cropped, rotated, deskewed, or otherwise transformed image, that transform MUST be deterministic and the handoff geometry MUST be returned in declared `source-page` coordinates. GPT-6 MUST NOT infer an undeclared detector transform.

## GPT-7 -> GPT-6 handoff

The result MUST conform to `StructuralDetectionEvidence v0.1` and the approved label ontology. GPT-7 returns semantic detection evidence only. It MUST NOT return canonical `GridLine`, `Node`, `Member`, `Surface`, engineering scale, topology, or final 3D geometry.

## Grid boundary

Grid reconstruction remains a GPT-6 responsibility. GPT-6 reconstructs grid axes from drawing geometry, bubbles, OCR, vector extraction, and other reviewed evidence. GPT-7 `column` or `beam` detections must not be used as a substitute for grid geometry.

## 3D generation gate

The website MUST NOT build the canonical 3D structural model directly from detector boxes or grid candidates. The sequence is:

```text
PDF/Image + story_count
          |
          v
GPT-6 source normalization + T_source_to_normalized
          |
          +---> GPT-7 column/beam detection ---+
          |                                           |
          +---> GPT-6 grid + OCR + scale ------------+
                                                       |
                                                       v
                                            GPT-6 fusion
                                                       |
                                                       v
                                            engineering geometry
                                                      |
                                                      v
                                            levels + nodes + topology
                                                      |
                                                    v
                                               review / validation
                                                      |
                                                    v
                                            Core v0.5 StructuralModel
                                                      |
                                                    v
                                                web 3D viewer
```

The 3D viewer MAY show review-pending overlays as non-canonical evidence, but only reviewed/resolved engineering facts may cross the Core writeback boundary.

## Level and column vertical extent rule

User-provided `story_count` defines the intended number of stories to reconstruct. It does not define the elevation of any level or prove that a detected column continues across all stories.

Canonical `Level` elevations and column vertical extents require reliable drawing evidence or explicit user calibration/confirmation. If missing, the reconstruction MUST require review and MUST NOT invent vertical geometry.

## Core boundary

All canonical writeback must validate against the current Core contract. At the time of this contract, GitHub `main` `@package.json` reports `0.5.0`. Core geometry must use global coordinates, explicit project units, and stable IDs. No raw source/pixel coordinates may cross the Core boundary.
