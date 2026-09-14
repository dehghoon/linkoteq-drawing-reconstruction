import json
from pathlib import Path

import pytest

from linkoteq_drawing_reconstruction.core_mapper import (
    CORE_SCHEMA_VERSION,
    AcceptedGridLine,
    AcceptedLevel,
    AccceptedNode,
    CoreMappingError,
    CoreProjectContext,
    map_minimal_structural_model,
)
from linkoteq_drawing_reconstruction.transforms import (
    Affine2D,
    CalibrationEvidence,
    Point2D,
    SourceToModelTransform,
    UnresolvedTransformError,
)


def transform() -> SourceToModelTransform:
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


def test_core_version_is_current_runtime_contract():
    assert CORE_SCHEMA_VERSION == "0.5"


def test_minimal_mapping_matches_core_v0_5_fixture():
    actual = map_minimal_structural_model(
        project=CoreProjectContext(
            id="project-fixture-001", name="Foundation Fixture", units="SI"
        ),
        transform=transform(),
        levels=(AcceptedLevel(id="level-L1", name="Level 1", elevation=3.5),),
        grids=(
            AcceptedGridLine(
                id="grid-A",
                label="A",
                source_start=Point2D(100.0, 200.0),
                source_end=Point2D(300.0, 200.0),
            ),
        ),
        nodes=(
            AcceptedNode(
                id="node-A1",
                source_position=Point2D(100.0, 200.0),
                level_id="level-L1",
            ),
        ),
    )
    expected = json.loads(
        (Path(__file__).parent / "fixtures" / "core_v0_5_minimal_model.json").read_text()
    )
    assert actual == expected


def test_private_source_geometry_does_not_cross_core_boundary():
    model = map_minimal_structural_model(
        project=CoreProjectContext(id="p", name="P", units="SI"),
        transform=transform(),
        grids=(
            AcceptedGridLine(
                id="g", label="1", source_start=Point2D(0, 0), source_end=Point2D(10, 0)
            ),
        ),
    )
    serialized = json.dumps(model)
    assert "source_start" not in serialized
    assert "source_end" not in serialized
    assert "pixel" not in serialized


def test_unresolved_transform_blocks_core_mapping():
    unresolved = SourceToModelTransform(
        source_id="drawing-001",
        page_id="page-1",
        source_space="pixel",
        source_to_normalized=Affine2D.identity(),
    )
    with pytest.raises(UnresolvedTransformError):
        map_minimal_structural_model(
            project=CoreProjectContext(id="p", name="P", units="SI"),
            transform=unresolved,
        )


def test_duplicate_ids_and_unknown_level_refs_are_rejected():
    with pytest.raises(CoreMappingError, match="Duplicate Node"):
        map_minimal_structural_model(
            project=CoreProjectContext(id="p", name="P", units="SI"),
            transform=transform(),
            nodes=(
                AccceptedNode(id="n", source_position=Point2D(0, 0)),
                AcceptedNode(id="n", source_position=Point2D(1, 1)),
            ),
        )

    with pytest.raises(CoreMappingError, match="unknown levelId"):
        map_minimal_structural_model(
            project=CoreProjectContext(id="p", name="P", units="SI"),
            transform=transform(),
            nodes=(
                AcceptedNode(id="n", source_position=Point2D(0, 0), level_id="missing"),
            ),
        )


def test_foundation_mapper_does_not_invent_members_materials_or_sections():
    model = map_minimal_structural_model(
        project=CoreProjectContext(id="p", name="P", units="SI"),
        transform=transform(),
    )
    assert model["members"] == []
    assert model["materials"] == []
    assert model["sections"] == []
