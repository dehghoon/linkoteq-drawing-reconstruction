import pytest

from linkoteq_drawing_reconstruction.scale_calibration import (
    ScaleObservation,
    UnresolvedScaleError,
    confirm_scale,
    review_scale,
)


def obs(
    evidence_id: str,
    normalized: float,
    engineering: float,
    *,
    source_id: str = "drawing-1",
    page_id: str = "page-1",
    unit: str = "mm",
    confidence: float = 1.0,
) -> ScaleObservation:
    return ScaleObservation(
        id=evidence_id,
        source_id=source_id,
        page_id=page_id,
        method="ocr-dimension",
        normalized_length=normalized,
        engineering_length=engineering,
        length_unit=unit,
        confidence=confidence,
    )


def test_reliable_proposal_still_requires_review_before_writeback():
    review = review_scale([obs("dim-1", 0.125, 6000.0)])

    assert review.status == "review-required"
    assert review.resolved is not None
    assert review.resolved.human_confirmed is False
    assert review.evidence_ids == ("dim-1",)

    with pytest.raises(UnresolvedScaleError, match="human confirmation"):
        review.resolved.normalized_to_model_xy()


def test_conflicting_evidence_preserves_all_ids_for_review():
    review = review_scale([
        obs("dim-2", 0.125, 5000.0),
        obs("dim-1", 0.125, 6000.0),
    ])

    assert review.status == "review-required"
    assert review.resolved is None
    assert review.evidence_ids == ("dim-1", "dim-2")
    assert "conflicting scale evidence" in (review.reason or "")


def test_cross_page_evidence_cannot_silently_resolve_scale():
    review = review_scale([
        obs("dim-1", 0.125, 6000.0, page_id="page-1"),
        obs("dim-2", 0.125, 6000.0, page_id="page-2"),
    ])

    assert review.status == "review-required"
    assert review.resolved is None
    assert "one source page" in (review.reason or "")


def test_explicit_user_calibration_can_resolve_an_unresolved_review():
    review = review_scale([])
    confirmed = confirm_scale(
        review,
        engineering_per_normalized=25000.0,
        length_unit="mm",
    )

    assert confirmed.human_confirmed is True
    assert confirmed.engineering_per_normalized == 25000.0
    assert confirmed.length_unit == "mm"
    assert confirmed.calibration.method == "user-calibration"

def test_low_confidence_evidence_remains_traceable_but_unresolved():
    review = review_scale([
        obs("dim-low", 0.125, 6000.0, confidence=0.4),
    ])

    assert review.status == "review-required"
    assert review.resolved is None
    assert review.evidence_ids == ("dim-low",)
    assert "no reliable scale evidence" in (review.reason or "")
