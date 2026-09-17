"""Importer-private OCR evidence and deterministic grid-axis label association."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from math import hypot
from typing import Literal, Sequence
from unicodedata import normalize as unicode_normalize

from .grid_geometry import GridAxisCandidate
from .transforms import Point2D

ReviewStatus = Literal["auto-accepted", "review-required", "rejected"]


class GridLabelingError(ValueError):
    pass


@dataclass(frozen=True)
class BoundingBox2D:
    min: Point2D
    max: Point2D

    def __post_init__(self):
        if self.min.x > self.max.x or self.min.y > self.max.y:
            raise GridLabelingError("bounding box min must not exceed max")

    @property
    def center(self):
        return Point2D((self.min.x + self.max.x) / 2.0, (self.min.y + self.max.y) / 2.0)


def normalize_grid_label(raw_text: str) -> str:
    """Normalize typography only; never guess OCR character substitutions."""
    normalized = unicode_normalize("NFKC", raw_text).strip()
    return "".join(normalized.split()).upper()


@dataclass(frozen=True)
class OcrLabelEvidence:
    id: str
    source_id: str
    page_id: str
    text: str
    bbox: BoundingBox2D
    confidence: float
    engine: str
    engine_version: str
    region_kind: Literal["grid-bubble", "grid-label"] = "grid-label"

    def __post_init__(self):
        if not self.id.strip() or not self.source_id.strip() or not self.page_id.strip():
            raise GridLabelingError("OCR evidence identity and provenance must be non-empty")
        if not self.text.strip():
            raise GridLabelingError("OCR text must be non-empty")
        if not self.engine.strip() or not self.engine_version.strip():
            raise GridLabelingError("OCR engine and version must be preserved")
        if not 0.0 <= self.confidence <= 1.0:
            raise GridLabelingError("OCR confidence must be between 0 and 1")

    @property
    def normalized_label(self) -> str:
        return normalize_grid_label(self.text)


@dataclass(frozen=True)
class GridLabelAssociation:
    id: str
    axis_id: str
    label_evidence_id: str | None
    label: str | None
    status: ReviewStatus
    distance: float | None
    competing_evidence_ids: tuple[str, ...] = ()


def _stable_id(prefix, *parts):
    return f"{prefix}-{sha1('|'.join(parts).encode()).hexdigest()[:12]}"


def _distance(a, b):
    return hypot(a.x - b.x, a.y - b.y)


def _endpoint_distance(axis, evidence):
    center = evidence.bbox.center
    return min(_distance(center, axis.start), _distance(center, axis.end))


def associate_grid_labels(
    axes: Sequence[GridAxisCandidate],
    evidence: Sequence[OcrLabelEvidence],
    *,
    max_endpoint_distance: float = 40.0,
    ambiguity_ratio: float = 1.25,
    min_ocr_confidence: float = 0.75,
) -> tuple[GridLabelAssociation, ...]:
    """Associate OCR evidence to axes deterministically without changing geometry.

    One OCR observation may label at most one axis. Raw OCR text remains on
    OcrLabelEvidence; associations use typography-normalized labels only.
    Ambiguity and duplicate normalized labels remain review evidence.
    """
    if max_endpoint_distance <= 0 or ambiguity_ratio <= 1.0 or not 0.0 <= min_ocr_confidence <= 1.0:
        raise GridLabelingError("invalid grid-label association thresholds")
    if not axes:
        return ()

    pages = {(item.source_id, item.page_id) for item in evidence}
    if len(pages) > 1:
        raise GridLabelingError("OCR evidence must belong to at most one source page")
    if len({axis.id for axis in axes}) != len(axes):
        raise GridLabelingError("grid axis ids must be unique")
    if len({item.id for item in evidence}) != len(evidence):
        raise GridLabelingError("OCR evidence ids must be unique")

    candidates = {}
    for axis in axes:
        candidates[axis.id] = sorted(
            (
                (distance, item)
                for item in evidence
                if (distance := _endpoint_distance(axis, item)) <= max_endpoint_distance
            ),
            key=lambda item: (item[0], item[1].id),
        )

    pairs = sorted(
        (
            (distance, axis.id, item.id)
            for axis in axes
            for distance, item in candidates[axis.id]
        ),
        key=lambda item: (item[0], item[1], item[2]),
    )
    assigned = {}
    used = set()
    by_id = {item.id: item for item in evidence}
    for distance, axis_id, evidence_id in pairs:
        if axis_id in assigned or evidence_id in used:
            continue
        assigned[axis_id] = (distance, by_id[evidence_id])
        used.add(evidence_id)

    result = []
    for axis in sorted(axes, key=lambda item: item.id):
        chosen = assigned.get(axis.id)
        if chosen is None:
            result.append(
                GridLabelAssociation(
                    _stable_id("grid-label", axis.id, "none"),
                    axis.id,
                    None,
                    None,
                    "review-required",
                    None,
                )
            )
            continue

        best_distance, best = chosen
        competing = tuple(
            sorted(
                item.id
                for distance, item in candidates[axis.id]
                if item.id != best.id and distance <= best_distance * ambiguity_ratio
            )
        )
        status: ReviewStatus = "auto-accepted"
        if best.confidence < min_ocr_confidence or competing:
            status = "review-required"

        result.append(
            GridLabelAssociation(
                _stable_id("grid-label", axis.id, best.id),
                axis.id,
                best.id,
                best.normalized_label,
                status,
                best_distance,
                competing,
            )
        )

    counts = {}
    for item in result:
        if item.label is not None:
            counts[item.label] = counts.get(item.label, 0) + 1

    return tuple(
        GridLabelAssociation(
            item.id,
            item.axis_id,
            item.label_evidence_id,
            item.label,
            "review-required" if item.label and counts[item.label] > 1 else item.status,
            item.distance,
            item.competing_evidence_ids,
        )
        for item in result
    )
