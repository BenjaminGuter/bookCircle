from dataclasses import dataclass
from uuid import UUID

from app.catalog.domain.cover import CoverImage
from app.shared.errors import DomainError


@dataclass
class Book:
    id: UUID
    title: str
    page_count: int
    author_ids: list[UUID]
    isbn: str | None = None
    cover: CoverImage | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise DomainError("Titel darf nicht leer sein")
        if self.page_count < 1:
            raise DomainError("Ein Buch braucht mindestens eine Seite")
        if not self.author_ids:
            raise DomainError("Ein Buch braucht mindestens einen Autor")

    def set_cover(self, cover: CoverImage) -> CoverImage | None:
        """Setzt/ersetzt das Cover und gibt das alte zurück (zum Aufräumen)."""
        old, self.cover = self.cover, cover
        return old

    def remove_cover(self) -> CoverImage | None:
        old, self.cover = self.cover, None
        return old
