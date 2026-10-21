"""Small vector helpers and the exact geometry behind picking and measuring.

Points are plain (x, y, z) tuples of floats, in the model's own units.
"""
from __future__ import annotations

import math

Vec = tuple[float, float, float]


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a: Vec, k: float) -> Vec:
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a: Vec) -> float:
    return math.sqrt(dot(a, a))


def distance(a: Vec, b: Vec) -> float:
    return length(sub(a, b))


def normalized(a: Vec) -> Vec:
    n = length(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 0 else (0.0, 0.0, 0.0)


def midpoint(a: Vec, b: Vec) -> Vec:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)


def angle_at(vertex: Vec, a: Vec, b: Vec) -> float:
    """The angle in degrees at `vertex` between the directions to `a` and to `b`."""
    u, v = sub(a, vertex), sub(b, vertex)
    nu, nv = length(u), length(v)
    if nu == 0 or nv == 0:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(u, v) / (nu * nv)))))


def circle_through(a: Vec, b: Vec, c: Vec) -> tuple[Vec, float] | None:
    """Centre and radius of the circle through three points; None when they are in a line."""
    ab, ac = sub(b, a), sub(c, a)
    n = cross(ab, ac)
    n2 = dot(n, n)
    if n2 < 1e-18:
        return None
    # Standard circumcentre formula, relative to `a`.
    t = scale(cross(n, ab), dot(ac, ac))
    u = scale(cross(ac, n), dot(ab, ab))
    offset = scale(add(t, u), 1.0 / (2.0 * n2))
    return add(a, offset), length(offset)


def ray_triangle(origin: Vec, direction: Vec, a: Vec, b: Vec, c: Vec) -> float | None:
    """Möller–Trumbore: the distance along the ray to the triangle, or None for a miss
    (the triangle is hit from either side)."""
    e1, e2 = sub(b, a), sub(c, a)
    p = cross(direction, e2)
    det = dot(e1, p)
    if abs(det) < 1e-18:
        return None
    inv = 1.0 / det
    s = sub(origin, a)
    u = dot(s, p) * inv
    if u < -1e-9 or u > 1 + 1e-9:
        return None
    q = cross(s, e1)
    v = dot(direction, q) * inv
    if v < -1e-9 or u + v > 1 + 1e-9:
        return None
    t = dot(e2, q) * inv
    return t if t >= 0 else None


def closest_on_segment(p: Vec, a: Vec, b: Vec) -> Vec:
    ab = sub(b, a)
    denom = dot(ab, ab)
    if denom == 0:
        return a
    t = max(0.0, min(1.0, dot(sub(p, a), ab) / denom))
    return add(a, scale(ab, t))
