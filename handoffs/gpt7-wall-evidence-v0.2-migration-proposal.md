# GPT-7 — GPT-6 Wall Evidence v0.2 Migration Proposal

## Status

Proposal only. Do not enable `wall` handoff yet. The current GPT-6 integration remains `StructuralDetectionEvidence v0.1` with `column` and `beam`.

## Source of truth

- Linkoteq Structural Core v0.5 remains the canonical engineering boundary.
- GPT-7 detection v0.1 currently approves `column` and `beam` only.
- The GPT-7 wall ontology impact analysis proposes ontology v0.2 with `column`, `beam`, and `wall`.
- GPT-6 currently declares `StructuralDetectionEvidence v0.1` as its detector contract and its `structural-detection-handoff` stage is `in-progress`.

## Proposed consumer migration

Before GPT-7 emits any `wall` evidence, GPT-6 should:

1. add version-aware support for the approved versioned detection-evidence contract;
2. accept `wall` only under the new contract and continue to reject `wall` when a record claims v0.1 semantics;
3. require explicit `coordinate_space: source-page` and non-empty traceable `provenance`;
4. preserve legacy v0.1 column/beam consumer fixtures;
5. add valid/and-invalid `wall` fixtures for the new contract;
6. keep fusion detector-agnostic and do not assume a detector box is engineering geometry.

## Ownership boundary

GPT-7 emits reviewed source-page wall evidence only.

GPT-6 remains the owner of:

- source-to-model transforms;
- engineering scale;
- wall centerline/boundary/thickness interpretation;
- opening and intersection reconstruction;
- level/elevation and vertical extent;
- connectivity and topology;
- human review of reconstruction;
- final engineering geometry;
- mapping to any canonical Core `Surface` or other Core entity.

## Non-goals

This proposal does not define a canonical wall geometry, wall thickness, wall endpoints, vertical extent, topology, or Core `Surface`. Those are GPT-6 reconstruction concerns.

## Required consumer regression

The GPT-6 migration is not ready until regression evidence covers:

1. a valid legacy v0.1 `column` record still passes;
2. a valid legacy v0.1 `beam` record still passes;
3. a `wall` record claiming v0.1 is rejected;
4. a valid `wall` record under the new contract passes;
5. wrong or missing `coordinate_space` is rejected;
6. empty or untraceable `provenance` is rejected;
7. unknown classes are rejected;
8. detector bounding boxes are not automatically treated as Core geometry.

## Coordination gate

GPT-7 MUST NOT enable wall handoff until the versioned ontology, annotation rules, validation rules, and StructuralDetectionEvidence contract are approved and GPT-6 consumer regression is passing.

GPT-6 should not mark the migration complete based on this proposal alone.

## References

- `dehghoon/linkoteq-structural-core/CORE_CONTRACT.md` v0.5
- `dehghoon/linkoteq-structural-detection/contracts/structural-detection-evidence-v0.1.md`
- `dehghoon/linkoteq-structural-detection/docs/gpt7/wall-ontology-impact-analysis-v0.2-proposal.md`
