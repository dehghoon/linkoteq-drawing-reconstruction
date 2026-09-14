from math import isclose

import pytest

from linkoteq_drawing_reconstruction.transforms import (
    Affine2D,
    CalibrationEvidence,
    Point2D,
    SourceToModelTransform,
    TransformError,
    UnresolvedTransformError,lass SourceToModelTransform() -> SourceToModelTransform:
    return SourceToModelTransform(
        source_id="drawing-001",
        page_id="page-1",
        source_space="pixel",
        source_to_normalized=Affine2D.from_rows(
            ((0.01, 0.0, 0.0), (0.0, 0.01, 0.0), (0.0, 0.0, 1.0))
        ),
        normalized_to_model_xy=Affine2D.from_rows(
            ((10.0, 0.0, 0.0), (0.0, 10.0, 0.0), (0.0, 0.0, 1.0))
        ),
        model_z=3.5,
        project_length_unit="m",
        calibration=CalibrationEvidence(
            method="user-calibration", length_unit="m", residual=0.0
        ),
    )


def test_transform_chain_is_deterministic_and_composed_in_order():
    transform = resolved_transform()
    source = Point2D(100.0, 200.0)

    normalized = transform.to_normalized_point(source)
    model = transform.to_model_point(source)

    assert normalized == Point2D(1.0, 2.0)
    assert isclose(model.x, 10.0)
    assert isclose(model.y, 20.0)
    assert isclose(model.z, 3.5)

    composed = transform.T_source_to_model_xy.apply(source)
    assert isclose(composed.x, model.x)
    assert isclose(composed.y, model.y)


def test_unresolved_scale_blocks_model_geometry_writeback():
    transform = SourceToModelTransform(
        source_id="drawing-001",
        page_id="page-1",
        source_space="pixel",
        source_to_normalized=Affine2D.identity(),
    )

    assert transform.is_resolved is False
    with pytest.raises(UnresolvedTransformError):
        transform.to_model_point(Point2D(10.0, 20.0))
    with pytest.raises(UnresolvedTransformError):
        _ = transform.T_source_to_model_xy


def test_calibration_unit_must_match_project_length_unit():
    transform = SourceToModelTransform(
        source_id="drawing-001",
        page_id="page-1",
        source_space="vector",
        source_to_normalized=Affine2D.identity(),
        normalized_to_model_xy=Affine2D.identity(),
        model_z=0.0,
        project_length_unit="m",
        calibration=CalibrationEvidence(method="vector-geometry", length_unit="ft"),
    )
    assert transform.is_resolved is False


def test_invalid_affine_bottom_row_is_rejected():
    with pytest.raises(TransformError):
        Affine2D.from_rows(((1, 0, 0), (0, 1, 0), (1, 0, 1)))
