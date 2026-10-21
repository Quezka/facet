"""How lengths, areas and weights are written: the chosen unit and number of decimals."""
from __future__ import annotations

from PySide6.QtCore import QLocale, QSettings

from ..application.units import UNITS, convert

DECIMAL_CHOICES = (1, 2, 3, 4)


class Measures:
    """The units the user picked. `unit` is what the model's numbers mean, and also what
    readings are shown in (changing it re-labels the model, it doesn't rescale it)."""

    def __init__(self):
        settings = QSettings()
        unit = str(settings.value("unit", "mm"))
        self.unit = unit if unit in UNITS else "mm"
        try:
            decimals = int(settings.value("decimals", 2))
        except (TypeError, ValueError):
            decimals = 2
        self.decimals = decimals if decimals in DECIMAL_CHOICES else 2

    def set_unit(self, unit: str):
        self.unit = unit if unit in UNITS else "mm"
        QSettings().setValue("unit", self.unit)

    def set_decimals(self, decimals: int):
        self.decimals = decimals if decimals in DECIMAL_CHOICES else 2
        QSettings().setValue("decimals", self.decimals)

    def number(self, value: float, decimals: int | None = None) -> str:
        places = self.decimals if decimals is None else decimals
        value = float(value)
        if abs(value) < 0.5 * 10 ** -places:
            value = 0.0  # never "-0.00"
        return QLocale().toString(value, "f", places)

    def length(self, value: float) -> str:
        return f"{self.number(value)} {self.unit}"

    def area(self, value: float) -> str:
        return f"{self.number(value)} {self.unit}²"

    def volume(self, value: float) -> str:
        cubic = f"{self.unit}³"
        text = f"{self.number(value)} {cubic}"
        if self.unit == "mm":  # the figure printers think in
            text += f"  ({self.number(value / 1000)} cm³)"
        return text

    def weight(self, grams: float) -> str:
        if grams >= 1000:
            return f"{self.number(grams / 1000)} kg"
        return f"{self.number(grams, 1 if grams >= 10 else 2)} g"

    def angle(self, degrees: float) -> str:
        return f"{self.number(degrees)}°"

    def point(self, p) -> str:
        return "  ".join(f"{axis} {self.number(v)}" for axis, v in zip("XYZ", p))

    def bytes(self, size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size} {unit}" if unit == "B" else f"{QLocale().toString(size, 'f', 1)} {unit}"
            size /= 1024
        return ""

    def count(self, n: int) -> str:
        return QLocale().toString(int(n))

    def convert(self, value: float, source: str) -> float:
        return convert(value, source, self.unit)
