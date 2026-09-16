"""Gates for canonical Core v0.5 Member writeback."""
from __future__ import annotations

from dataclasses import dataclass

FROM_CORE_VERSION = "0.5"


class MemberWritebackError(ValueError):
    """Raised when reconstruction evidence is not sufficient for a Core Member."""


@dataclass(frozen=True)
class ResolvedMemberEvidence:
    """Reviewed facts required before crossing the Core boundary."""
    id: str
    start_node_id: str | None
    end_node_id: str | None
    material_id: str | None
    section_id: str | None
    topology_accepted: bool
    scale_resolved: bool
    review_accepted: bool


def to_core_member(evidence: ResolvedMemberEvidence) -> dict:
    """Emit a Core-compatible beam Member only from fully resolved reviewed evidence."""
    if not evidence.id or not evidence.id.strip():
        raise MemberWritebackError("member requires a non-empty stable id")
    if not evidence.scale_resolved:
        raise MemberWritebackError("unresolved scale blocks canonical member writeback")
    if not evidence.topology_accepted:
        raise MemberWritebackError("unresolved topology blocks canonical member writeback")
    if not evidence.review_accepted:
        raise MemberWritebackError("review gate blocks canonical member writeback")
    if not evidence.start_node_id or not evidence.end_node_id:
        raise MemberWritebackError("two resolved structural nodes are required")
    if evidence.start_node_id == evidence.end_node_id:
        raise MemberWritebackError("member endpoints must reference distinct structural nodes")
    if not evidence.material_id or not evidence.section_id:
        raise MemberWritebackError("resolved materialId and sectionId are required")

    return {
        "id": evidence.id,
        "type": "beam",
        "startNodeId": evidence.start_node_id,
        "endNodeId": evidence.end_node_id,
        "materialId": evidence.material_id,
        "sectionId": evidence.section_id,
    }
