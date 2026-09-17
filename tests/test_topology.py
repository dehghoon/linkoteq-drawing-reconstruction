import pytest

from linkoteq_drawing_reconstruction.topology import (
    ReviewedLevel, ReviewedMemberTopology, ReviewedNodeTopology,
    TopologyError, validate_topology,
)

def test_reviewed_topology_accepts_resolved_distinct_nodes():
    validate_topology(
        levels=[ReviewedLevel("L1", "Level 1", 0.0)],
        nodes=[ReviewedNodeTopology("N1", "L1"), ReviewedNodeTopology("N2", "L1")],
        members=[ReviewedMemberTopology("B1", "N1", "N2", True)],
    )

def test_topology_rejects_unknown_level():
    with pytest.raises(TopologyError, match="unknown level"):
        validate_topology(
            levels=[ReviewedLevel("L1", "Level 1", 0.0)],
            nodes=[ReviewedNodeTopology("N1", "L2")], members=[],
        )

def test_topology_rejects_unreviewed_member():
    with pytest.raises(TopologyError, match="has not passed topology review"):
        validate_topology(
            levels=[ReviewedLevel("L1", "Level 1", 0.0)],
            nodes=[ReviewedNodeTopology("N1", "L1"), ReviewedNodeTopology("N2", "L1")],
            members=[ReviewedMemberTopology("B1", "N1", "N2", False)],
        )

def test_topology_never_accepts_same_node_member():
    with pytest.raises(TopologyError, match="distinct nodes"):
        ReviewedMemberTopology("B1", "N1", "N1", True)
