import pytest

from linkoteq_drawing_reconstruction.source_normalization import (
    PreprocessingTransformStep,
    SourceNormalizationError,
    SourcePageMetadata,
    classify_source,
    normalize_source_page,
)
from linkoteq_drawing_reconstruction.transforms import (
    Affine2D,
    Point2D,
    Projective2D,
    UnresolvedTransformError,
)


def test_source_classification_is_explicit_and_deterministic():
    assert classify_source(has_vector_geometry=True, has_raster_content=False) == "vector"
    assert classify_source(has_vector_geometry=False, has_raster_content=True) == "raster"
    assert classify_source(has_vector_geometry=True, has_raster_content=True) == "mixed"
    with pytest.raises(SourceNormalizationError):
        classify_source(has_vector_geometry=False, has_raster_content=False)


def test_mixed_page_prefers_vector_source_space_and_preserves_identity_metadata():
    source = SourcePageMetadata.create(
        source_id="drawing-A",
        page_id="drawing-A:p1",
        page_index=0,
        width=841.89,
        height=595.28,
        has_vector_geometry=True,
        has_raster_content=True,
        dpi=300.0,
        media_type="application/pdf",
    )
    assert source.kind == "mixed"
    assert source.source_space == "vector"
    assert source.source_id == "drawing-A"
    assert source.page_id == "drawing-A:p1"
    assert source.page_index == 0
    assert source.dpi == 300.0


def test_preprocessing_transform_order_is_deterministic():
    source = SourcePageMetadata.create(
        source_id="scan-1",
        page_id="scan-1:p1",
        page_index=0,
        width=1000,
        height=800,
        has_vector_geometry=False,
        has_raster_content=True,
        dpi=200,
    )
    crop = PreprocessingTransformStep(
        step_id="crop-1",
        operation="crop",
        transform=Affine2D.from_rows(((1, 0, -100), (0, 1, -50), (0, 0, 1))),
        output_width=800,
        output_height=700,
    )
    scale = PreprocessingTransformStep(
        step_id="scale-1",
        operation="scale",
        transform=Affine2D.from_rows(((0.5, 0, 0), (0, 0.5, 0), (0, 0, 1))),
        output_width=400,
        output_height=350,
    )
    normalized = normalize_source_page(source, (crop, scale))
    assert normalized.source_to_normalized.apply(Point2D(300, 250)) == Point2D(100, 100)
    assert normalized.normalized_width == 400
    assert normalized.normalized_height == 350
    assert tuple(step.step_id for step in normalized.steps) == ("crop-1", "scale-1")


def test_perspective_warp_is_tracked_without_inventing_engineering_scale():
    source = SourcePageMetadata.create(
        source_id="photo-1",
        page_id="photo-1:p1",
        page_index=0,
        width=1200,
        height=900,
        has_vector_geometry=False,
        has_raster_content=True,
    )
    perspective = Projective2D.from_rows(
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0005, 0.0, 1.0))
    )
    step = PreprocessingTransformStep(
        step_id="perspective-1",
        operation="perspective-correction",
        transform=perspective,
        output_width=1200,
        output_height=900,
    )
    normalized = normalize_source_page(source, (step,))
    p = normalized.source_to_normalized.apply(Point2D(100, 0))
    assert p.x == pytest.approx(100 / 1.05)
    unresolved = normalized.unresolved_model_transform()
    assert unresolved.is_resolved is False
    with pytest.raises(UnresolvedTransformError):
        unresolved.to_model_point(Point2D(100, 0))


def test_perspective_operation_rejects_affine_placeholder():
    with pytest.raises(SourceNormalizationError, match="projective"):
        PreprocessingTransformStep(
            step_id="perspective-1",
            operation="perspective-correction",
            transform=Affine2D.identity(),
            output_width=100,
            output_height=100,
        )


def test_duplicate_preprocessing_step_ids_are_rejected():
    source = SourcePageMetadata.create(
        source_id="scan-1",
        page_id="scan-1:p1",
        page_index=0,
        width=100,
        height=100,
        has_vector_geometry=False,
        has_raster_content=True,
    )
    step = PreprocessingTransformStep(
        step_id="same",
        operation="identity",
        transform=Affine2D.identity(),
        output_width=100,
        output_height=100,
    )
    with pytest.raises(SourceNormalizationError, match="Duplicate"):
        normalize_source_page(source, (step, step))


def test_invalid_source_space_or_dimensions_are_rejected():
    with pytest.raises(SourceNormalizationError, match="positive"):
        SourcePageMetadata.create(
            source_id="x",
            page_id="x:p1",
            page_index=0,
            width=0,
            height=100,
            has_vector_geometry=False,
            has_raster_content=True,
        )

    with pytest.raises(SourceNormalizationError, match="Mixed"):
        SourcePageMetadata(
            source_id="m",
            page_id="m:p1",
            page_index=0,
            width=100,
            height=100,
            has_vector_geometry=True,
            has_raster_content=True,
            source_space="pixel",
        )
