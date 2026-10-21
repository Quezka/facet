"""Reading model files: STL (binary and text), OBJ, PLY and 3MF, into a Mesh.

Only the triangles and, when a file has them, colours are kept. Textures, normals stored in
the file and animation are ignored: Facet works the normals out itself.
"""
from __future__ import annotations

import re
import struct
import sys
import zipfile
from array import array
from pathlib import Path
from xml.etree import ElementTree

from ..application.errors import FileAccessError, FileFormatError
from ..domain.mesh import Mesh

_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_VERTEX = re.compile(rf"vertex\s+({_NUMBER})\s+({_NUMBER})\s+({_NUMBER})", re.IGNORECASE)


def _floats(data: bytes | bytearray) -> array:
    out = array("f")
    out.frombytes(bytes(data))
    if sys.byteorder == "big":
        out.byteswap()
    return out


# ---- STL ----------------------------------------------------------------------------

def read_stl(path: Path) -> Mesh:
    data = path.read_bytes()
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if len(data) == 84 + 50 * count or (not data[:5].lower() == b"solid"
                                              and len(data) >= 84 + 50 * count):
            return _binary_stl(data, count, path)
    if data[:5].lower() == b"solid" or b"vertex" in data[:4096]:
        return _ascii_stl(data, path)
    raise FileFormatError("This doesn't look like an STL file.")


def _binary_stl(data: bytes, count: int, path: Path) -> Mesh:
    out = bytearray()
    for i in range(count):
        start = 84 + 50 * i + 12
        out += data[start:start + 36]
    positions = _floats(out)
    colors = None
    low, high = data[84 + 48:84 + 50 * count:50], data[84 + 49:84 + 50 * count:50]
    if any(high) or any(low):
        colors = _stl_colors(low, high)
    return Mesh(positions, colors, path.stem)


