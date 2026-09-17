import pytest

from linkoteq_drawing_reconstruction.grid_geometry import GridAxisCandidate
from linkoteq_drawing_reconstruction.grid_labeling import (
    BoundingBox2D,
    OcrLabelEvidence,
    associate_grid_labels,
    normalize_grid_label,
)
from linkoteq_drawing_reconstruction.transforms import Point2D


def axis(axis_id, start, end):
    return GridAxisCandidate(
        id=axis_id,
        source_id="drawing-1",
        page_id="page-1",
        start=Point2D(*start),
        end=Point2D(*end),
        method="vector",
        confidence=1.0,
    )


def evidence(evidence_id, text, center, *, confidence=0.95):
    x, y = center
    return OcrLabelEvidence(
        id=evidence_id,
        source_id="drawing-1",
        page_id="page-1",
        text=text,
        bbox=BoundingBox2D(Point2D(x - 1, y - 1), Point2D(x + 1, y + 1)),
        confidence=confidence,
        engine="fixture-ocr",
        engine_version="1.0",
        region_kind="grid-bubble",
    )


def test_normalize_grid_label_changes_typography_only():
    assert normalize_grid_label("  a  1 ") == "A1"
    assert normalize_grid_label("Ａ１") == "A1"
    assert normalize_grid_label("O1") == "O1"
    assert normalize_grid_label("01") == "01"


def test_association_is_deterministic_and_preserves_raw_ocr_evidence():
    axes = [axis("gx-1", (0, 0), (100, 0))]
    raw = evidence("ocr-1", " a 1 ", (0, 5))
    result = associate_grid_labels(axes, [raw], max_endpoint_distance=10)
    assert len(result) == 1
    assert result[0].label == "A1"
    assert result[0].label_evidence_id == "ocr-1"
    assert result[0].status == "auto-accepted"
    assert raw.text == " a 1 "


def test_competing_nearby_labels_require_review():
    axes = [axis("gx-1", (0, 0), (100, 0))]
    items = [
        evidence("ocr-a", "A", (0, 4)),
        evidence("ocr-b", "B", (0, 4.5)),
    ]
    result = associate_grid_labels(
        axes,
        items,
        max_endpoint_distance=10,
        ambiguity_ratio=1.25,
    )
    assert result[0].status == "review-required"
    assert result[0].competing_evidence_ids == ("ocr-b",)


def test_duplicate_normalized_labels_require_review():
    axes = [
        axis("gx-1", (0, 0), (100, 0)),
        axis("gx-2", (0, 50), (100, 50)),
    ]
    items = [
        evidence("ocr-1", "A", (0, 2)),
        evidence("ocr-2", " a ", (0, 52)),
    ]
    result = associate_grid_labels(axes, items, max_endpoint_distance=10)
    assert {item.status for item in result} == {"review-required"}
    assert {item.label for item in result} == {"A"}


def test_low_confidence_label_is_not_auto_accepted():
    axes = [axis("gx-1", (0, 0), (100, 0))]
    result = associate_grid_labels(
        axes,
        [evidence("ocr-1", "A", (0, 3), confidence=0.5)],
        max_endpoint_distance=10,
        min_ocr_confidence=0.75,
    )
    assert result[0].status == "review-required"
