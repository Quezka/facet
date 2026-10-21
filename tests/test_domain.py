import math
from array import array

import pytest

from facet.domain import geometry as g
from facet.domain.mesh import (Mesh, bounds, check_health, feature_edges, smooth_normals,
                               solid_properties, weld)

from .shapes import cube


def mesh_of(triangles) -> Mesh:
    return Mesh(array("f", [c for tri in triangles for v in tri for c in v]))


def test_distance_and_angle():
    assert g.distance((0, 0, 0), (3, 4, 0)) == 5
    assert g.angle_at((0, 0, 0), (1, 0, 0), (0, 1, 0)) == pytest.approx(90)
    assert g.angle_at((0, 0, 0), (1, 0, 0), (-1, 0, 0)) == pytest.approx(180)
    assert g.angle_at((1, 1, 1), (1, 1, 1), (2, 2, 2)) == 0.0  # no direction: no angle


def test_circle_through_three_points():
    centre, radius = g.circle_through((5, 0, 0), (0, 5, 0), (-5, 0, 0))
    assert radius == pytest.approx(5)
    assert centre == pytest.approx((0, 0, 0), abs=1e-9)
    # in a tilted plane too
    centre, radius = g.circle_through((1, 0, 2), (0, 1, 2), (-1, 0, 2))
    assert radius == pytest.approx(1) and centre[2] == pytest.approx(2)
    assert g.circle_through((0, 0, 0), (1, 1, 1), (2, 2, 2)) is None


def test_ray_triangle_hits_and_misses():
    tri = ((0, 0, 0), (4, 0, 0), (0, 4, 0))
    assert g.ray_triangle((1, 1, 5), (0, 0, -1), *tri) == pytest.approx(5)
    assert g.ray_triangle((1, 1, -5), (0, 0, 1), *tri) == pytest.approx(5)  # from below too
    assert g.ray_triangle((3, 3, 5), (0, 0, -1), *tri) is None
    assert g.ray_triangle((1, 1, 5), (0, 0, 1), *tri) is None  # behind the ray


def test_closest_point_on_segment():
    assert g.closest_on_segment((5, 3, 0), (0, 0, 0), (10, 0, 0)) == (5, 0, 0)
    assert g.closest_on_segment((-5, 3, 0), (0, 0, 0), (10, 0, 0)) == (0, 0, 0)


def test_box_volume_area_centre_and_bounds():
    box = mesh_of(cube(10, 20, 30))
    solid = solid_properties(box)
    assert solid.volume == pytest.approx(6000)
    assert solid.area == pytest.approx(2 * (200 + 300 + 600))
    assert solid.centroid == pytest.approx((5, 10, 15))
    assert bounds(box) == ((0, 0, 0), (10, 20, 30))


def test_volume_is_negative_for_inside_out_faces():
    flipped = mesh_of([(a, c, b) for a, b, c in cube(1, 1, 1)])
    assert solid_properties(flipped).volume == pytest.approx(-1)


def test_volume_is_right_far_from_the_origin():
    far = mesh_of([tuple((x + 1e5, y + 1e5, z + 1e5) for x, y, z in tri) for tri in cube(2, 2, 2)])
    assert solid_properties(far).volume == pytest.approx(8, rel=1e-3)


def test_closed_box_is_watertight_with_one_shell():
    box = mesh_of(cube(1, 2, 3))
    health = check_health(box, weld(box))
    assert health.watertight and health.shells == 1 and health.vertices == 8
    assert health.open_edges == 0 and health.degenerate == 0


def test_a_missing_triangle_leaves_open_edges():
    triangles = cube(1, 1, 1)[:-1]
    box = mesh_of(triangles)
    health = check_health(box, weld(box))
    assert not health.watertight and health.open_edges == 3


def test_two_separate_boxes_are_two_shells():
    far = [tuple((x + 10, y, z) for x, y, z in tri) for tri in cube(1, 1, 1)]
    both = mesh_of(cube(1, 1, 1) + far)
    assert check_health(both, weld(both)).shells == 2


def test_degenerate_triangle_is_counted():
    flat = mesh_of(cube(1, 1, 1) + [((0, 0, 0), (0, 0, 0), (1, 1, 1))])
    assert check_health(flat, weld(flat)).degenerate == 1


def test_box_has_all_its_edges_as_features_but_not_the_diagonals():
    box = mesh_of(cube(1, 1, 1))
    codes = feature_edges(box, weld(box))
    flagged = sum(bin(c).count("1") for c in codes)
    assert flagged == 2 * 12  # each of the 12 box edges is on two triangles; 6 diagonals aren't


def test_smooth_normals_follow_a_sphere_but_not_a_box():
    box = mesh_of(cube(1, 1, 1))
    normals = smooth_normals(box, weld(box))
    # a corner of the box keeps its face normal, each face is flat
    for t in range(box.triangle_count):
        n = normals[9 * t:9 * t + 3]
        assert sorted(abs(c) for c in n) == pytest.approx([0, 0, 1])
    sphere = mesh_of(_sphere(12, 8))
    top = smooth_normals(sphere, weld(sphere))
    # on a sphere, the smoothed normal at a vertex points away from the centre
    for i in range(0, 9 * 20, 3):
        x, y, z = sphere.positions[i:i + 3]
        n = top[i:i + 3]
        length = math.sqrt(x * x + y * y + z * z)
        assert (x * n[0] + y * n[1] + z * n[2]) / length > 0.9


def _sphere(segments, rings):
    pts = {}
    for r in range(rings + 1):
        for s in range(segments):
            theta, phi = math.pi * r / rings, 2 * math.pi * s / segments
            pts[(r, s)] = (math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi),
                           math.cos(theta))
    tris = []
    for r in range(rings):
        for s in range(segments):
            a, b = pts[(r, s)], pts[(r, (s + 1) % segments)]
            c, d = pts[(r + 1, s)], pts[(r + 1, (s + 1) % segments)]
            if r > 0:
                tris.append((a, c, b))
            if r < rings - 1:
                tris.append((b, c, d))
    return tris


def test_dragging_right_turns_the_model_to_the_right():
    from facet.presentation.camera import Camera
    camera = Camera()
    camera.frame((0, 0, 0), (10, 10, 10))
    camera.look_from("front")
    before = camera.project((5, 0, 5), 800, 600)[0]  # the middle of the front face
    camera.orbit(50, 0)                              # drag to the right
    after = camera.project((5, 0, 5), 800, 600)[0]
    assert after > before                            # the face in front moved right on screen
