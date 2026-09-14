"""Deterministic source-to-model transform tracking.

Importer-private geometry stays in source/normalized spaces until an explicit,
resolved engineering calibration and global placement are available.
"""
from __future_ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Literal, Sequence


class TransformError(ValueError):
    """Base error for invalid transform records."""


class UnresolvedTransformError(TransformError):
    """Raised when canonical model geometry is requested before calibration."""


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Affine2D:
    """Immutable 3x3 homogeneous affine transform."""

    matrix: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]

    def __post_init__(self) -> None:
        if len(self.matrix) != 3 or any(len(row) != 3 for row in self.matrix):
            raise TransformError("Affine2D requires a 3x3 matrix.")
        if not all(isclose(v, expected, rel_tol=0.0, abs_tol=1e-12)
                   for v, expected in zip(self.matrix[2], (0.0, 0.0, 1.0))):
            raise TransformError("Affine2D bottom row must be [0, 0, 1].")

    @classmethod
    def identity(cls) -> "Affine2D":
        return cls(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[float]]) -> "Affine2D":
        if len(rows) != 3 or any(len(row) != 3 for row in rows):
            raise TransformError("Affine2D requires exactly three rows of three values.")
        return cls(tuple(tuple(float(v) for v in row) for row in rows))  # type: ignore[arg-type]

    def apply(self, point: Point2D) -> Point2D:
        x, y = point.x, point.y
        m = self.matrix
        return Point2D(
            x=m[0][0] * x + m[0][1] * y + m[0][2],
            y=m[1][0] * x + m[1][1] * y + m[1][2],
        )

    def then(self, next_transform: "Affine2D") -> "Affine2D":
        """Compose transforms so result(p) == next_transform(self(p))."""
        a = self.matrix
        b = next_transform.matrix
        c = tuple(
            tuple(sum(b[i][k] * a[k][j] for k in range(3)) for j in range(3))
            for i in range(3)
        )
        return Affine2D(c)  # type: ignore[arg-type]


@dataclass(frozen=True)
class CalibrationEvidence:
    method: Literal["vector-geometry", "printed-scale", "ocr-dimension", "known-grid-spacing", "user-calibration"]
    length_unit: str
    residual: float | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.length_unit.strip():
            raise TransformError("Calibration length_unit must be explicit.")
        if self.residual is not None and self.residual < 0:
            raise TransformError("Calibration residual cannot be negative.")


@dataclass(frozen=True)
class SourceToModelTransform:
    """Per-source/page deterministic transform chain.

    ``source_to_normalized`` may operate on pixel or vector coordinates.
    ``normalized_to_model_xy`` is intentionally optional until engineering scale
    and global placement are resolved. Canonical writeback must call
    :meth:`to_model_point`, which blocks unresolved transforms.
    """

    source_id: str
    page_id: str
    source_space: Literal["pixel", "vector"]
    source_to_normalized: Affine2D
    normalized_to_model_xy: Affine2D | None = None
    model_z: float | None = None
    project_length_unit: str | None = None
    calibration: CalibrationEvidence | None = None

    @property
    def is_resolved(self) -> bool:
        return (
            self.normalized_to_model_xy is not None
            and self.model_z is not None
            and bool(self.project_length_unit and self.project_length_unit.strip())
            and self.calibration is not None
            and self.calibration.length_unit == self.project_length_unit
        )

    @property
    def T_source_to_model_xy(self) -> Affine2D:
        if not self.is_resolved:
            raise UnresolvedTransformError(
                "T_source_to_model is unresolved; scale/global placement must be explicit before canonical geometry writeback."
            )
        assert self.normalized_to_model_xy is not None
        return self.source_to_normalized.then(self.normalized_to_model_xy)

    def to_normalized_point(self, point: Point2D) -> Point2D:
        return self.source_to_normalized.apply(point)

    def to_model_point(self, point: Point2D) -> Point3D:
        if not self.is_resolved:
            raise UnresolvedTransformError(
                "Cannot map source geometry to Core before scale, project units, and global placement are resolved."
            )
        xy = self.T_source_to_model_xy.apply(point)
        assert self.model_Z is not None
        return Point3D(x=xy.x, y=xy.y, z=self.model_z)
