
import math
import pytest

from linkoteq_drawing_reconstruction.grid_geometry import (
    GridGeometryError,
    LineSegmentEvidence,
    reconstruct_grid_geometry,
)
from linkoteq_drawing_reconstruction.transforms import Point2D


def seg(id, x1, y1, x2, y2, confidence=1.0):
    return LineSegmentEvidence(
        id=id,
        source_id="drawing-1",
        page_id="page-1",
        start=Point2D(x1, y1),
        end=Point2D(x2, y2),
        method="fixture",
        confidence=confidence,
    )


def controlled_segments():
    return (
        seg("h1-a", 0, 100, 90, 100),
        seg("h1-b", 95, 100, 200, 100),
        seg("h2", 0, 200, 200, 200),
        seg("h3", 0, 300, 200, 300),
        seg("v1-a", 50, 50, 50, 180),
        seg("v1-b", 50, 185, 50, 350),
        seg("v2", 150, 50, 150, 350),
    )


def test_fragmented_collinear_segments_merge_into_geometric_axis():
    result = reconstruct_grid_geometry(controlled_segments(), min_axis_length=100, gap_tolerance=10)
    horizontal = [a for a in result.axes if abs(math.sin(a.orientation_rad)) < 1e-9]
    assert len(horizontal) == 3
    y100 = min(horizontal, key=lambda a: abs(a.start.y - 100))
    assert y100.source_segment_ids == ("h1-a", "h1-b")
    assert y100.length == pytest.approx(200.0)
    assert y100.start.x == pytest.approx(0.0)
    assert y100.end.x == pytest.approx(200.0)


def test_dominant_orientation_families_and_intersections_are_reconstructed():
    result = reconstruct_grid_geometry(controlled_segments(), min_axis_length=100)
    assert len(result.families) == 2
    assert len(result.axes) == 5
    assert len(result.intersections) == 6
    points = {(round(i.point.x, 6), round(i.point.y, 6)) for i in result.intersections}
    assert points == {
        (50.0, 100.0), (150.0, 100.0),
        (50.0, 200.0), (150.0, 200.0),
        (50.0, 300.0), (150.0, 300.0),
    }


def test_spacing_regularity_is_high_for_evenly_spaced_three_axis_family():
    result = reconstruct_grid_geometry(controlled_segments(), min_axis_length=100)
    horizontal_family = min(result.families, key=lambda f: abs(f.orientation_rad))
    assert horizontal_family.spacing_regularity == pytest.approx(1.0)


def test_results_and_stable_candidate_ids_do_not_depend_on_input_order():
    forward = reconstruct_grid_geometry(controlled_segments(), min_axis_length=100)
    reverse = reconstruct_grid_geometry(tuple(reversed(controlled_segments())), min_axis_length=100)
    assert forward == reverse


def test_short_non_grid_noise_is_filtered_without_becoming_axis():
    data = controlled_segments() + (seg("noise", 400, 400, 410, 410),)
    result = reconstruct_grid_geometry(data, min_axis_length=100)
    assert all("noise" not in axis.source_segment_ids for axis in result.axes)


def test_duplicate_segment_ids_and_cross_page_input_are_rejected():
    duplicate = (seg("same", 0, 0, 100, 0), seg("same", 0, 10, 100, 10))
    with pytest.raises(GridGeometryError, match="duplicate"):
        reconstruct_grid_geometry(duplicate)

    other_page = LineSegmentEvidence(
        id="other", source_id="drawing-1", page_id="page-2",
        start=Point2D(0, 0), end=Point2D(100, 0), method="fixture"
    )
    with pytest.raises(GridGeometryError, match="one source page"):
        reconstruct_grid_geometry((seg("first", 0, 0, 100, 0), other_page))


def test_grid_geometry_remains_normalized_importer_evidence_not_core_geometry():
    result = reconstruct_grid_geometry(controlled_segments(), min_axis_length=100)
    assert result.axes
    assert not hasattr(result.axes[0], "label")
    assert not hasattr(result.axes[0], "units")
    assert not hasattr(result.axes[0], "model_z")


def test_near_collinear_segments_outside_tolerance_remain_separate_axes():
    data = (
        seg("a", 0, 100, 100, 100),
        seg("b", 0, 105, 100, 105),
    )
    result = reconstruct_grid_geometry(data, min_axis_length=90, collinear_tolerance=2)
    assert len(result.axes) == 2
