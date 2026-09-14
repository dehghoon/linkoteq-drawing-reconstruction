"""Deterministic source-to-model transform tracking.

Importer-private geometry stays in source/normalized spaces until an explicit,
resolved engineering calibration and global placement are available.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Literal, Sequence, TypeAlias


Matrix3x3: TypeAlias = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


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


def _coerce_matrix(rows: Sequence[Sequence[float]]) -> Matrix3x3:
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise TransformError("A 2D homogeneous transform requires exactly three rows of three values.")
    return tuple(tuple(float(v) for v in row) for row in rows)  # type: ignore[return-value]


def _multiply(left: Matrix3x3, right: Matrix3x3) -> Matrix3x3:
    return tuple(
        tuple(sum(left[i][k] * right[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )  # type: ignore[return-value]


@dataclass(frozen=True)
class Projective2D:
    """Immutable 3x3 projective transform for tracked preprocessing warps."""

    matrix: Matrix3x3

    def __post_init__(self) -> None:
        _coerce_matrix(self.matrix)
        if all(isclose(v, 0.0, rel_tol=0.0, abs_tol=1e-15) for v in self.matrix[2]):
            raise TransformError("Projective2D bottom row cannot be all zeros.")

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[float]]) -> "Projective2D":
        return cls(_coerce_matrix(rows))

    def apply(self, point: Point2D) -> Point2D:
        x, y = point.x, point.y
        m = self.matrix
        w = m[2][0] * x + m[2][1] * y + m[2][2]
        if isclose(w, 0.0, rel_tol=0.0, abs_tol=1e-15):
            raise TransformError("Projective transform maps point to infinity.")
        return Point2D(
            x=(m[0][0] * x + m[0][1] * y + m[0][2]) / w,
            y=(m[1][0] * x + m[1][1] * y + m[1][2]) / w,
        )

    def then(self, next_transform: "Affine2D | Projective2D") -> "Projective2D":
        """Compose transforms so result(p) == next_transform(self(p))."""
        return Projective2D(_multiply(next_transform.matrix, self.matrix))


@dataclass(frozen=True)
class Affine2D:
    """Immutable 3x3 homogeneous affine transform."""

    matrix: Matrix3x3

    def __post_init__(self) -> None:
        _coerce_matrix(self.matrix)
        if not all(
            isclose(v, expected, rel_tol=0.0, abs_tol=1e-12)
            for v, expected in zip(self.matrix[2], (0.0, 0.0, 1.0))
        ):
            raise TransformError("Affine2D bottom row must be [0, 0, 1].")

    @classmethod
    def identity(cls) -> "Affine2D":
        return cls(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[float]]) -> "Affine2D":
        return cls(_coerce_matrix(rows))

    def apply(self, point: Point2D) -> Point2D:
        x, y = point.x, point.y
        m = self.matrix
        return Point2D(
            x=m[0][0] * x + m[0][1] * y + m[0][2],
            y=m[1][0] * x + m[1][1] * y + m[1][2],
        )

    def then(self, next_transform: "Affine2D | Projective2D") -> "Affine2D | Projective2D":
        """Compose transforms so result(p) == next_transform(self(p))."""
        matrix = _multiply(next_transform.matrix, self.matrix)
        if isinstance(next_transform, Affine2D):
            return Affine2D(matrix)
        return Projective2D(matrix)


Transform2D: TypeAlias = Affine2D | Projective2D


@dataclass(frozen=True)
class CalibrationEvidence:
    method: Literal[
        "vector-geometry",
        "printed-scale",
        "ocr-dimension",
        "known-grid-spacing",
        "user-calibration",
    ]
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

    ``source_to_normalized`` may operate on pixel or vector coordinates and may
    include a projective warp introduced by preprocessing. The
    ``normalized_to_model_xy`` transform is intentionally optional until
    engineering scale and global placement are resolved.
    """

    source_id: str
    page_id: str
    source_space: Literal["pixel", "vector"]
    source_to_normalized: Transform2D
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
    def T_source_to_model_xy(self) -> Transform2D:
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
        assert self.model_z is not None
        return Point3D(x=xy.x, y=xy.y, z=self.model_z)
