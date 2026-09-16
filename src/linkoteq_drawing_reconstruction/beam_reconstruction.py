"""Deterministic beam centerline and connectivity reconstruction.

Semantic detector boxes are evidence only. This module derives a candidate centerline
from the long axis of the detection, then associates endpoints to existing structural
node evidence. It does not emit a canonical Core Member."""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Literal, Sequence

from .structural_detection import StructuralDetectionEvidence
from .transforms import Affine2D, Point2D

BeamState = Literal["auto-accepted", "review-required", "preserved-unconnected"]


class BeamReconstructionError(ValueError):
    pass


@dataclass(frozen=True)
class StructuralNodeEvidence:
    id: str
    point: Point2D


@dataclass(frozen=True)
class BeamCenterlineEvidence:
    detection_id: str
    start: Point2D
    end: Point2D
    start_node_id: str | None
    end_node_id: str | None
    start_distance: float | None
    end_distance: float | None
    state: BeamState
    reason: str

    @property
    def can_create_member(self) -> bool:
        """Canonical member creation requires both resolved endpoints."""
        return self.state == "auto-accepted" and self.start_node_id is not None and self.end_node_id is not None


def _centerline(detection: StructuralDetectionEvidence, transform: Affine2D) -> tuple[Point2D, Point2D]:
    b = detection.source_box
    cx = (b.xmin + b.xmax) / 2.0
    cy = (b.ymin + b.ymax) / 2.0
    if (b.xmax - b.xmin) >= (b.ymax - b.ymin):
        a, c = Point2D(b.xmin, cy), Point2D(b.xmax, cy)
    else:
        a, c = Point2D(cx, b.ymin), Point2D(cx, b.ymax)
    return transform.apply(a), transform.apply(c)


def _nearest(point: Point2D, nodes: Sequence[StructuralNodeEvidence]) -> tuple[StructuralNodeEvidence, float] | None:
    if not nodes:
        return None
    ranked = sorted(
        ((hypot(point.x - n.point.x, point.y - n.point.y), n.id, n) for n in nodes),
        key=lambda v: (v[0], v[1]),
    )
    distance, _, node = ranked[0]
    return node, distance


def reconstruct_beam(
    detection: StructuralDetectionEvidence,
    source_to_normalized: Affine2D,
    nodes: Sequence[StructuralNodeEvidence],
    *,
    auto_endpoint_distance: float,
    review_endpoint_distance: float,
) -> BeamCenterlineEvidence:
    if detection.class_name != "beam":
        raise BeamReconstructionError("beam reconstruction requires a beam detection")
    if auto_endpoint_distance < 0 or review_endpoint_distance < auto_endpoint_distance:
        raise BeamReconstructionError("invalid endpoint distance thresholds")

    start, end = _centerline(detection, source_to_normalized)
    sn = _nearest(start, nodes)
    en = _nearest(end, nodes)
    if sn is None or en is None:
        return BeamCenterlineEvidence(detection.id, start, end, None, None, None, None, "preserved-unconnected", "no structural node evidence")

    sn0, sd = sn
    en0, ed = en
    if sd > review_endpoint_distance or ed > review_endpoint_distance:
        return BeamCenterlineEvidence(detection.id, start, end, None, None, sd, ed, "preserved-unconnected", "endpoint outside review threshold")

    state: BeamState = "auto-accepted" if sd <= auto_endpoint_distance and ed <= auto_endpoint_distance else "review-required"
    return BeamCenterlineEvidence(
        detection.id, sn0.point, en0.point, sn0.id, en0.id, sd, ed, state,
        "both endpoints resolved" if state == "auto-accepted" else "endpoint association requires review",
    )
