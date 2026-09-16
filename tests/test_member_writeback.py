import pytest

from linkoteq_drawing_reconstruction.member_writeback import (
    MemberWritebackError,
    ResolvedMemberEvidence,
    to_core_member,
)


def _evidence(**overrides):
    values = dict(
        id="member-1",
        start_node_id="node-1",
        end_node_id="node-2",
        material_id="mat-1",
        section_id="sec-1",
        topology_accepted=True,
        scale_resolved=True,
        review_accepted=True,
    )
    values.update(overrides)
    return ResolvedMemberEvidence(**values)


def test_emits_core_member_from_fully_resolved_evidence():
    assert to_core_member(_evidence()) == {
        "id": "member-1",
        "startNodeId": "node-1",
        "endNodeId": "node-2",
        "materialId": "mat-1",
        "sectionId": "sec-1",
    }


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"scale_resolved": False}, "unresolved scale"),
        ({"topology_accepted": False}, "unresolved topology"),
        ({"review_accepted": False}, "review gate"),
        ({"start_node_id": None}, "two resolved structural nodes"),
        ({"end_node_id": "node-1"}, "distinct structural nodes"),
        ({"material_id": None}, "resolved materialId and sectionId"),
        ({"section_id": None}, "resolved materialId and sectionId"),
    ],
)
def test_blocks_unresolved_member_writeback(overrides, message):
    with pytest.raises(MemberWritebackError) as exc:
        to_core_member(_evidence(**overrides))
    assert message in str(exc.value)


def test_blocks_empty_member_id():
    with pytest.raises(MemberWritebackError, match="stable id"):
        to_core_member(_evidence(id="  ")
