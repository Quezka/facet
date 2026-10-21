"""The viewer page: the 3D view with its toolbar, and the inspector beside it."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMenu, QScrollArea, QSlider, QToolButton, QVBoxLayout, QWidget,
)

from ...application.errors import ApplicationError
from ...application.services import Services
from .. import theme
from ..i18n import N_, _, plural
from ..measures import Measures
from ..viewport import SWATCHES, Viewport
from .common import Card, Page, Segmented, button, caption, icon_button, label, primary_button

N_("Distance"), N_("Angle"), N_("Supplement"), N_("Diameter"), N_("Radius")  # measurement names
INSPECTOR_WIDTH = 340


def hint(text: str) -> QLabel:
    """A quiet explanation that wraps inside the narrow inspector."""
    result = label(text, "hint")
    result.setWordWrap(True)
    return result


class Facts(QGridLayout):
    """Name and value rows."""

    def __init__(self):
        super().__init__()
        self.setHorizontalSpacing(14)
        self.setVerticalSpacing(6)
        self.setColumnStretch(1, 1)
        self.values: dict[str, QLabel] = {}

    def add(self, key: str, name: str, strong: bool = False) -> QLabel:
        row = self.rowCount()
        title = QLabel(name, objectName="muted")
        value = QLabel("—")
        value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value.setWordWrap(True)
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if strong:
            font = value.font()
            font.setBold(True)
            value.setFont(font)
        self.addWidget(title, row, 0, Qt.AlignTop)
        self.addWidget(value, row, 1)
        self.values[key] = value
        return value

    def set(self, key: str, text: str):
        self.values[key].setText(text)

    def text(self) -> str:
        lines = []
        for row in range(self.rowCount()):
            name, value = self.itemAtPosition(row, 0), self.itemAtPosition(row, 1)
            if name and value:
                lines.append(f"{name.widget().text()}: {value.widget().text()}")
        return "\n".join(lines)


class ViewerPage(Page):
    openRequested = Signal()
    previousRequested = Signal()
    nextRequested = Signal()
    unitChanged = Signal()

    def __init__(self, services: Services, measures: Measures, parent=None):
        super().__init__(parent, margins=(22, 18, 22, 20))
        self.services = services
        self.models = services.models
        self.measures = measures
        self.record = None
        self.analysis = None
        self.shading = None
        self.measured: list = []
        self.root.setSpacing(12)

        self.previous = icon_button("chevron-left", _("Previous model in the folder  (Alt+Left)"))
        self.next = icon_button("chevron-right", _("Next model in the folder  (Alt+Right)"))
        self.previous.clicked.connect(self.previousRequested)
        self.next.clicked.connect(self.nextRequested)
        picture = button(_("Picture"), "camera")
        menu = QMenu(picture)
        menu.addAction(_("Save picture…"), self.save_picture).setShortcut("Ctrl+Shift+S")
        menu.addAction(_("Copy picture"), self.copy_picture).setShortcut("Ctrl+Shift+C")
        picture.setMenu(menu)
        self.open_button = primary_button(_("Open…"), "folder")
        self.open_button.clicked.connect(self.openRequested)
        self.add_actions(self.previous, self.next, picture, self.open_button)

        self.viewport = Viewport(self.models)
        self.viewport.format_length = self.measures.length
        theme.themed(self.viewport.set_palette)
        self.viewport.measured.connect(self._measured)
        self.viewport.hint.connect(self._hint)
        self.viewport.toolFinished.connect(lambda: self.tools.set_value(""))

        self.root.addWidget(self._toolbar())
        body = QHBoxLayout()
        body.setSpacing(12)
        frame = QFrame(objectName="card")
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(2, 2, 2, 2)
        inner.addWidget(self.viewport)
        body.addWidget(frame, 1)
        self.inspector = self._inspector()
        body.addWidget(self.inspector)
        self.root.addLayout(body, 1)
        self.set_loaded(False)

    # ---- building --------------------------------------------------------------------
    def _toolbar(self) -> QWidget:
        bar = QFrame(objectName="card")
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 6, 10, 6)
        row.setSpacing(8)
        self.display = Segmented([(0, _("Solid")), (1, _("Edges")), (2, _("Wire"))])
        self.display.set_value(0)
        self.display.changed.connect(self._display_changed)
        row.addWidget(self.display)
        self.grid_toggle = self._toggle("grid", _("Grid"), True, self._grid)
        self.dimensions_toggle = self._toggle("dimensions", _("Box size"), False, self._dimensions)
        self.ortho_toggle = self._toggle("cube", _("Flat view"), False, self._ortho)
        self.ortho_toggle.setToolTip(_("Orthographic view: no perspective, parallel lines stay parallel (O)"))
        for toggle in (self.grid_toggle, self.dimensions_toggle, self.ortho_toggle):
            row.addWidget(toggle)
        views = QToolButton(objectName="tool", text=_("View"), popupMode=QToolButton.InstantPopup)
        views.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        theme.set_icon(views, "eye", "muted")
        menu = QMenu(views)
        for key, name, shortcut in ((("front", _("Front"), "1")), ("back", _("Back"), "2"),
                                    ("left", _("Left"), "3"), ("right", _("Right"), "4"),
                                    ("top", _("Top"), "5"), ("bottom", _("Bottom"), "6"),
                                    ("iso", _("Isometric"), "7")):
            action = menu.addAction(f"{name}\t{shortcut}")
            action.triggered.connect(lambda _c=False, k=key: self.viewport.look_from(k))
        views.setMenu(menu)
        row.addWidget(views)
        fit = QToolButton(objectName="tool", text=_("Fit"))
        fit.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        theme.set_icon(fit, "fit", "muted")
        fit.setToolTip(_("Fit the model to the window (F)"))
        fit.clicked.connect(self.viewport.fit)
        row.addWidget(fit)
        row.addStretch()
        self.status = QLabel("", objectName="muted")
        row.addWidget(self.status)
        return bar

    def _toggle(self, icon: str, text: str, checked: bool, slot) -> QToolButton:
        toggle = QToolButton(objectName="tool", text=text, checkable=True, checked=checked)
        toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        theme.set_icon(toggle, icon, "muted", "accent")
        toggle.toggled.connect(slot)
        return toggle

    def _inspector(self) -> QScrollArea:
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 4, 0)
        column.setSpacing(12)
        for card in (self._details_card(), self._health_card(), self._measure_card(),
                     self._section_card(), self._look_card()):
            column.addWidget(card)
        column.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedWidth(INSPECTOR_WIDTH + 18)
        scroll.setWidget(holder)
        return scroll

    def _details_card(self) -> Card:
        card = Card(_("Details"))
        copy = icon_button("copy", _("Copy these details"))
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.facts.text()))
        card.title_row.addWidget(copy)
        card.add(caption(_("The model's units")))
        self.units = Segmented([("mm", "mm"), ("cm", "cm"), ("m", "m"), ("in", "in")])
        self.units.set_value(self.measures.unit)
        self.units.changed.connect(self._unit_picked)
        card.add(self.units)
        self.facts = Facts()
        self.facts.add("x", _("Width (X)"), True)
        self.facts.add("y", _("Depth (Y)"), True)
        self.facts.add("z", _("Height (Z)"), True)
        self.facts.add("volume", _("Volume"))
        self.facts.add("area", _("Surface area"))
        self.facts.add("weight", _("Weight"))
        self.facts.add("centre", _("Centre of mass"))
        self.facts.add("triangles", _("Triangles"))
        self.facts.add("file", _("File"))
        card.body.addLayout(self.facts)
        row = QHBoxLayout()
        row.addWidget(QLabel(_("Material"), objectName="muted"))
        self.material = QComboBox()
        for m in self.models.materials():
            self.material.addItem(f"{m.name} · {m.density:g} g/cm³", m.name)
        self.material.currentIndexChanged.connect(self._refresh_weight)
        row.addWidget(self.material, 1)
        card.body.addLayout(row)
        card.add(hint(_("The weight is for a solid part; a printed one with infill weighs less.")))
        return card

    def _health_card(self) -> Card:
        card = Card(_("Mesh check"))
        self.health = QLabel(_("Open a model to check it."), objectName="muted")
        self.health.setWordWrap(True)
        self.health.setTextFormat(Qt.RichText)
        card.add(self.health)
        return card

    def _measure_card(self) -> Card:
        card = Card(_("Measure"))
        self.tools = Segmented([("", _("Off")), ("distance", _("Distance")), ("angle", _("Angle")),
                                ("circle", _("Hole"))])
        self.tools.set_value("")
        self.tools.changed.connect(self._tool_picked)
        card.add(self.tools)
        self.snap = QCheckBox(_("Snap to corners and edges"))
        self.snap.setChecked(True)
        self.snap.toggled.connect(self._snap_changed)
        card.add(self.snap)
        card.add(hint(_("Pick a tool, then click points on the model. Angle: the corner is the second point. Hole: three points around it.")))
        self.list = QListWidget(objectName="recent")
        self.list.setMinimumHeight(110)
        self.list.setMaximumHeight(200)
        self.list.currentRowChanged.connect(lambda _row: self._list_buttons())
        card.add(self.list)
        row = QHBoxLayout()
        self.copy_value = button(_("Copy"), "copy")
        self.remove = button(_("Remove"), "x")
        self.clear = button(_("Clear"), "trash")
        self.copy_value.clicked.connect(self._copy_measurement)
        self.remove.clicked.connect(self._remove_measurement)
        self.clear.clicked.connect(self._clear_measurements)
        for b in (self.copy_value, self.remove, self.clear):
            row.addWidget(b)
        card.body.addLayout(row)
        self._list_buttons()
        return card

    def _section_card(self) -> Card:
        card = Card(_("Section"))
        self.section_on = QCheckBox(_("Cut the model with a plane"))
        self.section_on.toggled.connect(self._section_changed)
        card.add(self.section_on)
        self.axis = Segmented([(0, "X"), (1, "Y"), (2, "Z")])
        self.axis.set_value(2)
        self.axis.changed.connect(self._section_changed)
        card.add(self.axis)
        self.depth = QSlider(Qt.Horizontal, minimum=0, maximum=1000, value=500)
        self.depth.valueChanged.connect(self._section_changed)
        card.add(self.depth)
        self.flip = QCheckBox(_("Keep the other side"))
        self.flip.toggled.connect(self._section_changed)
        card.add(self.flip)
        self.section_label = hint("")
        card.add(self.section_label)
        return card

    def _look_card(self) -> Card:
        card = Card(_("Look"))
        row = QHBoxLayout()
        row.setSpacing(6)
        self.swatches = []
        for name, colour in SWATCHES:
            b = QToolButton(checkable=True, toolTip=_(name))
            b.setFixedSize(30, 30)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"QToolButton {{ background: {colour}; border: 2px solid transparent;"
                            f" border-radius: 15px; padding: 0; }}"
                            f"QToolButton:checked {{ border: 3px solid {theme.current().accent}; }}")
            b.clicked.connect(lambda _c=False, c=colour, btn=b: self._colour(c, btn))
            self.swatches.append(b)
            row.addWidget(b)
        row.addStretch()
        card.body.addLayout(row)
        self.swatches[0].setChecked(True)
        self.smooth = QCheckBox(_("Smooth shading"))
        self.smooth.setChecked(True)
        self.smooth.toggled.connect(self._smooth)
        card.add(self.smooth)
        self.file_colours = QCheckBox(_("Use the colours stored in the file"))
        self.file_colours.setChecked(True)
        self.file_colours.toggled.connect(self._file_colours)
        card.add(self.file_colours)
        return card

    # ---- showing a model -------------------------------------------------------------
    def set_loaded(self, loaded: bool):
        self.inspector.setVisible(True)
        for w in (self.previous, self.next):
            w.setEnabled(loaded)

    def set_neighbours(self, has_previous: bool, has_next: bool):
        self.previous.setEnabled(has_previous)
        self.next.setEnabled(has_next)

    def loading(self, name: str):
        self.title.setText(name)
        self.subtitle.setText(_("Opening…"))

    def failed(self):
        self.subtitle.setText(self._subtitle())

    def _subtitle(self) -> str:
        if self.record is None:
            return _("No model open.")
        r = self.record
        return f"{self.measures.count(r.triangles)} " + _("triangles") + " · " + " × ".join(
            self.measures.number(v) for v in r.size) + f" {self.measures.unit}"

    def show_model(self, record):
        self.record, self.analysis, self.shading = record, None, None
        self.measured.clear()
        self.list.clear()
        self.tools.set_value("")
        self.viewport.set_tool(None)
        if record.unit_hint and record.unit_hint != self.measures.unit:
            self.measures.set_unit(record.unit_hint)
            self.units.set_value(record.unit_hint)
        self.viewport.set_model(record)
        self.title.setText(record.name)
        self.file_colours.setVisible(record.colors is not None)
        self.smooth.setEnabled(False)
        self.health.setText(_("Checking the mesh…"))
        self._fill_basics()
        for key in ("volume", "area", "weight", "centre"):
            self.facts.set(key, "…")
        self.set_loaded(True)
        self._section_changed()
        self.viewport.setFocus()

    def _fill_basics(self):
        r, m = self.record, self.measures
        if r is None:
            return
        for key, value in zip("xyz", r.size):
            self.facts.set(key, m.length(value))
        self.facts.set("triangles", m.count(r.triangles))
        self.facts.set("file", f"{r.format} · {m.bytes(r.file_size)}")
        self.subtitle.setText(self._subtitle())
        self.viewport.update()

    def set_analysis(self, analysis):
        if self.record is None or analysis.token != self.record.token:
            return
        self.analysis = analysis
        m = self.measures
        self.facts.set("volume", m.volume(abs(analysis.volume)))
        self.facts.set("area", m.area(analysis.area))
        self.facts.set("centre", m.point(analysis.centroid))
        self._refresh_weight()
        self.health.setText(self._health_html(analysis))

    def _health_html(self, a) -> str:
        t = theme.current()
        ok = f"<span style='color:{t.success}'>✔</span>"
        bad = f"<span style='color:{t.danger}'>⚠</span>"
        if not a.checked:
            return _("This model is too big to check its mesh.")
        lines = []
        if a.watertight:
            lines.append(f"{ok} " + _("Watertight: a closed solid, ready to print."))
        else:
            if a.open_edges:
                lines.append(f"{bad} " + _("{edges} open edges: the surface has holes or gaps.").format(
                    edges=self.measures.count(a.open_edges)))
            if a.non_manifold_edges:
                lines.append(f"{bad} " + _("{edges} edges shared by more than two faces.").format(
                    edges=self.measures.count(a.non_manifold_edges)))
        if a.inside_out:
            lines.append(f"{bad} " + _("The faces point inwards (inside out)."))
        if a.degenerate:
            lines.append(f"{bad} " + _("{n} triangles with no area.").format(
                n=self.measures.count(a.degenerate)))
        lines.append(plural(a.shells, "separate part") + " · "
                     + _("{n} vertices").format(n=self.measures.count(a.vertices)))
        return "<br>".join(lines)

    def set_shading(self, shading):
        if self.record is None or shading.token != self.record.token:
            return
        self.shading = shading
        self.viewport.set_shading(shading)
        self.smooth.setEnabled(shading.normals is not None)

    def _refresh_weight(self):
        if self.analysis is None:
            return
        grams = self.models.weight(self.analysis.volume, self.measures.unit, self.material.currentData())
        self.facts.set("weight", self.measures.weight(grams))

    # ---- toolbar and look ------------------------------------------------------------
    def _display_changed(self, mode):
        self.viewport.mode = mode
        self.viewport.update()

    def _grid(self, on):
        self.viewport.show_grid = on
        self.viewport.update()

    def _dimensions(self, on):
        self.viewport.show_dimensions = on
        self.viewport.update()

    def _ortho(self, on):
        self.viewport.camera.orthographic = on
        self.viewport.update()

    def _smooth(self, on):
        self.viewport.smooth = on
        self.viewport.update()

    def _file_colours(self, on):
        self.viewport.use_colors = on
        self.viewport.update()

    def _colour(self, colour: str, pressed):
        for b in self.swatches:
            b.setChecked(b is pressed)
        self.viewport.base = QColor(colour)
        if self.record is not None and self.record.colors is not None:
            self.file_colours.setChecked(False)  # picking a colour means "use this one"
        self.viewport.update()

    def toggle_orthographic(self):
        self.ortho_toggle.toggle()

    def cycle_display(self):
        self.display.set_value((self.display.value() + 1) % 3)
        self._display_changed(self.display.value())

    # ---- units -----------------------------------------------------------------------
    def _unit_picked(self, unit: str):
        self.measures.set_unit(unit)
        self.refresh_units()
        self.unitChanged.emit()

    def refresh_units(self):
        """Redraw every number after the unit or the decimals changed."""
        with QSignalBlocker(self.units):
            self.units.set_value(self.measures.unit)
        self._fill_basics()
        if self.analysis is not None:
            self.set_analysis(self.analysis)
        self.measured_texts()
        self._section_changed()

    # ---- measuring -------------------------------------------------------------------
    def _tool_picked(self, tool: str):
        self.viewport.set_tool(tool or None)
        if tool:
            self.viewport.setFocus()

    def _snap_changed(self, on):
        self.viewport.snapping = on

    def _hint(self, text: str):
        self.status.setText(text)

    def _measured(self, kind: str, points):
        try:
            if kind == "distance":
                record = self.models.measure_distance(*points)
            elif kind == "angle":
                record = self.models.measure_angle(*points)
            else:
                record = self.models.measure_circle(*points)
        except ApplicationError as error:
            self.status.setText(_(str(error)))
            return
        self.measured.append(record)
        self.measured_texts()
        self.list.setCurrentRow(self.list.count() - 1)

    def _value_text(self, value) -> str:
        m = self.measures
        return m.angle(value.value) if value.kind == "angle" else m.length(value.value)

    def _headline(self, record) -> str:
        first = record.values[0]
        text = self._value_text(first)
        return f"Ø {text}" if record.kind == "circle" else text

    def measured_texts(self):
        row = self.list.currentRow()
        self.list.clear()
        for number, record in enumerate(self.measured, 1):
            details = "  ·  ".join(f"{_(v.label)} {self._value_text(v)}" for v in record.values[1:])
            head = f"{number}. {_(record.values[0].label)}  {self._value_text(record.values[0])}"
            item = QListWidgetItem(f"{head}\n{details}")
            self.list.addItem(item)
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        self.viewport.measurements = [(r, self._headline(r)) for r in self.measured]
        self.viewport.update()
        self._list_buttons()

    def _list_buttons(self):
        has = self.list.currentRow() >= 0
        self.copy_value.setEnabled(has)
        self.remove.setEnabled(has)
        self.clear.setEnabled(self.list.count() > 0)

    def _copy_measurement(self):
        row = self.list.currentRow()
        if row >= 0:
            QGuiApplication.clipboard().setText(self.list.item(row).text().replace("\n", "  "))

    def _remove_measurement(self):
        row = self.list.currentRow()
        if row >= 0:
            del self.measured[row]
            self.measured_texts()

    def _clear_measurements(self):
        self.measured.clear()
        self.measured_texts()

    # ---- section ---------------------------------------------------------------------
    def _section_changed(self, *_args):
        on = self.section_on.isChecked() and self.record is not None
        self.axis.setEnabled(self.section_on.isChecked())
        self.depth.setEnabled(self.section_on.isChecked())
        self.flip.setEnabled(self.section_on.isChecked())
        if not on:
            self.viewport.section = None
            self.section_label.setText("")
        else:
            axis, t = self.axis.value(), self.depth.value() / 1000
            self.viewport.section = (axis, t, self.flip.isChecked())
            lo, hi = self.record.bounds_min[axis], self.record.bounds_max[axis]
            self.section_label.setText(f"{'XYZ'[axis]} = {self.measures.length(lo + t * (hi - lo))}")
        self.viewport.update()

    # ---- pictures --------------------------------------------------------------------
    def copy_picture(self):
        if self.record is not None:
            QGuiApplication.clipboard().setImage(self.viewport.snapshot())

    def save_picture(self):
        from PySide6.QtWidgets import QFileDialog
        if self.record is None:
            return
        suggestion = str(Path.home() / f"{Path(self.record.name).stem}.png")
        path, _filter = QFileDialog.getSaveFileName(self, _("Save picture"), suggestion,
                                                    _("PNG pictures") + " (*.png)")
        if path:
            if not Path(path).suffix:
                path += ".png"
            self.viewport.snapshot().save(path)

