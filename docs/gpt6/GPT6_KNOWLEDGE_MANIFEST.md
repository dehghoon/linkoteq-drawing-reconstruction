# GPT-6 Knowledge Manifest

## Purpose
Defines the static Knowledge package for the GPT-6 Custom GPT.

Runtime project state remains in GitHub. Static Knowledge must never replace repository inspection.

## Mandatory Knowledge files
Recommended uploads/configuration references:

1. `GPT6_MASTER_INSTRUCTIONS.md`
2. `GPT6_OPERATIONS_HANDBOOK.md`
3. `GPT6_KNOWLEDGE_MANIFEST.md`
4. `GPT6_BUILDER_SETUP.md`
5. `RECONSTRUCTION_SPEC.md`
6. `CORE_MAPPING.`dm`
7. latest `CORE_CONTRACT.md` snapshot
8. latest Core canonical TypeScript definitions snapshot
9. relevant `AI_GPT3_UPDATE_POLICY.md` snapshot
10. source research paper(s) used as methodological references

## Runtime files — read from GitHub
Do not rely on Knowledge uploads for:
- current Core version;
- repository source code;
- `project-status.json`;
- tests and fixture results;
- model manifests;
- model evaluation records;
- deployment configuration;
- API schemas;
- current handoffs;
- migration notes;
- release notes;
- CI evidence.

Primary runtime repositories:
- `dehghoon/linkoteq-structural-core`
- `dehghoon/linkoteq-drawing-reconstruction`

Integration targets may additionally include:
- `dehghoon/3D-Model`
- other Linkoteq repositories explicitly involved in the task.

## Research-paper rule
Research papers are methodological references, not platform contracts.

Do not copy a paper's detector output directly into canonical Core geometry merely because the paper uses that representation.

For the current structural drawing method:
- use object detection as semantic evidence;
- improve grid geometry with explicit line extraction;
- construct topology and scale before canonical writeback.

## Freshness rule
At the beginning of every task:
- fetch current Core;
- fetch current drawing-reconstruction repository;
- read project status;
- treat Knowledge as potentially stale.

## Update triggers
Refresh the static Knowledge package when practical after:
- breaking or material Core changes;
- major GPT-6 responsibility changes;
- model/reconstruction architecture changes;
- new security ownership boundaries;
- major repository workflow changes.

## Prohibited dependency
The Custom GPT must not depend on files being manually transferred from GPT-4/5/other agents when GitHub can store and retrieve them.
