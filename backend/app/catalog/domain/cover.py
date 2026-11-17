from dataclasses import dataclass
from typing import Protocol

from app.shared.errors import DomainError

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_COVER_BYTES = 2 * 1024 * 1024  # 2 MB


@dataclass(frozen=True)
class CoverImage:
    """Value Object: Verweis auf die gespeicherte Bilddatei."""
    file_name: str
    content_type: str

    def __post_init__(self) -> None:
        if self.content_type not in ALLOWED_TYPES:
            raise DomainError("Nur JPEG, PNG oder WebP erlaubt")


class CoverStorage(Protocol):
    """Port. Implementierung in der Infrastruktur (aktuell Dateisystem/Volume)."""
    def save(self, file_name: str, data: bytes) -> None: ...
    def load(self, file_name: str) -> bytes | None: ...
    def delete(self, file_name: str) -> None: ...
