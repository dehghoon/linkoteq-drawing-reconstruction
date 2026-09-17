import pytest

from linkoteq_drawing_reconstruction.scale_calibration import (
    ScaleObservation,
    UnresolvedScaleError,
    confirm_scale,
    review_scale,
)
from linkoteq_drawing_reconstruction.transforms import Point2D


def obs(id, normalized, engineering, confidence=1.0):
    return ScaleObservation(id, "drawing-1", "page-1", "ocr-dimension", normalized, engineering, "mm", confidence)


def test_reliable_ocr_scale_still_requires_human_confirmation():
    r = review_scale([obs("e1", 0.125, 6000.0), obs("e2", 0.25, 12000.0)])
    assert r.status == "review-required"
    assert r.resolved is not None
    assert r.resolved.engineering_per_normalized == pytest.approx(48000.0)
    assert r.resolved.human_confirmed is False
    with pytest.raises(UnresolvedScaleError, match="human confirmation"):
        r.resolved.normalized_to_model_xy()


def test_human_confirmation_unlocks_physical_transform():
    r = review_scale([obs("e1", 0.125, 6000.0)])
    confirmed = confirm_scale(r)
    assert confirmed.human_confirmed is True
    p = confirmed.normalized_to_model_xy().apply(Point2D(0.25, 0.5))
    assert p.x == pytest.approx(12000.0)
    assert p.y == pytest.approx(24000.0)


def test_no_reliable_number_requests_explicit_user_scale():
    r = review_scale([obs("e1", 0.125, 6000.0, 0.4)])
    assert r.status == "review-required"
    assert r.resolved is None
    with pytest.raises(UnresolvedScaleError, match="requires user-confirmed"):
        confirm_scale(r)
    confirmed = confirm_scale(r, engineering_per_normalized=48000.0, length_unit="mm")
    assert confirmed.human_confirmed is True
    assert confirmed.engineering_per_normalized == pytest.approx(48000.0)


def test_conflicting_scale_never_chooses_a_ratio():
    r = review_scale([obs("e1", 0.125, 6000.0), obs("e2", 0.125, 5000.0)])
    assert r.status == "review-required"
    assert r.resolved is None
    assert "conflicting scale evidence" in r.reason
