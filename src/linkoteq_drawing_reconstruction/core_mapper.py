from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .member_writeback import ResolvedMemberEvidence, to_core_member
from .transforms import Point2D, SourceToModelTransform, UnresolvedTransformError

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
    return {"x": point.x, "y": point.y, "z": point.zm
