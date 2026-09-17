"""Importer-private resolution of Material/Section references.

Detection/OCR is evidence only. This module never invents Core analysis properties.
"""
from __future_ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

ResolutionStatus = Literal["auto-accepted", "review-required", "rejected"]


class MaterialSectionResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ReferenceCandidate:
    id: str
    kind: Literal["material", "section"]
    core_id: str | None
    source_id: str
    page_id: str
    method: str
    confidence: float
    source_text: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.source_id.strip() or not self.page_id.strip():
            raise MaterialSectionResolutionError("candidate identity/provenance must be non-empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise MaterialSectionResolutionError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ReferenceResolution:
    kind: Literal["material", "section"]
    status: ResolutionStatus
    core_id: str | None
    candidate_ids: tuple[str, ...]
    reason: str | None


def resolve_reference(
    candidates: Sequence[ReferenceCandidate],
    *,
    kind: Literal["material", "section"],
    min_confidence: float = 0.90,
) -> ReferenceResolution:
    """Resolve a Core reference only when evidence is unanimous and high-confidence."""
    relevant = [c for c in candidates if c.kind == kind]
    ids = tuple(sorted(c.id for c in relevant))
    if not relevant:
        return ReferenceResolution(kind, "review-required", None, (), f"no {kind} evidence")

    reliable = [c for c in relevant if c.core_id and c.confidence >= min_confidence]
    if not reliable:
        return ReferenceResolution(kind, "review-required", None, ids, f"no reliable resolved {kind} reference")

    core_ids = {c.core_id for c in reliable}
    if len(core_ids) != 1:
        return ReferenceResolution(kind, "review-required", None, ids, f"conflicting {kind} associations")

    core_id = next(iter(core_ids))
    return ReferenceResolution(kind, "auto-accepted", core_id, ids, None)


def confirm_reference(resolution: ReferenceResolution, *, core_id: str | None = None) -> ReferenceResolution:
    """Human-confirm an auto proposal or supply an existing Core reference."""
    value = core_id or resolution.core_id
    if not value or not value.strip():
        raise MaterialSectionResolutionError(f"confirmed {resolution.kind} requires an existing Core id")
    return ReferenceResolution(resolution.kind, "auto-accepted", value, resolution.candidate_ids, "human-confirmed")
