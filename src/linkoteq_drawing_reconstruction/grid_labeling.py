"""Importer-private OCR evidence and grid-axis label association."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from math import hypot
from typing import Literal, Sequence

from .grid_geometry import GridAxisCandidate
from .transforms import Point2D

ReviewStatus = Literal["auto-accepted", "review-required", "rejected"]


class GridLabelingError(ValueError):
    pass


@dataclass(frozen=True)
class BoundingBox2D:
    min: Point2D
    max: Point2D

    def __post_init__(self) -> None:
        if self.min.x > self.max.x or self.min.y > self.max.y:
            raise GridLabelingError("bounding box min must not exceed max")

    @property
    def center(self) -> Point2D:
        return Point2D((self.min.x + self.max.x) / 2.0, (self.min.y + self.max.y) / 2.0)


@dataclass(frozen=True)
class OcrLabelEvidence:
    id: str
    source_id: str
    page_id: str
    text: str
    box: BoundingBox2D # already in normalized drawing coordinates
    confidence: float
    engine: str
    engine_version: str
    region_kind: Literal["grid-bubble", "grid-label"] = "grid-label"

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.source_id.strip() or not self.page_id.strip():
            raise GridLabelingError("OCR evidence identity and provenance must be non-empty")
        if not self.text.strip():
            raise GridLabelingError("OCR text must be non-empty")
        if not self.engine.strip() or not self.engine_version.strip():
            raise GridLabelingError("OCR engine and version must be preserved")
        if not 0.0 <= self.confidence <= 1.0:
            raise GridLabelingError("OCR confidence must be between 0 and 1")


@dataclass(frozen=True)
class GridLabelAssociation:
    id: str
    axis_id: str
    label_evidence_id: str | None
    label: str | None
    status: ReviewStatus
    distance: float | None
    competing_evidence_ids: tuple[str, ...] = ()


def _stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}-{sha1('|'.join(parts).encode('utf-8')).hexdigest()[:12]}"


def _distance(a: Point2D, b: Point2D) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def _endpoint_distance(axis: GridAxisCandidate, evidence: OcrLabelEvidence) -> float:
    c = evidence.box.center
    return min(_distance(c, axis.start), _distance(c, axis.end))


def associate_grid_labels(
    axes: Sequence[GridAxisCandidate],
    evidence: Sequence[OcrLabelEvidence],
    *,
    max_endpoint_distance: float = 40.0,
    ambiguity_ratio: float = 1.25,
    min_ocr_confidence: float = 0.75,
) -> tuple[GridLabelAssociation, ...]:
    """Associate OCR label evidence to reconstructed axes without changing geometry.

    Distances are in normalized drawing coordinates. Ambiguity is explicit:
    competing nearby labels, low OCR confidence, or duplicate text require review.
    """
    if max_endpoint_distance <= 0 or ambiguity_ratio <= 1.0 or not 0.0 <= min_ocr_confidence <= 1.0:
        raise GridLabelingError("invalid grid-label association thresholds")
    if not axes:
        return()

    pages = {(e.source_id, e.page_id) for e in evidence}
    if len(pages) > 1:
        raise GridLabelingError("OCR evidence must belong to at most one source page")

    ranked_by_axis: dict[str, list[tuple[float, OcrLabelEvidence]]] = {}
    for axis in axes:
        ranked = sorted(
            ((_endpoint_distance(axis, e), e) for e in evidence),
            key=lambda x: (x[0], x[1].id),
        )
        ranked_by_axis[axis.id] = ranked

    result: list[GridLabelAssociation] = []
    for axis in sorted(axes, key=lambda a: a.id):
        ranked = [x for x in ranked_by_axis[axis.id] if x[0] <= max_endpoint_distance]
        if not ranked:
            result.append(GridLabelAssociation(_stable_id("grid-label", axis.id, "none"), axis.id, None, None, "review-required", None))
            continue
        best_d, best = ranked[0]
        competing = [e.id for d, e in ranked[1:] if d <= best_d * ambiguity_ratio]
        status: ReviewStatus = "auto-accepted"
        if best.confidence < min_ocr_confidence or competing:
            status = "review-required"
        result.append(GridLabelAssociation(
            _stable_id("grid-label", axis.id, best.id), axis.id, best.id, best.text.strip(),
            status, best_d, tuple(sorted(competing))
        ))

    # The same label text on multiple axes is not auto-acceptable.
    counts: dict[str, int] = {}
    for item in result:
        if item.label is not None:
            counts[item.label] = counts.get(item.label, 0) + 1
    return tuple(
        GridLabelAssociation(x.id, x.axis_id, x.label_evidence_id, x.label, "review-required" if x.label and counts[x.label] > 1 else x.status, x.distance, x.competing_evidence_ids)
        for x in result
    )
