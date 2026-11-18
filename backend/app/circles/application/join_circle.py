from typing import Protocol
from uuid import UUID

from app.circles.domain.circle import ReadingCircle
# Beitritt verbindet zwei Contexts (Circles und Reading), deshalb importiert dieser Use Case beide Domains.
from app.reading.domain.progress import EditionRef, ReadingProgress
from app.shared.errors import DomainError, NotFoundError
from app.shared.events import DomainEvent


class CircleRepository(Protocol):
    def get(self, circle_id: UUID) -> ReadingCircle | None: ...
    def save(self, circle: ReadingCircle) -> None: ...


class EditionLookup(Protocol):
    def find(self, edition_id: UUID) -> EditionRef | None: ...


class ProgressRepository(Protocol):
    def get(self, user_id: UUID, book_id: UUID) -> ReadingProgress | None: ...
    def save(self, progress: ReadingProgress) -> None: ...


class JoinCircle:
    """Einem Lesekreis mit der eigenen Ausgabe beitreten."""

    def __init__(self, circles: CircleRepository, editions: EditionLookup, progress: ProgressRepository) -> None:
        self._circles = circles
        self._editions = editions
        self._progress = progress

    def execute(self, circle_id: UUID, user_id: UUID, edition_id: UUID) -> list[DomainEvent]:
        circle = self._circles.get(circle_id)
        if circle is None:
            raise NotFoundError("Lesekreis nicht gefunden")
        edition = self._editions.find(edition_id)
        if edition is None:
            raise NotFoundError("Ausgabe nicht gefunden")
        if edition.book_id != circle.book_id:
            raise DomainError("Die Ausgabe gehört nicht zum Buch dieses Lesekreises")

        circle.join(user_id)  # wirft, wenn schon Mitglied

        progress = self._progress.get(user_id, circle.book_id)
        if progress is None:
            progress = ReadingProgress.start(user_id, edition)
        else:
            progress.switch_edition(edition)  # wer das Buch schon liest, behält seinen Anteil

        self._circles.save(circle)
        self._progress.save(progress)
        return progress.pull_events()