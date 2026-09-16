import pytest

from linkoteq_drawing_reconstruction.scale_calibration import (
    ScaleObservation,
    UnresolvedScaleError,
    resolve_scale,
)

def obs(id, normalized, engineering, *, confidence=1.0, unit="mm", method="ocr-dimension"):
    return ScaleObservation(
        id=id,
        source_id="drawing-1",
        page_id="page-1",
        method=method,
        normalized_length=normalized,
        engineering_length=engineering,
        length_unit=unit,
        confidence=confidence,
    )


def test_resolves_explicit_scale_deterministically():
    result = resolve_scale([
        obs("dim-1", 0.125, 6000.0),
        obs("grid-1", 0.25, 12000.0, method="known-grid-spacing"),
    ])
    assert result.length_unit == "mm"
    assert result.engineering_per_normalized == pytest.approx(48000.0)
    assert result.residual == pytest.approx(0.0)
    assert result.evidence_ids == ("dim-1", "grid-1")


def test_low_confidence_evidence_does_not_invent_scale():
    with pytest.raises(UnresolvedScaleError, match="no reliable scale evidence"):
        resolve_scale([obs("dim-1", 0.125, 6000.0, confidence=0.4)])


def test_conflicting_evidence_blocks_physical_writeback():
    with pytest.raises(UnresolvedScaleError, match="conflicting scale evidence"):
        resolve_scale([
            obs("dim-1", 0.125, 6000.0),
            obs("dim-2", 0.125, 5000.0),
        ])


def test_evidence_must_share_unit():
    with pytest.raises(UnresolvedScaleError, match="one length_unit"):
        resolve_scale([
            obs("dim-1", 0.125, 6000.0, unit="mm"),
             obs("dim-2", 0.125, 6.0, unit="m"),
        ])


def test_resolved_scale_produces_deterministic_normalized_to_model_transform():
    result = resolve_scale([obs("dim-1", 0.125, 6000.0)])
    t = result.normalized_to_model_xy(origin_x=1000.0, origin_y=2000.0)
    p = t.apply_xy((0.25, 0.5))
    assert p.x == pytest.approx(13000.0)
    assert p.y == pytest.approx(26000.0)
