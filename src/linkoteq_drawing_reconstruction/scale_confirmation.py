"""Human-confirmation gate for engineering scale.

Automated scale evidence may propose a scale, but only an explicit
user confirmation may authorize canonical physical-geometry writeback.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

Status = Literal["confirmation-required", "confirmed", "corrected"]


class ScaleConfirmationError(ValueError):
    pass


@dataclass(frozen=True)
class ScaleConfirmationRequest:
    source_id: str
    page_id: str
    grid_a_id: str
    grid_b_id: str
    normalized_distance: float
    proposed_distance: float | None
    length_unit: str | None
    proposal_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.source_id, self.page_id, self.grid_a_id, self.grid_b_id):
            if not value.strip():
                raise ScaleConfirmationError("confirmation requires source, page, and two grid ids")
        if self.grid_a_id == self.grid_b_id:
            raise ScaleConfirmationError("confirmation requires two distinct grids")
        if not isfinite(self.normalized_distance) or self.normalized_distance <= 0:
            raise ScaleConfirmationError("normalized grid distance must be positive")
        if (self.proposed_distance is None) != (self.length_unit is None):
            raise ScaleConfirmationError("proposed distance and unit must be present together")


@dataclass(frozen=True)
class HumanScaleConfirmation:
    status: Status
    source_id: str
    page_id: str
    grid_a_id: str
    grid_b_id: str
    normalized_distance: float
    engineering_distance: float | None
    length_unit: str | None
    proposal_evidence_ids: tuple[str, ...] = ()


    @property
    def authorizes_writeback(self) -> bool:
        return self.status in {"confirmed", "corrected"} and self.engineering_distance is not None


def require_human_confirmation(request: ScaleConfirmationRequest) -> HumanScaleConfirmation:
    return HumanScaleConfirmation(
        "confirmation-required", request.source_id, request.page_id, request.grid_a_id, request.grid_b_id,
        request.normalized_distance, None, None, request.proposal_evidence_ids,
    )


def confirm_scale(request: ScaleConfirmationRequest, *, engineering_distance: float, length_unit: str) -> HumanScaleConfirmation:
    """Confirm or correct the proposed grid spacing."""
    if not isfinite(engineering_distance) or engineering_distance <= 0:
        raise ScaleConfirmationError("confirmed engineering distance must be positive")
    if not length_unit.strip():
        raise ScaleConfirmationError("confirmed length unit must be explicit")
    status: Status = "confirmed"
    if request.proposed_distance is None or request.length_unit is None:
        status = "corrected"
    elif engineering_distance != request.proposed_distance or length_unit != request.length_unit:
        status = "corrected"
    return HumanScaleConfirmation(
        status, request.source_id, request.page_id, request.grid_a_id, request.grid_b_id,
        request.normalized_distance, engineering_distance, length_unit, request.proposal_evidence_ids,
    )
