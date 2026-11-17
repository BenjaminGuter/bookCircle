import os
from pathlib import Path


class LocalCoverStorage:
    """Speichert Covers als Dateien in COVER_DIR (im Docker ein Volume)."""

    def __init__(self, directory: str | None = None) -> None:
        self._dir = Path(directory or os.getenv("COVER_DIR", "./data/covers"))
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, file_name: str) -> Path:
        if Path(file_name).name != file_name:  # kein Pfad, nur Dateiname
            raise ValueError("Ungültiger Dateiname")
        return self._dir / file_name

    def save(self, file_name: str, data: bytes) -> None:
        target = self._path(file_name)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)  # atomar: nie halb geschriebene Datei

    def load(self, file_name: str) -> bytes | None:
        path = self._path(file_name)
        return path.read_bytes() if path.exists() else None

    def delete(self, file_name: str) -> None:
        self._path(file_name).unlink(missing_ok=True)
