"""Length units and materials. A model file has no unit of its own; the user says what it is."""
from __future__ import annotations

from dataclasses import dataclass

UNITS = ("mm", "cm", "m", "in")
_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}


def to_mm(unit: str) -> float:
    return _TO_MM.get(unit, 1.0)


def convert(value: float, source: str, target: str) -> float:
    return value * to_mm(source) / to_mm(target)


@dataclass(frozen=True)
class Material:
    name: str
    density: float  # grams per cubic centimetre


MATERIALS = (
    Material("PLA", 1.24), Material("PETG", 1.27), Material("ABS", 1.04), Material("Nylon", 1.14),
    Material("Resin", 1.10), Material("Aluminium", 2.70), Material("Steel", 7.85),
    Material("Brass", 8.50), Material("Titanium", 4.51), Material("Wood (oak)", 0.75),
)


def weight_grams(volume: float, unit: str, density: float) -> float:
    """Mass of a solid of `volume` (cubic `unit`) made of a material of `density` g/cm³."""
    cubic_cm = abs(volume) * (to_mm(unit) / 10.0) ** 3
    return cubic_cm * density
