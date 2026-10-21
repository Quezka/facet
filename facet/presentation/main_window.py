from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QThreadPool
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QMessageBox,
    QSizePolicy, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from .. import HOMEPAGE, MODEL_EXTENSIONS, __version__
from ..application.errors import ApplicationError
from ..application.services import Services
from ..demo import write_samples
from . import theme
from .background import run_in_background
from .fit import clamp_window
from .uiscale import px
from .i18n import N_, _
from .icons import APP_ICON
from .measures import Measures
from .settings import SettingsDialog
from .updates_ui import UpdateChecker
from .views.home import HomePage
from .views.viewer import ViewerPage


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(px(206))
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        brand_icon = QLabel()
        brand_icon.setPixmap(QIcon(str(APP_ICON)).pixmap(px(28), px(28)))
        brand = QHBoxLayout()
        brand.setContentsMargins(px(12), px(4), px(12), 0)
        brand.setSpacing(px(10))
        brand.addWidget(brand_icon)
        brand.addWidget(QLabel(_("Facet"), objectName="brand"))
        brand.addStretch()
        self.nav = QVBoxLayout()
        self.nav.setSpacing(px(2))
        self.footer = QVBoxLayout()
        self.footer.setSpacing(px(2))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(px(12), px(20), px(12), px(14))
        layout.setSpacing(px(6))
        layout.addLayout(brand)
        layout.addSpacing(18)
        layout.addLayout(self.nav)
        layout.addStretch()
        layout.addLayout(self.footer)

    def nav_button(self, icon_name: str, text: str, checkable: bool = True) -> QToolButton:
        button = QToolButton(objectName="nav", text=f"  {text}", checkable=checkable)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setIconSize(QSize(px(18), px(18)))
        button.setCursor(Qt.PointingHandCursor)
        theme.set_icon(button, icon_name, "muted", "accent" if checkable else None)
        return button

    def add_page(self, icon_name: str, text: str, shortcut: str) -> QToolButton:
        button = self.nav_button(icon_name, text)
        button.setToolTip(f"{text}  ({shortcut})")
        self.group.addButton(button, len(self.group.buttons()))
        self.nav.addWidget(button)
        return button


