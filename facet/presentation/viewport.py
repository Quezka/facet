"""The 3D view: drawing, navigating, picking exact points and drawing measurements on top."""
from __future__ import annotations

import math
from array import array

from PySide6.QtCore import QPointF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage, QMatrix4x4, QPainter, QPen,
                           QPolygonF, QSurfaceFormat, QVector3D, QVector4D)
from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLFramebufferObject, QOpenGLShader,
                              QOpenGLShaderProgram)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..application.models import ModelService
from ..application.errors import ApplicationError
from . import shaders
from .camera import Camera
from .i18n import N_, _
from .uiscale import current as scale, px

GL_DEPTH_TEST, GL_BLEND, GL_CULL_FACE = 0x0B71, 0x0BE2, 0x0B44
GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT = 0x4000, 0x100
GL_TRIANGLES, GL_LINES, GL_FLOAT, GL_UNSIGNED_BYTE = 4, 1, 0x1406, 0x1401
GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_DITHER, GL_LEQUAL = 0x302, 0x303, 0x0BD0, 0x203

TOOLS = {"distance": 2, "angle": 3, "circle": 3}
TOOL_HINTS = {
    "distance": [N_("Click the first point"), N_("Click the second point")],
    "angle": [N_("Click a point on the first side"), N_("Click the corner of the angle"),
              N_("Click a point on the second side")],
    "circle": [N_("Click a point on the hole or curve"), N_("Click a second point on it"),
               N_("Click a third point on it")],
}
EDGE_PATTERNS = [
    b"".join(bytes(corner + flags) for corner in ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)))
    for flags in [(f & 1, f >> 1 & 1, f >> 2 & 1, 0) for f in range(8)]
]
SWATCHES = [(N_("Clay"), "#b9bdc9"), (N_("Indigo"), "#7f80e8"), (N_("Amber"), "#f0a830"),
            (N_("Mint"), "#4cc79a"), (N_("Rose"), "#e5738b"), (N_("Steel"), "#9db1c8"),
            (N_("White"), "#f2f2f2")]


PICK_OFFSETS = sorted(((dx, dy) for dx in range(-6, 7) for dy in range(-6, 7)
                       if dx * dx + dy * dy <= 36), key=lambda o: o[0] ** 2 + o[1] ** 2)


def nice_step(extent: float) -> float:
    """A round grid spacing (1, 2 or 5 times a power of ten) giving about eight cells."""
    raw = extent / 8
    if raw <= 0:
        return 1.0
    power = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 5, 10):
        if raw <= m * power:
            return m * power
    return 10 * power


