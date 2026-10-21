"""Opening, inspecting and measuring a model."""
from __future__ import annotations

from pathlib import Path

from ..domain import geometry
from ..domain.mesh import (Mesh, Topology, bounds, check_health, feature_edges, smooth_normals,
                           solid_properties, weld)
from .errors import MeasureError, NoModelError
from .ports import KeyValueStore, MeshReader
from .records import (AnalysisRecord, MaterialRecord, MeasuredValue, MeasurementRecord,
                      ModelRecord, Point, ShadingRecord, SnapRecord)
from .units import MATERIALS, weight_grams

SMOOTH_LIMIT = 600_000      # above this many triangles, smooth shading is skipped
CHECK_LIMIT = 2_000_000     # above this, the mesh isn't welded or checked at all
RECENT_LIMIT = 10
RECENT_KEY = "recent"


class ModelService:
    def __init__(self, reader: MeshReader, settings: KeyValueStore):
        self._reader = reader
        self._settings = settings
        self._mesh: Mesh | None = None
        self._topology: Topology | None = None
        self._token = 0

    # ---- opening -------------------------------------------------------------------
    def open(self, path: str) -> ModelRecord:
        """Read a model (slow for big ones: run it off the UI thread)."""
        mesh = self._reader.read(path)
        lo, hi = bounds(mesh)
        self._token += 1
        self._mesh, self._topology = mesh, None
        self._remember(path)
        return ModelRecord(
            self._token, path, Path(path).name, Path(path).suffix.lstrip(".").upper(),
            self._reader.size(path), mesh.triangle_count, mesh.positions, mesh.colors, lo, hi,
            mesh.unit_hint)

    def close(self):
        self._mesh, self._topology = None, None
        self._token += 1

    @property
    def is_open(self) -> bool:
        return self._mesh is not None

    def _need(self) -> Mesh:
        if self._mesh is None:
            raise NoModelError("No model is open.")
        return self._mesh

    # ---- inspecting ----------------------------------------------------------------
    def _welded(self, mesh: Mesh) -> Topology | None:
        if mesh.triangle_count > CHECK_LIMIT:
            return None
        if self._topology is None:
            self._topology = weld(mesh)
        return self._topology

    def analyse(self) -> AnalysisRecord:
        mesh, token = self._need(), self._token
        solid = solid_properties(mesh)
        topology = self._welded(mesh)
        if topology is None:
            return AnalysisRecord(token, solid.volume, solid.area, solid.centroid,
                                  solid.volume < 0, False, 0, 0, 0, 0, 0, False)
        health = check_health(mesh, topology)
        return AnalysisRecord(
            token, solid.volume, solid.area, solid.centroid, solid.volume < 0, True,
            health.vertices, health.shells, health.open_edges, health.non_manifold_edges,
            health.degenerate, health.watertight)

    def shading(self, smooth: bool, edges: bool) -> ShadingRecord:
        """Smooth normals and outline edges, for models small enough to work them out."""
        mesh, token = self._need(), self._token
        topology = self._welded(mesh)
        normals = codes = None
        if topology is not None:
            if smooth and mesh.triangle_count <= SMOOTH_LIMIT:
                normals = smooth_normals(mesh, topology)
            if edges:
                codes = feature_edges(mesh, topology)
        return ShadingRecord(token, normals, codes)

    def weight(self, volume: float, unit: str, material: str) -> float:
        density = next((m.density for m in MATERIALS if m.name == material), MATERIALS[0].density)
        return weight_grams(volume, unit, density)

    def materials(self) -> tuple[MaterialRecord, ...]:
        return tuple(MaterialRecord(m.name, m.density) for m in MATERIALS)

    # ---- picking and measuring -----------------------------------------------------
    def corners(self, triangle: int) -> tuple[Point, Point, Point]:
        mesh = self._need()
        if not 0 <= triangle < mesh.triangle_count:
            raise MeasureError("That point isn't on the model.")
        return mesh.triangle(triangle)

    def snap(self, triangle: int, origin: Point, direction: Point, radius: float,
             corners: bool = True, edges: bool = True) -> SnapRecord:
        """The point a click at this ray means: a corner or a spot on an edge when one is
        within `radius` (model units) of where the ray lands, else the exact spot on the face."""
        a, b, c = self.corners(triangle)
        t = geometry.ray_triangle(origin, direction, a, b, c)
        if t is None:  # the click was on the very rim: use the triangle's plane
            n = geometry.cross(geometry.sub(b, a), geometry.sub(c, a))
            denom = geometry.dot(direction, n)
            t = geometry.dot(geometry.sub(a, origin), n) / denom if abs(denom) > 1e-18 else 0.0
        point = geometry.add(origin, geometry.scale(direction, t))
        if corners:
            nearest = min((a, b, c), key=lambda v: geometry.distance(v, point))
            if geometry.distance(nearest, point) <= radius:
                return SnapRecord(nearest, "corner")
        if edges:
            best = min((geometry.closest_on_segment(point, u, v)
                        for u, v in ((a, b), (b, c), (c, a))),
                       key=lambda q: geometry.distance(q, point))
            if geometry.distance(best, point) <= radius * 0.6:
                return SnapRecord(best, "edge")
        return SnapRecord(point, "surface")

    def measure_distance(self, a: Point, b: Point) -> MeasurementRecord:
        d = geometry.sub(b, a)
        return MeasurementRecord("distance", (a, b), (
            MeasuredValue("Distance", geometry.length(d), "length"),
            MeasuredValue("ΔX", abs(d[0]), "length"), MeasuredValue("ΔY", abs(d[1]), "length"),
            MeasuredValue("ΔZ", abs(d[2]), "length")))

    def measure_angle(self, a: Point, vertex: Point, b: Point) -> MeasurementRecord:
        if geometry.distance(a, vertex) == 0 or geometry.distance(b, vertex) == 0:
            raise MeasureError("Pick three different points.")
        angle = geometry.angle_at(vertex, a, b)
        return MeasurementRecord("angle", (a, vertex, b), (
            MeasuredValue("Angle", angle, "angle"),
            MeasuredValue("Supplement", 180.0 - angle, "angle")))

    def measure_circle(self, a: Point, b: Point, c: Point) -> MeasurementRecord:
        found = geometry.circle_through(a, b, c)
        if found is None:
            raise MeasureError("The three points are in a line: pick points around the hole.")
        centre, radius = found
        return MeasurementRecord("circle", (a, b, c), (
            MeasuredValue("Diameter", radius * 2, "length"),
            MeasuredValue("Radius", radius, "length")), centre)

    # ---- the folder and the recent list -------------------------------------------
    def siblings(self, path: str) -> list[str]:
        return self._reader.siblings(path)

    def recent(self) -> list[str]:
        raw = self._settings.get(RECENT_KEY) or ""
        return [p for p in raw.split("\n") if p and Path(p).is_file()]

    def _remember(self, path: str):
        paths = [path] + [p for p in (self._settings.get(RECENT_KEY) or "").split("\n")
                          if p and p != path]
        self._settings.set(RECENT_KEY, "\n".join(paths[:RECENT_LIMIT]))

    def forget(self, path: str):
        paths = [p for p in (self._settings.get(RECENT_KEY) or "").split("\n") if p != path]
        self._settings.set(RECENT_KEY, "\n".join(paths) or None)
