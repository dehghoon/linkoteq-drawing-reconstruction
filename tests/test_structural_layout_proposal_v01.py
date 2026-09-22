import pytest
from linkoteq_drawing_reconstruction.structural_layout_proposal import (
    Point2D, TransformStep, StructuralLayoutProposal, StructuralLayoutProposalError,
    validate_no_automatic_columns_from_grid_intersections,
)

def p(**kw):
    d=dict(proposal_id="p1",source_id="s1",page_id="pg1",object_type="column",
           origin="proposed",coordinate_space="source-page",geometry=(Point2D(1,2),),
           basis=("architectural-alignment","review-context"),provenance=("source:s1/page:pg1",),
           confidence=.6)
    d.update(kw)
    return StructuralLayoutProposal(**d)

def test_no_grid_no_visible_column_input_remains_valid():
    assert [] == []

def test_zero_detector_columns_not_engineering_absence():
    detector_columns=[]
    proposal=p()
    assert not detector_columns and proposal.origin=="proposed"

def test_proposed_grid_distinct_from_observed():
    g=p(object_type="grid_axis", origin="proposed")
    o=p(proposal_id="o1",object_type="grid_axis",origin="observed",detection_evidence_ids=("det-1",))
    assert g.origin != o.origin

def test_proposed_column_distinct_from_observed_detected_column():
    assert p().origin=="proposed"
    assert p(proposal_id="o2",origin="observed",detection_evidence_ids=("det-2",)).origin=="observed"

def test_grid_intersection_alone_cannot_create_column():
    c=p(basis=("grid-intersection",))
    with pytest.raises(StructuralLayoutProposalError):
        validate_no_automatic_columns_from_grid_intersections((c,))

def test_provenance_required_and_transform_chain_preserved():
    with pytest.raises(StructuralLayoutProposalError): p(provenance=())
    t=TransformStep("normalized","source-page",((1,0,0),(0,1,0),(0,0,1)))
    q=p(coordinate_space="normalized",transform_chain=(t,))
    assert q.transform_chain[-1].to_space=="source-page"

def test_synthetic_proposal_cannot_become_detection_evidence():
    with pytest.raises(StructuralLayoutProposalError): p().to_detection_evidence()

def test_unapproved_proposal_cannot_write_core_geometry():
    q=p()
    assert q.core_writeback_eligible is False
    assert q.can_write_core_geometry_directly is False
    with pytest.raises(StructuralLayoutProposalError): p(core_writeback_eligible=True)

def test_approved_still_cannot_bypass_core_mapping():
    q=p(origin="reconstructed",review_state="approved",core_writeback_eligible=True)
    assert q.core_writeback_eligible is True
    assert q.can_write_core_geometry_directly is False

def test_contract_version_and_object_types():
    for typ in ("grid_axis","column","beam","wall"):
        assert p(proposal_id=typ,object_type=typ).object_type==typ
    with pytest.raises(StructuralLayoutProposalError): p(contract_version="0.2")
