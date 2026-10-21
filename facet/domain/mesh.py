"""A triangle mesh and what can be worked out from it: size, volume, health, shading data.

Positions are one flat float array, nine numbers per triangle (three corners, x y z each),
so a mesh of a million triangles stays a few dozen megabytes and goes to the graphics card
as it is. Units are whatever the file used; Facet only calls them millimetres by default.
"""
from __future__ import annotations

import math
from array import array
from dataclasses import dataclass

from .geometry import Vec


@dataclass
class Mesh:
    positions: array                     # 'f', 9 per triangle
    colors: array | None = None          # 'B', 9 per triangle (r g b for each corner)
    name: str = ""
    unit_hint: str | None = None         # "mm", "cm", "m", "in" when the file says

    @property
    def triangle_count(self) -> int:
        return len(self.positions) // 9

    def triangle(self, index: int) -> tuple[Vec, Vec, Vec]:
        p = self.positions
        i = index * 9
        return ((p[i], p[i + 1], p[i + 2]), (p[i + 3], p[i + 4], p[i + 5]),
                (p[i + 6], p[i + 7], p[i + 8]))


def bounds(mesh: Mesh) -> tuple[Vec, Vec]:
    p = mesh.positions
    if not len(p):
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    xs, ys, zs = p[0::3], p[1::3], p[2::3]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _columns(positions: array):
    return zip(*(positions[i::9] for i in range(9)))


@dataclass(frozen=True)
class Solid:
    """What a closed surface encloses (meaningless, but still computed, for open ones)."""
    volume: float        # negative when the faces point inwards
    area: float
    centroid: Vec        # centre of mass of the enclosed volume (of the surface if flat)


def solid_properties(mesh: Mesh) -> Solid:
    lo, hi = bounds(mesh)
    ox, oy, oz = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
    volume = area = 0.0
    cx = cy = cz = 0.0
    sx = sy = sz = 0.0  # area-weighted centres, for surfaces with no volume
    for ax, ay, az, bx, by, bz, cx_, cy_, cz_ in _columns(mesh.positions):
        ax -= ox; ay -= oy; az -= oz
        bx -= ox; by -= oy; bz -= oz
        cx_ -= ox; cy_ -= oy; cz_ -= oz
        nx = (by - ay) * (cz_ - az) - (bz - az) * (cy_ - ay)
        ny = (bz - az) * (cx_ - ax) - (bx - ax) * (cz_ - az)
        nz = (bx - ax) * (cy_ - ay) - (by - ay) * (cx_ - ax)
        twice = math.sqrt(nx * nx + ny * ny + nz * nz)
        area += twice / 2
        v = (ax * (by * cz_ - bz * cy_) - ay * (bx * cz_ - bz * cx_)
             + az * (bx * cy_ - by * cx_)) / 6.0
        volume += v
        cx += v * (ax + bx + cx_) / 4
        cy += v * (ay + by + cy_) / 4
        cz += v * (az + bz + cz_) / 4
        sx += twice * (ax + bx + cx_) / 6
        sy += twice * (ay + by + cy_) / 6
        sz += twice * (az + bz + cz_) / 6
    if abs(volume) > 1e-12 * max(1.0, area):
        centre = (cx / volume + ox, cy / volume + oy, cz / volume + oz)
    elif area > 0:
        centre = (sx / area + ox, sy / area + oy, sz / area + oz)
    else:
        centre = (ox, oy, oz)
    return Solid(volume, area, centre)


# ---- topology: which corners are the same point -------------------------------------------

@dataclass
class Topology:
    corner_ids: array     # 'i', one welded vertex id per corner (3 per triangle)
    vertex_count: int

    @property
    def triangle_count(self) -> int:
        return len(self.corner_ids) // 3


def weld(mesh: Mesh) -> Topology:
    """Give corners that sit at the same place the same vertex id (to a millionth of the model)."""
    lo, hi = bounds(mesh)
    diagonal = math.dist(lo, hi) or 1.0
    inv = 1.0 / (diagonal * 1e-6)
    ids: dict[tuple[int, int, int], int] = {}
    out = array("i")
    p = mesh.positions
    setdefault = ids.setdefault
    for x, y, z in zip(p[0::3], p[1::3], p[2::3]):
        key = (round(x * inv), round(y * inv), round(z * inv))
        out.append(setdefault(key, len(ids)))
    return Topology(out, len(ids))


