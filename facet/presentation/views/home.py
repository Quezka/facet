"""The start page: open a model, try a sample, recent models."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QGridLayout, QListWidget, QListWidgetItem, QSizePolicy, QToolButton

from .. import theme
from ..i18n import _
from .common import Card, Page, label


class HomePage(Page):
    openRequested = Signal(str)  # a path, or "" to choose one
    sampleRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title.setText(_("Facet"))
        self.subtitle.setText(_("Look at 3D models, and measure the ones that need it."))

        start = Card(_("Start"))
        grid = QGridLayout()
        grid.setSpacing(10)
        tiles = (
            ("folder", _("Open a model…"), _("STL, OBJ, PLY or 3MF"),
             lambda: self.openRequested.emit("")),
            ("ruler", _("Sample part"), _("A plate with a hole, to try measuring"),
             lambda: self.sampleRequested.emit(0)),
            ("cube", _("Sample shape"), _("A smooth vase, a curved model"),
             lambda: self.sampleRequested.emit(1)),
        )
        for column, (icon, text, detail, action) in enumerate(tiles):
            tile = QToolButton(objectName="startTile")
            tile.setText(f"{text}\n{detail}")
            tile.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tile.setIconSize(QSize(30, 30))
            tile.setMinimumSize(210, 120)
            tile.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tile.setCursor(Qt.PointingHandCursor)
            theme.set_icon(tile, icon, "accent", size=30)
            tile.clicked.connect(action)
            grid.addWidget(tile, 0, column)
            grid.setColumnStretch(column, 1)
        start.body.addLayout(grid)
        start.add(label(_("Drag a file onto the window to open it. In the view: drag to turn, right-drag or Shift-drag to move, wheel to zoom."), "hint"))

        self.recent_card = Card(_("Recent"))
        self.recent = QListWidget(objectName="recent")
        self.recent.itemActivated.connect(lambda item: self.openRequested.emit(item.data(Qt.UserRole)))
        self.recent.itemClicked.connect(lambda item: self.openRequested.emit(item.data(Qt.UserRole)))
        self.recent_card.add(self.recent, 1)
        self.root.addWidget(start)
        self.root.addWidget(self.recent_card, 1)
        self.root.addStretch(1)

    def set_recent(self, paths: list[str]):
        self.recent.clear()
        for p in paths:
            item = QListWidgetItem(f"{Path(p).name}\n{Path(p).parent}")
            item.setData(Qt.UserRole, p)
            self.recent.addItem(item)
        self.recent_card.setVisible(bool(paths))
