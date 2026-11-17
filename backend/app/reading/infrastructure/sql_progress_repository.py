from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.reading.domain.progress import ReadingProgress


class SqlReadingProgressRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, user_id: UUID, book_id: UUID) -> ReadingProgress | None:
        row = self._s.execute(
            text("""SELECT user_id, book_id, last_read_page, total_pages
                    FROM reading.progress WHERE user_id = :u AND book_id = :b"""),
            {"u": user_id, "b": book_id},
        ).one_or_none()
        if row is None:
            return None
        return ReadingProgress(row.user_id, row.book_id, row.total_pages, row.last_read_page)

    def save(self, p: ReadingProgress) -> None:  
        self._s.execute(
            text("""INSERT INTO reading.progress (user_id, book_id, last_read_page, total_pages)
                    VALUES (:u, :b, :c, :t)
                    ON CONFLICT (user_id, book_id)
                    DO UPDATE SET last_read_page = EXCLUDED.last_read_page, updated_at = now()"""),
            {"u": p.user_id, "b": p.book_id, "c": p.last_read_page, "t": p.total_pages},
        )
