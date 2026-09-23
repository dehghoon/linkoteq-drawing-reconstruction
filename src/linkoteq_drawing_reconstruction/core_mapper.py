from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .member_writeback import ResolvedMemberEvidence, to_core_member
from .transforms import Point2D, SourceToModelTransform
from .wall_reconstruction import ResolvedWallSurface

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

@dataclass(frozen=True)
class AcceptedNode:
    id: str
    source_position: Point2D
    level_id: str | None = None

@dataclass(frozen=True)
class CoreProjectContext:
    id: str
    name: str
    units: Literal["SI", "US"]

def _require_stable_ids(records, record_name: str) -> None:
    ids: list[str] = []
    for record in records:
        value = getattr(record, "id", None)
        if not isinstance(value, str) or not value.strip():
            raise CoreMappingError(f"{record_name} requires a non-empty stable id.")
        ids.append(value)
    if len(ids) != len(set(ids)):
        raise CoreMappingError(f"Duplicate {record_name} ids are not allowed.")

def _vec3(point: object) -> dict[str, float]:
    return {"x": point.x, "y": point.y, "z": point.zm

def _core_surface(surface: ResolvedWallSurface) -> dict[str, object]:
    if not surface.id.strip() or not surface.level_id.strip():
        raise CoreMappingError("Wall Surface requires stable id and levelId.")
    if not surface.provenance or not surface.basis:
        raise CoreMappingError("Wall Surface requires traceable reconstruction basis and provenance.")
    return {
        "id": surface.id,
        "type": "wall",
        "boundaryNodeIds": [f"{surface.id}:boundary:{i}" for i in range(4)],
        "levelId": surface.level_id,
        "thickness": {"value": surface.thickness, "unit": surface.length_unit},
    }

def map_minimal_structural_model(
    *,
    project: CoreProjectContext,
    transform: SourceToModelTransform,
    levels: list[AcceptedLevel] | tuple[AcceptedLevel, ...] = (),
    grids: list[AcceptedGridLine] | tuple[AcceptedGridLine, ...] = (),
    nodes: list[AcceptedNode] | tuple[AcceptedNode, ...] = (),
    members: list[ResolvedMemberEvidence] | tuple[ResolvedMemberEvidence, ...] = (),
    surfaces: list[ResolvedWallSurface] | tuple[ResolvedWallSurface, ...] = (),
) -> dict[str, object]:
    """Map reviewed reconstruction facts to the Core v0.5 StructuralModel boundary."""
    if not transform.is_resolved:
        transform.to_model_point(Point2D(0.0, 0.0))

    _require_stable_ids(levels, "Level")
    _require_stable_ids(grids, "GridLine")
    _require_stable_ids(nodes, "Node")
    _require_stable_ids(surfaces, "Surface")

    level_ids = {level.id for level in levels}
    for node in nodes:
        if node.level_id is not None and node.level_id not in level_ids:
            raise CoreMappingError(f"Node {node.id!r} references unknown levelId {node.level_id!r}.")
    for surface in surfaces:
        if surface.level_id not in level_ids:
            raise CoreMappingError(f"Surface {surface.id!r} references unknown levelId {surface.level_id!r}.")
        if transform.source_id != surface.source_id or transform.page_id != surface.page_id:
            raise CoreMappingError(
                f"Surface {surface.id!r} provenance does not match the active source/page transform."
            )
        if surface.length_unit != transform.project_length_unit:
            raise CoreMappingError(f"Surface {surface.id!r} length unit does not match the resolved transform.")

    core_levels = [{"id": level.id, "name": level.name, "elevation": level.elevation} for level in levels]
    core_grids = []
    for grid in grids:
        start = transform.to_model_point(grid.source_start)
        end = transform.to_model_point(grid.source_end)
        core_grids.append({"id": grid.id, "label": grid.label, "start": _vec3(start), "end": _vec3(end)})

    core_nodes = []
    for node in nodes:
        position = transform.to_model_point(node.source_position)
        item: dict[str, object] = {"id": node.id, "position": _vec3(position)}
        if node.level_id is not None:
            item["levelId"] = node.level_id
        core_nodes.append(item)

    core_members = [to_core_member(member) for member in members]
    core_surfaces = []
    generated_node_ids = set(node.id for node in nodes)
    for surface in surfaces:
        boundary_ids = [f"{surface.id}:boundary:{i}" for i in range(4)]
        if generated_node_ids.intersection(boundary_ids):
            raise CoreMappingError(f"Surface {surface.id!r} boundary node ids collide with existing nodes.")
        for node_id, point in zip(boundary_ids, surface.boundary_points):
            core_nodes.append({"id": node_id, "position": _vec3(point), "levelId": surface.level_id})
            generated_node_ids.add(node_id)
        core_surfaces.append(_core_surface(surface))

    return {
        "schemaVersion": CORE_SCHEMA_VERSION,
        "project": {"id": project.id, "name": project.name, "units": project.units},
        "levels": core_levels,
        "grids": core_grids,
        "nodes": core_nodes,
        "members": core_members,
        "surfaces": core_surfaces,
        "diaphragms": [],
        "materials": [],
        "sections": [],
        "supports": [],
        "loadCases": [],
        "loads": [],
        "loadCombinations": [],
    }
