import pytest

from linkoteq_drawing_reconstruction.structural_detection import (
    SourceBox2D,
    StructuralDetectionError,
    StructuralDetectionEvidence,
)


def make_evidence(**overrides):
    data = dict(
        id="det-1",
        source_id="drawing-1",
        page_id="page-1",
        class_name="column",
        confidence=0.94,
        source_box=SourceBox2D(10.0, 20.0, 30.0, 40.0),
        model_name="structural-detector",
        model_version="0.1.0",
    )
    data.update(overrides)
    return StructuralDetectionEvidence(**data)


def test_detection_preserves_provenance_and_model_metadata():
    e = make_evidence()
    assert e.source_id == "drawing-1"
    assert e.page_id == "page-1"
    assert e.model_name == "structural-detector"
    assert e.model_version == "0.1.0"
    assert e.state == "review-required"


def test_raw_detector_evidence_never_authorizes_core_writeback():
    assert make_evidence().can_write_core_geometry is False


def test_source_box_must_have_positive_area():
    with pytest.raises(StructuralDetectionError, match="positive area"):
        SourceBox2D(10.0, 20.0, 10.0, 40.0)


def test_confidence_must_be_bounded():
    with pytest.raises(StructuralDetectionError, match="confidence"):
        make_evidence(confidence=1.1)
