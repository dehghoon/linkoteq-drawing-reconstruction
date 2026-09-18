"""Importer-private versioned structural detection evidence.

These records preserve detector output for fusion/review. They are not
Core geometry and must never be mapped directly to Node/Member/Surface.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Literal

StructuralClass = Literal["column", "beam", "wall"]
DetectionState = Literal["auto-accepted", "review-required", "rejected", "preserved-off-grid"]
CoordinateSpace = Literal["source-page"]
EvidenceContractVersion = Literal["0.1", "0.2"]
ALLOWED_CLASSES_BY_CONTRACT = {
    "0.1": {"column", "beam"},
    "0.2": {"column", "beam", "wall"},
}

class StructuralDetectionError(ValueError):
    pass

@dataclass(frozen=True)
class SourceBox2D:
    """Detector box in source/page coordinates only."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        vals = (self.xmin, self.ymin, self.xmax, self.ymax)
        if not all(isfinite(v) for v in vals):
            raise StructuralDetectionError("source box coordinates must be finite")
        if self.xmax <= self.xmin or self.ymax <= self.ymin:
            raise StructuralDetectionError("source box must have positive area")

@dataclass(frozen=True)
class StructuralDetectionEvidence:
    id: str
    source_id: str
    page_id: str
    class_name: StructuralClass
    confidence: float
    source_box: SourceBox2D
    coordinate_space: CoordinateSpace
    model_name: str
    model_version: str
    provenance: str
    state: DetectionState = "review-required"
    contract_version: EvidenceContractVersion = "0.1"

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (self.id, self.source_id, self.page_id, self.model_name, self.model_version, self.provenance)
        ):
            raise StructuralDetectionError("identity, provenance, and model metadata must be non-empty")
        if self.contract_version not in ALLOWED_CLASSES_BY_CONTRACT:
            raise StructuralDetectionError("unsupported detection evidence contract version")
        if self.class_name not in ALLOWED_CLASSES_BY_CONTRACT[self.contract_version]:
            allowed = ", ".join(sorted(ALLOWED_CLASSES_BY_CONTRACT[self.contract_version]))
            raise StructuralDetectionError(f"class_name must be one of {allowed} under v{self.contract_version}")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise StructuralDetectionError("confidence must be finite and between 0 and 1")
        if self.coordinate_space != "source-page":
            raise StructuralDetectionError("coordinate_space must be source-page")
        if self.state not in ("auto-accepted", "review-required", "rejected", "preserved-off-grid"):
            raise StructuralDetectionError("unsupported detection state")

    @property
    def can_write_core_geometry(self) -> bool:
        """Detector evidence, including wall boxes, is never canonical engineering geometry."""
        return False
