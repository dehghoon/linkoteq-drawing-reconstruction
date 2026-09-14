"""Source classification and deterministic normalization metadata.

This module tracks source/page identity and geometric preprocessing only.
It does not detect grids, run OCR/YOLO, infer engineering scale, or emit Core geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .transforms import (
    Affine2D,
    Projective2D,
    SourceToModelTransform,
    Transform2D,
    TransformError,
)


SourceKind = Literal["vector", "raster", "mixed"]
SourceSpace = Literal["pixel", "vector"]
PreprocessOperation = Literal[
    "identity",
    "crop",
    "rotation",
    "deskew",
    "scale",
    "translation",
    "perspective-correction",
]


class SourceNormalizationError(ValueError):
    """Raised when source metadata or preprocessing evidence is inconsistent."""


def classify_source(*, has_vector_geometry: bool, has_raster_content: bool) -> SourceKind:
    if has_vector_geometry and has_raster_content:
        return "mixed"
    if has_vector_geometry:
        return "vector"
    if has_raster_content:
        return "raster"
    raise SourceNormalizationError("A page must contain vector geometry, raster content, or both.")


@dataclass(frozen=True)
class SourcePageMetadata:
    source_id: str
    page_id: str
    page_index: int
    width: float
    height: float
    has_vector_geometry: bool
    has_raster_content: bool
    source_space: SourceSpace
    dpi: float | None = None
    media_type: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise SourceNormalizationError("source_id must be non-empty.")
        if not self.page_id.strip():
            raise SourceNormalizationError("page_id must be non-empty.")
        if self.page_index < 0:
            raise SourceNormalizationError("page_index must be zero-based and non-negative.")
        if self.width <= 0 or self.height <= 0:
            raise SourceNormalizationError("source width and height must be positive.")
        if self.dpi is not None and self.dpi <= 0:
            raise SourceNormalizationError("dpi must be positive when provided.")

        kind = self.kind
        if self.source_space == "vector" and not self.has_vector_geometry:
            raise SourceNormalizationError("vector source_space requires vector geometry evidence.")
        if self.source_space == "pixel" and not self.has_raster_content:
            raise SourceNormalizationError("pixel source_space requires raster content evidence.")
        if kind == "mixed" and self.source_space != "vector":
            raise SourceNormalizationError(
                "Mixed pages must normalize from vector space so native vector geometry is preserved."
            )

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        page_id: str,
        page_index: int,
        width: float,
        height: float,
        has_vector_geometry: bool,
        has_raster_content: bool,
        dpi: float | None = None,
        media_type: str | None = None,
    ) -> "SourcePageMetadata":
        kind = classify_source(
            has_vector_geometry=has_vector_geometry,
            has_raster_content=has_raster_content,
        )
        source_space: SourceSpace = "vector" if kind in ("vector", "mixed") else "pixel"
        return cls(
            source_id=source_id,
            page_id=page_id,
            page_index=page_index,
            width=width,
            height=height,
            has_vector_geometry=has_vector_geometry,
            has_raster_content=has_raster_content,
            source_space=source_space,
            dpi=dpi,
            media_type=media_type,
        )

    @property
    def kind(self) -> SourceKind:
        return classify_source(
            has_vector_geometry=self.has_vector_geometry,
            has_raster_content=self.has_raster_content,
        )


@dataclass(frozen=True)
class PreprocessingTransformStep:
    step_id: str
    operation: PreprocessOperation
    transform: Transform2D
    output_width: float
    output_height: float
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise SourceNormalizationError("preprocessing step_id must be non-empty.")
        if self.output_width <= 0 or self.output_height <= 0:
            raise SourceNormalizationError("preprocessing output dimensions must be positive.")
        if self.operation == "perspective-correction" and isinstance(self.transform, Affine2D):
            raise SourceNormalizationError(
                "perspective-correction must retain a projective transform, not an affine placeholder."
            )


@dataclass(frozen=True)
class NormalizedSourcePage:
    source: SourcePageMetadata
    steps: tuple[PreprocessingTransformStep, ...]
    source_to_normalized: Transform2D
    normalized_width: float
    normalized_height: float

    def unresolved_model_transform(self) -> SourceToModelTransform:
        """Create a transform record that remains blocked at the Core boundary."""
        return SourceToModelTransform(
            source_id=self.source.source_id,
            page_id=self.source.page_id,
            source_space=self.source.source_space,
            source_to_normalized=self.source_to_normalized,
        )


def normalize_source_page(
    source: SourcePageMetadata,
    steps: Sequence[PreprocessingTransformStep] = (),
) -> NormalizedSourcePage:
    """Accumulate preprocessing transforms in declared order.

    Pixel/vector source coordinates are preserved as source-space evidence.
    Only the derived normalized coordinate transform is accumulated.
    """
    seen: set[str] = set()
    current: Transform2D = Affine2D.identity()
    width, height = source.width, source.height

    for step in steps:
        if step.step_id in seen:
            raise SourceNormalizationError(f"Duplicate preprocessing step_id {step.step_id!r}.")
        seen.add(step.step_id)
        current = current.then(step.transform)
        width, height = step.output_width, step.output_height

    return NormalizedSourcePage(
        source=source,
        steps=tuple(steps),
        source_to_normalized=current,
        normalized_width=width,
        normalized_height=height,
    )
