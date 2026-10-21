import math

import pytest

from facet.application.errors import FileFormatError, MeasureError, NoModelError
from facet.application.models import ModelService
from facet.demo import write_samples
from facet.infrastructure.mesh_files import MeshFiles
from facet.infrastructure.settings import MemorySettings


def test_open_gives_a_record_with_exact_size(models, cube_file):
    record = models.open(str(cube_file))
    assert record.name == "box.stl" and record.format == "STL" and record.triangles == 12
    assert record.size == (10, 20, 30)
    assert record.file_size == cube_file.stat().st_size


def test_analysis_of_a_box(models, cube_file):
    models.open(str(cube_file))
    a = models.analyse()
    assert a.volume == pytest.approx(6000) and a.area == pytest.approx(2200)
    assert a.watertight and a.shells == 1 and not a.inside_out
    assert a.centroid == pytest.approx((5, 10, 15))


def test_results_carry_the_token_of_their_model(models, cube_file, tmp_path):
    first = models.open(str(cube_file))
    old = models.analyse()
    second = models.open(str(cube_file))
    assert old.token == first.token != second.token == models.analyse().token


def test_nothing_open_is_an_error():
    service = ModelService(MeshFiles(), MemorySettings())
    with pytest.raises(NoModelError):
        service.analyse()
    with pytest.raises(NoModelError):
        service.corners(0)
    assert service.measure_distance((0, 0, 0), (1, 1, 1)).values[0].value > 0  # needs no model


def test_bad_file_keeps_the_previous_model(models, cube_file, tmp_path):
    models.open(str(cube_file))
    bad = tmp_path / "bad.stl"
    bad.write_bytes(b"junk")
    with pytest.raises(FileFormatError):
        models.open(str(bad))
    assert models.is_open and models.analyse().volume == pytest.approx(6000)


def test_shading_gives_normals_and_edges(models, cube_file):
    models.open(str(cube_file))
    shading = models.shading(smooth=True, edges=True)
    assert len(shading.normals) == 12 * 9 and len(shading.edge_codes) == 12
    flat = models.shading(smooth=False, edges=False)
    assert flat.normals is None and flat.edge_codes is None


def test_weight_by_material(models):
    # 10 cm cube of water-like density 1 is 1 kg; PLA is 1.24
    assert models.weight(1_000_000, "mm", "PLA") == pytest.approx(1240)
    assert models.weight(-1_000_000, "mm", "PLA") == pytest.approx(1240)  # inside out is still mass
    assert models.weight(1000, "cm", "Steel") == pytest.approx(7850)
    assert models.weight(1, "in", "PLA") == pytest.approx(16.387064 * 1.24)


def test_distance_has_its_axis_parts(models):
    m = models.measure_distance((0, 0, 0), (3, 4, 12))
    assert [(v.label, v.value) for v in m.values] == [
        ("Distance", 13.0), ("ΔX", 3.0), ("ΔY", 4.0), ("ΔZ", 12.0)]


def test_angle_and_circle(models):
    angle = models.measure_angle((1, 0, 0), (0, 0, 0), (0, 1, 0))
    assert angle.values[0].value == pytest.approx(90) and angle.values[1].value == pytest.approx(90)
    circle = models.measure_circle((6, 0, 0), (0, 6, 0), (-6, 0, 0))
    assert circle.values[0].value == pytest.approx(12) and circle.values[1].value == pytest.approx(6)
    assert circle.centre == pytest.approx((0, 0, 0), abs=1e-9)
    with pytest.raises(MeasureError):
        models.measure_circle((0, 0, 0), (1, 0, 0), (2, 0, 0))
    with pytest.raises(MeasureError):
        models.measure_angle((0, 0, 0), (0, 0, 0), (1, 0, 0))


def test_snap_finds_corner_edge_or_surface(models, cube_file):
    models.open(str(cube_file))
    # the bottom face is z = 0; its triangles come first. Shoot straight up at a point near a corner.
    ray_down = (0, 0, -1)
    bottom = 0
    near_corner = models.snap(bottom, (0.3, 0.2, 5), ray_down, radius=1.0)
    assert near_corner.kind == "corner" and near_corner.point == (0, 0, 0)
    near_edge = models.snap(1, (5, 0.2, 5), ray_down, radius=1.0)  # triangle 1 owns the y = 0 edge
    assert near_edge.kind == "edge" and near_edge.point[1] == pytest.approx(0, abs=1e-9)
    surface = models.snap(bottom, (2.5, 10, 5), ray_down, radius=1.0)
    assert surface.kind == "surface" and surface.point == pytest.approx((2.5, 10, 0))
    no_snap = models.snap(bottom, (0.3, 0.2, 5), ray_down, radius=1.0, corners=False, edges=False)
    assert no_snap.kind == "surface"


def test_snap_on_the_rim_of_a_triangle_still_gives_a_point(models, cube_file):
    models.open(str(cube_file))
    # just outside the triangle: the click landed on its rim
    snap = models.snap(0, (10.0000001, 20.0000001, 5), (0, 0, -1), radius=0.5)
    assert snap.point[2] == pytest.approx(0)


def test_recent_models_are_remembered_most_recent_first(models, cube_file, tmp_path):
    other = tmp_path / "other.stl"
    other.write_bytes(cube_file.read_bytes())
    models.open(str(cube_file))
    models.open(str(other))
    assert models.recent() == [str(other), str(cube_file)]
    models.open(str(cube_file))
    assert models.recent()[0] == str(cube_file)
    models.forget(str(cube_file))
    assert models.recent() == [str(other)]
    other.unlink()
    assert models.recent() == []  # files that are gone drop out


def test_demo_bracket_is_a_precise_part(models, tmp_path):
    bracket, vase = write_samples(tmp_path)
    record = models.open(str(bracket))
    assert record.size == pytest.approx((60, 40, 8))
    expected = 60 * 40 * 8 - math.pi * 6 ** 2 * 8  # the hole is a 96-sided polygon: a hair less
    assert models.analyse().volume == pytest.approx(expected, rel=2e-3)
    assert models.analyse().watertight
    models.open(str(vase))
    assert models.analyse().watertight
