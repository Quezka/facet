"""Two sample models, written as binary STL: a precise part and an organic shape."""
from __future__ import annotations

import math
import struct
from pathlib import Path

Tri = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def write_stl(path: Path, triangles: list[Tri], name: str = "Facet sample") -> None:
    out = bytearray(name.encode("ascii", "replace")[:80].ljust(80, b" "))
    out += struct.pack("<I", len(triangles))
    for a, b, c in triangles:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        length = math.sqrt(sum(x * x for x in n)) or 1.0
        out += struct.pack("<12fH", *(x / length for x in n), *a, *b, *c, 0)
    path.write_bytes(bytes(out))


def bracket(width: float = 60.0, depth: float = 40.0, thickness: float = 8.0,
            hole: float = 12.0, steps: int = 96) -> list[Tri]:
    """A plate with a round hole through it, to the millimetre: `width` x `depth` x `thickness`."""
    outer, inner = [], []
    corners = [math.atan2(sy * depth / 2, sx * width / 2) % (2 * math.pi)
               for sx in (1, -1) for sy in (1, -1)]  # so the corners are real corners
    angles = sorted([2 * math.pi * i / steps for i in range(steps)] + corners)
    steps = len(angles)
    for t in angles:
        c, s = math.cos(t), math.sin(t)
        k = min(width / 2 / abs(c) if abs(c) > 1e-12 else math.inf,
                depth / 2 / abs(s) if abs(s) > 1e-12 else math.inf)
        outer.append((c * k, s * k))
        inner.append((c * hole / 2, s * hole / 2))
    tris: list[Tri] = []
    z0, z1 = 0.0, thickness
    for i in range(steps):
        j = (i + 1) % steps
        o0, o1, i0, i1 = outer[i], outer[j], inner[i], inner[j]
        # top (counter-clockwise seen from above) and bottom
        tris += [((o0[0], o0[1], z1), (o1[0], o1[1], z1), (i1[0], i1[1], z1)),
                 ((o0[0], o0[1], z1), (i1[0], i1[1], z1), (i0[0], i0[1], z1)),
                 ((o0[0], o0[1], z0), (i1[0], i1[1], z0), (o1[0], o1[1], z0)),
                 ((o0[0], o0[1], z0), (i0[0], i0[1], z0), (i1[0], i1[1], z0))]
        # outer wall faces outwards, the hole's wall faces the axis
        tris += [((o0[0], o0[1], z0), (o1[0], o1[1], z0), (o1[0], o1[1], z1)),
                 ((o0[0], o0[1], z0), (o1[0], o1[1], z1), (o0[0], o0[1], z1)),
                 ((i0[0], i0[1], z0), (i1[0], i1[1], z1), (i1[0], i1[1], z0)),
                 ((i0[0], i0[1], z0), (i0[0], i0[1], z1), (i1[0], i1[1], z1))]
    return tris


def vase(height: float = 90.0, steps: int = 72, rings: int = 60) -> list[Tri]:
    """A smooth, closed vase (a surface of revolution)."""
    def radius(u: float) -> float:
        return 18 + 14 * math.sin(u * math.pi * 1.6 + 0.4) * (1 - u * 0.4) + 10 * math.sin(u * math.pi)

    profile = [(0.0, 0.0)] + [(max(radius(k / rings), 0.5), height * k / rings)
                              for k in range(rings + 1)] + [(0.0, height)]
    tris: list[Tri] = []
    for a in range(len(profile) - 1):
        (r0, z0), (r1, z1) = profile[a], profile[a + 1]
        for i in range(steps):
            t0, t1 = 2 * math.pi * i / steps, 2 * math.pi * (i + 1) / steps
            p00 = (r0 * math.cos(t0), r0 * math.sin(t0), z0)
            p01 = (r0 * math.cos(t1), r0 * math.sin(t1), z0)
            p10 = (r1 * math.cos(t0), r1 * math.sin(t0), z1)
            p11 = (r1 * math.cos(t1), r1 * math.sin(t1), z1)
            if r0 == 0:
                tris.append((p00, p11, p10) if z1 == z0 else (p00, p01, p11))
                continue
            if r1 == 0:
                tris.append((p00, p01, p10))
                continue
            tris += [(p00, p01, p11), (p00, p11, p10)]
    return tris


def write_samples(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / "bracket.stl", folder / "vase.stl"]
    write_stl(paths[0], bracket(), "Facet sample: plate, 60 x 40 x 8 mm, hole 12 mm")
    write_stl(paths[1], vase(), "Facet sample: vase")
    return paths
