from linkoteq_drawing_reconstruction.scale_calibration import ScaleObservation, review_scale


def obs(id, normalized, engineering, confidence=1.0):
    return ScaleObservation(id, "drawing-1", "page-1", "ocr-dimension", normalized, engineering, "mm", confidence)


def test_low_confidence_scale_becomes_review_required_without_value():
    r = review_scale([obs("e1", 0.125, 6000.0, 0.4)])
    assert r.status == "review-required"
    assert r.resolved is None
    assert "no reliable scale evidence" in r.reason
    assert r.evidence_ids == ("e1",)


def test_conflicting_scale_becomes_review_required_without_choosing_a ratio():
    r = review_scale([obs("e1", 0.125, 6000.0), obs("e2", 0.125, 5000.0)])
    assert r.status == "review-required"
    assert r.resolved is None
    assert "conflicting scale evidence" in r.reason
    assert r.evidence_ids == ("e1", "e2")


def test_agreeing_scale_is_auto_accepted_and_produces_transform():
    r = review_scale([obs("e1", 0.125, 6000.0), obs("e2", 0.25, 12000.0)])
    assert r.status == "auto-accepted"
    assert r.resolved is not None
    assert r.resolved.engineering_per_normalized == 48000.0
