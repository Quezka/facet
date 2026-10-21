"""One scale for the whole interface, chosen in Settings (or automatic for small screens).

The interface is *built* at the chosen size: text, icons, spacing and the style sheet are
multiplied by the factor (`px()`, `scale_stylesheet()`, the application font). It is not
magnified afterwards with Qt's scale factor, which leaves the 3D view and every repaint at a
fractional pixel ratio. The choice applies after a restart.
"""
from __future__ import annotations

import os
import re

from PySide6.QtCore import QSettings

CHOICES = ("auto", "80", "90", "100", "115", "130", "150", "175", "200")  # percent
AUTO_BELOW = 800  # screens up to this tall (like 1366x768) get the smaller interface
SMALL = 0.85

_factor = 1.0
base_pt = 0.0  # the system's text size, before scaling (set once the application exists)


def chosen() -> str:
    value = str(QSettings().value("ui_scale", "auto"))
    return value if value in CHOICES else "auto"


def set_chosen(choice: str):
    QSettings().setValue("ui_scale", choice if choice in CHOICES else "auto")


def factor(choice: str, screen_height: int | None) -> float:
    """The scale factor for a choice; "auto" depends on how tall the screen is."""
    if choice == "auto":
        return SMALL if screen_height and screen_height <= AUTO_BELOW else 1.0
    return int(choice) / 100 if choice in CHOICES else 1.0


def configure(screen_height: int | None) -> float:
    """Fix the factor for this run. A QT_SCALE_FACTOR set by hand wins: Qt then does the scaling."""
    global _factor
    _factor = 1.0 if "QT_SCALE_FACTOR" in os.environ else factor(chosen(), screen_height)
    return _factor


def font_rule() -> str:
    """A style sheet rule giving every widget the scaled text size. Setting the application
    font alone isn't enough: desktop themes give some widget classes (labels, menus) their
    own fonts, which would stay at full size."""
    return f"font-size: {base_pt:g}pt;" if _factor != 1.0 and base_pt else ""


def current() -> float:
    return _factor


def px(value: float) -> int:
    """A size in pixels at the current scale (never vanishing: a 1 px line stays 1 px)."""
    if not value:
        return 0
    return max(1, round(value * _factor))


_UNIT = re.compile(r"(?<![\w#.])(\d+(?:\.\d+)?)(px|pt)\b")


def scale_stylesheet(qss: str) -> str:
    """Multiply every `px` and `pt` length in a style sheet by the factor."""
    if _factor == 1.0:
        return qss

    def scaled(match: re.Match) -> str:
        number, unit = float(match.group(1)), match.group(2)
        if unit == "px":
            return f"{px(number)}px"
        return f"{round(number * _factor, 1):g}pt"

    return _UNIT.sub(scaled, qss)
