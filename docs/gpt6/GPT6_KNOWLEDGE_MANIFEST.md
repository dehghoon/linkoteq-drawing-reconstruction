# GPT-6 Knowledge Manifest

## Purpose
Defines the static Knowledge package for the GPT-6 Custom GPT. Runtime project state remains in GitHub. Static Knowledge must never replace repository inspection.

## Mandatory Knowledge files
Refresh these from the current drawing-reconstruction repository when the GPT Builder package is updated:
1. `GPT6_MASTER_INSTRUCTIONS.md`
2. `GPT6_OPERATIONS_HANDBOOK.md`
3. `GPT6_KNOWLEDGE_MANIFEST.md`
4. `GPT6_BUILDER_SETUP.md`
5. `RECONSTRUCTION_SPEC.md`
6. `CORE_MAPPING.md`
7. latest `CORE_CONTRACT.md` snapshot
8. relevant `AI_GPT_UPDATE_POLICY.md` snapshot
9. research papers only as methodological references.

## Runtime sources of truth
At the beginning of every engineering task inspect:
- `dehghoon/linkoteq-structural-core`;
- `dehghoon/linkoteq-drawing-reconstruction`;
- `dehghoon/linkoteq-structural-detection` when detector evidence or the GPT-7 boundary is relevant;
- `project-status.json`;
- relevant handoffs, tests, fixtures, and migration evidence.

Do not rely on Knowledge uploads for current Core version, repository source code, project status, test results, detector model manifests/evaluation, deployment, API schemas, handoffs, release notes, or CI evidence.

## GPT-7 detection boundary
GPT-7 owns dataset/annotation lifecycle, detector selection and benchmarking, training/fine-tuning, detector evaluation and active learning, model registry/artifacts, and framework-specific inference.

GPT-6 consumes approved detector-agnostic `StructuralDetectionEvidence` only. GPT-6 retains geometry-semantic fusion, column/beam engineering geometry reconstruction, scale, topology, review, Core mapping, and 3D integration.

GPT-7 output is evidence only and must not be treated as canonical Core geometry.

## Research-paper rule
Research papers are methodological references, not platform contracts. Do not copy a paper's detector output directly into canonical Core geometry.

## Freshness and update triggers
Treat Knowledge as potentially stale. Refresh the static package after material Core changes, GPT-6/GPT-7 ownership or boundary changes, major reconstruction architecture changes, or major repository workflow changes.

## Prohibited dependency
The Custom GPT must not depend on manual file transfers between GPT-4/5/6/7 when GitHub can store and retrieve the runtime artifact.
