"""The ports: what the use cases need from the outside world."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain.mesh import Mesh


class MeshReader(Protocol):
    def read(self, path: str) -> Mesh:
        """Load a model. Raises FileFormatError / FileAccessError."""
        ...

    def size(self, path: str) -> int: ...

    def siblings(self, path: str) -> list[str]:
        """The model files in the same folder, by name."""
        ...


class KeyValueStore(Protocol):
    """Small persistent settings (e.g. when updates were last checked)."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str | None) -> None: ...


# ---- updates ------------------------------------------------------------------------

@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int
    sha256: str | None = None  # published checksum, when the host provides one


@dataclass(frozen=True)
class ReleaseInfo:
    version: str  # e.g. "0.2.0"
    notes: str  # Markdown
    page_url: str
    assets: tuple[ReleaseAsset, ...]


class ReleaseFeed(Protocol):
    """Where new versions are published (e.g. GitHub releases). Network only."""

    def latest(self) -> ReleaseInfo | None: ...

    def download(self, asset: ReleaseAsset, progress) -> str:
        """Fetch the file, check its size and checksum, and return its local path.
        `progress(done_bytes, total_bytes)` is called as it goes."""
        ...


class UpdateInstaller(Protocol):
    """Installs a downloaded release on this platform."""

    def supported(self) -> bool:
        """False when this copy can't update itself (e.g. running from source)."""
        ...

    def pick(self, assets: tuple[ReleaseAsset, ...]) -> ReleaseAsset | None: ...

    def install(self, path: str) -> bool:
        """Install it. True: the installer took over and the app must quit now (it will be
        started again). False: installed, restart the app to use the new version."""
        ...
