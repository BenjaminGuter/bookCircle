from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.catalog.domain.book import Book
from app.catalog.domain.cover import CoverImage


class SqlBookRepository:
    """get/add/save. search(query, filters) kommt später dazu."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, book_id: UUID) -> Book | None:
        row = self._s.execute(
            text("""SELECT id, title, page_count, isbn, cover_file, cover_content_type
                    FROM catalog.books WHERE id = :id"""),
            {"id": book_id},
        ).one_or_none()
        if row is None:
            return None
        authors = self._s.execute(
            text("SELECT author_id FROM catalog.book_authors WHERE book_id = :id"), {"id": book_id}
        ).scalars().all()
        cover = CoverImage(row.cover_file, row.cover_content_type) if row.cover_file else None
        return Book(row.id, row.title, row.page_count, list(authors), row.isbn, cover)

    def list_overview(self) -> list[dict]:
        """Read-Seite für die Buchliste (Lesemodell, kein Aggregate): Autorennamen inklusive."""
        rows = self._s.execute(
            text("""SELECT b.id, b.title, b.page_count, b.isbn,
                           (b.cover_file IS NOT NULL) AS has_cover,
                           COALESCE(array_agg(a.name ORDER BY a.name) FILTER (WHERE a.id IS NOT NULL),
                                    '{}') AS authors
                    FROM catalog.books b
                    LEFT JOIN catalog.book_authors ba ON ba.book_id = b.id
                    LEFT JOIN catalog.authors a ON a.id = ba.author_id
                    GROUP BY b.id
                    ORDER BY lower(b.title)""")
        ).all()
        return [
            {"id": r.id, "title": r.title, "page_count": r.page_count, "isbn": r.isbn,
             "authors": list(r.authors), "has_cover": r.has_cover}
            for r in rows
        ]

    def add(self, book: Book) -> None:
        self._s.execute(
            text("""INSERT INTO catalog.books (id, title, page_count, isbn, cover_file, cover_content_type)
                    VALUES (:id, :title, :pages, :isbn, :cf, :ct)"""),
            self._params(book),
        )
        self._sync_authors(book)

    def save(self, book: Book) -> None:
        self._s.execute(
            text("""UPDATE catalog.books SET title = :title, page_count = :pages, isbn = :isbn,
                           cover_file = :cf, cover_content_type = :ct
                    WHERE id = :id"""),
            self._params(book),
        )
        self._sync_authors(book)

    @staticmethod
    def _params(book: Book) -> dict:
        return {
            "id": book.id, "title": book.title, "pages": book.page_count, "isbn": book.isbn,
            "cf": book.cover.file_name if book.cover else None,
            "ct": book.cover.content_type if book.cover else None,
        }

    def _sync_authors(self, book: Book) -> None:
        self._s.execute(
            text("""DELETE FROM catalog.book_authors
                    WHERE book_id = :b AND author_id <> ALL(CAST(:keep AS uuid[]))"""),
            {"b": book.id, "keep": list(book.author_ids)},
        )
        for author_id in book.author_ids:
            self._s.execute(
                text("""INSERT INTO catalog.book_authors (book_id, author_id)
                        VALUES (:b, :a) ON CONFLICT DO NOTHING"""),
                {"b": book.id, "a": author_id},
            )