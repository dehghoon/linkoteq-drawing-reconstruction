from linkoteq_drawing_reconstruction.scale_confirmation import (
    ScaleConfirmationRequest, confirm_scale, require_human_confirmation,
)


def request(proposed=6000.0, unit="mm"):
    return ScaleConfirmationRequest(
        "drawing-1", "page-1", "grid-A", "grid-B", 0.125, proposed, unit, ("ocr-1",)
    )


def test_proposed_scale_does_not_authorize_writeback():
    p = require_human_confirmation(request())
    assert p.status == "confirmation-required"
    assert not p.authorizes_writeback


def test_user_confirmation_authorizes_writeback():
    c = confirm_scale(request(), engineering_distance=6000.0, length_unit="mm")
    assert c.status == "confirmed"
    assert c.authorizes_writeback


def test_user_can_correct_automated_proposal():
    c = confirm_scale(request(), engineering_distance=5800.0, length_unit="mm")
    assert c.status == "corrected"
    assert c.engineering_distance == 5800.0
    assert c.authorizes_writeback


def test_no_automated_proposal_still_requires_user_calibration():
    r = request(None, None)
    p = require_human_confirmation(r)
    assert not p.authorizes_writeback
    c = confirm_scale(r, engineering_distance=6000.0, length_unit="mm")
    assert c.status == "corrected"
    assert c.authorizes_writeback
