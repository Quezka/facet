import struct
import zipfile

import pytest

from facet.application.errors import FileFormatError
from facet.infrastructure.mesh_files import MeshFiles

from .shapes import cube, write_ascii_stl, write_binary_stl

reader = MeshFiles()


def test_binary_stl(cube_file):
    mesh = reader.read(str(cube_file))
    assert mesh.triangle_count == 12 and mesh.colors is None
    assert mesh.name == "box"


def test_binary_stl_that_starts_with_solid_is_still_binary(tmp_path):
    path = tmp_path / "tricky.stl"
    write_binary_stl(path, cube(1, 1, 1))
    data = bytearray(path.read_bytes())
    data[:5] = b"solid"
    path.write_bytes(bytes(data))
    assert reader.read(str(path)).triangle_count == 12


def test_ascii_stl(tmp_path):
    path = tmp_path / "text.stl"
    write_ascii_stl(path, cube(1, 2, 3))
    mesh = reader.read(str(path))
    assert mesh.triangle_count == 12
    assert max(mesh.positions) == 3


def test_binary_stl_colours(tmp_path):
    path = tmp_path / "coloured.stl"
    red = 0x8000 | (31 << 10)  # Magics: bit 15 = colour given, then R, G, B in 5 bits
    write_binary_stl(path, cube(1, 1, 1), attributes=[red] * 12)
    mesh = reader.read(str(path))
    assert list(mesh.colors[:3]) == [255, 0, 0]


def test_garbage_is_refused(tmp_path):
    path = tmp_path / "bad.stl"
    path.write_bytes(b"not a model at all")
    with pytest.raises(FileFormatError):
        reader.read(str(path))
    other = tmp_path / "x.dwg"
    other.write_bytes(b"x")
    with pytest.raises(FileFormatError):
        reader.read(str(other))


def test_empty_stl_is_refused(tmp_path):
    path = tmp_path / "empty.stl"
    write_binary_stl(path, [])
    with pytest.raises(FileFormatError):
        reader.read(str(path))


def test_obj_triangulates_quads_and_reads_material_colours(tmp_path):
    (tmp_path / "m.mtl").write_text("newmtl red\nKd 1 0 0\n")
    path = tmp_path / "quad.obj"
    path.write_text("mtllib m.mtl\nv 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nusemtl red\nf 1 2 3 4\n")
    mesh = reader.read(str(path))
    assert mesh.triangle_count == 2
    assert list(mesh.colors[:3]) == [255, 0, 0]


def test_obj_with_negative_indices_and_vertex_colours(tmp_path):
    path = tmp_path / "neg.obj"
    path.write_text("v 0 0 0 0 1 0\nv 1 0 0 0 1 0\nv 0 1 0 0 1 0\nf -3/1/1 -2/2/1 -1/3/1\n")
    mesh = reader.read(str(path))
    assert mesh.triangle_count == 1 and list(mesh.colors[:3]) == [0, 255, 0]


def test_ply_ascii_and_binary(tmp_path):
    ascii_ply = tmp_path / "a.ply"
    ascii_ply.write_text("ply\nformat ascii 1.0\nelement vertex 4\nproperty float x\nproperty float y\n"
                         "property float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\n"
                         "element face 1\nproperty list uchar int vertex_indices\nend_header\n"
                         "0 0 0 255 0 0\n1 0 0 255 0 0\n1 1 0 255 0 0\n0 1 0 255 0 0\n4 0 1 2 3\n")
    mesh = reader.read(str(ascii_ply))
    assert mesh.triangle_count == 2 and list(mesh.colors[:3]) == [255, 0, 0]

    binary = tmp_path / "b.ply"
    header = (b"ply\nformat binary_little_endian 1.0\nelement vertex 3\nproperty float x\n"
              b"property float y\nproperty float z\nelement face 1\n"
              b"property list uchar int vertex_indices\nend_header\n")
    body = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0) + struct.pack("<B3i", 3, 0, 1, 2)
    binary.write_bytes(header + body)
    assert reader.read(str(binary)).triangle_count == 1


def test_3mf_units_and_transforms(tmp_path):
    model = """<?xml version="1.0"?>
<model unit="inch" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <resources><object id="1" type="model"><mesh>
  <vertices><vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/><vertex x="0" y="1" z="0"/></vertices>
  <triangles><triangle v1="0" v2="1" v3="2"/></triangles></mesh></object></resources>
 <build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 10 0 0"/></build></model>"""
    path = tmp_path / "part.3mf"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("3D/3dmodel.model", model)
    mesh = reader.read(str(path))
    assert mesh.triangle_count == 1 and mesh.unit_hint == "in"
    assert min(mesh.positions[0::3]) == 10  # moved by the build item's transform


def test_siblings_lists_model_files_by_name(tmp_path):
    for name in ("b.stl", "a.obj", "notes.txt", "C.PLY"):
        (tmp_path / name).write_bytes(b"x")
    names = [p.rsplit("/", 1)[-1] for p in reader.siblings(str(tmp_path / "b.stl"))]
    assert names == ["a.obj", "b.stl", "C.PLY"]
