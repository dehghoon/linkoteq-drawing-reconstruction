import pytest
from linkoteq_drawing_reconstruction.continuous_improvement import (
 BenchmarkCase,CandidateImprovement,ContinuousImprovementError,FrozenBenchmark,ImprovementCase,
 PromotionGateEvidence,PromotionRecord,ReconstructionVersion,RollbackRecord,
 assert_no_synthetic_detector_provenance,evaluate_candidate,validate_no_grid_only_column_rule)
def case(**kw):
 d=dict(case_id="c1",source_id="s",page_id="p",project_group_id="g1",input_contract_versions=("StructuralDetectionEvidence v0.2","StructuralLayoutProposal v0.1"),source_page_provenance=("source.pdf#page=1",),coordinate_space="source-page",transform_chain=(),detector_evidence_ids=(),original_output_ref="out:base",adjudicated_outcome_ref="out:review",correction_category="topology",affected_object_types=("beam",),rationale_evidence_refs=("review:R1",),review_state="adjudicated",created_at="2026-09-22T00:00:00Z",reviewed_at="2026-09-22T01:00:00Z",benchmark_eligible=True,evidence_kind="reconstructed")
 d.update(kw); return ImprovementCase(**d)
def bench(): return FrozenBenchmark("rb","0.1.0","2026-09-22T00:00:00Z",(BenchmarkCase("c1","g1","e1"),BenchmarkCase("c2","g2","e2")),"sha256:abc")
def cand(): return CandidateImprovement("cand",ReconstructionVersion("base","aaa","cfg1","thr1"),ReconstructionVersion("cand","bbb","cfg2","thr2"),("c1",),"0.1.0",("known",))
def gates(**kw):
 d={k:True for k in PromotionGateEvidence.__dataclass_fields__}; d.update(kw); return PromotionGateEvidence(**d)
def test_single_correction_not_permanent_rule(): assert case().creates_permanent_rule is False
def test_case_preserves_source_page_project_group_provenance(): assert (case().source_id,case().page_id,case().project_group_id)==("s","p","g1")
def test_project_group_benchmark_isolation(): assert [x.case_id for x in bench().cases_for_project_group("g1")]==["c1"]
def test_proposed_observed_distinguishable(): assert case(evidence_kind="observed").evidence_kind!=case(evidence_kind="proposed").evidence_kind
def test_zero_detector_observations_not_absence(): assert case().proves_engineering_absence is False
def test_grid_intersection_not_automatic_column():
 with pytest.raises(ContinuousImprovementError): validate_no_grid_only_column_rule(case(correction_category="column-from-grid-intersection-only"))
def test_synthetic_overlay_not_detector_provenance():
 with pytest.raises(ContinuousImprovementError): assert_no_synthetic_detector_provenance("proposed",("det1",))
def test_candidate_cannot_auto_promote(): assert cand().auto_promotable is False
def test_frozen_benchmark_unique_cases():
 with pytest.raises(ContinuousImprovementError): FrozenBenchmark("b","1","t",(BenchmarkCase("x","g","e"),BenchmarkCase("x","g","e")),"sha")
def test_same_frozen_benchmark_required():
 with pytest.raises(ContinuousImprovementError): evaluate_candidate(bench(),cand(),{"c1":True},{"c1":True,"c2":True})
def test_report_exposes_improvements_regressions():
 r=evaluate_candidate(bench(),cand(),{"c1":False,"c2":True},{"c1":True,"c2":False}); assert r.improvements==("c1",) and r.regressions==("c2",)
def test_critical_regression_fails():
 r=evaluate_candidate(bench(),cand(),{"c1":True,"c2":True},{"c1":True,"c2":False},("c2",)); assert not r.passed and r.critical_regressions==("c2",)
def test_human_admin_gate_required():
 with pytest.raises(ContinuousImprovementError): PromotionRecord("bbb","aaa","0.1","eval","approval","0.5","core","0.2","0.1","aaa",gates(human_admin_approved=False))
def test_rollback_target_required():
 with pytest.raises(ContinuousImprovementError): PromotionRecord("bbb","aaa","0.1","eval","approval","0.5","core","0.2","0.1","zzz",gates())
def test_valid_promotion_records_boundaries():
 p=PromotionRecord("bbb","aaa","0.1","eval","approval","0.5","core","0.2","0.1","aaa",gates()); assert p.rollback_target=="aaa"
def test_explicit_rollback_record(): assert RollbackRecord("bbb","aaa","regression","admin","t").to_commit=="aaa"
def test_adjudicated_requires_review_time():
 with pytest.raises(ContinuousImprovementError): case(reviewed_at=None)
def test_candidate_tracks_versions(): assert (cand().base.commit_sha,cand().candidate.commit_sha,cand().benchmark_version)==("aaa","bbb","0.1.0")
