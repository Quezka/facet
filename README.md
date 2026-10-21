# Facet

A light 3D model viewer for the desktop (Linux and Windows), built like its siblings
[Quire](https://github.com/Quezka/quire), [Ligature](https://github.com/Quezka/ligature) and
[Folio](https://github.com/Quezka/folio). It suits two kinds of model: a figure you want to turn
around and look at, and a technical part whose sizes you need exactly.

- **Formats:** STL (binary and text), OBJ (+ colours), PLY, 3MF.
- **Looking:** orbit, pan, zoom to cursor, standard views, perspective or flat view, solid /
  edges / wireframe, smooth shading, a section plane to look inside, a grid with a round step.
- **Measuring:** distance (with ΔX ΔY ΔZ), angle, hole diameter; picked points are exact and
  snap to corners and edges; mm, cm, m or inches.
- **Knowing:** size, volume, surface area, centre of mass, weight in PLA, ABS, steel…, and a
  mesh check (watertight? flipped faces? separate parts?).
- Pictures to a file or the clipboard; English, Italian, Russian; large, high-contrast look.

## Run

```
pip install -e .
facet               # or: facet model.stl   /   facet --demo
```

Needs PySide6 and a working OpenGL 2.1+ driver (software rendering is fine).

## Keys

| | |
|---|---|
| drag / right-drag or Shift-drag / wheel | turn / move / zoom |
| 1 2 3 4 5 6 7 | front, back, left, right, top, bottom, isometric |
| F | fit the model to the window |
| O / W | flat (orthographic) view / cycle solid-edges-wire |
| Esc | cancel the measurement in progress, then leave the tool |
| Alt+← / Alt+→ or PgUp / PgDn | previous / next model in the folder |
| Ctrl+O, Ctrl+Shift+S, Ctrl+Shift+C | open, save picture, copy picture |

## Develop

Python 3.10+, `domain → application → infrastructure + presentation`, wired in
`facet/bootstrap.py`; `tests/test_architecture.py` enforces the layering. See `CLAUDE.md`.

```
QT_QPA_PLATFORM=offscreen python -m pytest -q
python scripts/build.py --deb          # Linux package
python scripts/build.py --installer    # Windows setup (needs Inno Setup 6)
```

Free software under the GNU General Public License, version 3 or later.
