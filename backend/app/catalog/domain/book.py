from dataclasses import dataclass
from uuid import UUID

from app.catalog.domain.edition import Edition
from app.shared.errors import DomainError


@dataclass
class Book:
    """Aggregate Root: das Werk. Seitenzahl, ISBN und Cover liegen an den Ausgaben."""
    id: UUID
    title: str
    author_ids: list[UUID]
    editions: list[Edition]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise DomainError("Titel darf nicht leer sein")
        if not self.author_ids:
            raise DomainError("Ein Buch braucht mindestens einen Autor")
        if not self.editions:
            raise DomainError("Ein Buch braucht mindestens eine Ausgabe")
        if len({e.id for e in self.editions}) != len(self.editions):
            raise DomainError("Ausgaben-IDs müssen eindeutig sein")

    def add_edition(self, edition: Edition) -> None:
        if any(e.id == edition.id for e in self.editions):
            raise DomainError("Ausgabe existiert bereits")
        if edition.isbn and any(e.isbn == edition.isbn for e in self.editions):
            raise DomainError("ISBN ist bei diesem Buch schon vergeben")
        self.editions.append(edition)

    def get_edition(self, edition_id: UUID) -> Edition | None:
        return next((e for e in self.editions if e.id == edition_id), None)