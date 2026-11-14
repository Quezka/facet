# Changelog

## [0.8.0] - 2026-11-14

The suite's new look: **Material 3, tonal** (no more liquid glass).

- A **navigation rail**: each page an icon with its name under it; icons only in a narrow window.
- Soft tonal background, white cards with big round corners, filled text boxes, darker text, one filled button for the main action.
- Menus, lists and tooltips are solid; the "Glass look" and "See-through windows" settings are gone, and the app leaves GNOME Blur my Shell's list (smoother scrolling).

## [0.7.2] - 2026-11-14

- **The sidebar fits its title and page names**, and shows only icons while the window is narrow.

## [0.7.1] - 2026-11-09

- Smoother scrolling and window moves: the app only asks GNOME's Blur my Shell to blur behind its windows while they're see-through (with see-through off, that blur was redone on every frame for nothing). The glass header over scrolling pages is cheaper to draw.

## [0.7.0] - 2026-11-09

The suite's new shared look (one design system for every app, `suite-rs/design/tokens.json`):

- **Neutral greys** instead of blue-tinted backgrounds, sidebars and borders; indigo stays as the one accent colour.
- **Bigger, clearer text** on one type scale shared with the phone apps: body text 16 px, nothing smaller than 13 px;
  titles and buttons follow the same sizes everywhere (the Interface size setting still scales it all).
- The same corner radii and spacing in every app.

## [0.6.0] - 2026-11-09

Corners that line up (suite-kit 0.10).

- The sidebar, cards and the Settings list share one radius and one gap, and what's inside them is rounded to match,
  so the curves run side by side. The Settings header floats over the cards, as wide as them.
- The glass look's description in Settings says what it really does now. Facet's 3D view stays opaque.

## [0.5.0] - 2026-11-08

### Changed
- **Liquid glass done properly, the Apple way.** Backgrounds are plain again and content stays solid; the chrome is glass. Menus, drop-down lists and tooltips blur what's really under them, settings headers float over their cards and blur them as they scroll, and the sidebar floats as an inset panel. On Windows 11 the window shows the system's Mica behind the sidebar. The colour wash is gone.

## [0.4.0] - 2026-11-08

### Changed
- **A glass look on top of Material 3, with brighter colours:** frosted, see-through surfaces over a soft wash of colour. Settings turns it off; High contrast stays solid.
- **Settings is redone in the suite's new window:** sections on the left, cards of rows with switches, nothing cut off on a small screen. Every other window gets its title on top and a filled Save button.

## [0.3.0] - 2026-11-04

### Changed
- The icons are Material Symbols now: outlined, and filled for what is selected.

## [0.2.0] - 2026-11-04

### Changed
- A new look: Material 3 shapes and tonal colours, and the Manrope typeface. A flick on a trackpad now keeps gliding; a mouse wheel works as before.

## [0.1.10] - 2026-10-26

The interface size set to Automatic is a compact 85% now (the shared toolkit's new standard; 80% and 90% are new choices). Larger sizes stay in Settings.

## [0.1.9] - 2026-10-26

- Icons, translations and the dialog fitting come from the suite's shared toolkit; Enter now lets go of a one-line text box.

## [0.1.8] - 2026-10-21
- (0.1.7 was never published: a new test broke the others. Same content, fixed.)
- Windows: the installer gives `.stl`, `.obj`, `.ply` and `.3mf` the same Facet file icons as on
  Linux, one per format, and lists Facet under "Open with". Windows shows a file type's icon
  from the app that is its default, so the icons appear once you make Facet the default for
  that format ("Open with" -> "Always").

## [0.1.6] - 2026-10-21
- Linux: `.stl`, `.obj`, `.ply` and `.3mf` files get a Facet icon in the file manager (a page
  with the faceted cube and the format's name) as soon as the package is installed. Facet
  registers its own file types, kinds of the usual ones, so every other app that opens STL
  still does.

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
