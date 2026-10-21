# Changelog

## [0.1.5] - 2026-10-21
- The interface is built at its size instead of being magnified by Qt: text, icons, spacing and
  the style sheet are multiplied by the chosen scale (Settings, applies after a restart). This
  keeps the 3D view and repaints at whole pixels. A `QT_SCALE_FACTOR` you set yourself still wins.
- Fixed: dragging in the 3D view turned the model the wrong way sideways; dragging right now
  turns it to the right.

## [0.1.4] - 2026-10-21
- The buttons on the Home page (and everything else outside the 3D view) react without lag:
  the 3D view is now only created when the first model is opened. A window that holds an
  OpenGL widget is drawn through the graphics card on every repaint, which made even a hover
  highlight heavier.

## [0.1.3] - 2026-10-21
- Opening a second model while the first is still being checked can no longer mix up their
  data (the mesh check is now tied to the model it belongs to), and closing the window waits
  for a running check. 0.1.2 was never published because of this; its fix is included here.

## [0.1.2] - 2026-10-21
- Fixed: choosing an interface size in Settings and pressing "Restart" now really applies it
  (the restarted app used to mistake the old size for one you had forced from the command line).

## [0.1.1] - 2026-10-21
- The interface is now the same size as Quire and the other apps: "Automatic" picks 85% on
  short screens (like a 1366x768 laptop) and 100% elsewhere, and the text uses the system
  size. Larger sizes (up to 200%) are still in Settings for anyone who wants them.

## [0.1.0] - 2026-10-21
- First release. Opens STL (binary and text), OBJ (with vertex and material colours), PLY and
  3MF models; drop a file on the window or give it on the command line, and step through the
  other models in the same folder with Alt+Left / Alt+Right.
- A fast OpenGL view: drag to turn, right-drag or Shift-drag to move, wheel to zoom towards the
  cursor, double-click to turn around a point, standard views (keys 1-7), perspective or flat
  (orthographic) projection, solid / outlined-edges / wireframe, smooth or faceted shading.
- Exact measuring for technical parts: click two points for a distance (with its X, Y and Z
  parts), three for an angle, or three around a hole for its diameter and radius. Points are
  found exactly (not from the picture) and snap to corners and edges. The model's units are
  mm, cm, m or inches, with 1 to 4 decimals; sizes of the bounding box can be drawn on the model.
- A details panel: size, volume, surface area, centre of mass, and weight in ten common
  materials. A mesh check reports holes, edges shared by three faces, flipped faces, empty
  triangles and separate parts. A section plane cuts the model along X, Y or Z.
- Save or copy a picture of the view.
- Like the other apps: light, dark and high-contrast looks, large text and an interface size up
  to 200%, English / Italian / Russian, daily update check, `.deb` and Windows installer.
