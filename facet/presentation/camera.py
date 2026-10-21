"""An orbiting camera (Z is up, like in STL files and 3D printing) and its matrices."""
from __future__ import annotations

import math

from PySide6.QtGui import QMatrix4x4, QVector3D, QVector4D

VIEWS = {  # name -> (yaw, pitch) in degrees; the camera looks at the centre from there
    "front": (0.0, 0.0), "back": (180.0, 0.0), "left": (90.0, 0.0), "right": (-90.0, 0.0),
    "top": (0.0, 89.9), "bottom": (0.0, -89.9), "iso": (-35.0, 30.0),
}


class Camera:
    FOV = 40.0

    def __init__(self):
        self.centre = QVector3D(0, 0, 0)
        self.radius = 1.0            # size of what we look at (half the bounding diagonal)
        self.distance = 3.0
        self.yaw, self.pitch = VIEWS["iso"]
        self.orthographic = False
        self.aspect = 1.0

    # ---- placing it ------------------------------------------------------------------
    def frame(self, lo, hi):
        self.centre = QVector3D(*((a + b) / 2 for a, b in zip(lo, hi)))
        self.radius = max(math.dist(lo, hi) / 2, 1e-6)
        self.distance = self.radius / math.sin(math.radians(self.FOV / 2)) * 1.05

    def look_from(self, name: str):
        self.yaw, self.pitch = VIEWS[name]

    def orbit(self, dx: float, dy: float):
        self.yaw -= dx * 0.4
        self.pitch = max(-89.9, min(89.9, self.pitch + dy * 0.4))

    def eye(self) -> QVector3D:
        yaw, pitch = math.radians(self.yaw), math.radians(self.pitch)
        offset = QVector3D(math.sin(yaw) * math.cos(pitch) * -1, -math.cos(yaw) * math.cos(pitch),
                           math.sin(pitch))
        return self.centre + offset * self.distance

    def right_up(self) -> tuple[QVector3D, QVector3D]:
        view = self.view_matrix()
        inv, _ok = view.inverted()
        return (inv.map(QVector4D(1, 0, 0, 0)).toVector3D(),
                inv.map(QVector4D(0, 1, 0, 0)).toVector3D())

    def pan(self, dx: float, dy: float, height_px: int):
        """Move the view by a mouse drag so the model follows the cursor."""
        right, up = self.right_up()
        world_per_px = self.visible_height() / max(height_px, 1)
        self.centre = self.centre - right * dx * world_per_px + up * dy * world_per_px

    def visible_height(self) -> float:
        if self.orthographic:
            return 2 * self.distance * math.tan(math.radians(self.FOV / 2))
        return 2 * self.distance * math.tan(math.radians(self.FOV / 2))

    def zoom(self, factor: float):
        self.distance = max(self.radius * 0.02, min(self.radius * 200, self.distance / factor))

    # ---- matrices --------------------------------------------------------------------
    def view_matrix(self) -> QMatrix4x4:
        m = QMatrix4x4()
        up = QVector3D(0, 0, 1)
        if abs(self.pitch) > 89.0:  # looking straight down: 'up' is the yaw direction
            yaw = math.radians(self.yaw)
            up = QVector3D(math.sin(yaw), math.cos(yaw), 0) * (1 if self.pitch > 0 else -1)
        m.lookAt(self.eye(), self.centre, up)
        return m

    def clip_planes(self) -> tuple[float, float]:
        near = max(self.distance - self.radius * 1.5, self.radius * 0.01)
        return near, self.distance + self.radius * 3

    def projection_matrix(self) -> QMatrix4x4:
        m = QMatrix4x4()
        near, far = self.clip_planes()
        if self.orthographic:
            h = self.visible_height() / 2
            m.ortho(-h * self.aspect, h * self.aspect, -h, h, -far, far)
        else:
            m.perspective(self.FOV, self.aspect, near, far)
        return m

    # ---- between the screen and the model ------------------------------------------
    def project(self, point, width: int, height: int):
        """Pixel position (x, y from top-left) of a model point, and whether it's in front."""
        clip = (self.projection_matrix() * self.view_matrix()).map(QVector4D(*point, 1.0))
        if clip.w() == 0:
            return None
        x, y, z = clip.x() / clip.w(), clip.y() / clip.w(), clip.z() / clip.w()
        return ((x + 1) / 2 * width, (1 - y) / 2 * height, z)

    def ray(self, px: float, py: float, width: int, height: int):
        """The line through a pixel as (origin, unit direction), in model space."""
        x, y = px / width * 2 - 1, 1 - py / height * 2
        inv, _ok = (self.projection_matrix() * self.view_matrix()).inverted()
        near = inv.map(QVector4D(x, y, -1, 1))
        far = inv.map(QVector4D(x, y, 1, 1))
        near3 = near.toVector3D() / near.w()
        far3 = far.toVector3D() / far.w()
        direction = (far3 - near3).normalized()
        return (near3.x(), near3.y(), near3.z()), (direction.x(), direction.y(), direction.z())
