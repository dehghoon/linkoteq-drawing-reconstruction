import pytest

from linkoteq_drawing_reconstruction.structural_detection import (
    SourceBox2D,
    StructuralDetectionError,
    StructuralDetectionEvidence,
)


def make_evidence(**overrides):
    data = dict(
        id="det-1", source_id="drawing-1", page_id="page-1",
        class_name="column", confidence=0.94,
        source_box=SourceBox2D(10.0, 20.0, 30.0, 40.0),
        coordinate_space="source-page",
        model_name="structural-detector", model_version="0.1.0",
        provenance="gpt7-fixture", contract_version="0.1",
    )
    data.update(overrides)
    return StructuralDetectionEvidence(**data)


def test_legacy_v01_column_passes():
    assert make_evidence().class_name == "column"

def test_legacy_v01_beam_passes():
    assert make_evidence(class_name="beam").class_name == "beam"

def test_v01_wall_is_rejected():
    with pytest.raises(StructuralDetectionError, match="class_name"):
        make_evidence(class_name="wall")

def test_v02_wall_passes():
    e = make_evidence(class_name="wall", contract_version="0.2", model_version="0.2.0")
    assert e.class_name == "wall"
    assert e.contract_version == "0.2"
    assert e.can_write_core_geometry is False

def test_v02_column_and_beam_pass():
    for cls in ("column", "beam"):
        assert make_evidence(class_name=cls, contract_version="0.2").class_name == cls

def test_unsupported_contract_version_is_rejected():
    with pytest.raises(StructuralDetectionError, match="contract version"):
        make_evidence(contract_version="9.9")

def test_preserves_provenance_and_model_metadata():
    e = make_evidence()
    assert e.source_id == "drawing-1"
    assert e.page_id == "page-1"
    assert e.coordinate_space == "source-page"
    assert e.model_name == "structural-detector"
    assert e.provenance == "gpt7-fixture"
    assert e.state == "review-required"

def test_raw_detector_evidence_never_authorizes_core_writeback():
    for class_name, version in (("column","0.1"), ("beam","0.1"), ("wall","0.2")):
        assert make_evidence(class_name=class_name, contract_version=version).can_write_core_geometry is False

def test_source_box_must_have_positive_area():
    with pytest.raises(StructuralDetectionError, match="positive area"):
        SourceBox2D(10.0, 20.0, 10.0, 40.0)

def test_confidence_must_be_bounded_and_finite():
    with pytest.raises(StructuralDetectionError, match="confidence"):
        make_evidence(confidence=1.1)
    with pytest.raises(StructuralDetectionError, match="confidence"):
        make_evidence(confidence=float("nan"))

def test_contract_requires_source_page():
    with pytest.raises(StructuralDetectionError, match="coordinate_space"):
        make_evidence(coordinate_space="model", contract_version="0.2")

def test_provenance_must_be_non_empty():
    with pytest.raises(StructuralDetectionError, match="non-empty"):
        make_evidence(provenance=" ", contract_version="0.2")
