"""GPT-6-owned StructuralLayoutProposal v0.1 boundary."""
from dataclasses import dataclass
from math import isfinite

class StructuralLayoutProposalError(ValueError): pass

@dataclass(frozen=True)
class Point2D:
    x: float
    y: float
    def __post_init__(self):
        if not (isfinite(self.x) and isfinite(self.y)): raise StructuralLayoutProposalError("geometry coordinates must be finite")

@dataclass(frozen=True)
class TransformStep:
    from_space: str
    to_space: str
    matrix: tuple
    def __post_init__(self):
        if not self.from_space.strip() or not self.to_space.strip(): raise StructuralLayoutProposalError("transform spaces must be non-empty")
        if len(self.matrix)!=3 or any(len(r)!=3 for r in self.matrix): raise StructuralLayoutProposalError("transform matrix must be 3x3")
        if not all(isfinite(v) for r in self.matrix for v in r): raise StructuralLayoutProposalError("transform matrix must be finite")

@dataclass(frozen=True)
class StructuralLayoutProposal:
    proposal_id: str
    source_id: str
    page_id: str
    object_type: str
    origin: str
    coordinate_space: str
    geometry: tuple
    basis: tuple
    provenance: tuple
    confidence: float
    review_state: str = "proposed"
    core_writeback_eligible: bool = False
    contract_version: str = "0.1"
    transform_chain: tuple = ()
    detection_evidence_ids: tuple = ()

    def __post_init__(self):
        if self.contract_version!="0.1": raise StructuralLayoutProposalError("contract_version must be 0.1")
        if not all(v.strip() for v in (self.proposal_id,self.source_id,self.page_id,self.coordinate_space)): raise StructuralLayoutProposalError("identity and coordinate space must be non-empty")
        if self.object_type not in ("grid_axis","column","beam","wall"): raise StructuralLayoutProposalError("unsupported object_type")
        if self.origin not in ("observed","reconstructed","proposed"): raise StructuralLayoutProposalError("unsupported origin")
        if self.review_state not in ("proposed","review-required","approved","rejected"): raise StructuralLayoutProposalError("unsupported review_state")
        if not isfinite(self.confidence) or not 0<=self.confidence<=1: raise StructuralLayoutProposalError("confidence must be finite and between 0 and 1")
        if not self.geometry: raise StructuralLayoutProposalError("geometry must be non-empty")
        if not self.basis or not all(v.strip() for v in self.basis): raise StructuralLayoutProposalError("basis must be non-empty and traceable")
        if not self.provenance or not all(v.strip() for v in self.provenance): raise StructuralLayoutProposalError("provenance must be non-empty and traceable")
        if self.origin=="proposed" and self.core_writeback_eligible: raise StructuralLayoutProposalError("new proposals default to non-eligible Core writeback")
        if self.core_writeback_eligible and self.review_state!="approved": raise StructuralLayoutProposalError("Core writeback eligibility requires approval")
        if self.coordinate_space!="source-page":
            if not self.transform_chain: raise StructuralLayoutProposalError("derived space requires transform chain to source-page")
            cur=self.coordinate_space
            for step in self.transform_chain:
                if step.from_space!=cur: raise StructuralLayoutProposalError("transform chain must be contiguous")
                cur=step.to_space
            if cur!="source-page": raise StructuralLayoutProposalError("transform chain must terminate at source-page")

    @property
    def can_write_core_geometry_directly(self): return False

    def to_detection_evidence(self):
        raise StructuralLayoutProposalError("StructuralLayoutProposal MUST NOT be serialized as StructuralDetectionEvidence")

def validate_no_automatic_columns_from_grid_intersections(column_proposals):
    for p in column_proposals:
        if p.object_type!="column": raise StructuralLayoutProposalError("column_proposals must contain columns only")
        if p.origin=="proposed" and set(p.basis)<= {"grid-intersection"}:
            raise StructuralLayoutProposalError("grid intersection alone cannot create a column proposal")
