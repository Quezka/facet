import pytest

from facet.presentation import uiscale


def test_automatic_scale_depends_on_the_screen():
    assert uiscale.factor("auto", 768) == 0.85  # small laptop screens get the smaller interface, like Quire
    assert uiscale.factor("auto", 1080) == 0.85 and uiscale.factor("auto", None) == 0.85
    assert uiscale.factor("115", 768) == 1.15 and uiscale.factor("200", 2160) == 2.0
    assert uiscale.factor("nonsense", 768) == 1.0


def test_the_choice_is_remembered_and_junk_is_ignored(monkeypatch):
    from PySide6.QtCore import QSettings
    store = {}
    monkeypatch.setattr(QSettings, "value", lambda self, key, default=None: store.get(key, default))
    monkeypatch.setattr(QSettings, "setValue", lambda self, key, value: store.__setitem__(key, value))
    assert uiscale.chosen() == "auto"
    uiscale.set_chosen("115")
    assert uiscale.chosen() == "115"
    store["ui_scale"] = "7"
    assert uiscale.chosen() == "auto"


def test_sizes_and_style_sheets_are_built_at_the_chosen_scale(monkeypatch):
    monkeypatch.setattr(uiscale, "_factor", 0.8)
    assert uiscale.px(10) == 8 and uiscale.px(1) == 1 and uiscale.px(0) == 0  # a line never vanishes
    qss = "QLabel { padding: 10px 20px; font-size: 19pt; border: 1px solid #1e3a8a; margin: 0; }"
    assert uiscale.scale_stylesheet(qss) == (
        "QLabel { padding: 8px 16px; font-size: 15.2pt; border: 1px solid #1e3a8a; margin: 0; }")
    monkeypatch.setattr(uiscale, "_factor", 1.0)
    assert uiscale.scale_stylesheet(qss) == qss


def test_configure_follows_the_choice_and_leaves_a_forced_qt_scale_alone(monkeypatch):
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    monkeypatch.setattr(uiscale, "chosen", lambda: "130")
    assert uiscale.configure(1080) == 1.3 and uiscale.px(10) == 13
    monkeypatch.setattr(uiscale, "chosen", lambda: "auto")
    assert uiscale.configure(768) == 0.85
    monkeypatch.setenv("QT_SCALE_FACTOR", "2")  # forced by hand: Qt scales, so we don't
    assert uiscale.configure(768) == 1.0
    monkeypatch.delenv("QT_SCALE_FACTOR")
    uiscale.configure(1080)


@pytest.mark.parametrize("height", [768, 1080])
def test_windows_and_dialogs_stay_inside_the_screen(height, monkeypatch):
    from PySide6.QtCore import QRect
    from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget

    from facet.presentation import fit
    from facet.presentation.qt_app import create_application
    create_application(["t"])
    monkeypatch.setattr(fit, "available", lambda widget=None: QRect(0, 0, 1366, height - 40))
    window = QWidget()
    fit.clamp_window(window, 1400, 900, 1020, 660)
    assert window.width() <= 1366 and window.height() <= height - 40 - fit.MARGIN
    dialog = QDialog()
    column = QVBoxLayout(dialog)
    for i in range(60):
        column.addWidget(QLabel(f"row {i}"))
    fit.scrollable(dialog)
    assert dialog.height() <= int((height - 40) * 0.9)
