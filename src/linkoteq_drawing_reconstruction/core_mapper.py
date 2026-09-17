"""Boundary mapper from reviewed reconstruction facts to Core v0.5 records.""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .member_writeback import ResolvedMemberEvidence, to_core_member
from .transforms import Point2D, SourceToModelTransform, UnresolvedTransformError

CORE_SCHEMA_VERSION = "0.5"


class CoreMappingError(ValueError):
    """Raised when reconstruction facts do not satisfy Core writeback gates."""


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


def _require_stable_ids(records: Sequence[object], record_name: str) -> None:
    ids: list[str] = []
    for record in records:
        value = getattr(record, "id", None)
        if not isinstance(value, str) or not value.strip():
            raise CoreMappingError(f"{record_name} requires a non-empty stable id.")
        ids.append(value)
    if len(ids) != len(set(ids)):
        raise CoreMappingError(f"Duplicate {record_name} ids are not allowed.")


def _vec3(point) -> dict[str, float]:
    return {"x": point.x, "y": point.y, "z": point.z}


def map_minimal_structural_model(
    *,
    project: CoreProjectContext,
    transform: SourceToModelTransform,
    levels: Sequence[AcceptedLevel] = (),
    grids: Sequence[AcceptedGridLine] = (),
    nodes: Sequence[AcceptedNode] = (),
    members: Sequence[ResolvedMemberEvidence] = (),
) -> dict:
    """Map only reviewed and resolved facts to Core v0.5."""
    if not transform.is_resolved:
        raise UnresolvedTransformError("Core mapping is blocked until T_source_to_model is fully resolved.")

    _require_stable_ids(levels, "Level")
    _require_stable_ids(grids, "GridLine")
    _require_stable_ids(nodes, "Node")
    _require_stable_ids(members, "Member")

    level_ids = {level.id for level in levels}
    node_ids = {node.id for node in nodes}

    mapped_grids = []
    for grid in grids:
        start = transform.to_model_point(grid.source_start)
        end = transform.to_model_point(grid.source_end)
        if start == end:
            raise CoreMappingError(f"GridLine {grid.id!r} collapses to zero length.")
        mapped_grids.append({"id": grid.id, "label": grid.label, "start": _vec3(start), "end": _vec3(end)})

    mapped_nodes = []
    for node in nodes:
        if node.level_id is not None and node.level_id not in level_ids:
            raise CoreMappingError(f"Node {node.id!r} references unknown levelId {node.level_id!r}.")
        position = transform.to_model_point(node.source_position)
        record = {"id": node.id, "position": _vec3(position)}
        if node.level_id is not None:
            record["levelId"] = node.level_id
        mapped_nodes.append(record)

    mapped_members = []
    for member in members:
        record = to_core_member(member)
        if record["startNodeId"] not in node_ids or record["endNodeId"] not in node_ids:
            raise CoreMappingError(f"Member {member.id!r} references unknown structural node.")
        mapped_members.append(record)

    return {
        "schemaVersion": CORE_SCHEMA_VERSION,
        "project": {"id": project.id, "name": project.name, "units": project.units},
        "levels": [{"id": l.id, "name": l.name, "elevation": l.elevation} for l in levels],
        "grids": mapped_grids,
        "nodes": mapped_nodes,
        "members": mapped_members,
        "surfaces": [], "diaphragms": [], "materials": [], "sections": [],
        "supports": [], "loadCases": [], "loads": [], "loadCombinations": [],
    }
