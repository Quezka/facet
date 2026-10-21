"""Everything the UI can ask for, in one place (built by `bootstrap`)."""
from __future__ import annotations

from dataclasses import dataclass

from .models import ModelService
from .updates import AvailableUpdate, UpdateService


@dataclass
class Services:
    models: ModelService
    updates: UpdateService


__all__ = ["AvailableUpdate", "Services"]
