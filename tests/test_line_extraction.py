import pytest

from linkoteq_drawing_reconstruction.line_extraction import (
    LineExtractionError,
    RasterLineSettings,
    _make_evidence,
    extract_lines_from_pdf,
)
from linkoteq_drawing_reconstruction.source_normalization import SourcePageMetadata
from linkoteq_drawing_reconstruction.transforms import Affine2D, Point2D


def vector_source(*, mixed=False):
    return SourcePageMetadata.create(
        source_id="drawing-pdf",
        page_id="drawing-pdf:p1",
        page_index=0,
        width=200.0,
        height=200.0,
        has_vector_geometry=True,
        has_raster_content=mixed,
        media_type="application/pdf",
    )


def raster_source():
    return SourcePageMetadata.create(
        source_id="scan",
        page_id="scan:p1",
        page_index=0,
        width=256,
        height=256,
        has_vector_geometry=False,
        has_raster_content=True,
        dpi=200.0,
        media_type="image/png",
    )


def test_make_evidence_normalizes_and_produces_stable_id():
    transform = Affine2D.from_rows(
        ((0.5, 0.0, 5.0), (0.0, 0.5, 7.0), (0.0, 0.0, 1.0))
    )
    first = _make_evidence(
        source=vector_source(),
        method="vector",
        start=Point2D(10.0, 20.0),
        end=Point2D(190.0, 20.0),
        source_to_normalized=transform,
    )
    second = _make_evidence(
        source=vector_source(),
        method="vector",
        start=Point2D(190.0, 20.0),
        end=Point2D(10.0, 20.0),
        source_to_normalized=transform,
    )
    assert first == second
    assert first.start == Point2D(10.0, 17.0)
    assert first.end == Point2D(100.0, 17.0)
    assert first.method == "vector"


def test_raster_settings_validate_thresholds():
    with pytest.raises(LineExtractionError, match="Canny"):
        RasterLineSettings(canny_threshold1=100.0, canny_threshold2=50.0)
    with pytest.raises(LineExtractionError, match="render_dpi"):
        RasterLineSettings(render_dpi=0.0)


def test_pdf_dispatch_prefers_vector_for_mixed_pages(monkeypatch):
    sentinel = ("vector-result",)
    import linkoteq_drawing_reconstruction.line_extraction as module

    monkeypatch.setattr(
        module,
        "extract_vector_lines_from_pdf",
        lambda *args, **kwargs: sentinel,
    )
    monkeypatch.setattr(
        module,
        "extract_raster_lines_from_pdf",
        lambda *args, **kwargs: pytest.fail("raster fallback should not run"),
    )

    result = extract_lines_from_pdf(
        "fixture.pdf",
        page_index=0,
        source=vector_source(mixed=True),
        source_to_normalized=Affine2D.identity(),
    )
    assert result == sentinel


def test_pdf_dispatch_uses_raster_for_raster_only_pages(monkeypatch):
    sentinel = ("raster-result",)
    import linkoteq_drawing_reconstruction.line_extraction as module

    monkeypatch.setattr(
        module,
        "extract_vector_lines_from_pdf",
        lambda *args, **kwargs: pytest.fail("vector path should not run"),
    )
    monkeypatch.setattr(
        module,
        "extract_raster_lines_from_pdf",
        lambda *args, **kwargs: sentinel,
    )

    result = extract_lines_from_pdf(
        "fixture.pdf",
        page_index=0,
        source=raster_source(),
        source_to_normalized=Affine2D.identity(),
    )
    assert result == sentinel


def test_real_vector_pdf_adapter_when_pymupdf_available(tmp_path):
    fitz = pytest.importorskip("fitz")
    from linkoteq_drawing_reconstruction.line_extraction import extract_vector_lines_from_pdf

    path = tmp_path / "vector.pdf"
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    page.draw_line((10, 20), (190, 20), width=1)
    page.draw_line((50, 10), (50, 190), width=1)
    doc.save(path)
    doc.close()

    lines = extract_vector_lines_from_pdf(
        path,
        page_index=0,
        source=vector_source(),
        source_to_normalized=Affine2D.identity(),
    )
    assert len(lines) == 2
    assert {line.method for line in lines} == {"vector"}


def test_real_raster_image_adapter_when_opencv_available(tmp_path):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    from linkoteq_drawing_reconstruction.line_extraction import extract_raster_lines_from_image

    frame = np.full((256, 256, 3), 255, dtype=np.uint8)
    cv2.line(frame, (20, 64), (236, 64), (0, 0, 0), 2)
    cv2.line(frame, (128, 20), (128, 236), (0, 0, 0), 2)
    path = tmp_path / "drawing.png"
    assert cv2.imwrite(str(path), frame)

    settings = RasterLineSettings(
        canny_threshold1=40,
        canny_threshold2=120,
        hough_threshold=30,
        min_line_length=80,
        max_line_gap=5,
    )
    first = extract_raster_lines_from_image(
        path,
        source=raster_source(),
        source_to_normalized=Affine2D.identity(),
        settings=settings,
    )
    second = extract_raster_lines_from_image(
        path,
        source=raster_source(),
        source_to_normalized=Affine2D.identity(),
        settings=settings,
    )
    assert first
    assert first == second
    assert {line.method for line in first} == {"hough"}
