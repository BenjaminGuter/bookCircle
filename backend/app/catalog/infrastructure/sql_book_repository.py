from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.catalog.domain.book import Book
from app.catalog.domain.cover import CoverImage
from app.catalog.domain.edition import Edition, EditionFormat


class SqlBookRepository:
    """get/get_by_edition/add/save. search(query, filters) kommt später dazu."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, book_id: UUID) -> Book | None:
        row = self._s.execute(
            text("SELECT id, title FROM catalog.books WHERE id = :id"), {"id": book_id}
        ).one_or_none()
        return self._build(row)

    def get_by_edition(self, edition_id: UUID) -> Book | None:
        row = self._s.execute(
            text("""SELECT b.id, b.title FROM catalog.books b
                    JOIN catalog.editions e ON e.book_id = b.id WHERE e.id = :id"""),
            {"id": edition_id},
        ).one_or_none()
        return self._build(row)

    def _build(self, row) -> Book | None:
        if row is None:
            return None
        authors = self._s.execute(
            text("SELECT author_id FROM catalog.book_authors WHERE book_id = :id"), {"id": row.id}
        ).scalars().all()
        editions = self._s.execute(
            text("""SELECT id, page_count, format, isbn, publisher, published_year,
                           cover_file, cover_content_type
                    FROM catalog.editions WHERE book_id = :id ORDER BY page_count, id"""),
            {"id": row.id},
        ).all()
        return Book(
            row.id, row.title, list(authors),
            [
                Edition(
                    e.id, e.page_count, EditionFormat(e.format), e.isbn, e.publisher, e.published_year,
                    CoverImage(e.cover_file, e.cover_content_type) if e.cover_file else None,
                )
                for e in editions
            ],
        )

    def list_overview(self) -> list[dict]:
        """Read-Seite für die Buchliste (Lesemodell, kein Aggregate): Werke mit Autorennamen und Ausgaben."""
        rows = self._s.execute(
            text("""SELECT b.id, b.title,
                      COALESCE((SELECT array_agg(a.name ORDER BY a.name)
                                FROM catalog.book_authors ba JOIN catalog.authors a ON a.id = ba.author_id
                                WHERE ba.book_id = b.id), '{}') AS authors,
                      COALESCE((SELECT json_agg(json_build_object(
                                    'id', e.id, 'format', e.format, 'page_count', e.page_count,
                                    'isbn', e.isbn, 'publisher', e.publisher,
                                    'published_year', e.published_year,
                                    'has_cover', e.cover_file IS NOT NULL)
                                    ORDER BY e.page_count, e.id)
                                FROM catalog.editions e WHERE e.book_id = b.id), '[]'::json) AS editions
                    FROM catalog.books b
                    ORDER BY lower(b.title)""")
        ).all()
        return [
            {"id": r.id, "title": r.title, "authors": list(r.authors), "editions": r.editions}
            for r in rows
        ]

    def add(self, book: Book) -> None:
        self._s.execute(
            text("INSERT INTO catalog.books (id, title) VALUES (:id, :title)"),
            {"id": book.id, "title": book.title},
        )
        self._sync(book)

    def save(self, book: Book) -> None:
        self._s.execute(
            text("UPDATE catalog.books SET title = :title WHERE id = :id"),
            {"id": book.id, "title": book.title},
        )
        self._sync(book)

    def _sync(self, book: Book) -> None:
        # Autoren
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
        # Ausgaben (Komposition: gehören dem Book)
        self._s.execute(
            text("""DELETE FROM catalog.editions
                    WHERE book_id = :b AND id <> ALL(CAST(:keep AS uuid[]))"""),
            {"b": book.id, "keep": [e.id for e in book.editions]},
        )
        for e in book.editions:
            self._s.execute(
                text("""INSERT INTO catalog.editions
                            (id, book_id, isbn, page_count, format, publisher, published_year,
                             cover_file, cover_content_type)
                        VALUES (:id, :b, :isbn, :pages, :fmt, :pub, :year, :cf, :ct)
                        ON CONFLICT (id) DO UPDATE SET
                            isbn = EXCLUDED.isbn, page_count = EXCLUDED.page_count,
                            format = EXCLUDED.format, publisher = EXCLUDED.publisher,
                            published_year = EXCLUDED.published_year,
                            cover_file = EXCLUDED.cover_file,
                            cover_content_type = EXCLUDED.cover_content_type"""),
                {
                    "id": e.id, "b": book.id, "isbn": e.isbn, "pages": e.page_count,
                    "fmt": e.format.value, "pub": e.publisher, "year": e.published_year,
                    "cf": e.cover.file_name if e.cover else None,
                    "ct": e.cover.content_type if e.cover else None,
                },
            )