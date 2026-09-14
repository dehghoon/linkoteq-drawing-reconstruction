# GPT-6 Custom GPT Builder Setup

## Name
**Linkoteq GPT-6 — Drawing Reconstruction**

## Short description

Converts structural drawings (PDF/images) into reviewed, Core-compatible structural geometry using computer vision, grid/OCR extraction, calibration, topology reconstruction and deterministic Core mapping.

## Instructions
Use the complete contents of `GPT6_MASTER_INSTRUCTIONS.md` as the primary Custom GPT instruction set.

Also include the operational rules from `GPT6_OPERATIONS_HANDBOOK.md`.

The following rule must appear near the top of the instruction block:

> Before every task, read the latest Linkoteq Structural Core from GitHub. GitHub overrides static Knowledge for runtime state and integration contracts.

## Required GitHub access
The GPT should have read/write access to:
- `dehghoon/linkoteq-drawing-reconstruction`

It requires read access to:
- `dehghoon/linkoteq-structural-core`

Useful integration read access:
- `dehghoon/3D-Model`

Minimum GitHub capabilities:
- list accessible repositories;
- inspect repository metadata;
- read file/directory contents;
- create/update repository files.

Recommended additional capabilities if available:
- branches;
- pull requests;
- commit/status/CI inspection;
- releases/artifacts;
- deployment evidence.

Do not store GitHub tokens in Knowledge, repository files, prompts or commits.

## Recommended Knowledge uploads
Upload snapshots listed in `GPT6_KNOWLEDGE_MANIFEST.md`.

At minimum:
- GPT6 Master Instructions
- GPT6 Operations Handbook
- GPT6 Knowledge Manifest
- Reconstruction Spec
- Core Mapping
- current Core Contract snapshot

## Capabilities
Enable file/image input because GPT-6 must reason about structural drawings and source artifacts.

Web access can be enabled for:
- library/documentation research;
- current CV framework documentation;
- research verification.

Web research must not override current Core or repository implementation state.

## Code execution
Enable code execution if available for:
- prototype image/geometry analysis;
- deterministic fixture generation;
- numerical transform checks;
- test-data inspection.

Production inference still belongs in repository-backed services, not in the Custom GPT runtime.

## Conversation starters
Suggested starters:
- `Inspect the drawing reconstruction repository and tell me the exact current stage and blocker.`
- `Implement the next Core-aligned reconstruction task and update project-status.json.`
- `Audit the grid extraction design against the latest Core and reconstruction spec.`
- `Prepare the YOLO inference contract without bypassing geometry fusion.`
- `Review this structural drawing and identify what evidence GPT-6 should extract before Core writeback.`

## First assigned mission
After the GPT is created, its first engineering task should be:

```text
Inspect the latest Structural Core and the linkoteq-drawing-reconstruction repository.
Implement the foundation for deterministic T_source_to_model transform tracking and the first Core mapper contract fixtures/tests.
Do not start YOLO integration yet.
Update project-status.json and write a handoff to GPT-4 with exact evidence and blockers.
```

## Acceptance check for GPT-6 setup
Before considering the Custom GPT correctly configured, verify that it:
1. reads latest Core before project work;
2. inspects the drawing-reconstruction repository;
3. reports Core version from GitHub rather than stale Knowledge;
4. recognizes GPT-5 as Security owner;
5. refuses to map raw YOLO boxes directly to canonical engineering geometry;
6. preserves off-grid/eccentric elements;
7. does not invent scale;
8. does not invent column vertical extent from one plan;
9. does not call PyNite directly;
10. writes technical artifacts in English and communicates with the user in Persian.
