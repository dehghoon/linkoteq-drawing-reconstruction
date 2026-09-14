# Linkoteq GPT-6 — Operations Handbook

## 1. Startup procedure
Before every task:
1. inspect latest `dehghoon/linkoteq-structural-core`;
2. inspect `dehghoon/linkoteq-drawing-reconstruction`;
3. read `project-status.json`;
4. read relevant handoffs;
5. read `docs/RECONSTRUCTION_SPEC.md`;
6. read `docs/CORE_MAPPING.md`;
7. classify the requested work by module and stage.

## 2. Standard stages

### Stage A — Foundation
Deliver:
- Core mapping contract;
- internal reconstruction boundaries;
- project status;
- fixture strategy;
- transform contract.

Exit criteria:
- Core version known;
- no competing cross-product schema;
- writeback gates defined;
- `T_source_to_model` representation defined.

### Stage B — Source Normalization
Deliver:
- vector/raster/mixed source classification;
- preprocessing;
- deskew/perspective correction where required;
- transform tracking.

Exit criteria:
- source transformations are deterministic and testable;
- page identity and source geometry are preserved.

### Stage C — Grid Reconstruction
Deliver:
- line candidates;
- line clustering/merging;
- grid families;
- intersections;
- grid confidence;
- OCR/bubble association.

Exit criteria:
- controlled fixtures recover expected grid axes/intersections;
- grid output is geometric, not detector-bbox based.

### Stage D — Scale Calibration
Deliver:
- calibration evidence model;
- source-to-engineering scale;
- residual/error reporting;
- unresolved-scale blocking behavior.

Exit criteria:
- known-scale fixtures meet tolerance;
- unresolved scale cannot silently produce physical Core geometry.

### Stage E — Column Reconstruction
Deliver:
- column detector interface;
- centroid/shape evidence;
- grid association;
- snap/review/off-grid logic.

Exit criteria:
- normal grid columns associate correctly;
- intentional off-grid column is preserved;
- plan-only input does not invent vertical extent.

### Stage F — Beam Reconstruction
Deliver:
- beam detector interface;
- centerline reconstruction;
- endpoint inference;
- node association;
- connectivity checks.

Exit criteria:
- controlled beams connect expected nodes;
- ambiguous endpoint cases enter review.

### Stage G — Core Writeback
Deliver:
- validated mapping to current Core;
- deterministic stable IDs;
- contract tests.

Exit criteria:
- output validates against current Core;
- units/global coordinates are explicit;
- all member references resolve;
- no direct solver dependency.

### Stage H — Review UI/API Integration
Deliver:
- review states;
- evidence payloads;
- accept/reject/edit decisions;
- API/application integration.

### Stage I — Production
Deliver:
- approved model artifacts;
- service deployment;
- health checks;
- representative reconstruction smoke tests;
- version/commit/model provenance.

## 3. Work selection
When choosing the next task, prioritize the earliest incomplete dependency.

Default order:
1. Core mapper fixtures and contract tests
2. `T_source_to_model`
3. source normalization
4. grid extraction
5. OCR/grid labels
6. scale calibration
7. column reconstruction
8. beam reconstruction
9. review workflow
10. additional classes

Do not start YOLO integration merely because it is available if coordinate/grid/scale foundations are unresolved.

## 4. Detection service rule
Object detection should be exposed behind a stable internal interface.

Example conceptual interface:
```text
infer(image, model_version, threshold) -> Detection[]
```

The application may call a separate inference service in production. GPT-6 controls the contract and implementation repository, but Custom GPT itself is not the GPU runtime.

## 5. Evidence record
Each reconstruction candidate should be traceable to evidence:
- source artifact/page;
- source geometry;
- preprocessing/transform version;
- detector/OCR model and version when applicable;
- confidence;
- calibration source;
- association decision;
- review status.

## 6. Status updates
Update `project-status.json` when:
- stage begins/completes;
- blocker appears/resolves;
- Core version changes;
- model/reconstruction integration state changes;
- deployment/production verification changes.

Use statuses such as:
- `not-started`
- `in-progress`
- `blocked`
- `ready-for-next-stage`
- `complete`
- `superseded`

## 7. Handoff to GPT-4
Handoff should contain:
- current Core version;
- source commit(s);
- completed modules;
- tests and evidence;
- unresolved blockers;
- security-review needs;
- exact next action;
- forbidden changes.

## 8. Core migration
If Core changes:
1. inspect changed canonical types/rules;
2. identify importer-boundary impact;
3. update mapper/tests/docs;
4. preserve verified CV/reconstruction behavior unless requirements changed;
5. add migration notes;
6. re-run contract tests.

Do not retrain or rewrite verified detection models solely because Core changed unless the reconstruction requirements themselves changed.

## 9. Security escalation
Send to GPT-5:
- untrusted upload threat model;
- parser sandboxing;
- malware/file-bomb defenses;
- model artifact signing/integrity;
- secret management;
- dependency vulnerability response;
- tenant/privacy controls.

## 10. Completion language
Do not say “complete” unless the claimed layer is verified.
A commit is not a passing test.
A passing test is not a deployment.
A deployment is not a verified production reconstruction.
