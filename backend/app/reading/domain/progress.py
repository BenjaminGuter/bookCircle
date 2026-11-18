from dataclasses import dataclass, field
from uuid import UUID

from app.shared.errors import DomainError
from app.shared.events import DomainEvent


@dataclass(frozen=True)
class EditionRef:
    """Was der Context Reading von einer Ausgabe wissen muss (kommt aus dem Catalog)."""
    edition_id: UUID
    book_id: UUID
    page_count: int


@dataclass(frozen=True, kw_only=True)
class ReadingProgressChanged(DomainEvent):
    user_id: UUID
    book_id: UUID
    page: int
    total_pages: int  # Discussion braucht beides für den exakten Vergleich


@dataclass(frozen=True, kw_only=True)
class BookFinished(DomainEvent):
    user_id: UUID
    book_id: UUID


@dataclass
class ReadingProgress:
    """Aggregate Root. Identität = (user_id, book_id), unabhängig von Lesekreisen.
    Pro Werk gibt es genau einen Fortschritt, auch wenn man die Ausgabe wechselt."""
    user_id: UUID
    book_id: UUID
    edition_id: UUID
    total_pages: int  # Snapshot der Seitenzahl der Ausgabe
    last_read_page: int = 0
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def start(cls, user_id: UUID, edition: EditionRef) -> "ReadingProgress":
        if edition.page_count < 1:
            raise DomainError("Eine Ausgabe braucht mindestens eine Seite")
        return cls(user_id, edition.book_id, edition.edition_id, edition.page_count)

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

    def switch_edition(self, edition: EditionRef) -> None:
        """Ausgabe wechseln (z. B. Taschenbuch -> E-Book). Der Fortschritt wird nach Anteil umgerechnet,
        abgerundet: im Zweifel steht man etwas früher im Buch, nie später (kein Spoiler-Risiko)."""
        if edition.book_id != self.book_id:
            raise DomainError("Die Ausgabe gehört zu einem anderen Buch")
        if edition.page_count < 1:
            raise DomainError("Eine Ausgabe braucht mindestens eine Seite")
        if edition.edition_id == self.edition_id and edition.page_count == self.total_pages:
            return
        new_page = self.last_read_page * edition.page_count // self.total_pages
        self.edition_id = edition.edition_id
        self.total_pages = edition.page_count
        self.last_read_page = new_page
        # Kein BookFinished: ein schon beendetes Buch bleibt beendet, ohne das Event erneut auszulösen
        self._events.append(
            ReadingProgressChanged(
                user_id=self.user_id, book_id=self.book_id, page=new_page, total_pages=self.total_pages
            )
        )

    def percentage(self) -> int:
        return 100 * self.last_read_page // self.total_pages  # abgerundet: 100 % erst auf der letzten Seite

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
        self._events.append(
            ReadingProgressChanged(
                user_id=self.user_id, book_id=self.book_id, page=page, total_pages=self.total_pages
            )
        )
        if page == self.total_pages:
            self._events.append(BookFinished(user_id=self.user_id, book_id=self.book_id))