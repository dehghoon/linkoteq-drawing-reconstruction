# Linkoteq Drawing Reconstruction

Independent reconstruction service for converting structural drawings (PDF/images) into reviewable, Core-compatible structural geometry.

## Source of truth

The latest released `dehghoon/linkoteq-structural-core` repository is authoritative for cross-product integration. Current target schema at initialization: **v0.5**.

## Scope

Initial MVP:

- drawing preprocessing and transform tracking
- grid geometry extraction
- OCR/grid labeling
- scale calibration
- column detection and grid association
- beam reconstruction and connectivity
- validation/human-review flags
- mapping to Core `StructuralModel`

The service must not call PyNite directly. Analysis remains behind the Core-defined PyNite Analysis Adapter.

## Repository layout

```text
docs/
src/
tests/
models/
handoffs/
project-status.json
```

## Agent ownership

GPT-6 owns drawing reconstruction functionality.
GPT-4 coordinates Core compliance and integration.
GPT-5 owns security-specific review.
