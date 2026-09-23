"""Review-preserving wall reconstruction from SDE=0.2 evidence."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

from .structural_detection import StructuralDetectionEvidence
from .structural_layout_proposal import StructuralLayoutProposal
from .transforms import Point2D, Point3D, SourceToModelTransform


class WallReconstructionError(ValueError):
    pass


@dataclass(frozen=True)
class WallEngineeringEvidence:
    """Explicit engineering evidence; detector box is intentionally absent."""

    wall_id: str
    centerline_start: Point2D | None
    centerline_end: Point2D | None
    thickness: float | None
    level_id: str | None
    bottom_elevation: float | None
    top_elevation: float | None
    basis: tuple[str, ...]
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.wall_id.strip():
            raise WallReconstructionError("wall_id must be non-empty")
        if not self.basis or not all(x.strip() for x in self.basis):
            raise WallReconstructionError("basis must be non-empty and traceable")
        if not self.provenance or not all(x.strip() for x in self.provenance):
            raise WallReconstructionError("provenance must be non-empty and traceable")


@dataclass(frozen=True)
class ResolvedWallSurface:
    id: str
    source_id: str
    page_id: str
    level_id: str
    boundary_points: tuple[Point3D, Point3D, Point3D, Point3D]
    thickness: float
    length_unit: str
    origin: Literal["reconstructed", "proposed"]
    basis: tuple[str, ...]
    provenance: tuple[str, ...]
    detection_evidence_id: str


@dataclass(frozen=True)
class WallReconstructionDecision:
    state: Literal["eligible", "review-required", "rejected"]
    reasons: tuple[str, ...]
    surface: ResolvedWallSurface | None = None


def reconstruct_wall(
    *,
    detection: StructuralDetectionEvidence,
    engineering: WallEngineeringEvidence,
    transform: SourceToModelTransform,
    review_state: str,
    proposal: StructuralLayoutProposal | None = None,
) -> WallReconstructionDecision:
    """Reconstruct a Core-eligible wall only after all engineering gates pass."""
    if detection.contract_version != "0.2" or detection.class_name != "wall":
        raise WallReconstructionError("wall reconstruction requires valid v0.2 wall evidence")
    if detection.state == "rejected":
        return WallReconstructionDecision("rejected", ("detector evidence is rejected",))
    if detection.source_id != transform.source_id or detection.page_id != transform.page_id:
        raise WallReconstructionError("source/page identity must match the transform chain")

    reasons: list[str] = []
    if not transform.is_resolved:
        reasons.append("unresolved required physical scale/transform")
    if engineering.centerline_start is None or engineering.centerline_end is None:
        reasons.append("explicit centerline endpoints are required")
    elif engineering.centerline_start == engineering.centerline_end:
        reasons.append("centerline endpoints must be distinct")
    if engineering.thickness is None or not isfinite(engineering.thickness) or engineering.thickness <= 0:
        reasons.append("explicit positive wall thickness is required")
    if not engineering.level_id:
        reasons.append("explicit level association is required")
    if (
        engineering.bottom_elevation is None
        or engineering.top_elevation is None
        or not isfinite(engineering.bottom_elevation)
        or not isfinite(engineering.top_elevation)
        or engineering.top_elevation <= engineering.bottom_elevation
    ):
        reasons.append("explicit traceable vertical extent is required")
    if review_state != "approved":
        reasons.append("wall engineering geometry requires approved review")

    origin: Literal["reconstructed", "proposed"] = "reconstructed"
    if proposal is not None:
        origin = "proposed"
        if proposal.object_type != "wall" or proposal.source_id != detection.source_id or proposal.page_id != detection.page_id:
            raise WallReconstructionError("wall proposal must match detection source/page")
        if proposal.origin != "proposed" or proposal.review_state != "approved" or not proposal.core_writeback_eligible:
            reasons.append("proposed wall is not approved and Cor-writeback eligible")

    if reasons:
        return WallReconstructionDecision("review-required", tuple(reasons))

    assert engineering.centerline_start is not None and engineering.centerline_end is not None
    assert engineering.thickness is not None and engineering.level_id is not None
    assert engineering.bottom_elevation is not None and engineering.top_elevation is not None
    a = transform.to_model_point(engineering.centerline_start)
    b = transform.to_model_point(engineering.centerline_end)
    bottom, top = engineering.bottom_elevation, engineering.top_elevation
    boundary = (Point3D(a.x,a.y,bottom), Point3D(b.x,b.y,bottom), Point3D(b.x,b.y,top), Point3D(a.x,a.y,top))
    surface = ResolvedWallSurface(
        id=engineering.wall_id, source_id=detection.source_id, page_id=detection.page_id,
        level_id=engineering.level_id, boundary_points=boundary, thickness=engineering.thickness,
        length_unit=transform.project_length_unit or "", origin=origin, basis=engineering.basis,
        provenance=engineering.provenance + (detection.provenance,), detection_evidence_id=detection.id,
    )
    return WallReconstructionDecision("eligible", (), surface)