@dataclass(frozen=True)
class Health:
    vertices: int           # welded
    shells: int             # separate connected pieces
    open_edges: int         # edges used by one triangle only: holes
    non_manifold_edges: int  # edges shared by three or more triangles
    degenerate: int         # triangles with no area
    watertight: bool


def check_health(mesh: Mesh, topology: Topology) -> Health:
    ids = topology.corner_ids
    n = topology.vertex_count
    counts: dict[int, int] = {}
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    degenerate = 0
    for t in range(topology.triangle_count):
        a, b, c = ids[3 * t], ids[3 * t + 1], ids[3 * t + 2]
        if a == b or b == c or a == c:
            degenerate += 1
            continue
        for u, v in ((a, b), (b, c), (c, a)):
            key = u * n + v if u < v else v * n + u
            counts[key] = counts.get(key, 0) + 1
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    used = {find(i) for i in set(ids)}
    open_edges = sum(1 for c in counts.values() if c == 1)
    odd = sum(1 for c in counts.values() if c > 2)
    return Health(n, len(used), open_edges, odd, degenerate, open_edges == 0 and odd == 0)


def _face_normals(mesh: Mesh) -> list[Vec]:
    """Unnormalised normals (length = twice the area), one per triangle."""
    out = []
    for ax, ay, az, bx, by, bz, cx, cy, cz in _columns(mesh.positions):
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        out.append((uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx))
    return out


def smooth_normals(mesh: Mesh, topology: Topology, crease_degrees: float = 50.0) -> array:
    """One normal per corner: the average of the neighbouring faces, but never across an edge
    sharper than `crease_degrees`, so round things look round and boxes keep their edges."""
    ids = topology.corner_ids
    faces = _face_normals(mesh)
    unit = []
    for fx, fy, fz in faces:
        n = math.sqrt(fx * fx + fy * fy + fz * fz)
        unit.append((fx / n, fy / n, fz / n) if n > 0 else (0.0, 0.0, 0.0))
    at_vertex: list[list[int]] = [[] for _ in range(topology.vertex_count)]
    for corner, v in enumerate(ids):
        at_vertex[v].append(corner // 3)
    limit = math.cos(math.radians(crease_degrees))
    out = array("f", bytes(4 * len(ids) * 3))
    for corner, v in enumerate(ids):
        f = corner // 3
        ux, uy, uz = unit[f]
        sx = sy = sz = 0.0
        for g in at_vertex[v]:
            gx, gy, gz = unit[g]
            if ux * gx + uy * gy + uz * gz >= limit:
                nx, ny, nz = faces[g]
                sx += nx; sy += ny; sz += nz
        n = math.sqrt(sx * sx + sy * sy + sz * sz)
        if n > 0:
            out[corner * 3], out[corner * 3 + 1], out[corner * 3 + 2] = sx / n, sy / n, sz / n
        else:
            out[corner * 3], out[corner * 3 + 1], out[corner * 3 + 2] = ux, uy, uz
    return out


def feature_edges(mesh: Mesh, topology: Topology, angle_degrees: float = 30.0) -> bytes:
    """One byte per triangle: bit i is set when the edge opposite corner i should be drawn
    as an outline (a boundary, or a fold sharper than `angle_degrees`)."""
    ids = topology.corner_ids
    n = topology.vertex_count
    faces = _face_normals(mesh)
    first: dict[int, int] = {}
    second: dict[int, int] = {}
    many: set[int] = set()
    keys = []
    for t in range(topology.triangle_count):
        a, b, c = ids[3 * t], ids[3 * t + 1], ids[3 * t + 2]
        row = []
        for u, v in ((b, c), (c, a), (a, b)):  # the edge opposite corner 0, 1, 2
            key = u * n + v if u < v else v * n + u
            row.append(key)
            if key not in first:
                first[key] = t
            elif key not in second:
                second[key] = t
            else:
                many.add(key)
        keys.append(row)
    limit = math.cos(math.radians(angle_degrees))
    out = bytearray(topology.triangle_count)
    for t, row in enumerate(keys):
        bits = 0
        fx, fy, fz = faces[t]
        fl = math.sqrt(fx * fx + fy * fy + fz * fz)
        for i, key in enumerate(row):
            other = second.get(key)
            if other is None or key in many:
                bits |= 1 << i
                continue
            other = first[key] if first[key] != t else other
            gx, gy, gz = faces[other]
            gl = math.sqrt(gx * gx + gy * gy + gz * gz)
            if fl > 0 and gl > 0 and (fx * gx + fy * gy + fz * gz) / (fl * gl) < limit:
                bits |= 1 << i
        out[t] = bits
    return bytes(out)
