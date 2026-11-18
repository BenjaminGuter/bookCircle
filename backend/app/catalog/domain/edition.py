import re
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.catalog.domain.cover import CoverImage
from app.shared.errors import DomainError

ISBN_PATTERN = re.compile(r"^[0-9]{10}([0-9]{3})?$")


class EditionFormat(str, Enum):
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    EBOOK = "ebook"


@dataclass
class Edition:
    """Entity innerhalb des Aggregates Book: eine konkrete Ausgabe eines Werks."""
    id: UUID
    page_count: int
    format: EditionFormat
    isbn: str | None = None
    publisher: str | None = None
    published_year: int | None = None
    cover: CoverImage | None = None

    def __post_init__(self) -> None:
        if self.page_count < 1:
            raise DomainError("Eine Ausgabe braucht mindestens eine Seite")
        if self.isbn is not None and not ISBN_PATTERN.match(self.isbn):
            raise DomainError("ISBN muss aus 10 oder 13 Ziffern bestehen")
        if self.published_year is not None and not 1000 <= self.published_year <= 2100:
            raise DomainError("Erscheinungsjahr außerhalb des gültigen Bereichs")

    def set_cover(self, cover: CoverImage) -> CoverImage | None:
        """Setzt/ersetzt das Cover und gibt das alte zurück (zum Aufräumen der Datei)."""
        old, self.cover = self.cover, cover
        return old

    def remove_cover(self) -> CoverImage | None:
        old, self.cover = self.cover, None
        return old