"""GPT-6 Reconstruction Continuous Improvement v0.1 lifecycle boundary."""
from dataclasses import dataclass
from typing import Literal, Mapping, Sequence
CONTRACT_VERSION="0.1"
EvidenceKind=Literal["observed","reconstructed","proposed"]
class ContinuousImprovementError(ValueError): pass
def _req(n,v):
    if not isinstance(v,str) or not v.strip(): raise ContinuousImprovementError(f"{n} must be non-empty")
@dataclass(frozen=True)
class ImprovementCase:
    case_id:str; source_id:str; page_id:str; project_group_id:str
    input_contract_versions:tuple[str,...]; source_page_provenance:tuple[str,...]
    coordinate_space:str; transform_chain:tuple[str,...]; detector_evidence_ids:tuple[str,...]
    original_output_ref:str; adjudicated_outcome_ref:str; correction_category:str
    affected_object_types:tuple[str,...]; rationale_evidence_refs:tuple[str,...]
    review_state:str; created_at:str; reviewed_at:str|None; benchmark_eligible:bool
    evidence_kind:EvidenceKind; contract_version:str=CONTRACT_VERSION
    def __post_init__(self):
        for n in ("case_id","source_id","page_id","project_group_id","coordinate_space","original_output_ref","adjudicated_outcome_ref","correction_category","created_at"): _req(n,getattr(self,n))
        if self.contract_version!="0.1": raise ContinuousImprovementError("contract_version must be 0.1")
        if not self.input_contract_versions or not all(x.strip() for x in self.input_contract_versions): raise ContinuousImprovementError("input contract versions required")
        if not self.source_page_provenance or not all(x.strip() for x in self.source_page_provenance): raise ContinuousImprovementError("traceable source/page provenance required")
        if not self.rationale_evidence_refs or not all(x.strip() for x in self.rationale_evidence_refs): raise ContinuousImprovementError("rationale/evidence references required")
        if self.evidence_kind not in ("observed","reconstructed","proposed"): raise ContinuousImprovementError("invalid evidence_kind")
        if self.review_state not in ("review-required","adjudicated","rejected"): raise ContinuousImprovementError("invalid review_state")
        if self.review_state=="adjudicated" and not self.reviewed_at: raise ContinuousImprovementError("adjudicated cases require reviewed_at")
    @property
    def creates_permanent_rule(self): return False
    @property
    def proves_engineering_absence(self): return False
@dataclass(frozen=True)
class BenchmarkCase:
    case_id:str; project_group_id:str; expected_outcome_ref:str
    def __post_init__(self):
        for n in ("case_id","project_group_id","expected_outcome_ref"): _req(n,getattr(self,n))
@dataclass(frozen=True)
class FrozenBenchmark:
    benchmark_id:str; version:str; frozen_at:str; cases:tuple[BenchmarkCase,...]; source_manifest_sha256:str
    def __post_init__(self):
        for n in ("benchmark_id","version","frozen_at","source_manifest_sha256"): _req(n,getattr(self,n))
        if not self.cases: raise ContinuousImprovementError("benchmark must contain cases")
        if len({c.case_id for c in self.cases})!=len(self.cases): raise ContinuousImprovementError("benchmark case ids must be unique")
    def cases_for_project_group(self,g): return tuple(c for c in self.cases if c.project_group_id==g)
@dataclass(frozen=True)
class ReconstructionVersion:
    version_id:str; commit_sha:str; config_ref:str; threshold_ref:str
    def __post_init__(self):
        for n in ("version_id","commit_sha","config_ref","threshold_ref"): _req(n,getattr(self,n))
@dataclass(frozen=True)
class CandidateImprovement:
    candidate_id:str; base:ReconstructionVersion; candidate:ReconstructionVersion
    motivating_case_ids:tuple[str,...]; benchmark_version:str; known_limitations:tuple[str,...]
    def __post_init__(self):
        _req("candidate_id",self.candidate_id); _req("benchmark_version",self.benchmark_version)
        if not self.motivating_case_ids: raise ContinuousImprovementError("motivating cases required")
        if self.base.commit_sha==self.candidate.commit_sha: raise ContinuousImprovementError("candidate commit must differ")
    @property
    def auto_promotable(self): return False
