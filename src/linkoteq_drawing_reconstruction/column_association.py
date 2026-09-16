"""Deterministic column-to-grid association.

Raw detector boxes are evidence only. A plan detection establishes XY location
only and never invents vertical extent or a canonical Core Member.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Literal, Sequence

from .grid_geometry import GridIntersection
from .structural_detection import StructuralDetectionEvidence
from .transforms import Affine2D, Point2D

AssociationState = Literal["auto-accepted", "review-required", "preserved-off-grid"]


class ColumnAssociationError(ValueError):
    pass


@dataclass(frozen=True)
class ColumnLocationEvidence:
    detection_id: str
    point: Point2D
    grid_intersection_id: str | None
    snap_distance: float | None
    state: AssociationState
    reason: str

    @property
    def can_create_column_member(self) -> bool:
        """Plan XY evidence alone never establishes vertical column extent."""
        return False


def _box_center(detection: StructuralDetectionEvidence) -> Point2D:
    b = detection.source_box
    return Point2D((b.xmin + b.xmax) / 2.0, (b.ymin + b.ymax) / 2.0)


def associate_column_to_grid(
    detection: StructuralDetectionEvidence,
    source_to_normalized: Affine2D,
    intersections: Sequence[GridIntersection],
    *,
    auto_snap_distance: float,
    review_snap_distance: float,
) -> ColumnLocationEvidence:
    """Associate column centroid with reconstructed grid geometry.

    Thresholds are in normalized drawing coordinates. No scale is inferred and
    no canonical engineering geometry is emitted.
    """
    if detection.class_name != "column":
        raise ColumnAssociationError("column association requires a column detection")
    if auto_snap_distance < 0.0 or review_snap_distance < auto_snap_distance:
        raise ColumnAssociationError("invalid snap distance thresholds")

    point = source_to_normalized.apply(_box_center(detection))
    if not intersections:
        return ColumnLocationEvidence(
            detection.id, point, None, None, "preserved-off-grid",
            "no grid intersection evidence",
        )

    ranked = sorted(
        (
            (hypot(point.x - item.point.x, point.y - item.point.y), item.id, item)
            for item in intersections
        ),
        key=lambda value: (value[0], value[1]),
    )
    distance, _, nearest = ranked[0]

    if distance <= auto_snap_distance:
        return ColumnLocationEvidence(
            detection.id, nearest.point, nearest.id, distance, "auto-accepted",
            "within auto snap threshold",
        )
    if distance <= review_snap_distance:
        return ColumnLocationEvidence(
            detection.id, nearest.point, nearest.id, distance, "review-required",
            "excessive snap distance requires review",
        )
    return ColumnLocationEvidence(
        detection.id, point, None, distance, "preserved-off-grid",
        "nearest grid intersection is outside review threshold",
    )
