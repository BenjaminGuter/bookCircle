from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.reading.domain.progress import EditionRef


class SqlEditionLookup:
    """Liefert dem Context Reading/Circles die Eckdaten einer Ausgabe (Werk und Seitenzahl)."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def find(self, edition_id: UUID) -> EditionRef | None:
        row = self._s.execute(
            text("SELECT id, book_id, page_count FROM catalog.editions WHERE id = :id"),
            {"id": edition_id},
        ).one_or_none()
        return EditionRef(row.id, row.book_id, row.page_count) if row else None