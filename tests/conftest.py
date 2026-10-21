import os
from datetime import datetime
from pathlib import Path

import pytest

os.environ.setdefault("QT_SCALE_FACTOR", "1")  # tests measure pixels: no automatic scaling

from facet.application.models import ModelService
from facet.application.services import Services
from facet.application.updates import UpdateService
from facet.infrastructure.mesh_files import MeshFiles
from facet.infrastructure.settings import MemorySettings

from .fakes import FakeInstaller, FakeReleases
from .shapes import cube, write_binary_stl


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 21, 10, 0)

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def releases():
    return FakeReleases()


@pytest.fixture
def installer():
    return FakeInstaller()


@pytest.fixture
def cube_file(tmp_path) -> Path:
    """A 10 x 20 x 30 box, binary STL."""
    path = tmp_path / "box.stl"
    write_binary_stl(path, cube(10, 20, 30))
    return path


@pytest.fixture
def models():
    return ModelService(MeshFiles(), MemorySettings())


@pytest.fixture
def services(releases, installer, clock):
    return Services(ModelService(MeshFiles(), MemorySettings()),
                    UpdateService(releases, installer, MemorySettings(), "0.1.0", clock))


@pytest.fixture(scope="session", autouse=True)
def empty_clipboard():
    """Qt's headless test platform crashes at exit when the clipboard still holds data a
    test copied (real desktops don't), so empty it before the tests end."""
    yield
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return
    app = QApplication.instance()
    if app is not None:
        app.clipboard().clear()


@pytest.fixture(autouse=True)
def full_hd_screen(monkeypatch):
    """The headless test screen is tiny; windows are clamped to the screen, so pretend it is
    a normal one (the clamp itself is tested in test_uiscale)."""
    try:
        from PySide6.QtCore import QRect
        from facet.presentation import fit
    except ImportError:
        return
    monkeypatch.setattr(fit, "available", lambda widget=None: QRect(0, 0, 1920, 1040))
