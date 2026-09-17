"""Deterministic reviewed topology facts for Core-bound reconstruction."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

class TopologyError(ValueError):
    pass

@dataclass(frozen=True)
class ReviewedLevel:
    id: str
    name: str
    elevation: float
    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise TopologyError("level requires stable id and name")
        if not isfinite(self.elevation):
            raise TopologyError("level elevation must be finite")

@dataclass(frozen=True)
class ReviewedNodeTopology:
    id: str
    level_id: str
    def __post_init__(self) -> None:
        if not self.id.strip() or not self.level_id.strip():
            raise TopologyError("node topology requires stable node and level ids")

@dataclass(frozen=True)
class ReviewedMemberTopology:
    id: str
    start_node_id: str
    end_node_id: str
    accepted: bool
    def __post_init__(self) -> None:
        if not self.id.strip() or not self.start_node_id.strip() or not self.end_node_id.strip():
            raise TopologyError("member topology requires stable ids")
        if self.start_node_id == self.end_node_id:
            raise TopologyError("member endpoints must reference distinct nodes")

def validate_topology(*, levels, nodes, members) -> None:
    """Validate reviewed references without inventing missing evidence."""
    level_ids = [x.id for x in levels]
    node_ids = [x.id for x in nodes]
    member_ids = [x.id for x in members]
    for values, label in ((level_ids, "level"), (node_ids, "node"), (member_ids, "member")):
        if len(values) != len(set(values)):
            raise TopologyError(f"duplicate {label} ids are not allowed")
    known_levels, known_nodes = set(level_ids), set(node_ids)
    for node in nodes:
        if node.level_id not in known_levels:
            raise TopologyError(f"node {node.id!r} references unknown level {node.level_id!r}")
    for member in members:
        if not member.accepted:
            raise TopologyError(f"member {member.id!r} has not passed topology review")
        if member.start_node_id not in known_nodes or member.end_node_id not in known_nodes:
            raise TopologyError(f"member {member.id!r} references unknown structural node")
