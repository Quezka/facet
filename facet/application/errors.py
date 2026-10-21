"""Errors the use cases raise. Their messages are shown to the user (translated)."""


class ApplicationError(Exception):
    """Something the user can understand and act on."""


class FileFormatError(ApplicationError):
    """The file isn't a model Facet can open."""


class FileAccessError(ApplicationError):
    """The file couldn't be read (missing, no permission…)."""


class NoModelError(ApplicationError):
    """No model is open."""


class MeasureError(ApplicationError):
    """The points picked don't make that measurement."""


class UpdateError(ApplicationError):
    """Checking for, downloading or installing a new version didn't work."""