class MainWindow(QMainWindow):
    HOME, VIEWER = range(2)
    PAGES = [("home", N_("Home")), ("cube", N_("Viewer"))]

    def __init__(self, services: Services):
        super().__init__()
        self.services = services
        self.models = services.models
        self.measures = Measures()
        self.record = None
        self.siblings: list[str] = []
        self._opening = 0
        clamp_window(self, px(1320), px(840), px(1000), px(640))
        self.setAcceptDrops(True)

        self.home = HomePage()
        self.viewer = ViewerPage(services, self.measures)
        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        for i, (page, (icon, text)) in enumerate(zip((self.home, self.viewer), self.PAGES)):
            self.stack.addWidget(page)
            self.sidebar.add_page(icon, _(text), f"Ctrl+{i + 1}")
        self.sidebar.group.idClicked.connect(self.show_page)
        more = self.sidebar.nav_button("more", _("More"), checkable=False)
        more.setPopupMode(QToolButton.InstantPopup)
        more.setMenu(self._more_menu())
        self.sidebar.footer.addWidget(more)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.home.openRequested.connect(lambda path: self.open_file(path or None))
        self.home.sampleRequested.connect(self.open_sample)
        self.viewer.openRequested.connect(lambda: self.open_file())
        self.viewer.previousRequested.connect(lambda: self.step(-1))
        self.viewer.nextRequested.connect(lambda: self.step(1))
        self.viewer.unitChanged.connect(lambda: None)
        self.updater = UpdateChecker(self.services, self)
        self._shortcuts()

        geometry = QSettings().value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.home.set_recent(self.models.recent())
        self._retitle()
        self.show_page(self.HOME)

    # ---- pages -----------------------------------------------------------------------
    def show_page(self, index: int):
        if index == self.VIEWER and self.record is None:
            index = self.HOME
        self.stack.setCurrentIndex(index)
        self.sidebar.group.button(index).setChecked(True)
        if index == self.VIEWER:
            self.viewer.viewport.setFocus()

    def _retitle(self):
        self.setWindowTitle(f"{self.record.name} — Facet" if self.record else "Facet")
        self.sidebar.group.button(self.VIEWER).setEnabled(self.record is not None)

    # ---- opening ---------------------------------------------------------------------
    def _folder(self) -> str:
        folder = QSettings().value("folder", "")
        return folder if folder and Path(folder).is_dir() else str(Path.home())

    def open_file(self, path: str | None = None):
        if not path:
            patterns = " ".join(f"*{e}" for e in MODEL_EXTENSIONS)
            path, _filter = QFileDialog.getOpenFileName(
                self, _("Open a model"), self._folder(),
                _("3D models") + f" ({patterns});;" + _("All files") + " (*)")
        if not path:
            return
        QSettings().setValue("folder", str(Path(path).parent))
        self._opening += 1
        ticket = self._opening
        self.viewer.loading(Path(path).name)
        self.statusBar().showMessage(_("Opening {name}…").format(name=Path(path).name))
        run_in_background(lambda: self.models.open(path),
                          lambda record: self._opened(record, ticket),
                          lambda error: self._open_failed(error, path, ticket))

    def _opened(self, record, ticket: int):
        if ticket != self._opening:
            return
        self.statusBar().clearMessage()
        self.record = record
        self.siblings = self.models.siblings(record.path)
        self.viewer.show_model(record)
        self._neighbours()
        self._retitle()
        self.home.set_recent(self.models.recent())
        self.show_page(self.VIEWER)
        run_in_background(self.models.analyse, self._analysed, self._ignore)

    def _analysed(self, analysis):
        self.viewer.set_analysis(analysis)
        # Smooth shading and outline edges need the welded mesh the analysis just built.
        run_in_background(lambda: self.models.shading(True, True), self.viewer.set_shading,
                          self._ignore)

    def _ignore(self, _error):
        pass

    def _open_failed(self, error, path: str, ticket: int):
        if ticket != self._opening:
            return
        self.statusBar().clearMessage()
        self.viewer.failed()
        self.models.forget(path)
        self.home.set_recent(self.models.recent())
        text = _(str(error)) if isinstance(error, ApplicationError) else _(
            "Something went wrong: {error}").format(error=error)
        QMessageBox.warning(self, "Facet", f"{Path(path).name}\n\n{text}")

    def open_sample(self, which: int):
        paths = write_samples(Path(__import__("tempfile").gettempdir()) / "facet-samples")
        self.open_file(str(paths[which]))

    def _neighbours(self):
        here = self.record.path if self.record else None
        index = self.siblings.index(here) if here in self.siblings else -1
        self.viewer.set_neighbours(index > 0, 0 <= index < len(self.siblings) - 1)

    def step(self, direction: int):
        if self.record is None or self.record.path not in self.siblings:
            return
        index = self.siblings.index(self.record.path) + direction
        if 0 <= index < len(self.siblings):
            self.open_file(self.siblings[index])

    def numbers_changed(self):
        self.viewer.refresh_units()

    # ---- menus and shortcuts ---------------------------------------------------------
    def _shortcut(self, keys, slot):
        action = QAction(self)
        action.setShortcut(QKeySequence(keys))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(slot)
        self.addAction(action)

    def _shortcuts(self):
        for i in range(len(self.PAGES)):
            self._shortcut(f"Ctrl+{i + 1}", lambda _c=False, i=i: self.show_page(i))
        self._shortcut(QKeySequence.Open, lambda: self.open_file())
        self._shortcut("Ctrl+,", self.open_settings)
        self._shortcut("Ctrl+Q", self.close)
        self._shortcut("Alt+Left", lambda: self.step(-1))
        self._shortcut("Alt+Right", lambda: self.step(1))
        self._shortcut("PgUp", lambda: self.step(-1))
        self._shortcut("PgDown", lambda: self.step(1))
        self._shortcut("Ctrl+Shift+S", self._with_model(self.viewer.save_picture))
        self._shortcut("Ctrl+Shift+C", self._with_model(self.viewer.copy_picture))
        self._shortcut("O", self._with_model(self.viewer.toggle_orthographic))
        self._shortcut("W", self._with_model(self.viewer.cycle_display))
        self._shortcut("I", self._toggle_inspector)

    def _with_model(self, action):
        """A viewer shortcut that does nothing until a model is open (it would otherwise
        build the 3D view for nothing)."""
        return lambda: action() if self.record is not None else None

    def _toggle_inspector(self):
        if self.stack.currentIndex() == self.VIEWER:
            self.viewer.inspector.setVisible(not self.viewer.inspector.isVisible())

    def _more_menu(self) -> QMenu:
        menu = QMenu(self)
        entries = [
            (_("Open a model…"), "Ctrl+O", lambda: self.open_file()),
            (_("Save picture…"), "Ctrl+Shift+S", self._with_model(self.viewer.save_picture)),
            None,
            (_("Settings…"), "Ctrl+,", self.open_settings),
            (_("Check for updates…"), None, lambda: self.updater.check_now()),
            (_("About Facet"), None, self.about),
            None,
            (_("Quit Facet"), "Ctrl+Q", self.close),
        ]
        for entry in entries:
            if entry is None:
                menu.addSeparator()
                continue
            text, keys, slot = entry
            action = menu.addAction(text, slot)
            if keys:
                action.setShortcut(QKeySequence(keys))
                action.setShortcutVisibleInContextMenu(True)
                action.setShortcutContext(Qt.WidgetShortcut)
        return menu

    def open_settings(self):
        SettingsDialog(self.services, self.measures, self.updater, self).exec()

    def about(self):
        QMessageBox.about(
            self, _("About Facet"),
            f"<h3>Facet {__version__}</h3>"
            f"<p>{_('A light 3D model viewer, for models you look at and models you measure.')}</p>"
            f"<p><a href='{HOMEPAGE}'>{HOMEPAGE}</a></p>"
            f"<p>{_('Free software under the GNU General Public License, version 3 or later.')}</p>")

    # ---- window ----------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.open_file(url.toLocalFile())
                break

    def closeEvent(self, event):
        QSettings().setValue("window/geometry", self.saveGeometry())
        QThreadPool.globalInstance().waitForDone(3000)  # let a running check finish first
        self.models.close()
        super().closeEvent(event)
