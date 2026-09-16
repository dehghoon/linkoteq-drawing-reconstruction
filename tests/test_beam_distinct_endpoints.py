from linkoteq_drawing_reconstruction.beam_reconstruction import StructuralNodeEvidence, reconstruct_beam
from linkoteq_drawing_reconstruction.structural_detection import SourceBox2D, StructuralDetectionEvidence
from linkoteq_drawing_reconstruction.transforms import Affine2D, Point2D


def test_same_node_beam_endpoints_require_review():
    detection = StructuralDetectionEvidence(
        id="beam-same-node",
        source_id="drawing-1",
        page_id="p-1",
        class_name="beam",
        confidence=0.95,
        source_box=SourceBox2D(0, -1, 2, 1),
        model_name="detector",
        model_version="v1",
    )
    nodes = (StructuralNodeEvidence("n-1", Point2D(1, 0)),)

    result = reconstruct_beam(
        detection,
        Affine2D.identity(),
        nodes,
        auto_endpoint_distance=1.0,
        review_endpoint_distance=5.0,
    )

    assert result.start_node_id == "n-1"
    assert result.end_node_id == "n-1"
    assert result.state == "review-required"
    assert not result.can_create_member
    assert "same structural node" in result.reason
