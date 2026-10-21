"""Tiny meshes for tests."""
import struct


def cube(x: float, y: float, z: float):
    """A box from the origin, faces counter-clockwise seen from outside (12 triangles)."""
    p = [(0, 0, 0), (x, 0, 0), (x, y, 0), (0, y, 0), (0, 0, z), (x, 0, z), (x, y, z), (0, y, z)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, d in quads:
        tris += [(p[a], p[b], p[c]), (p[a], p[c], p[d])]
    return tris


def write_binary_stl(path, triangles, attributes=None):
    out = bytearray(b"test".ljust(80, b" ")) + struct.pack("<I", len(triangles))
    for i, (a, b, c) in enumerate(triangles):
        attribute = attributes[i] if attributes else 0
        out += struct.pack("<12fH", 0, 0, 0, *a, *b, *c, attribute)
    path.write_bytes(bytes(out))


def write_ascii_stl(path, triangles):
    lines = ["solid test"]
    for a, b, c in triangles:
        lines.append("facet normal 0 0 0\n outer loop")
        lines += [f"  vertex {v[0]} {v[1]} {v[2]}" for v in (a, b, c)]
        lines.append(" endloop\nendfacet")
    lines.append("endsolid test")
    path.write_text("\n".join(lines), encoding="ascii")