def _stl_colors(low: bytes, high: bytes) -> array | None:
    """Magics-style colours: bit 15 set means 'colour given', then 5 bits each of B, G, R."""
    valid = sum(1 for h in high if h & 0x80)
    if valid < len(high) / 2:
        return None
    out = bytearray()
    for lo, hi in zip(low, high):
        value = lo | (hi << 8)
        if value & 0x8000:
            r, g, b = (value >> 10) & 31, (value >> 5) & 31, value & 31
            rgb = bytes((r * 255 // 31, g * 255 // 31, b * 255 // 31))
        else:
            rgb = b"\xc8\xc8\xc8"
        out += rgb * 3
    return array("B", out)


def _ascii_stl(data: bytes, path: Path) -> Mesh:
    text = data.decode("utf-8", errors="replace")
    values = _VERTEX.findall(text)
    if not values or len(values) % 3:
        raise FileFormatError("This STL file is damaged or empty.")
    positions = array("f", (float(v) for triple in values for v in triple))
    return Mesh(positions, None, path.stem)


# ---- OBJ ----------------------------------------------------------------------------

def read_obj(path: Path) -> Mesh:
    vertices: list[tuple[float, float, float]] = []
    vertex_colors: list[tuple[int, int, int] | None] = []
    materials = _read_mtl(path)
    current = None
    positions = array("f")
    colors = bytearray()
    any_color = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("v "):
            parts = line.split()
            try:
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            except (IndexError, ValueError):
                raise FileFormatError("This OBJ file is damaged.") from None
            if len(parts) >= 7:
                try:
                    vertex_colors.append(tuple(max(0, min(255, round(float(c) * 255)))
                                               for c in parts[4:7]))
                    any_color = True
                except ValueError:
                    vertex_colors.append(None)
            else:
                vertex_colors.append(None)
        elif line.startswith("usemtl"):
            current = materials.get(line.split(None, 1)[1].strip()) if " " in line else None
        elif line.startswith("f "):
            corners = []
            for token in line.split()[1:]:
                index = int(token.split("/")[0])
                corners.append(index - 1 if index > 0 else len(vertices) + index)
            for k in range(1, len(corners) - 1):
                for c in (corners[0], corners[k], corners[k + 1]):
                    try:
                        positions.extend(vertices[c])
                    except IndexError:
                        raise FileFormatError("This OBJ file is damaged.") from None
                    colour = vertex_colors[c] or current or (200, 200, 200)
                    colors += bytes(colour)
                    if current:
                        any_color = True
    if not len(positions):
        raise FileFormatError("This OBJ file has no faces.")
    return Mesh(positions, array("B", colors) if any_color else None, path.stem)


def _read_mtl(obj: Path) -> dict[str, tuple[int, int, int]]:
    """Diffuse colours of the materials named by the OBJ's `mtllib` lines."""
    found: dict[str, tuple[int, int, int]] = {}
    try:
        text = obj.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return found
    for line in text.splitlines():
        if line.startswith("mtllib"):
            name = line.split(None, 1)[1].strip() if " " in line else ""
            path = obj.with_name(name)
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            material = None
            for row in lines:
                row = row.strip()
                if row.startswith("newmtl"):
                    material = row.split(None, 1)[1].strip() if " " in row else None
                elif row.startswith("Kd") and material:
                    try:
                        found[material] = tuple(max(0, min(255, round(float(c) * 255)))
                                                for c in row.split()[1:4])
                    except ValueError:
                        pass
    return found


# ---- PLY ----------------------------------------------------------------------------

_PLY_TYPES = {"char": "b", "int8": "b", "uchar": "B", "uint8": "B", "short": "h", "int16": "h",
              "ushort": "H", "uint16": "H", "int": "i", "int32": "i", "uint": "I",
              "uint32": "I", "float": "f", "float32": "f", "double": "d", "float64": "d"}


def read_ply(path: Path) -> Mesh:
    data = path.read_bytes()
    end = data.find(b"end_header")
    if not data.startswith(b"ply") or end < 0:
        raise FileFormatError("This doesn't look like a PLY file.")
    body_start = data.index(b"\n", end) + 1
    header = data[:end].decode("ascii", errors="replace").splitlines()
    fmt = "ascii"
    elements: list[tuple[str, int, list[tuple]]] = []
    for line in header:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "format":
            fmt = parts[1]
        elif parts[0] == "element":
            elements.append((parts[1], int(parts[2]), []))
        elif parts[0] == "property" and elements:
            if parts[1] == "list":
                elements[-1][2].append(("list", parts[4], parts[2], parts[3]))
            else:
                elements[-1][2].append(("scalar", parts[2], parts[1]))
    vertices: list[tuple[float, float, float]] = []
    colours: list[tuple[int, int, int] | None] = []
    faces: list[list[int]] = []
    if fmt == "ascii":
        tokens = iter(data[body_start:].split())

        def read(kind: str):
            token = next(tokens)
            return float(token) if kind in ("f", "d") else int(token)
    else:
        order = "<" if fmt == "binary_little_endian" else ">"
        cursor = [body_start]

        def read(kind: str):
            size = struct.calcsize(kind)
            value = struct.unpack_from(order + kind, data, cursor[0])[0]
            cursor[0] += size
            return value
    try:
        for name, count, props in elements:
            for _ in range(count):
                row = {}
                for prop in props:
                    if prop[0] == "scalar":
                        row[prop[1]] = read(_PLY_TYPES[prop[2]])
                    else:
                        n = int(read(_PLY_TYPES[prop[2]]))
                        row[prop[1]] = [int(read(_PLY_TYPES[prop[3]])) for _ in range(n)]
                if name == "vertex":
                    vertices.append((float(row["x"]), float(row["y"]), float(row["z"])))
                    colours.append((int(row["red"]), int(row["green"]), int(row["blue"]))
                                   if "red" in row else None)
                elif name == "face":
                    faces.append(row.get("vertex_indices") or row.get("vertex_index") or [])
    except (KeyError, StopIteration, struct.error, ValueError):
        raise FileFormatError("This PLY file is damaged.") from None
    positions = array("f")
    colors = bytearray()
    any_color = any(c is not None for c in colours)
    for face in faces:
        for k in range(1, len(face) - 1):
            for c in (face[0], face[k], face[k + 1]):
                try:
                    positions.extend(vertices[c])
                except IndexError:
                    raise FileFormatError("This PLY file is damaged.") from None
                colors += bytes(colours[c] or (200, 200, 200))
    if not len(positions):
        raise FileFormatError("This PLY file has no faces.")
    return Mesh(positions, array("B", colors) if any_color else None, path.stem)


# ---- 3MF ----------------------------------------------------------------------------

_UNITS = {"micron": "mm", "millimeter": "mm", "centimeter": "cm", "meter": "m", "inch": "in",
          "foot": None}
_UNIT_SCALE = {"micron": 0.001}


def read_3mf(path: Path) -> Mesh:
    try:
        with zipfile.ZipFile(path) as archive:
            name = next((n for n in archive.namelist() if n.lower().endswith(".model")), None)
            if name is None:
                raise FileFormatError("This 3MF file has no model in it.")
            root = ElementTree.fromstring(archive.read(name))
    except zipfile.BadZipFile:
        raise FileFormatError("This doesn't look like a 3MF file.") from None
    except ElementTree.ParseError:
        raise FileFormatError("This 3MF file is damaged.") from None

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    unit = root.get("unit", "millimeter")
    factor = _UNIT_SCALE.get(unit, 1.0)
    objects: dict[str, ElementTree.Element] = {}
    build: list[ElementTree.Element] = []
    for child in root.iter():
        if local(child.tag) == "object":
            objects[child.get("id")] = child
        elif local(child.tag) == "item":
            build.append(child)

    positions = array("f")

    def matrix(text: str | None):
        if not text:
            return None
        v = [float(x) for x in text.split()]
        return v if len(v) == 12 else None

    def apply(m, p):
        if m is None:
            return p
        x, y, z = p
        return (m[0] * x + m[3] * y + m[6] * z + m[9], m[1] * x + m[4] * y + m[7] * z + m[10],
                m[2] * x + m[5] * y + m[8] * z + m[11])

    def emit(obj: ElementTree.Element, transforms: list, depth: int = 0):
        if depth > 8:
            return
        for child in obj:
            if local(child.tag) == "mesh":
                points = []
                triangles = []
                for part in child.iter():
                    if local(part.tag) == "vertex":
                        points.append((float(part.get("x")), float(part.get("y")),
                                       float(part.get("z"))))
                    elif local(part.tag) == "triangle":
                        triangles.append((int(part.get("v1")), int(part.get("v2")),
                                          int(part.get("v3"))))
                for tri in triangles:
                    for index in tri:
                        p = points[index]
                        for m in reversed(transforms):
                            p = apply(m, p)
                        positions.extend(p)
            elif local(child.tag) == "components":
                for comp in child:
                    target = objects.get(comp.get("objectid"))
                    if target is not None:
                        emit(target, transforms + [matrix(comp.get("transform"))], depth + 1)

    try:
        for item in build or [None]:
            if item is None:
                for obj in objects.values():
                    emit(obj, [])
                break
            target = objects.get(item.get("objectid"))
            if target is not None:
                emit(target, [matrix(item.get("transform"))])
    except (TypeError, ValueError, IndexError):
        raise FileFormatError("This 3MF file is damaged.") from None
    if not len(positions):
        raise FileFormatError("This 3MF file has no mesh in it.")
    if factor != 1.0:
        positions = array("f", (v * factor for v in positions))
    return Mesh(positions, None, path.stem, unit_hint=_UNITS.get(unit))


READERS = {".stl": read_stl, ".obj": read_obj, ".ply": read_ply, ".3mf": read_3mf}


class MeshFiles:
    """Reads a model from disk by its extension."""

    def read(self, path: str) -> Mesh:
        target = Path(path)
        reader = READERS.get(target.suffix.lower())
        if reader is None:
            raise FileFormatError("Facet can't open this kind of file.")
        try:
            mesh = reader(target)
        except OSError:
            raise FileAccessError("The file couldn't be read.") from None
        except (UnicodeError, struct.error, IndexError):
            raise FileFormatError("This file is damaged.") from None
        if not mesh.triangle_count:
            raise FileFormatError("This file has no triangles in it.")
        return mesh

    def size(self, path: str) -> int:
        try:
            return Path(path).stat().st_size
        except OSError:
            return 0

    def siblings(self, path: str) -> list[str]:
        from .. import MODEL_EXTENSIONS
        folder = Path(path).parent
        try:
            names = [p for p in folder.iterdir()
                     if p.is_file() and p.suffix.lower() in MODEL_EXTENSIONS]
        except OSError:
            return []
        return [str(p) for p in sorted(names, key=lambda p: p.name.lower())]
