"""The windows, driven the way a person would, on the headless test platform (which may
have no OpenGL: nothing here needs the 3D view to draw)."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest

from facet.demo import write_samples
from facet.presentation import i18n, theme


@pytest.fixture(scope="module")
def app():
    from facet.presentation import qt_app
    application = qt_app.create_application(["facet-tests"])
    yield application


@pytest.fixture(autouse=True)
def clean_settings(app):
    QSettings().clear()
    yield
    QSettings().clear()


def wait_for(condition, timeout=8000):
    waited = 0
    while not condition() and waited < timeout:
        QTest.qWait(50)
        waited += 50
    assert condition(), "timed out"


@pytest.fixture
def window(app, services):
    from facet.presentation.main_window import MainWindow
    w = MainWindow(services)
    w.show()
    yield w
    w.close()


@pytest.fixture
def samples(tmp_path):
    return write_samples(tmp_path)


def open_and_wait(window, path):
    window.open_file(str(path))
    wait_for(lambda: window.record is not None and window.record.path == str(path))
    wait_for(lambda: window.viewer.analysis is not None)


def test_dark_theme_applies_first(app):
    manager = theme.manager()
    manager.set_mode("dark")
    assert manager.theme.dark
    manager.set_mode("light")
    assert not manager.theme.dark


def test_starts_on_home_and_viewer_needs_a_model(window):
    assert window.stack.currentIndex() == window.HOME
    window.show_page(window.VIEWER)
    assert window.stack.currentIndex() == window.HOME
    assert not window.sidebar.group.button(window.VIEWER).isEnabled()


def test_opening_a_model_fills_the_details(window, samples):
    open_and_wait(window, samples[0])
    assert window.stack.currentIndex() == window.VIEWER
    v = window.viewer
    assert v.facts.values["x"].text() == "60.00 mm"
    assert v.facts.values["z"].text() == "8.00 mm"
    assert "Watertight" in v.health.text()
    assert window.windowTitle() == "bracket.stl — Facet"
    assert v.subtitle.text().startswith("800 triangles")
    assert "g" in v.facts.values["weight"].text()


def test_changing_units_relabels_everything(window, samples):
    open_and_wait(window, samples[0])
    v = window.viewer
    v.units.set_value("in")
    v._unit_picked("in")
    assert v.facts.values["x"].text().endswith(" in")
    assert v.facts.values["volume"].text().endswith("in³")
    v.units.set_value("cm")
    v._unit_picked("cm")
    assert v.facts.values["x"].text().startswith("6")  # 60 mm written as 6 cm, no conversion of the model
    assert QSettings().value("unit") == "cm"


def test_decimals_setting_changes_readings(window, samples):
    open_and_wait(window, samples[0])
    window.measures.set_decimals(3)
    window.numbers_changed()
    assert window.viewer.facts.values["x"].text() == "60.000 mm"


def test_measuring_a_distance_lists_it_with_its_axis_parts(window, samples):
    open_and_wait(window, samples[0])
    v = window.viewer
    v._measured("distance", ((0, 0, 0), (30, 40, 0)))
    assert v.list.count() == 1
    text = v.list.item(0).text()
    assert "50.00 mm" in text and "ΔX 30.00 mm" in text and "ΔY 40.00 mm" in text
    assert v.viewport.measurements[0][1] == "50.00 mm"
    v._measured("circle", ((6, 0, 0), (0, 6, 0), (-6, 0, 0)))
    assert "Ø 12.00 mm" == v.viewport.measurements[1][1]
    v._measured("angle", ((1, 0, 0), (0, 0, 0), (0, 1, 0)))
    assert "90.00°" in v.list.item(2).text()
    v.list.setCurrentRow(0)
    v._remove_measurement()
    assert v.list.count() == 2
    v._clear_measurements()
    assert v.list.count() == 0 and not v.clear.isEnabled()


def test_a_bad_measurement_says_why(window, samples):
    open_and_wait(window, samples[0])
    v = window.viewer
    v._measured("circle", ((0, 0, 0), (1, 0, 0), (2, 0, 0)))
    assert v.list.count() == 0
    assert "line" in v.status.text()


def test_measurements_follow_the_unit(window, samples):
    open_and_wait(window, samples[0])
    v = window.viewer
    v._measured("distance", ((0, 0, 0), (25.4, 0, 0)))
    v.units.set_value("in")
    v._unit_picked("in")
    assert "25.40 in" in v.list.item(0).text()  # the model's numbers are now inches


def test_section_controls_set_the_plane(window, samples):
    open_and_wait(window, samples[0])
    v = window.viewer
    assert v.viewport.section is None
    v.section_on.setChecked(True)
    assert v.viewport.section == (2, 0.5, False)
    assert v.section_label.text() == "Z = 4.00 mm"
    v.axis.set_value(0)
    v._section_changed()
    v.flip.setChecked(True)
    assert v.viewport.section == (0, 0.5, True)
    v.section_on.setChecked(False)
    assert v.viewport.section is None


def test_display_modes_and_toggles_reach_the_view(window, samples):
    open_and_wait(window, samples[0])
    v = window.viewer
    v.cycle_display()
    assert v.viewport.mode == 1
    v.cycle_display(); v.cycle_display()
    assert v.viewport.mode == 0
    v.toggle_orthographic()
    assert v.viewport.camera.orthographic
    v.dimensions_toggle.setChecked(True)
    assert v.viewport.show_dimensions


def test_a_second_model_replaces_the_first_and_clears_measurements(window, samples):
    open_and_wait(window, samples[0])
    window.viewer._measured("distance", ((0, 0, 0), (1, 0, 0)))
    open_and_wait(window, samples[1])
    assert window.viewer.list.count() == 0
    assert window.windowTitle() == "vase.stl — Facet"
    assert window.viewer.facts.values["z"].text() == "90.00 mm"


def test_folder_navigation_steps_through_models(window, samples):
    open_and_wait(window, samples[0])  # bracket.stl
    assert window.viewer.next.isEnabled() and not window.viewer.previous.isEnabled()
    window.step(1)
    wait_for(lambda: window.record.name == "vase.stl")
    assert window.viewer.previous.isEnabled() and not window.viewer.next.isEnabled()


def test_a_broken_file_is_reported_and_forgotten(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: shown.append(a[2]))
    bad = tmp_path / "bad.stl"
    bad.write_bytes(b"nonsense")
    window.open_file(str(bad))
    wait_for(lambda: shown)
    assert "bad.stl" in shown[0] and "STL" in shown[0]
    assert window.record is None


def test_recent_models_show_on_home(window, samples):
    open_and_wait(window, samples[0])
    assert window.home.recent.count() == 1
    assert window.home.recent_card.isVisibleTo(window.home)


def test_settings_dialog_opens_and_changes_decimals(window, services):
    from facet.presentation.settings import SettingsDialog
    dialog = SettingsDialog(services, window.measures, window.updater, window)
    dialog._decimals(4)
    assert window.measures.decimals == 4
    dialog.close()


def test_italian_ui_builds(app, services):
    from facet.presentation.main_window import MainWindow
    i18n.install("it")
    try:
        w = MainWindow(services)
        assert w.sidebar.group.button(w.VIEWER).text().strip() == "Visualizzatore"
        w.close()
    finally:
        i18n.install("en")
