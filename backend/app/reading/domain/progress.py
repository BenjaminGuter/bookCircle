from dataclasses import dataclass, field
from uuid import UUID

from app.shared.book_position import to_position
from app.shared.errors import DomainError
from app.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ReadingProgressChanged(DomainEvent):
    user_id: UUID
    book_id: UUID
    page: int
    position: int  # Promille, das nutzt Discussion


@dataclass(frozen=True, kw_only=True)
class BookFinished(DomainEvent):
    user_id: UUID
    book_id: UUID


@dataclass
class ReadingProgress:
    """Aggregate Root. Identität = (user_id, book_id), unabhängig von Lesekreisen."""
    user_id: UUID
    book_id: UUID
    total_pages: int
    last_read_page: int = 0
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def start(cls, user_id: UUID, book_id: UUID, total_pages: int) -> "ReadingProgress":
        if total_pages < 1:
            raise DomainError("Ein Buch braucht mindestens eine Seite")
        return cls(user_id, book_id, total_pages)

    def advance_to(self, page: int) -> None:
        """Normalfall: nur vorwärts."""
        self._check_range(page)
        if page < self.last_read_page:
            raise DomainError("Fortschritt sinkt nur über correct_to")
        self._set(page)

    def correct_to(self, page: int) -> None:
        """Korrektur: darf sinken (z. B. versehentlich zu weit gesetzt)."""
        self._check_range(page)
        self._set(page)

    @property
    def position(self) -> int:
        return to_position(self.last_read_page, self.total_pages)

    def percentage(self) -> int:
        return round(100 * self.last_read_page / self.total_pages)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events

    def _check_range(self, page: int) -> None:
        if not 0 <= page <= self.total_pages:
            raise DomainError("Seite außerhalb des Buchs")

    def _set(self, page: int) -> None:
        if page == self.last_read_page:
            return
        self.last_read_page = page
        self._events.append(ReadingProgressChanged(
            user_id=self.user_id, book_id=self.book_id, page=page, position=self.position
        ))
        if page == self.total_pages:
            self._events.append(BookFinished(user_id=self.user_id, book_id=self.book_id))
