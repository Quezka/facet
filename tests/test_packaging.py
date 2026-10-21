"""Keep store/packaging metadata consistent with facet/__init__.py."""
import ast
import configparser
import importlib.util
import xml.etree.ElementTree as ET

import pytest
from pathlib import Path

import facet

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"
METAINFO = PACKAGING / f"{facet.APP_ID}.metainfo.xml"
DESKTOP = PACKAGING / f"{facet.APP_ID}.desktop"


def metainfo():
    return ET.parse(METAINFO).getroot()


def test_metainfo_identifies_app_and_developer():
    root = metainfo()
    assert root.findtext("id") == facet.APP_ID
    assert root.findtext("name") == facet.APP_NAME
    developer = root.find("developer")
    assert developer.get("id") == facet.DEVELOPER_ID
    assert developer.findtext("name") == facet.DEVELOPER
    assert root.findtext("launchable") == DESKTOP.name
    assert root.find("url[@type='homepage']").text == facet.HOMEPAGE


def test_current_version_is_the_newest_release():
    releases = metainfo().findall("releases/release")
    assert releases, "metainfo has no <release> entries"
    assert releases[0].get("version") == facet.__version__, (
        f"add <release version=\"{facet.__version__}\"> at the top of {METAINFO.name}")


def test_desktop_file_points_at_app_id():
    entry = configparser.ConfigParser(interpolation=None)
    entry.optionxform = str
    entry.read(DESKTOP, encoding="utf-8")
    assert entry["Desktop Entry"]["Icon"] == facet.APP_ID
    assert entry["Desktop Entry"]["Exec"].split()[0] == "facet"


def test_windows_version_file_is_valid_python(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_script", ROOT / "scripts" / "build.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    monkeypatch.setattr(build, "BUILD", tmp_path)
    text = build.write_windows_version_file().read_text(encoding="utf-8")
    ast.parse(text)
    assert f"'CompanyName', '{facet.DEVELOPER}'" in text
    assert f"'ProductVersion', '{facet.__version__}'" in text


def load_release_notes():
    spec = importlib.util.spec_from_file_location("release_notes",
                                                  ROOT / "scripts" / "release_notes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_changelog_has_notes_for_current_version():
    notes = load_release_notes().notes_for(facet.__version__)
    assert notes and not notes.startswith("## ")


def test_release_notes_stop_at_the_next_version():
    text = "# Changelog\n\n## [1.1.0] - x\n- new\n\n## [1.0.0] - y\n- old\n"
    assert load_release_notes().notes_for("1.1.0", text) == "- new"
    with pytest.raises(SystemExit):
        load_release_notes().notes_for("9.9.9", text)


def test_version_is_semver():
    import re
    assert re.fullmatch(r"\d+\.\d+\.\d+", facet.__version__)


def test_every_3d_file_type_has_an_icon_and_is_offered_by_the_desktop_file():
    mime = ET.parse(PACKAGING / f"{facet.APP_ID}.xml").getroot()
    ns = "{http://www.freedesktop.org/standards/shared-mime-info}"
    entry = configparser.ConfigParser(interpolation=None)
    entry.optionxform = str
    entry.read(DESKTOP, encoding="utf-8")
    offered = entry["Desktop Entry"]["MimeType"].split(";")
    globs = set()
    for kind in mime.findall(f"{ns}mime-type"):
        name = kind.get("type")
        icon = kind.find(f"{ns}icon").get("name")
        assert (PACKAGING / "icons" / f"{icon}.svg").is_file(), f"no icon file for {name}"
        assert name in offered, f"{name} is missing from the desktop file's MimeType"
        glob = kind.find(f"{ns}glob")
        assert int(glob.get("weight")) > 50  # beats the stock type, whose icon the theme owns
        globs.add(glob.get("pattern"))
    assert globs == {f"*{ext}" for ext in facet.MODEL_EXTENSIONS}


def test_file_icons_are_up_to_date(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("icons_script", ROOT / "scripts" / "make_file_icons.py")
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    monkeypatch.setattr(script, "OUT", tmp_path)
    script.main()
    for made in tmp_path.glob("*.svg"):
        assert made.read_text(encoding="utf-8") == (PACKAGING / "icons" / made.name).read_text(
            encoding="utf-8"), f"run scripts/make_file_icons.py ({made.name} is stale)"


def test_windows_file_icons_are_valid_multi_size_icos(tmp_path):
    """Run apart: building the icons starts a bare Qt application, which must not be the
    one the other tests' windows later try to share."""
    import struct
    import subprocess
    import sys

    pytest.importorskip("PySide6")
    code = (
        "import importlib.util, pathlib, sys\n"
        "spec = importlib.util.spec_from_file_location('b', sys.argv[1] + '/scripts/build.py')\n"
        "build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)\n"
        "build.BUILD = pathlib.Path(sys.argv[2]); build.render_file_icons()\n")
    done = subprocess.run([sys.executable, "-c", code, str(ROOT), str(tmp_path)],
                          capture_output=True, text=True, timeout=120,
                          env={**__import__("os").environ, "QT_QPA_PLATFORM": "offscreen"})
    assert done.returncode == 0, done.stderr
    folder = tmp_path / "file-icons"
    icos = {p.stem: p.read_bytes() for p in folder.glob("*.ico")}
    assert set(icos) == {ext.lstrip(".") for ext in facet.MODEL_EXTENSIONS}
    for data in icos.values():
        reserved, kind, count = struct.unpack_from("<HHH", data)
        assert (reserved, kind, count) == (0, 1, 4)
        sizes = []
        for i in range(count):
            w, h, _c, _r, planes, bits, length, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
            sizes.append(w or 256)
            assert data[offset:offset + 8] == b"\x89PNG\r\n\x1a\n" and offset + length <= len(data)
        assert sizes == [16, 32, 48, 256]


def test_installer_registers_each_3d_format_with_its_icon():
    script = (PACKAGING / "facet.iss").read_text(encoding="utf-8")
    for ext in facet.MODEL_EXTENSIONS:
        name = ext.lstrip(".")
        assert f'Classes\\{ext}\\OpenWithProgids' in script
        assert f"icons\\{name}.ico" in script
    assert "FileIconsDir" in script
