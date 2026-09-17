from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .member_writeback import ResolvedMemberEvidence, to_core_member
from .transforms import Point2D, SourceToModelTransform

CORE_SCHEMA_VERSION = "0.5"


class CoreMappingError(ValueError):
    pass


@dataclass(frozen=True)
class AcceptedLevel:
    id: str
    name: str
    elevation: float


@dataclass(frozen=True)
class AcceptedGridLine:
    id: str
    label: str
    source_start: Point2D
    source_end: Point2D


@dataclas(frozen=True)
class AcceptedNode:
    id: str
    source_position: Point2D
    level_id: str | None = None


@dataclass(frozen=True)
class CoreProjectContext:
    id: str
    name: str
    units: Literal["SI", "US"]


def _require_stable_ids(records: Sequence[object], record_name: str) -> None:
    ids: list[str] = []
    for record in records:
        value = getattr(record, "id", None)
        if not isinstance(value, str) or not value.strip():
            raise CoreMappingError(f"{record_name} requires a non-empty stable id.")
        ids.append(value)
    if len(ids) != len(set(ids)):
        raise CoreMappingError(f"Duplicate {record_name} ids are not allowed.")


def _vec3(point: object) -> dict[str, float]:
    return {"x": point.x, "y": point.y, "z": point.z}


def map_minimal_structural_model(
    *,
    project: CoreProjectContext,
    transform: SourceToModelTransform,
    levels: Sequence[AcceptedLevel] = (),
    grids: Sequence[AcceptedGridLine] = (),
    nodes: Sequence[AcceptedNode] = (),
    members: Sequence[ResolvedMemberEvidence] = (),
) -> dict[str, object]:
    """Map reviewed reconstruction facts to the Core v0.5 StructuralModel boundary."""
    if not transform.is_resolved:
        # Preserve the transform module's canonical unresolved-scale error.
        transform.to_model_point(Point2D(0.0, 0.0))

    _require_stable_ids(levels, "Level")
    _require_stable_ids(grids, "GridLine")
    _require_stable_ids(nodes, "Node")

    level_ids = {level.id for level in levels}
    for node in nodes:
        if node.level_id is not None and node.level_id not in level_ids:
            raise CoreMappingError(f"Node {node.id!r} references unknown levelId {node.level_id!r}.")

    core_levels = [
        {"id": level.id, "name": level.name, "elevation": level.elevation}
        for level in levels
    ]
    core_grids = []
    for grid in grids:
        start = transform.to_model_point(grid.source_start)
        end = transform.to_model_point(grid.source_end)
        core_grids.append(
            {"id": grid.id, "label": grid.label, "start": _vec3(start), "end": _vec3(end)}
        )

    core_nodes = []
    for node in nodes:
        position = transform.to_model_point(node.source_position)
        item: dict[str, object] = {"id": node.id, "position": _vec3(position)}
        if node.level_id is not None:
            item["levelId"] = node.level_id
        core_nodes.append(item)

    core_members = [to_core_member(member) for member in members]

    return {
        "schemaVersion": CORE_SCHEMA_VERSION,
        "project": {"id": project.id, "name": project.name, "units": project.units},
        "levels": core_levels,
        "grids": core_grids,
        "nodes": core_nodes,
        "members": core_members,
        "surfaces": [],
        "diaphragms": [],
        "materials": [],
        "sections": [],
        "supports": [],
        "loadCases": [],
        "loads": [],
        "loadCombinations": [],
    }
