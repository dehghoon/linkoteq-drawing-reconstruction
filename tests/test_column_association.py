import pytest

from linkoteq_drawing_reconstruction.column_association import (
    ColumnAssociationError,
    associate_column_to_grid,
)
from linkoteq_drawing_reconstruction.grid_geometry import GridIntersection
from linkoteq_drawing_reconstruction.structural_detection import (
    SourceBox2D,
    StructuralDetectionEvidence,
)
from linkoteq_drawing_reconstruction.transforms import Affine2D, Point2D


def detection(class_name="column", box=None):
    return StructuralDetectionEvidence(
        id="det-1",
        source_id="drawing-1",
        page_id="page-1",
        class_name=class_name,
        confidence=0.95,
        source_box=box or SourceBox2D(9.0, 9.0, 11.0, 11.0),
        coordinate_space="source-page",
        model_name="structural-detector",
        model_version="0.1.0",
        provenance="gpt7-fixture",
    )


def intersection(id, x, y):
    return GridIntersection(id, "family-x", "family-y", Point2D(x, y))


def test_auto_snaps_clear_near_intersection():
    r = associate_column_to_grid(
        detection(),
        Affine2D.identity(),
        (intersection("i-1", 10.5, 10.0),),
        auto_snap_distance=1.0,
        review_snap_distance=3.0,
    )
    assert r.state == "auto-accepted"
    assert r.grid_intersection_id == "i-1"
    assert r.point == Point2D(10.5, 10.0)


def test_excessive_snap_distance_requires_review():
    r = associate_column_to_grid(
        detection(),
        Affine2D.identity(),
        (intersection("i-1", 12.0, 10.0),),
        auto_snap_distance=1.0,
        review_snap_distance=3.0,
    )
    assert r.state == "review-required"
    assert r.grid_intersection_id == "i-1"


def test_far_column_is_preserved_off_grid_without_forced_snap():
    r = associate_column_to_grid(
        detection(),
        Affine2D.identity(),
        (intersection("i-1", 20.0, 20.0),),
        auto_snap_distance=1.0,
        review_snap_distance=3.0,
    )
    assert r.state == "preserved-off-grid"
    assert r.grid_intersection_id is None
    assert r.point == Point2D(10.0, 10.0)


def test_plan_detection_never_creates_vertical_column_member():
    r = associate_column_to_grid(
        detection(),
        Affine2D.identity(),
        (intersection("i-1", 10.0, 10.0),),
        auto_snap_distance=1.0,
        review_snap_distance=3.0,
    )
    assert r.can_create_column_member is False


def test_no_grid_evidence_preserves_column_off_grid():
    r = associate_column_to_grid(
        detection(),
        Affine2D.identity(),
        (),
        auto_snap_distance=1.0,
        review_snap_distance=3.0,
    )
    assert r.state == "preserved-off-grid"
    assert r.point == Point2D(10.0, 10.0)


def test_beam_detection_cannot_enter_column_association():
    with pytest.raises(ColumnAssociationError, match="requires a column detection"):
        associate_column_to_grid(
            detection(class_name="beam"),
            Affine2D.identity(),
            (),
            auto_snap_distance=1.0,
            review_snap_distance=3.0,
        )