@dataclass(frozen=True)
class CaseEvaluation:
    case_id:str; baseline_passed:bool; candidate_passed:bool; critical_contract_case:bool=False
@dataclass(frozen=True)
class RegressionReport:
    benchmark_id:str; benchmark_version:str; baseline_version_id:str; candidate_version_id:str
    evaluations:tuple[CaseEvaluation,...]; improvements:tuple[str,...]; regressions:tuple[str,...]
    critical_regressions:tuple[str,...]; passed:bool
def evaluate_candidate(benchmark,candidate,baseline_results:Mapping[str,bool],candidate_results:Mapping[str,bool],critical_case_ids:Sequence[str]=()):
    if candidate.benchmark_version!=benchmark.version: raise ContinuousImprovementError("benchmark version mismatch")
    ids=tuple(c.case_id for c in benchmark.cases)
    if set(baseline_results)!=set(ids) or set(candidate_results)!=set(ids): raise ContinuousImprovementError("same frozen benchmark required")
    crit=set(critical_case_ids); ev=tuple(CaseEvaluation(i,bool(baseline_results[i]),bool(candidate_results[i]),i in crit) for i in ids)
    imp=tuple(e.case_id for e in ev if not e.baseline_passed and e.candidate_passed)
    reg=tuple(e.case_id for e in ev if e.baseline_passed and not e.candidate_passed)
    creg=tuple(i for i in reg if i in crit)
    return RegressionReport(benchmark.benchmark_id,benchmark.version,candidate.base.version_id,candidate.candidate.version_id,ev,imp,reg,creg,not creg)
@dataclass(frozen=True)
class PromotionGateEvidence:
    active_contract_tests_pass:bool; proposal_v01_pass:bool; detection_v02_pass:bool; legacy_v01_pass:bool
    frozen_benchmark_pass:bool; no_critical_regressions:bool; provenance_traceable:bool
    unapproved_proposals_blocked:bool; approved_proposals_core_validated:bool; core_compatibility_pass:bool
    no_direct_pynite_dependency:bool; human_admin_approved:bool
    @property
    def all_pass(self): return all(getattr(self,f) for f in self.__dataclass_fields__)
@dataclass(frozen=True)
class PromotionRecord:
    promoted_commit:str; previous_active_commit:str; benchmark_version:str; evaluation_artifact_ref:str
    approval_evidence_ref:str; core_contract_version:str; core_contract_sha:str
    detector_contract_version:str; proposal_contract_version:str; rollback_target:str; gate_evidence:PromotionGateEvidence
    def __post_init__(self):
        for n in ("promoted_commit","previous_active_commit","benchmark_version","evaluation_artifact_ref","approval_evidence_ref","core_contract_version","core_contract_sha","detector_contract_version","proposal_contract_version","rollback_target"): _req(n,getattr(self,n))
        if not self.gate_evidence.all_pass: raise ContinuousImprovementError("all promotion gates including human/admin approval required")
        if self.rollback_target!=self.previous_active_commit: raise ContinuousImprovementError("rollback target must be previous active commit")
@dataclass(frozen=True)
class RollbackRecord:
    from_commit:str; to_commit:str; reason:str; approved_by:str; recorded_at:str
    def __post_init__(self):
        for n in ("from_commit","to_commit","reason","approved_by","recorded_at"): _req(n,getattr(self,n))
def assert_no_synthetic_detector_provenance(evidence_kind,detector_evidence_ids):
    if evidence_kind in ("proposed","reconstructed") and detector_evidence_ids: raise ContinuousImprovementError("synthetic/reconstructed artifacts cannot manufacture detector provenance")
def validate_no_grid_only_column_rule(case):
    if case.correction_category=="column-from-grid-intersection-only": raise ContinuousImprovementError("grid intersections cannot automatically create columns")
