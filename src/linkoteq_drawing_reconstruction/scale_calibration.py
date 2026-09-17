"""Deterministic importer-private scale calibration with mandatory human confirmation."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from statistics import median
from typing import Literal, Sequence

from .transforms import Affine2D, CalibrationEvidence

ScaleMethod = Literal[
    "vector-geometry", "printed-scale", "ocr-dimension",
    "known-grid-spacing", "user-calibration",
]
ScaleReviewStatus = Literal["review-required", "human-confirmed"]


class ScaleCalibrationError(ValueError):
    pass


class UnresolvedScaleError(ScaleCalibrationError):
    pass


@dataclass(frozen=True)
class ScaleObservation:
    id: str
    source_id: str
    page_id: str
    method: ScaleMethod
    normalized_length: float
    engineering_length: float
    length_unit: str
    confidence: float = 1.0
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.source_id.strip() or not self.page_id.strip():
            raise ScaleCalibrationError("scale evidence identity/provenance must be non-empty")
        if not self.length_unit.strip():
            raise ScaleCalibrationError("length_unit must be explicit")
        if not isfinite(self.normalized_length) or self.normalized_length <= 0:
            raise ScaleCalibrationError("normalized_length must be finite and positive")
        if not isfinite(self.engineering_length) or self.engineering_length <= 0:
            raise ScaleCalibrationError("engineering_length must be finite and positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ScaleCalibrationError("confidence must be between 0 and 1")

@dataclass(frozen=True)
class ResolvedScale:
    length_unit: str
    engineering_per_normalized: float
    evidence_ids: tuple[str, ...]
    residual: float
    calibration: CalibrationEvidence
    human_confirmed: bool = False

    def normalized_to_model_xy(self, *, origin_x: float = 0.0, origin_y: float = 0.0) -> Affine2D:
        if not self.human_confirmed:
            raise UnresolvedScaleError("scale requires human confirmation before physical-geometry writeback")
        s = self.engineering_per_normalized
        return Affine2D.from_rows((
            (s, 0.0, origin_x),
            (0.0, s, origin_y),
            (0.0, 0.0, 1.0),
         ))

@dataclass(frozen=True)
class ScaleReviewResult:
    status: ScaleReviewStatus
    resolved: ResolvedScale | None
    reason: str | None
    evidence_ids: tuple[str, ...]


def resolve_scale(observations: Sequence[ScaleObservation], *, min_confidence: float = 0.75, max_relative_residual: float = 0.02) -> ResolvedScale:
    if not 0.0 <= min_confidence <= 1.0 or max_relative_residual < 0:
        raise ScaleCalibrationError("invalid scale resolution thresholds")
    accepted = [o for o in observations if o.confidence >= min_confidence]
    if not accepted:
        raise UnresolvedScaleError("no reliable scale evidence")
    pages = {(o.source_id, o.page_id) for o in accepted}
    units = {o.length_unit for o in accepted}
    if len(pages) != 1 or len(units) != 1:
        raise UnresolvedScaleError("scale evidence must share one source page and one length unit")
    ratios = [o.engineering_length / o.normalized_length for o in accepted]
    scale = median(ratios)
    residual = max(abs(r - scale) / scale for r in ratios)
    if residual > max_relative_residual:
        raise UnresolvedScaleError("conflicting scale evidence requires human review")
    unit = next(iter(units))
    methods = sorted({o.method for o in accepted})
    calibration = CalibrationEvidence(method=accepted[0].method if len(methods) == 1 else "user-calibration", length_unit=unit, residual=residual, note="scale-solver: " + ";".join(methods))
    return ResolvedScale(unit, scale, tuple(sorted(o.id for o in accepted)), residual, calibration, human_confirmed=False)


def review_scale(observations: Sequence[ScaleObservation], *, min_confidence: float = 0.75, max_relative_residual: float = 0.02) -> ScaleReviewResult:
    evidence_ids = tuple(sorted(o.id for o in observations))
    try:
        proposed = resolve_scale(observations, min_confidence=min_confidence, max_relative_residual=max_relative_residual)
    except UnresolvedScaleError as exc:
        return ScaleReviewResult("review-required", None, str(exc), evidence_ids)
    return ScaleReviewResult("review-required", proposed, "human confirmation required for scale before physical-geometry writeback", proposed.evidence_ids)


def confirm_scale(review: ScaleReviewResult, *, engineering_per_normalized: float | None = None, length_unit: str | None = None) -> ResolvedScale:
    """Confirm a proposed scale, or supply explicit user calibration when no proposal exists."""
    if review.status != "review-required":
        raise ScaleCalibrationError("scale review is not awaiting confirmation")
    if review.resolved is not None:
        proposed = review.resolved
        value = proposed.engineering_per_normalized if engineering_per_normalized is None else engineering_per_normalized
        unit = proposed.length_unit if length_unit is None else length_unit
        evidence_ids = proposed.evidence_ids
        residual = proposed.residual
    else:
        if engineering_per_normalized is None or length_unit is None:
            raise UnresolvedScaleError("unresolved scale requires user-confirmed engineering_per_normalized and length_unit")
        value = engineering_per_normalized
        unit = length_unit
        evidence_ids = review.evidence_ids
        residual = 0.0
    if not isfinite(value) or value <= 0:
        raise ScaleCalibrationError("confirmed scale must be finite and positive")
    if not unit.strip():
        raise ScaleCalibrationError("confirmed length_unit must be explicit")
    calibration = CalibrationEvidence(method="user-calibration", length_unit=unit, residual=residual, note="human-confirmed scale")
    return ResolvedScale(unit, value, evidence_ids, residual, calibration, human_confirmed=True)
