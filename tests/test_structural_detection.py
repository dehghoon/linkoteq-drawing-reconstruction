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
        coordinate_space="source-page",
        model_name="structural-detector",
        model_version="0.1.0",
        provenance="gpt7-fixture",
    )
    data.update(overrides)
    return StructuralDetectionEvidence(**data)


def test_detection_preserves_provenance_and_model_metadata():
    e = make_evidence()
    assert e.source_id == "drawing-1"
    assert e.page_id == "page-1"
    assert e.coordinate_space == "source-page"
    assert e.model_name == "structural-detector"
    assert e.model_version == "0.1.0"
    assert e.provenance == "gpt7-fixture"
    assert e.state == "review-required"


def test_raw_detector_evidence_never_authorizes_core_writeback():
    assert make_evidence().can_write_core_geometry is False


def test_source_box_must_have_positive_area():
    with pytest.raises(StructuralDetectionError, match="positive area"):
        SourceBox2D(10.0, 20.0, 10.0, 40.0)


def test_confidence_must_be_bounded_and_finite():
    with pytest.raises(StructuralDetectionError, match="confidence"):
        make_evidence(confidence=1.1)
    with pytest.raises(StructuralDetectionError, match="confidence"):
        make_evidence(confidence=float("nan"))


def test_coordinate_space_is_explicit_and_source_page_only():
    with pytest.raises(StructuralDetectionError, match="coordinate_space"):
        make_evidence(coordinate_space="model")


def test_provenance_must_be_non_empty():
    with pytest.raises(StructuralDetectionError, match="non-empty"):
        make_evidence(provenance=" ")
