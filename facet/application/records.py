"""What the use cases hand back: plain data, never domain classes."""
from __future__ import annotations

from array import array
from dataclasses import dataclass

Point = tuple[float, float, float]


@dataclass(frozen=True)
class ModelRecord:
    token: int                    # tells a stale result from the current model
    path: str
    name: str
    format: str                   # "STL", "OBJ"…
    file_size: int
    triangles: int
    positions: array              # 'f', 9 per triangle
    colors: array | None          # 'B', 9 per triangle
    bounds_min: Point
    bounds_max: Point
    unit_hint: str | None

    @property
    def size(self) -> Point:
        return tuple(b - a for a, b in zip(self.bounds_min, self.bounds_max))


@dataclass(frozen=True)
class AnalysisRecord:
    token: int
    volume: float
    area: float
    centroid: Point
    inside_out: bool              # the faces point inwards (negative volume)
    checked: bool                 # False for models too big to check the mesh health of
    vertices: int
    shells: int
    open_edges: int
    non_manifold_edges: int
    degenerate: int
    watertight: bool


@dataclass(frozen=True)
class ShadingRecord:
    token: int
    normals: array | None         # 'f', one per corner; None = flat shading
    edge_codes: bytes | None      # one byte per triangle, see domain.mesh.feature_edges


@dataclass(frozen=True)
class MeasuredValue:
    label: str                    # English; the UI translates it
    value: float
    kind: str                     # "length" (in the model's units) or "angle" (degrees)


@dataclass(frozen=True)
class MeasurementRecord:
    kind: str                     # "distance", "angle" or "circle"
    points: tuple[Point, ...]
    values: tuple[MeasuredValue, ...]
    centre: Point | None = None   # the middle of a circle


@dataclass(frozen=True)
class MaterialRecord:
    name: str
    density: float


@dataclass(frozen=True)
class SnapRecord:
    point: Point
    kind: str                     # "corner", "edge" or "surface"
