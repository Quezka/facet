# Facet

Python 3.10+ / PySide6 desktop app (Linux + Windows): a light 3D model viewer with exact
measuring. Sibling of Quire, Ligature and Folio (`../quire`, `../ligature`, `../folio`): same
look, toolkit, release process (see their CLAUDE.md files).

- Layers: `facet/domain` → `facet/application` → `facet/infrastructure` + `facet/presentation`; wired in `facet/bootstrap.py`. `tests/test_architecture.py` enforces it; the UI never imports the domain; use cases return the plain records of `application/records.py`, never domain classes.
- Run: `.venv/bin/facet --demo`. Test: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` (check the exit code). The venv is `--without-pip` and borrows `../ligature/.venv` site-packages through a `.pth` file.
- `domain/mesh.py`: a `Mesh` is one flat `array('f')`, 9 floats per triangle (so a million triangles go to the GPU as they are). Welding (`weld`), health, smooth normals and feature edges are computed in background jobs from a `Topology`. `domain/geometry.py`: exact ray/triangle, circle through three points, angle.
- Reading files: `infrastructure/mesh_files.py` (STL/OBJ/PLY/3MF, stdlib only; colours kept as bytes). `application/models.py` is the one use-case service (`ModelService`); it keeps the open mesh and hands out records with a `token` so the UI can drop stale results.
- Rendering (`presentation/viewport.py`, `shaders.py`): GLSL 1.20 on a compatibility context. Edges come from a barycentric attribute plus per-triangle feature-edge flags, not from polygon modes. Picking draws triangle ids into an FBO, reads the pixel, then `ModelService.snap` computes the exact point on that one triangle (corner/edge snapping included). Overlay (measurements, gizmo, labels) is QPainter in `paintGL`.
- PySide6 gotchas found the hard way: `QMatrix4x4 * QVector4D` is unsupported (use `.map`); `setUniformValue(name, float)` fails (use `setUniformValue1f`, and `QVector3D/4D` for vectors); `setAttributeValue` with a name crashes (leave disabled attributes alone); `QOpenGLShaderProgram.setAttributeBuffer` NORMALISES byte attributes (0..255 arrives as 0..1); `QWidget.grab()` of a window can miss the QPainter overlay of a QOpenGLWidget, use `grabFramebuffer()`. A job's Python objects must stay referenced and its result must be delivered by a UI-thread QObject slot (`presentation/background.py`).
- UI text: wrap in `_()`/`N_()`, add Russian and Italian to `presentation/locales/ru.py` and `it.py` (`tests/test_i18n.py`). Application error messages are fixed strings, translated by the UI via `_(str(e))`.
- Look: larger text and high contrast by default (the user doesn't see well), UI scale up to 200%.
- Releases: bump `__version__`, add a CHANGELOG section and a metainfo `<release>`, commit as arsdom15@gmail.com, tag `vX.Y.Z`, push the commit and the tag; CI publishes `facet_<v>_<arch>.deb` and `Facet-<v>-windows-x64-setup.exe` (in-app updates depend on those names). Windows installer registers Facet under "Open with" only.
