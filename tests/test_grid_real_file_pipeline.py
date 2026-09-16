import pytest

from linkoteq_drawing_reconstruction.grid_geometry import reconstruct_grid_geometry
from linkoteq_drawing_reconstruction.line_extraction import (
    RasterLineSettings,
    extract_lines_from_pdf,
    extract_raster_lines_from_image,
)
from linkoteq_drawing_reconstruction.source_normalization import SourcePageMetadata
from linkoteq_drawing_reconstruction.transforms import Affine2D


def _assert_reconstructed_grid(result):
    # Real-file detectors may emit multiple edge-segments per drawn axis.
    # Stage C acceptance here is intentionally geometric: both dominant
    # orientation families survive filtering, axes are reconstructed, and they
    # produce cross-family intersections.
    assert len(result.families) >= 2
    assert len(result.axes) >= 4
    assert result.intersections


def test_real_vector_pdf_to_reconstructed_grid(tmp_path):
    fitz = pytest.importorskip("fitz")

    path = tmp_path / "vector-grid.pdf"
    doc = fitz.open()
    page = doc.new_page(width=400, height=400)
    for y in (100.0, 200.0, 300.0):
        page.draw_line((20.0, y), (380.0, y), width=1)
    for x in (100.0, 200.0, 300.0):
        page.draw_line((x, 20.0), (x, 380.0), width=1)
    doc.save(path)
    doc.close()

    source = SourcePageMetadata.create(
        source_id="real-vector-grid",
        page_id="real-vector-grid:p1",
        page_index=0,
        width=400.0,
        height=400.0,
        has_vector_geometry=True,
        has_raster_content=False,
        media_type="application/pdf",
    )
    evidence = extract_lines_from_pdf(
        path,
        page_index=0,
        source=source,
        source_to_normalized=Affine2D.identity(),
    )
    result = reconstruct_grid_geometry(
        evidence,
        min_axis_length=300.0,
        collinear_tolerance=1.0,
        gap_tolerance=5.0,
    )
    _assert_reconstructed_grid(result)


def test_real_raster_image_to_reconstructed_grid(tmp_path):
    cv 2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")

    frame = np.full((400, 400, 3), 255, dtype=np.uint8)
    for y in (100, 200, 300):
        cv 2.line(frame, (20, y), (380, y), (0, 0, 0), 1)
    for x in (100, 200, 300):
        cv 2.line(frame, (x, 20), (x, 380), (0, 0, 0), 1)
    path = tmp_path / "raster-grid.png"
    assert cv 2.imwrite(str(path), frame)

    source = SourcePageMetadata.create(
        source_id="real-raster-grid",
        page_id="real-raster-grid:p1",
        page_index=0,
        width=400.0,
        height=400.0,
        has_vector_geometry=False,
        has_raster_content=True,
        dpi=200.0,
        media_type="image/png",
    )
    settings = RasterLineSettings(
        canny_threshold1=40,
        canny_threshold2=120,
        hough_threshold=50,
        min_line_length=250,
        max_line_gap=5,
    )
    evidence = extract_raster_lines_from_image(
        path,
        source=source,
        source_to_normalized=Affine2D.identity(),
        settings=settings,
    )
    result = reconstruct_grid_geometry(
        evidence,
        min_axis_length=250.0,
        collinear_tolerance=3.0,
        gap_tolerance=10.0,
    )
    _assert_reconstructed_grid(result)
