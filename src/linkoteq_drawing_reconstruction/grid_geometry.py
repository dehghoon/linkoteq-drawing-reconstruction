
"""Deterministic geometric grid reconstruction from normalized line-segment evidence.

This module is importer-private. It reconstructs geometric grid-axis candidates from
line segments; it does not emit Core GridLine records, infer scale, run OCR/YOLO, or
write pixel coordinates to canonical geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from math import atan2, cos, degrees, hypot, pi, sin
from statistics import mean
from typing import Iterable, Literal, Sequence

from .transforms import Point2D

ExtractionMethod = Literal["vector", "hough", "lsd", "edlines", "fixture"]


class GridGeometryError(ValueError):
    """Raised when geometric grid evidence is invalid or inconsistent."""


@dataclass(frozen=True)
class LineSegmentEvidence:
    id: str
    source_id: str
    page_id: str
    start: Point2D
    end: Point2D
    method: ExtractionMethod
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise GridGeometryError("segment id must be non-empty")
        if not self.source_id.strip() or not self.page_id.strip():
            raise GridGeometryError("source_id and page_id must be non-empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise GridGeometryError("segment confidence must be between 0 and 1")
        if self.length <= 0.0:
            raise GridGeometryError("line segment must have non-zero length")

    @property
    def length(self) -> float:
        return hypot(self.end.x - self.start.x, self.end.y - self.start.y)

    @property
    def orientation_rad(self) -> float:
        angle = atan2(self.end.y - self.start.y, self.end.x - self.start.x) % pi
        return 0.0 if abs(angle - pi) < 1e-12 else angle


@dataclass(frozen=True)
class GridAxisCandidate:
    id: str
    family_id: str
    start: Point2D
    end: Point2D
    source_segment_ids: tuple[str, ...]
    length: float
    confidence: float
    normal_offset: float
    orientation_rad: float


@dataclass(frozen=True)
class GridFamily:
    id: str
    orientation_rad: float
    axis_ids: tuple[str, ...]
    spacing_regularity: float | None


@dataclass(frozen=True)
class GridIntersection:
    id: str
    axis_a_id: str
    axis_b_id: str
    point: Point2D


@dataclass(frozen=True)
class GridGeometryResult:
    families: tuple[GridFamily, ...]
    axes: tuple[GridAxisCandidate, ...]
    intersections: tuple[GridIntersection, ...]


def _stable_id(prefix: str, parts: Iterable[str]) -> str:
    payload = "|".join(parts).encode("utf-8")
    return f"{prefix}-{sha1(payload).hexdigest()[:12]}"


def _angular_distance(a: float, b: float) -> float:
    d = abs(a - b) % pi
    return min(d, pi - d)


def _family_orientation(segments: Sequence[LineSegmentEvidence]) -> float:
    # Axial/circular mean uses doubled angles so 0 and pi describe the same line direction.
    sx = sum(s.length * cos(2.0 * s.orientation_rad) for s in segments)
    sy = sum(s.length * sin(2.0 * s.orientation_rad) for s in segments)
    angle = 0.5 * atan2(sy, sx)
    return angle % pi


def cluster_orientation_families(
    segments: Sequence[LineSegmentEvidence], *, angle_tolerance_deg: float = 3.0
) -> tuple[tuple[LineSegmentEvidence, ...], ...]:
    if angle_tolerance_deg <= 0.0 or angle_tolerance_deg >= 45.0:
        raise GridGeometryError("angle_tolerance_deg must be in (0, 45)")
    ids = [s.id for s in segments]
    if len(ids) != len(set(ids)):
        raise GridGeometryError("duplicate line-segment ids are not allowed")

    tolerance = angle_tolerance_deg * pi / 180.0
    remaining = sorted(segments, key=lambda s: (s.orientation_rad, s.id))
    families: list[list[LineSegmentEvidence]] = []
    for segment in remaining:
        best_index: int | None = None
        best_distance = float("inf")
        for i, family in enumerate(families):
            distance = _angular_distance(segment.orientation_rad, _family_orientation(family))
            if distance <= tolerance and distance < best_distance:
                best_index = i
                best_distance = distance
        if best_index is None:
            families.append([segment])
        else:
            families[best_index].append(segment)

    # Merge wrap-around families (angles close to both 0 and pi) deterministically.
    changed = True
    while changed:
        changed = False
        for i in range(len(families)):
            for j in range(i + 1, len(families)):
                if _angular_distance(_family_orientation(families[i]), _family_orientation(families[j])) <= tolerance:
                    families[i].extend(families[j])
                    del families[j]
                    changed = True
                    break
            if changed:
                break

    normalized = [
        tuple(sorted(family, key=lambda s: s.id))
        for family in families
    ]
    normalized.sort(key=lambda family: (_family_orientation(family), tuple(s.id for s in family)))
    return tuple(normalized)


def _project(point: Point2D, ux: float, uy: float, nx: float, ny: float) -> tuple[float, float]:
    return point.x * ux + point.y * uy, point.x * nx + point.y * ny


def _axis_from_cluster(
    family_id: str,
    orientation: float,
    cluster: Sequence[LineSegmentEvidence],
) -> GridAxisCandidate:
    ux, uy = cos(orientation), sin(orientation)
    nx, ny = -uy, ux
    ts: list[float] = []
    offsets: list[float] = []
    weights: list[float] = []
    for segment in cluster:
        for point in (segment.start, segment.end):
            t, o = _project(point, ux, uy, nx, ny)
            ts.append(t)
            offsets.append(o)
            weights.append(segment.length)
    normal_offset = sum(o * w for o, w in zip(offsets, weights)) / sum(weights)
    t0, t1 = min(ts), max(ts)
    start = Point2D(t0 * ux + normal_offset * nx, t0 * uy + normal_offset * ny)
    end = Point2D(t1 * ux + normal_offset * nx, t1 * uy + normal_offset * ny)
    length = t1 - t0
    source_ids = tuple(sorted(s.id for s in cluster))
    confidence = sum(s.confidence * s.length for s in cluster) / sum(s.length for s in cluster)
    axis_id = _stable_id("grid-candidate", (family_id, *source_ids))
    return GridAxisCandidate(
        id=axis_id,
        family_id=family_id,
        start=start,
        end=end,
        source_segment_ids=source_ids,
        length=length,
        confidence=confidence,
        normal_offset=normal_offset,
        orientation_rad=orientation,
    )


def _merge_family_segments(
    family_id: str,
    segments: Sequence[LineSegmentEvidence],
    *,
    collinear_tolerance: float,
    gap_tolerance: float,
    min_axis_length: float,
) -> tuple[GridAxisCandidate, ...]:
    orientation = _family_orientation(segments)
    ux, uy = cos(orientation), sin(orientation)
    nx, ny = -uy, ux

    enriched = []
    for segment in segments:
        p0 = _project(segment.start, ux, uy, nx, ny)
        p1 = _project(segment.end, ux, uy, nx, ny)
        t0, t1 = sorted((p0[0], p1[0]))
        offset = (p0[1] + p1[1]) / 2.0
        enriched.append((offset, t0, t1, segment))
    enriched.sort(key=lambda item: (item[0], item[1], item[3].id))

    line_groups: list[list[tuple[float, float, float, LineSegmentEvidence]]] = []
    for item in enriched:
        best: int | None = None
        best_distance = float("inf")
        for i, group in enumerate(line_groups):
            avg_offset = mean(x[0] for x in group)
            distance = abs(item[0] - avg_offset)
            if distance <= collinear_tolerance and distance < best_distance:
                best, best_distance = i, distance
        if best is None:
            line_groups.append([item])
        else:
            line_groups[best].append(item)

    axes: list[GridAxisCandidate] = []
    for group in line_groups:
        group.sort(key=lambda item: (item[1], item[2], item[3].id))
        runs: list[list[tuple[float, float, float, LineSegmentEvidence]]] = []
        for item in group:
            if not runs:
                runs.append([item])
                continue
            current_end = max(x[2] for x in runs[-1])
            if item[1] <= current_end + gap_tolerance:
                runs[-1].append(item)
            else:
                runs.append([item])
        for run in runs:
            candidate = _axis_from_cluster(family_id, orientation, [x[3] for x in run])
            if candidate.length >= min_axis_length:
                axes.append(candidate)

    axes.sort(key=lambda a: (a.normal_offset, a.id))
    return tuple(axes)


def _spacing_regularity(axes: Sequence[GridAxisCandidate]) -> float | None:
    if len(axes) < 3:
        return None
    offsets = sorted(a.normal_offset for a in axes)
    spacings = [b - a for a, b in zip(offsets, offsets[1:])]
    avg = mean(spacings)
    if abs(avg) < 1e-12:
        return 0.0
    variance = mean((s - avg) ** 2 for s in spacings)
    cv = variance ** 0.5 / abs(avg)
    return max(0.0, min(1.0, 1.0 - cv))


def _line_intersection(a: GridAxisCandidate, b: GridAxisCandidate, parallel_tolerance: float) -> Point2D | None:
    x1, y1, x2, y2 = a.start.x, a.start.y, a.end.x, a.end.y
    x3, y3, x4, y4 = b.start.x, b.start.y, b.end.x, b.end.y
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    scale = max(a.length * b.length, 1.0)
    if abs(den) <= parallel_tolerance * scale:
        return None
    det1 = x1 * y2 - y1 * x2
    det2 = x3 * y4 - y3 * x4
    px = (det1 * (x3 - x4) - (x1 - x2) * det2) / den
    py = (det1 * (y3 - y4) - (y1 - y2) * det2) / den
    return Point2D(px, py)


def reconstruct_grid_geometry(
    segments: Sequence[LineSegmentEvidence],
    *,
    angle_tolerance_deg: float = 3.0,
    collinear_tolerance: float = 2.0,
    gap_tolerance: float = 10.0,
    min_axis_length: float = 50.0,
    parallel_tolerance: float = 1e-6,
) -> GridGeometryResult:
    """Reconstruct geometric grid-axis candidates from normalized segment evidence.

    All tolerances are expressed in normalized drawing coordinates. No engineering
    units or scale are inferred here.
    """
    if collinear_tolerance < 0.0 or gap_tolerance < 0.0 or min_axis_length <= 0.0:
        raise GridGeometryError("geometric tolerances must be non-negative and min_axis_length positive")
    if parallel_tolerance < 0.0:
        raise GridGeometryError("parallel_tolerance must be non-negative")
    if not segments:
        return GridGeometryResult((), (), ())

    source_pages = {(s.source_id, s.page_id) for s in segments}
    if len(source_pages) != 1:
        raise GridGeometryError("grid reconstruction input must belong to exactly one source page")

    orientation_families = cluster_orientation_families(
        segments, angle_tolerance_deg=angle_tolerance_deg
    )
    families: list[GridFamily] = []
    all_axes: list[GridAxisCandidate] = []

    for raw_family in orientation_families:
        orientation = _family_orientation(raw_family)
        family_id = _stable_id(
            "grid-family",
            [raw_family[0].source_id, raw_family[0].page_id, *(s.id for s in raw_family)],
        )
        axes = _merge_family_segments(
            family_id,
            raw_family,
            collinear_tolerance=collinear_tolerance,
            gap_tolerance=gap_tolerance,
            min_axis_length=min_axis_length,
        )
        if not axes:
            continue
        families.append(
            GridFamily(
                id=family_id,
                orientation_rad=orientation,
                axis_ids=tuple(a.id for a in axes),
                spacing_regularity=_spacing_regularity(axes),
            )
        )
        all_axes.extend(axes)

    families.sort(key=lambda f: (f.orientation_rad, f.id))
    family_by_id = {f.id: f for f in families}
    axes_by_family = {f.id: [a for a in all_axes if a.family_id == f.id] for f in families}

    intersections: list[GridIntersection] = []
    for i, family_a in enumerate(families):
        for family_b in families[i + 1:]:
            if _angular_distance(family_a.orientation_rad, family_b.orientation_rad) <= angle_tolerance_deg * pi / 180.0:
                continue
            for axis_a in axes_by_family[family_a.id]:
                for axis_b in axes_by_family[family_b.id]:
                    point = _line_intersection(axis_a, axis_b, parallel_tolerance)
                    if point is None:
                        continue
                    a_id, b_id = sorted((axis_a.id, axis_b.id))
                    intersections.append(
                        GridIntersection(
                            id=_stable_id("grid-intersection", (a_id, b_id)),
                            axis_a_id=a_id,
                            axis_b_id=b_id,
                            point=point,
                        )
                    )

    all_axes.sort(key=lambda a: (family_by_id[a.family_id].orientation_rad, a.normal_offset, a.id))
    intersections.sort(key=lambda x: (x.axis_a_id, x.axis_b_id, x.id))
    return GridGeometryResult(tuple(families), tuple(all_axes), tuple(intersections))