class Viewport(QOpenGLWidget):
    measured = Signal(str, object)    # tool, the points picked
    hint = Signal(str)                # what to do next, for the status line
    toolFinished = Signal()

    def __init__(self, models: ModelService, parent=None):
        super().__init__(parent)
        self.models = models
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(px(320), px(260))
        fmt = QSurfaceFormat()  # smooth edges and a depth buffer, for this widget only: the rest
        fmt.setDepthBufferSize(24)  # of the window stays an ordinary, cheap-to-repaint window
        fmt.setSamples(4)
        self.setFormat(fmt)
        self.camera = Camera()
        self.failure: str | None = None

        self.record = None
        self.shading = None
        self.mode = 0                 # 0 solid, 1 edges, 2 wire
        self.smooth = True
        self.use_colors = True
        self.base = QColor("#b9bdc9")
        self.show_grid = True
        self.show_dimensions = False
        self.section: tuple[int, float, bool] | None = None   # axis, 0..1, flipped
        self.tool: str | None = None
        self.snapping = True
        self.pending: list[tuple[float, float, float]] = []
        self.measurements: list[tuple[object, str]] = []
        self.format_length = lambda v: f"{v:.2f}"
        self.hover: tuple[tuple[float, float, float], str] | None = None
        self.palette_colors = {"bg": QColor("#e9ebf0"), "grid": QColor(0, 0, 0, 40),
                               "text": QColor("#0e1116"), "accent": QColor("#4b4bc8"),
                               "edge": QColor("#14161c"), "surface": QColor("#ffffff")}

        self._gl_ready = False
        self._buffers: dict[str, QOpenGLBuffer] = {}
        self._dirty: set[str] = set()
        self._count = 0
        self._programs: dict[str, QOpenGLShaderProgram] = {}
        self._drag = None
        self._moved = False
        self._hover_timer = QTimer(self, singleShot=True, interval=45)
        self._hover_timer.timeout.connect(self._update_hover)
        self._hover_at = (0, 0)

    # ---- what the owner controls -----------------------------------------------------
    def set_model(self, record):
        self.record = record
        self.shading = None
        self.pending.clear()
        self.measurements.clear()
        self.hover = None
        self._dirty |= {"pos", "color", "normal", "edge", "id"}
        self._count = record.triangles * 3 if record else 0
        if record:
            self.camera.frame(record.bounds_min, record.bounds_max)
            self.camera.look_from("iso")
        self.update()

    def set_shading(self, shading):
        self.shading = shading
        self._dirty |= {"normal", "edge"}
        self.update()

    def set_palette(self, theme):
        colors = self.palette_colors
        high = theme.border in ("#000000", "#ffffff")
        colors["bg"] = QColor(theme.surface if high else "#101114" if theme.dark else "#e7e9ef")
        grid = QColor(theme.text)
        grid.setAlpha(46)
        colors["grid"] = grid
        colors["text"] = QColor(theme.text)
        colors["accent"] = QColor(theme.accent)
        colors["edge"] = QColor("#e8e9ee" if theme.dark else "#1b1d24")
        colors["surface"] = QColor(theme.surface)
        self.update()

    def set_tool(self, tool: str | None):
        self.tool = tool
        self.pending.clear()
        self.hover = None
        self._announce()
        self.setCursor(Qt.CrossCursor if tool else Qt.ArrowCursor)
        self.update()

    def cancel(self):
        if self.pending:
            self.pending.clear()
            self._announce()
            self.update()
        elif self.tool:
            self.set_tool(None)
            self.toolFinished.emit()

    def fit(self):
        if self.record:
            self.camera.frame(self.record.bounds_min, self.record.bounds_max)
            self.update()

    def look_from(self, name: str):
        self.camera.look_from(name)
        self.update()

    def snapshot(self) -> QImage:
        return self.grabFramebuffer()

    def _announce(self):
        if self.tool:
            self.hint.emit(_(TOOL_HINTS[self.tool][len(self.pending)]))
        else:
            self.hint.emit("")

    # ---- OpenGL ----------------------------------------------------------------------
    def initializeGL(self):
        try:
            self._programs["model"] = self._program(shaders.MODEL_VERTEX, shaders.MODEL_FRAGMENT)
            self._programs["pick"] = self._program(shaders.PICK_VERTEX, shaders.PICK_FRAGMENT)
            self._programs["line"] = self._program(shaders.LINE_VERTEX, shaders.LINE_FRAGMENT)
            self._buffers = {name: QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                             for name in ("pos", "color", "normal", "edge", "id", "line")}
            for buffer in self._buffers.values():
                buffer.create()
            self._gl_ready = True
        except RuntimeError as error:
            self.failure = str(error)

    def _program(self, vertex: str, fragment: str) -> QOpenGLShaderProgram:
        program = QOpenGLShaderProgram(self)
        if not (program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, vertex)
                and program.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, fragment)
                and program.link()):
            raise RuntimeError(program.log())
        return program

    def _upload(self):
        """Send whatever changed to the graphics card (the buffers hold bytes, nothing more)."""
        r = self.record
        for name in sorted(self._dirty):
            buffer = self._buffers[name]
            data = b""
            if r is not None:
                if name == "pos":
                    data = r.positions.tobytes()
                elif name == "color" and r.colors is not None:
                    data = r.colors.tobytes()
                elif name == "normal" and self.shading and self.shading.normals is not None:
                    data = self.shading.normals.tobytes()
                elif name == "edge":
                    codes = self.shading.edge_codes if self.shading else None
                    data = (b"".join(EDGE_PATTERNS[c] for c in codes) if codes is not None
                            else EDGE_PATTERNS[0] * r.triangles)
                elif name == "id" and self._need_ids:
                    data = b"".join(bytes(((t + 1) & 255, (t + 1) >> 8 & 255, (t + 1) >> 16 & 255, 255)) * 3
                                    for t in range(r.triangles))
            buffer.bind()
            buffer.allocate(data, len(data)) if data else buffer.allocate(4)
            buffer.release()
        self._dirty.clear()

    _need_ids = False

    def _uses(self, name: str) -> bool:
        r = self.record
        if name == "color":
            return bool(r and r.colors is not None and self.use_colors)
        if name == "normal":
            return bool(self.shading and self.shading.normals is not None and self.smooth)
        return True

    def _matrices(self) -> tuple[QMatrix4x4, QMatrix4x4]:
        self.camera.aspect = max(self.width(), 1) / max(self.height(), 1)
        view = self.camera.view_matrix()
        return self.camera.projection_matrix() * view, view

    def _section_plane(self):
        if self.section is None or self.record is None:
            return None
        axis, t, flip = self.section
        lo, hi = self.record.bounds_min[axis], self.record.bounds_max[axis]
        normal = [0.0, 0.0, 0.0]
        normal[axis] = -1.0 if flip else 1.0
        offset = lo + t * (hi - lo)
        return (*normal, -offset if flip else offset)

    def _bind_model_attributes(self, program, with_ids: bool = False):
        program.bind()
        self._buffers["pos"].bind()
        program.enableAttributeArray("aPos")
        program.setAttributeBuffer("aPos", GL_FLOAT, 0, 3, 12)
        if with_ids:
            self._buffers["id"].bind()
            program.enableAttributeArray("aId")
            program.setAttributeBuffer("aId", GL_UNSIGNED_BYTE, 0, 4, 4)

    def paintGL(self):
        f = self.context().functions()
        bg = self.palette_colors["bg"]
        f.glClearColor(bg.redF(), bg.greenF(), bg.blueF(), 1.0)
        f.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self._gl_ready and self.record is not None:
            if self._dirty:
                self._upload()
            f.glEnable(GL_DEPTH_TEST)
            f.glDepthFunc(GL_LEQUAL)
            if self.show_grid:
                self._draw_grid(f)
            self._draw_model(f)
            self._draw_section_plane(f)
            f.glDisable(GL_DEPTH_TEST)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._paint_overlay(painter)
        painter.end()

    def _draw_model(self, f):
        program = self._programs["model"]
        mvp, view = self._matrices()
        self._bind_model_attributes(program)
        has_color, has_normal = self._uses("color"), self._uses("normal")
        if has_color:
            self._buffers["color"].bind()
            program.enableAttributeArray("aColor")
            program.setAttributeBuffer("aColor", GL_UNSIGNED_BYTE, 0, 3, 3)
        else:
            program.disableAttributeArray("aColor")
        if has_normal:
            self._buffers["normal"].bind()
            program.enableAttributeArray("aNormal")
            program.setAttributeBuffer("aNormal", GL_FLOAT, 0, 3, 12)
        else:
            program.disableAttributeArray("aNormal")
        self._buffers["edge"].bind()
        program.enableAttributeArray("aBary")
        program.setAttributeBuffer("aBary", GL_UNSIGNED_BYTE, 0, 4, 8)
        program.enableAttributeArray("aFlags")
        program.setAttributeBuffer("aFlags", GL_UNSIGNED_BYTE, 4, 4, 8)
        program.setUniformValue("uMVP", mvp)
        program.setUniformValue("uView", view)
        program.setUniformValue("uBase", QVector3D(self.base.redF(), self.base.greenF(), self.base.blueF()))
        edge = self.palette_colors["edge"]
        program.setUniformValue("uEdgeColor", QVector3D(edge.redF(), edge.greenF(), edge.blueF()))
        program.setUniformValue("uBackColor", QVector3D(0.96, 0.62, 0.15))
        plane = self._section_plane()
        program.setUniformValue1f("uSectionOn", 1.0 if plane else 0.0)
        program.setUniformValue("uSection", QVector4D(*(plane or (0.0, 0.0, 1.0, 0.0))))
        program.setUniformValue1f("uUseColors", 1.0 if has_color else 0.0)
        program.setUniformValue1f("uSmooth", 1.0 if has_normal else 0.0)
        program.setUniformValue1f("uOrtho", 1.0 if self.camera.orthographic else 0.0)
        program.setUniformValue1f("uMode", float(self.mode))
        program.setUniformValue1f("uAllEdges", 1.0 if self.mode == 2 or not (
            self.shading and self.shading.edge_codes is not None) else 0.0)
        program.setUniformValue1f("uLine", 1.6 * self.devicePixelRatioF())
        f.glDrawArrays(GL_TRIANGLES, 0, self._count)
        for name in ("aPos", "aColor", "aNormal", "aBary", "aFlags"):
            program.disableAttributeArray(name)
        self._buffers["edge"].release()
        program.release()

    def _lines(self, f, vertices: list[float], colour: QColor, mode: int = GL_LINES):
        program = self._programs["line"]
        buffer = self._buffers["line"]
        data = array("f", vertices).tobytes()
        buffer.bind()
        buffer.allocate(data, len(data))
        program.bind()
        program.setUniformValue("uMVP", self._matrices()[0])
        program.setUniformValue("uColor", QVector4D(colour.redF(), colour.greenF(), colour.blueF(),
                                                    colour.alphaF()))
        program.enableAttributeArray("aPos")
        program.setAttributeBuffer("aPos", GL_FLOAT, 0, 3, 12)
        f.glDrawArrays(mode, 0, len(vertices) // 3)
        program.disableAttributeArray("aPos")
        program.release()
        buffer.release()

    def _draw_grid(self, f):
        r = self.record
        lo, hi = r.bounds_min, r.bounds_max
        extent = max(hi[0] - lo[0], hi[1] - lo[1], 1e-9) * 1.6
        step = nice_step(extent)
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        half = math.ceil(extent / 2 / step) * step
        x0, y0 = round(cx / step) * step, round(cy / step) * step
        z = lo[2]
        vertices: list[float] = []
        n = int(half / step)
        for i in range(-n, n + 1):
            vertices += [x0 + i * step, y0 - half, z, x0 + i * step, y0 + half, z]
            vertices += [x0 - half, y0 + i * step, z, x0 + half, y0 + i * step, z]
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._lines(f, vertices, self.palette_colors["grid"])
        f.glDisable(GL_BLEND)
        self.grid_step = step

    grid_step = 0.0

    def _draw_section_plane(self, f):
        plane = self._section_plane()
        if plane is None:
            return
        r = self.record
        axis = self.section[0]
        lo, hi = list(r.bounds_min), list(r.bounds_max)
        value = abs(plane[3])
        value = lo[axis] + self.section[1] * (hi[axis] - lo[axis])
        pad = max(h - l for l, h in zip(lo, hi)) * 0.06
        others = [a for a in range(3) if a != axis]
        corners = []
        for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
            p = [0.0, 0.0, 0.0]
            p[axis] = value
            p[others[0]] = (lo[others[0]] - pad) if u == 0 else (hi[others[0]] + pad)
            p[others[1]] = (lo[others[1]] - pad) if v == 0 else (hi[others[1]] + pad)
            corners.append(p)
        quad = [c for i in (0, 1, 2, 0, 2, 3) for c in corners[i]]
        accent = QColor(self.palette_colors["accent"])
        accent.setAlpha(34)
        f.glEnable(GL_BLEND)
        f.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._lines(f, quad, accent, GL_TRIANGLES)
        accent.setAlpha(200)
        outline = [c for i in (0, 1, 1, 2, 2, 3, 3, 0) for c in corners[i]]
        self._lines(f, outline, accent)
        f.glDisable(GL_BLEND)

    # ---- picking ---------------------------------------------------------------------
    def _pick_triangle(self, x: float, y: float) -> int | None:
        """Which triangle is under a pixel: draw each in its own colour and read it back."""
        if not self._gl_ready or self.record is None:
            return None
        if not self._need_ids:
            self._need_ids = True
            self._dirty.add("id")
        self.makeCurrent()
        try:
            if self._dirty:
                self._upload()
            f = self.context().functions()
            ratio = self.devicePixelRatioF()
            size = QSize(max(int(self.width() * ratio), 1), max(int(self.height() * ratio), 1))
            fbo = QOpenGLFramebufferObject(size, QOpenGLFramebufferObject.CombinedDepthStencil)
            fbo.bind()
            f.glViewport(0, 0, size.width(), size.height())
            f.glDisable(GL_BLEND)
            f.glDisable(GL_DITHER)
            f.glClearColor(0, 0, 0, 0)
            f.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            f.glEnable(GL_DEPTH_TEST)
            program = self._programs["pick"]
            self._bind_model_attributes(program, with_ids=True)
            program.setUniformValue("uMVP", self._matrices()[0])
            plane = self._section_plane()
            program.setUniformValue1f("uSectionOn", 1.0 if plane else 0.0)
            program.setUniformValue("uSection", QVector4D(*(plane or (0.0, 0.0, 1.0, 0.0))))
            f.glDrawArrays(GL_TRIANGLES, 0, self._count)
            program.disableAttributeArray("aPos")
            program.disableAttributeArray("aId")
            program.release()
            image = fbo.toImage()
            fbo.release()
            f.glDisable(GL_DEPTH_TEST)
            for dx, dy in PICK_OFFSETS:  # nearest first: a corner sits right on the outline
                px = int(x * ratio) + dx
                py = int(y * ratio) + dy
                if 0 <= px < image.width() and 0 <= py < image.height():
                    c = image.pixelColor(px, py)
                    ident = c.red() | c.green() << 8 | c.blue() << 16
                    if c.alpha() == 255 and ident:
                        return ident - 1
            return None
        finally:
            self.doneCurrent()

    def _snap_at(self, x: float, y: float):
        triangle = self._pick_triangle(x, y)
        if triangle is None:
            return None
        origin, direction = self.camera.ray(x, y, self.width(), self.height())
        # how far a pixel is in model units at that distance, for a ~12 px snap radius
        approx = self.camera.visible_height() / max(self.height(), 1)
        if not self.camera.orthographic:
            eye = self.camera.eye()
            corner = self.models.corners(triangle)[0]
            depth = math.dist((eye.x(), eye.y(), eye.z()), corner)
            approx = 2 * depth * math.tan(math.radians(self.camera.FOV / 2)) / max(self.height(), 1)
        radius = approx * 12
        try:
            return self.models.snap(triangle, origin, direction, radius,
                                    corners=self.snapping, edges=self.snapping)
        except ApplicationError:
            return None

    def _update_hover(self):
        if not self.tool:
            return
        snap = self._snap_at(*self._hover_at)
        self.hover = (snap.point, snap.kind) if snap else None
        self.update()

    # ---- the mouse and keyboard --------------------------------------------------------
    def mousePressEvent(self, event):
        self.setFocus()
        self._drag = (event.position(), event.button(), event.modifiers())
        self._moved = False

    def mouseMoveEvent(self, event):
        if self._drag is None:
            if self.tool:
                self._hover_at = (event.position().x(), event.position().y())
                self._hover_timer.start()
            return
        start, button, modifiers = self._drag
        pos = event.position()
        dx, dy = pos.x() - start.x(), pos.y() - start.y()
        if abs(dx) + abs(dy) > 3:
            self._moved = True
        if not self._moved:
            return
        pan = button in (Qt.MiddleButton, Qt.RightButton) or bool(modifiers & Qt.ShiftModifier)
        if pan:
            self.camera.pan(dx, dy, self.height())
        else:
            self.camera.orbit(dx, dy)
        self._drag = (pos, button, modifiers)
        self.update()

    def mouseReleaseEvent(self, event):
        drag, self._drag = self._drag, None
        if drag is None or self._moved or drag[1] != Qt.LeftButton or not self.tool:
            return
        self._click_point(event.position().x(), event.position().y())

    def mouseDoubleClickEvent(self, event):
        if self.tool or event.button() != Qt.LeftButton:
            return
        snap = self._snap_at(event.position().x(), event.position().y())
        if snap is not None:
            self.camera.centre = QVector3D(*snap.point)
            self.update()

    def _click_point(self, x: float, y: float):
        snap = self._snap_at(x, y)
        if snap is None:
            return
        self.pending.append(snap.point)
        if len(self.pending) == TOOLS[self.tool]:
            points, self.pending = tuple(self.pending), []
            self.hover = None
            self.measured.emit(self.tool, points)
        self._announce()
        self.update()

    def _plane_point(self, x: float, y: float) -> QVector3D:
        """Where a pixel lands on the plane through the view centre, facing the camera."""
        (ox, oy, oz), (dx, dy, dz) = self.camera.ray(x, y, self.width(), self.height())
        normal = (self.camera.centre - self.camera.eye()).normalized()
        o, d = QVector3D(ox, oy, oz), QVector3D(dx, dy, dz)
        denom = QVector3D.dotProduct(d, normal)
        if abs(denom) < 1e-9:
            return self.camera.centre
        t = QVector3D.dotProduct(self.camera.centre - o, normal) / denom
        return o + d * t

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120.0
        if not steps:
            return
        pos = event.position()
        before = self._plane_point(pos.x(), pos.y())
        self.camera.zoom(1.18 ** steps)
        after = self._plane_point(pos.x(), pos.y())
        self.camera.centre = self.camera.centre + (before - after)
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        views = {Qt.Key_1: "front", Qt.Key_2: "back", Qt.Key_3: "left", Qt.Key_4: "right",
                 Qt.Key_5: "top", Qt.Key_6: "bottom", Qt.Key_7: "iso"}
        if key in views:
            self.look_from(views[key])
        elif key in (Qt.Key_F, Qt.Key_Home):
            self.fit()
        elif key == Qt.Key_Escape:
            self.cancel()
        elif key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            self.camera.orbit({Qt.Key_Left: -20, Qt.Key_Right: 20}.get(key, 0),
                              {Qt.Key_Up: -20, Qt.Key_Down: 20}.get(key, 0))
            self.update()
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self.camera.zoom(1.2); self.update()
        elif key == Qt.Key_Minus:
            self.camera.zoom(1 / 1.2); self.update()
        else:
            super().keyPressEvent(event)

    # ---- drawing on top ----------------------------------------------------------------
    def _screen(self, point):
        p = self.camera.project(point, self.width(), self.height())
        return None if p is None or not -1 <= p[2] <= 1 else QPointF(p[0], p[1])

    def _label(self, painter: QPainter, at: QPointF, text: str, accent: bool = False):
        font = QFont(painter.font())
        font.setPointSizeF(max(font.pointSizeF(), 10.5 * scale()))
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        width, height = metrics.horizontalAdvance(text) + px(16), metrics.height() + px(8)
        x = min(max(at.x() - width / 2, 4), self.width() - width - 4)
        y = min(max(at.y() - height / 2, 4), self.height() - height - 4)
        painter.setPen(QPen(self.palette_colors["accent"] if accent else self.palette_colors["text"], 1.5))
        painter.setBrush(self.palette_colors["surface"])
        painter.drawRoundedRect(x, y, width, height, px(7), px(7))
        painter.drawText(int(x), int(y), int(width), int(height), Qt.AlignCenter, text)

    def _paint_overlay(self, painter: QPainter):
        c = self.palette_colors
        if self.failure or (not self._gl_ready):
            painter.setPen(c["text"])
            painter.drawText(self.rect().adjusted(24, 24, -24, -24), Qt.AlignCenter | Qt.TextWordWrap,
                             _("The 3D view couldn't start on this computer.") + "\n"
                             + (self.failure or ""))
            return
        if self.record is None:
            return
        if self.show_dimensions:
            self._paint_dimensions(painter)
        accent = c["accent"]
        for record, text in self.measurements:
            self._paint_measurement(painter, record, text, accent)
        for i, point in enumerate(self.pending):
            at = self._screen(point)
            if at:
                self._dot(painter, at, str(i + 1))
        if self.tool and self.hover:
            at = self._screen(self.hover[0])
            if at:
                painter.setPen(QPen(accent, 2.5))
                painter.setBrush(Qt.NoBrush)
                if self.hover[1] == "corner":
                    painter.drawRect(at.x() - 7, at.y() - 7, 14, 14)
                elif self.hover[1] == "edge":
                    painter.drawEllipse(at, 7, 7)
                else:
                    painter.drawLine(at.x() - 6, at.y(), at.x() + 6, at.y())
                    painter.drawLine(at.x(), at.y() - 6, at.x(), at.y() + 6)
        self._paint_gizmo(painter)
        if self.grid_step and self.show_grid:
            self._paint_scale(painter)

    def _dot(self, painter, at: QPointF, text: str = ""):
        painter.setPen(QPen(self.palette_colors["surface"], 2))
        painter.setBrush(self.palette_colors["accent"])
        painter.drawEllipse(at, px(6), px(6))
        if text:
            font = QFont(painter.font())
            font.setBold(True)
            font.setPointSizeF(9 * scale())
            painter.setFont(font)
            painter.setPen(self.palette_colors["accent"])
            painter.drawText(at + QPointF(9, -9), text)

    def _paint_measurement(self, painter, record, text, accent):
        painter.setPen(QPen(accent, 2.2))
        points = [self._screen(p) for p in record.points]
        if record.kind == "circle" and record.centre is not None:
            a, b, cc = record.points
            centre = QVector3D(*record.centre)
            radius = QVector3D(*a).distanceToPoint(centre)
            u = (QVector3D(*a) - centre).normalized()
            n = QVector3D.crossProduct(QVector3D(*b) - QVector3D(*a), QVector3D(*cc) - QVector3D(*a)).normalized()
            v = QVector3D.crossProduct(n, u)
            ring = []
            for i in range(97):
                t = 2 * math.pi * i / 96
                p = centre + (u * math.cos(t) + v * math.sin(t)) * radius
                s = self._screen((p.x(), p.y(), p.z()))
                if s:
                    ring.append(s)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolyline(QPolygonF(ring))
            mid = self._screen(record.centre)
            if mid:
                painter.drawLine(mid.x() - 6, mid.y(), mid.x() + 6, mid.y())
                painter.drawLine(mid.x(), mid.y() - 6, mid.x(), mid.y() + 6)
                self._label(painter, mid + QPointF(0, -26), text, True)
        elif all(points):
            order = [0, 1] if record.kind == "distance" else [0, 1, 2]
            painter.drawPolyline(QPolygonF([points[i] for i in order]))
            anchor = (points[0] + points[1]) / 2 if record.kind == "distance" else points[1]
            self._label(painter, anchor + QPointF(0, -22), text, True)
        for p in points:
            if p:
                self._dot(painter, p)

    def _paint_dimensions(self, painter):
        lo, hi = self.record.bounds_min, self.record.bounds_max
        corners = [(x, y, z) for z in (lo[2], hi[2]) for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
        pairs = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7),
                 (0, 4), (1, 5), (2, 6), (3, 7)]
        pen = QPen(self.palette_colors["text"], 1.2, Qt.DashLine)
        painter.setPen(pen)
        screen = [self._screen(p) for p in corners]
        for a, b in pairs:
            if screen[a] and screen[b]:
                painter.drawLine(screen[a], screen[b])
        for (a, b), axis in (((0, 1), 0), ((0, 2), 1), ((0, 4), 2)):
            if screen[a] and screen[b]:
                size = hi[axis] - lo[axis]
                self._label(painter, (screen[a] + screen[b]) / 2, f"{'XYZ'[axis]} {self.format_length(size)}")

    def _paint_gizmo(self, painter):
        view = self.camera.view_matrix()
        origin = QPointF(px(46), self.height() - px(46))
        axes = [("X", (1, 0, 0), "#e5484d"), ("Y", (0, 1, 0), "#30a46c"), ("Z", (0, 0, 1), "#3e63dd")]
        projected = []
        for name, vec, colour in axes:
            mapped = view.mapVector(QVector3D(*vec))
            projected.append((mapped.z(), name, mapped, colour))
        font = QFont(painter.font())
        font.setBold(True)
        painter.setFont(font)
        for _z, name, mapped, colour in sorted(projected, key=lambda t: t[0]):
            tip = origin + QPointF(mapped.x(), -mapped.y()) * px(30)
            painter.setPen(QPen(QColor(colour), 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(origin, tip)
            painter.drawText(tip + QPointF(-px(5), px(5)) + QPointF(mapped.x(), -mapped.y()) * px(7), name)

    def _paint_scale(self, painter):
        text = _("Grid: {step}").format(step=self.format_length(self.grid_step))
        font = QFont(painter.font())
        painter.setFont(font)
        painter.setPen(self.palette_colors["text"])
        painter.drawText(self.rect().adjusted(0, 0, -12, -10), Qt.AlignRight | Qt.AlignBottom, text)
