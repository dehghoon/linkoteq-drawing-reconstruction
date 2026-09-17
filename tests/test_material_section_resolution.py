import pytest

from linkoteq_drawing_reconstruction.material_section_resolution import (
    MaterialSectionResolutionError,
    ReferenceCandidate,
    confirm_reference,
    resolve_reference,
)


def candidate(id, kind, core_id, confidence=0.95):
    return ReferenceCandidate(
        id=id,
        kind=kind,
        core_id=core_id,
        source_id="drawing-1",
        page_id="page-1",
        method="ocr-tag-association",
        confidence=confidence,
    source_text=core_id,
    )


def test_no_evidence_requires_review():
    r = resolve_reference([], kind="material")
    assert r.status == "review-required"
    assert r.core_id is None


def test_low_confidence_requires_review():
    r = resolve_reference([candidate("c1", "section", "sec-1", 0.5)], kind="section")
    assert r.status == "review-required"
    assert r.core_id is None


def test_conflicting_associations_require_review():
    r = resolve_reference(
        [candidate("c1", "material", "mat-1"), candidate("c2", "material", "mat-2")],
        kind="material",
    )
    assert r.status == "review-required"
    assert r.core_id is None
    assert "conflicting" in r.reason


def test_unanimous_high_confidence_evidence_proposes_existing_core_id():
    r = resolve_reference(
        [candidate("c1", "section", "sec-1"), candidate("c2", "section", "sec-1")],
        kind="section",
    )
    assert r.status == "auto-accepted"
    assert r.core_id == "sec-1"


def test_human_can_confirm_review_required_existing_reference():
    r = resolve_reference([], kind="material")
    confirmed = confirm_reference(r, core_id="mat-1")
    assert confirmed.core_id == "mat-1"
    assert confirmed.reason == "human-confirmed"


def test_confirmation_never_invents_core_reference():
    r = resolve_reference([], kind="section")
    with pytest.raises(MaterialSectionResolutionError, match="existing Core id"):
        confirm_reference(r)
