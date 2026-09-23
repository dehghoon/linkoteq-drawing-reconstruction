import pytest

from linkoteq_drawing_reconstruction.core_mapper import AcceptedLevel, CoreProjectContext, map_minimal_structural_model
from linkoteq_drawing_reconstruction.structural_detection import SourceBox2D, StructuralDetectionEvidence, StructuralDetectionError
from linkoteq_drawing_reconstruction.transforms import Affine2D, CalibrationEvidence, Point2D, SourceToModelTransform
from linkoteq_drawing_reconstruction.wall_reconstruction import WallEngineeringEvidence, reconstruct_wall


def detection():
    return StructuralDetectionEvidence(
        id="det-wall-1", source_id="drawing-1", page_id="page-1", class_name="wall",
        confidence=0.9, source_box=SourceBox2D(0, 0, 100, 20), coordinate_space="source-page",
        model_name="detector", model_version="1", provenance="run://1/model://1",
        state="review-required", contract_version="0.2",
    )


def transform(resolved=True):
    return SourceToModelTransform(
        source_id="drawing-1", page_id="page-1", source_space="vector",
        source_to_normalized=Affine2D.identity(),
        normalized_to_model_xy=Affine2D.identity() if resolved else None,
        model_z=0.0 if resolved else None,
        project_length_unit="m" if resolved else None,
        calibration=CalibrationEvidence(method="user-calibration", length_unit="m") if resolved else None,
    )


def engineering(**changes):
    values = dict(
        wall_id="wall-1", centerline_start=Point2D(1, 2), centerline_end=Point2D(5, 2),
        thickness=0.2, level_id="L1", bottom_elevation=0.0, top_elevation=3.0,
        basis=("dimension-line", "section-A"), provenance=("drawing-1/page-1/dim-7",),
    )
    values.update(changes)
    return WallEngineeringEvidence(**values)


def test_detector_bbox_alone_and_plan_detection_cannot_create_surface():
    decision = reconstruct_wall(
        detection=detection(),
        engineering=engineering(centerline_start=None, centerline_end=None, thickness=None,
                                level_id=None, bottom_elevation=None, top_elevation=None),
        transform=transform(), review_state="approved",
    )
    assert decision.state == "review-required"
    assert decision.surface is None
    assert any("centerline" in x for x in decision.reasons)
    assert any("vertical extent" in x for x in decision.reasons)


def test_unresolved_scale_and_unapproved_review_block_wall_writeback():
    unresolved = reconstruct_wall(detection=detection(), engineering=engineering(), transform=transform(False), review_state="approved")
    assert unresolved.state == "review-required" and unresolved.surface is None
    unapproved = reconstruct_wall(detection=detection(), engineering=engineering(), transform=transform(), review_state="review-required")
    assert unapproved.state == "review-required" and unapproved.surface is None


def test_v01_wall_rejected_and_v02_wall_accepted():
    with pytest.raises(StructuralDetectionError):
        StructuralDetectionEvidence(
            id="x", source_id="s", page_id="p", class_name="wall", confidence=.8,
            source_box=SourceBox2D(0,0,1,1), coordinate_space="source-page",
            model_name="m", model_version="1", provenance="run://x", contract_version="0.1",
        )
    assert detection().class_name == "wall"


def test_reviewed_reconstructed_wall_maps_to_core_surface_with_traceable_nodes():
    decision = reconstruct_wall(detection=detection(), engineering=engineering(), transform=transform(), review_state="approved")
    assert decision.state == "eligible"
    assert decision.surface is not None
    assert decision.surface.origin == "reconstructed"
    assert decision.surface.detection_evidence_id == "det-wall-1"
    model = map_minimal_structural_model(
        project=CoreProjectContext(id="p", name="P", units="SI"),
        transform=transform(), levels=(AcceptedLevel(id="L1", name="Level 1", elevation=0.0),),
        surfaces=(decision.surface,),
    )
    surface = model["surfaces"][0]
    assert surface["type"] == "wall"
    assert surface["thickness"] == {"value": 0.2, "unit": "m"}
    assert len(surface["boundaryNodeIds"]) == 4
    assert set(surface["boundaryNodeIds"]) <= {n["id"] for n in model["nodes"]}
    assert model["nodes"][2]["position"]["z"] == 3.0
