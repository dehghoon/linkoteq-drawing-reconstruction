"""Real-file line extraction adapters for Stage C grid reconstruction.

Vector/mixed PDF pages prefer native PDF line primitives. Raster images and raster-only
PDF pages use a deterministic Canny + Probabilistic Hough adapter. All emitted
LineSegmentEvidence is transformed into normalized drawing coordinates. This module
does not run OCR/YOLO, infer engineering scale, emit Core geometry, or call a solver.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from importlib import import_module
from math import pi
from pathlib import Path
from typing import Any, Iterable, Sequence

from .grid_geometry import LineSegmentEvidence
from .source_normalization import SourcePageMetadata
from .transforms import Affine2D, Point2D, Transform2D


class LineExtractionError(RuntimeError):
    """Raised when a real-file line adapter cannot produce valid evidence."""


@dataclass(frozen=True)
class RasterLineSettings:
    canny_threshold1: float = 50.0
    canny_threshold2: float = 150.0
    hough_rho: float = 1.0
    hough_theta_deg: float = 1.0
    hough_threshold: int = 80
    min_line_length: float = 50.0
    max_line_gap: float = 10.0
    render_dpi: float = 150.0

    def __post_init__(self) -> None:
        if not (0.0 < self.canny_threshold1 < self.canny_threshold2):
            raise LineExtractionError("Canny thresholds must satisfy 0 < t1 < t2.")
        if self.hough_rho <= 0.0 or self.hough_theta_deg <= 0.0:
            raise LineExtractionError("Hough rho/theta must be positive.")
        if self.hough_threshold <= 0 or self.min_line_length <= 0.0 or self.max_line_gap < 0.0:
            raise LineExtractionError(
                "Hough threshold/min_line_length must be positive and max_line_gap non-negative."
            )
        if self.render_dpi <= 0.0:
            raise LineExtractionError("render_dpi must be positive.")


def _fitz() -> Any:
    try:
        return import_module("fitz")
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise LineExtractionError(
            "PyMuPDF is required for PDF line extraction; install the project 'pdf' extra."
        ) from exc


def _cv2() -> Any:
    try:
        return import_module("cv2")
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise LineExtractionError(
            "OpenCV is required for raster line extraction; install the project 'raster' extra."
        ) from exc


def _numpy() -> Any:
    try:
        return import_module("numpy")
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise LineExtractionError(
            "NumPy is required for raster line extraction; install the project 'raster' extra."
        ) from exc


def _ordered(start: Point2D, end: Point2D) -> tuple[Point2D, Point2D]:
    return (start, end) if (start.x, start.y) <= (end.x, end.y) else (end, start)


def _stable_segment_id(
    source_id: str,
    page_id: str,
    method: str,
    start: Point2D,
    end: Point2D,
) -> str:
    payload = (
        f"{source_id}|{page_id}|{method}|"
        f"{start.x:.6f},{start.y:.6f}|{end.x:.6f},{end.y:.6f}"
    ).encode("utf-8")
    return f"line-{sha1(payload).hexdigest()[:16]}"


def _make_evidence(
    *,
    source: SourcePageMetadata,
    method: str,
    start: Point2D,
    end: Point2D,
    source_to_normalized: Transform2D,
    confidence: float = 1.0,
) -> LineSegmentEvidence:
    normalized_start = source_to_normalized.apply(start)
    normalized_end = source_to_normalized.apply(end)
    normalized_start, normalized_end = _ordered(normalized_start, normalized_end)
    if normalized_start == normalized_end:
        raise LineExtractionError("A transformed line segment collapsed to zero length.")
    return LineSegmentEvidence(
        id=_stable_segment_id(
            source.source_id,
            source.page_id,
            method,
            normalized_start,
            normalized_end,
        ),
        source_id=source.source_id,
        page_id=source.page_id,
        start=normalized_start,
        end=normalized_end,
        method=method,  # type: ignore[arg-type]
        confidence=confidence,
    )


def _dedupe_and_sort(
    items: Iterable[LineSegmentEvidence],
) -> tuple[LineSegmentEvidence, ...]:
    unique: dict[str, LineSegmentEvidence] = {}
    for item in items:
        unique[item.id] = item
    return tuple(
        sorted(
            unique.values(),
            key=lambda s: (s.start.x, s.start.y, s.end.x, s.end.y, s.id),
        )
    )


def extract_vector_lines_from_pdf(
    pdf_path: str | Path,
    *,
    page_index: int,
    source: SourcePageMetadata,
    source_to_normalized: Transform2D,
) -> tuple[LineSegmentEvidence, ...]:
    """Extract native straight-line PDF primitives as normalized evidence."""
    if page_index != source.page_index:
        raise LineExtractionError("page_index must match source metadata.")
    if not source.has_vector_geometry or source.source_space != "vector":
        raise LineExtractionError(
            "Native PDF vector extraction requires vector source metadata."
        )

    fitz = _fitz()
    document = fitz.open(str(pdf_path))
    try:
        if page_index < 0 or page_index >= len(document):
            raise LineExtractionError("PDF page_index is out of range.")
        page = document[page_index]
        rect = page.rect
        if (
            abs(float(rect.width) - source.width) > 1e-6
            or abs(float(rect.height) - source.height) > 1e-6
        ):
            raise LineExtractionError(
                "PDF page dimensions do not match vector source metadata."
            )

        evidence: list[LineSegmentEvidence] = []
        for drawing in page.get_drawings():
            for item in drawing.get("items", ()):
                if not item or item[0] != "l":
                    continue
                p1, p2 = item[1], item[2]
                start = Point2D(float(p1.x), float(p1.y))
                end = Point2D(float(p2.x), float(p2.y))
                if start == end:
                    continue
                evidence.append(
                    _make_evidence(
                        source=source,
                        method="vector",
                        start=start,
                        end=end,
                        source_to_normalized=source_to_normalized,
                    )
                )
        return _dedupe_and_sort(evidence)
    finally:
        document.close()


def _hough_lines(
    frame: Any,
    settings: RasterLineSettings,
) -> Sequence[tuple[float, float, float, float]]:
    cv2 = _cv2()
    np = _numpy()
    if len(frame.shape) == 3:
        if frame.shape[2] == 4:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    edges = cv2.Canny(
        gray,
        settings.canny_threshold1,
        settings.canny_threshold2,
    )
    lines = cv2.HoughLinesP(
        edges,
        settings.hough_rho,
        np.deg2rad(settings.hough_theta_deg),
        settings.hough_threshold,
        minLineLength=settings.min_line_length,
        maxLineGap=settings.max_line_gap,
    )
    if lines is None:
        return ()
    result = []
    for row in lines:
        x1, y1, x2, y2 = row[0]
        result.append((float(x1), float(y1), float(x2), float(y2)))
    result.sort()
    return tuple(result)


def _raster_evidence(
    *,
    frame: Any,
    source: SourcePageMetadata,
    pixel_to_normalized: Transform2D,
    settings: RasterLineSettings,
) -> tuple[LineSegmentEvidence, ...]:
    evidence = []
    for x1, y1, x2, y2 in _hough_lines(frame, settings):
        evidence.append(
            _make_evidence(
                source=source,
                method="hough",
                start=Point2D(x1, y1),
                end=Point2D(x2, y2),
                source_to_normalized=pixel_to_normalized,
            )
        )
    return _dedupe_and_sort(evidence)


def extract_raster_lines_from_image(
    image_path: str | Path,
    *,
    source: SourcePageMetadata,
    source_to_normalized: Transform2D,
    settings: RasterLineSettings = RasterLineSettings(),
) -> tuple[LineSegmentEvidence, ...]:
    """Extract Hough line evidence from a real raster image file."""
    if source.source_space != "pixel" or not source.has_raster_content:
        raise LineExtractionError(
            "Raster image extraction requires pixel source space and raster content."
        )
    cv2 = _cv2()
    frame = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if frame is None:
        raise LineExtractionError(f"Could not read raster image: {image_path!s}")
    height, width = frame.shape[:2]
    if width != int(round(source.width)) or height != int(round(source.height)):
        raise LineExtractionError(
            "Image dimensions do not match pixel source metadata."
        )
    return _raster_evidence(
        frame=frame,
        source=source,
        pixel_to_normalized=source_to_normalized,
        settings=settings,
    )


def extract_raster_lines_from_pdf(
    pdf_path: str | Path,
    *,
    page_index: int,
    source: SourcePageMetadata,
    source_to_normalized: Transform2D,
    settings: RasterLineSettings = RasterLineSettings(),
) -> tuple[LineSegmentEvidence, ...]:
    """Rasterize a PDF page deterministically and map Hough pixels to normalized geometry.

    For pixel-space source metadata, the PDF is rendered to exactly source.width x
    source.height pixels. For vector-space metadata, render pixels are mapped back to
    PDF page coordinates before applying source_to_normalized.
    """
    if page_index != source.page_index:
        raise LineExtractionError("page_index must match source metadata.")
    fitz = _fitz()
    np = _numpy()
    cv2 = _cv2()
    document = fitz.open(str(pdf_path))
    try:
        if page_index < 0 or page_index >= len(document):
            raise LineExtractionError("PDF page_index is out of range.")
        page = document[page_index]
        rect = page.rect

        if source.source_space == "vector":
            if (
                abs(float(rect.width) - source.width) > 1e-6
                or abs(float(rect.height) - source.height) > 1e-6
            ):
                raise LineExtractionError(
                    "PDF page dimensions do not match vector source metadata."
                )
            zoom = settings.render_dpi / 72.0
            pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            pixel_to_source = Affine2D.from_rows(
                (
                    (float(rect.width) / pixmap.width, 0.0, 0.0),
                    (0.0, float(rect.height) / pixmap.height, 0.0),
                    (0.0, 0.0, 1.0),
                )
            )
            pixel_to_normalized = pixel_to_source.then(source_to_normalized)
        else:
            target_width = int(round(source.width))
            target_height = int(round(source.height))
            if target_width <= 0 or target_height <= 0:
                raise LineExtractionError("Pixel source dimensions must be positive.")
            matrix = fitz.Matrix(
                target_width / float(rect.width),
                target_height / float(rect.height),
            )
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            if pixmap.width != target_width or pixmap.height != target_height:
                raise LineExtractionError(
                    "PDF rasterization did not match declared pixel source dimensions."
                )
            pixel_to_normalized = source_to_normalized

        frame = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height,
            pixmap.width,
            pixmap.n,
        )
        if pixmap.n == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGRA)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return _raster_evidence(
            frame=frame,
            source=source,
            pixel_to_normalized=pixel_to_normalized,
            settings=settings,
        )
    finally:
        document.close()


def extract_lines_from_pdf(
    pdf_path: str | Path,
    *,
    page_index: int,
    source: SourcePageMetadata,
    source_to_normalized: Transform2D,
    settings: RasterLineSettings = RasterLineSettings(),
) -> tuple[LineSegmentEvidence, ...]:
    """Select the Stage C adapter: native vector first, raster fallback otherwise."""
    if source.has_vector_geometry:
        return extract_vector_lines_from_pdf(
            pdf_path,
            page_index=page_index,
            source=source,
            source_to_normalized=source_to_normalized,
        )
    if source.has_raster_content:
        return extract_raster_lines_from_pdf(
            pdf_path,
            page_index=page_index,
            source=source,
            source_to_normalized=source_to_normalized,
            settings=settings,
        )
    raise LineExtractionError("PDF source metadata has neither vector nor raster content.")
