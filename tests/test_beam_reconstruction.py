from linkoteq_drawing_reconstruction.beam_reconstruction import (
    BeamReconstructionError,
    StructuralNodeEvidence,
    reconstruct_beam,
)
from linkoteq_drawing_reconstruction.structural_detection import SourceBox2D, StructuralDetectionEvidence
from linkoteq_drawing_reconstruction.transforms import Affine2D, Point2D

import pytest


def detection(*, class_name="beam", box=SourceBox2D(10, 19, 90, 21)):
    return StructuralDetectionEvidence(
        id="det-1",
        source_id="drawing-1",
        page_id="p-1",
        class_name=class_name,
        confidence=0.95,
        source_box=box,
        model_name="detector",
        model_version="v1",
    )


def nodes():
    return (
        StructuralNodeEvidence("n-1", Point2D(10, 20)),
        StructuralNodeEvidence("n-2", Point2D(90, 20)),
    )


def test_horizontal_beam_reconstructs_centerline_and_connectivity():
    r = reconstruct_beam(
        detection(),
        Affine2D.identity(),
        nodes(),
        auto_endpoint_distance=1.0,
        review_endpoint_distance=5.0,
     )
    assert r.start == Point2D(10, 20)
    assert r.end == Point2D(90, 20)
    assert (r.start_node_id, r.end_node_id) == ("n-1", "n-2")
    assert r.state == "auto-accepted"
    assert r.can_create_member


def test_vertical_beam_uses_long_axis_centerline():
    d = detection(box=SourceBox2D(19, 10, 21, 90))
    n = (
        StructuralNodeEvidence("a", Point2D(20, 10)),
        StructuralNodeEvidence("b", Point2D(20, 90)),
     )
    r = reconstruct_beam(d, Affine2D.identity(), n, auto_endpoint_distance=1, review_endpoint_distance=5)
    assert r.start == Point2D(20, 10)
    assert r.end == Point2D(20, 90)
    assert r.can_create_member


def test_near_but_not_auto_endpoint_requires_review():
    n = (
        StructuralNodeEvidence("n-1", Point2D(11.5, 20)),
        StructuralNodeEvidence("n-2", Point2D(88.5, 20)),
    )
    r = reconstruct_beam(detection(), Affine2D.identity(), n, auto_endpoint_distance=1, review_endpoint_distance=3)
    assert r.state == "review-required"
    assert not r.can_create_member


def test_far_endpoint_preserves_unconnected_evidence():
    n = (StructuralNodeEvidence("far", Point2D(200, 200)),)
    r = reconstruct_beam(detection(), Affine2D.identity(), n, auto_endpoint_distance=1, review_endpoint_distance=5)
    assert r.state == "preserved-unconnected"
    assert r.start_node_id is None
    assert r.end_node_id is None
    assert not r.can_create_member


def test_no_nodes_preserves_unconnected_evidence():
    r = reconstruct_beam(detection(), Affine2D.identity(), (), auto_endpoint_distance=1, review_endpoint_distance=5)
    assert r.state == "preserved-unconnected"
    assert not r.can_create_member


def test_non_beam_detection_is_rejected():
    with pytest.raises(BeamReconstructionError, match="requires a beam detection"):
        reconstruct_beam(detection(class_name="column"), Affine2D.identity(), nodes(), auto_endpoint_distance=1, review_endpoint_distance=5)


def test_invalid_thresholds_are_rejected():
    with pytest.raises(BeamReconstructionError):
        reconstruct_beam(detection(), Affine2D.identity(), nodes(), auto_endpoint_distance=5, review_endpoint_distance=1)
