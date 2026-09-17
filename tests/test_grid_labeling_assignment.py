from linkoteq_drawing_reconstruction.grid_geometry import GridAxisCandidate
from linkoteq_drawing_reconstruction.grid_labeling import BoundingBox2D, OcrLabelEvidence, associate_grid_labels
from linkoteq_drawing_reconstruction.transforms import Point2D


def axis(aid, y):
    return GridAxisCandidate(aid, "f", Point2D(0, y), Point2D(100, y), ("s",), 100.0, 1.0, 0.0, 0.0)


def ocr(eid, text, x, y):
    return OcrLabelEvidence(
        eid, "src", "p1", text,
        BoundingBox2D(Point2D(x - 1, y - 1), Point2D(x + 1, y + 1)),
        0.95, "fixture-ocr", "1.0", "grid-bubble",
    )


def test_single_ocr_observation_cannot_label_two_axes():
    result = associate_grid_labels(
        (axis("a1", 0), axis("a2", 2)),
        (ocr("e1", "A", 0, 1),),
        max_endpoint_distance=5,
    )
    assigned = [x for x in result if x.label_evidence_id == "e1"]
    assert len(assigned) == 1
    assert sum(x.status == "review-required" for x in result) >= 1


def test_assignment_is_deterministic_under_input_reordering():
    axes = (axis("a2", 2), axis("a1", 0))
    evidence = (ocr("e2", "B", 0, 2), ocr("e1", "A", 0, 0))
    first = associate_grid_labels(axes, evidence, max_endpoint_distance=5)
    second = associate_grid_labels(tuple(reversed(axes)), tuple(reversed(evidence)), max_endpoint_distance=5)
    assert first == second
