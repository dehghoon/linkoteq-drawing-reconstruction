import pytest
from linkoteq_drawing_reconstruction.structural_detection import SourceBox2D, StructuralDetectionError, StructuralDetectionEvidence

def ev(cls="wall", version="0.2", **kw):
    data=dict(id="det-v02", source_id="drawing-1", page_id="page-1", class_name=cls, confidence=0.91, source_box=SourceBox2D(10,20,30,40), coordinate_space="source-page", model_name="gpt7-detector", model_version="0.2.0", provenance="run:model:artifact", contract_version=version)
    data.update(kw)
    return StructuralDetectionEvidence(**data)

def test_v02_accepts_wall():
    assert ev().class_name == "wall"

def test_v01_rejects_wall():
    with pytest.raises(StructuralDetectionError):
        ev(version="0.1")

def test_legacy_v01_column_beam_remain_valid():
    for cls in ("column","beam"):
        assert ev(cls=cls, version="0.1").class_name == cls

def test_v02_requires_source_page():
    with pytest.raises(StructuralDetectionError):
        ev(coordinate_space="model")

def test_v02_requires_traceable_provenance():
    with pytest.raises(StructuralDetectionError):
        ev(provenance=" ")

def test_detector_evidence_never_authorizes_core_geometry():
    for cls in ("column","beam","wall"):
        assert ev(cls=cls).can_write_core_geometry is False
