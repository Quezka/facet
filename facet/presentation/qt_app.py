"""Starts the Qt event loop around an already-wired set of services."""
from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .. import APP_ID
from ..application.services import Services
from . import i18n, theme, uiscale
from .icons import APP_ICON


def create_application(argv: list[str]) -> QApplication:
    QApplication.setApplicationName("Facet")
    QApplication.setOrganizationName("Facet")
    QApplication.setDesktopFileName(APP_ID)
    app = QApplication.instance() or QApplication(argv)
    screen = app.primaryScreen()
    uiscale.configure(screen.size().height() if screen else None)
    app.setStyle("Fusion")
    font = app.font()
    uiscale.base_pt = font.pointSizeF()
    font.setPointSizeF(font.pointSizeF() * uiscale.current())  # the interface is built at its size
    app.setFont(font)
    app.setWindowIcon(QIcon(str(APP_ICON)))
    i18n.install(app=app)  # before any window is built: texts are translated as they're made
    theme.install(app)
    return app


def run(services: Services, argv: list[str], file: Path | None = None,
        demo: bool = False) -> int:
    from ..demo import write_samples
    from .main_window import MainWindow

    app = create_application(argv)
    window = MainWindow(services)
    window.show()
    if file is not None:
        window.open_file(str(file))
    elif demo:
        window.open_file(str(write_samples(Path(tempfile.gettempdir()) / "facet-samples")[0]))
    return app.exec()
