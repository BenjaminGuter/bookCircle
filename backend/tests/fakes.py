#Übung 5: In-Memory-Ersatz für Datenbank und Dateispeicher, damit die Tests ohne PostgreSQL laufen

"""In-Memory-Ersatz für Datenbank und Dateisystem (Übung 5 mit In-Memory-Repository)

Die Anwendung nutzt im Betrieb PostgreSQL. Die Tests prüfen die fachlichen Regeln
und brauchen dafür keine Datenbank.
"""

from uuid import UUID, uuid4

from app.catalog.domain.book import Book
from app.catalog.domain.edition import Edition, EditionFormat
from app.circles.domain.circle import ReadingCircle
from app.reading.domain.progress import EditionRef, ReadingProgress

# Kleinste gültige Bilddateien: nur die "Magic Bytes", an denen der Typ erkannt wird
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 16
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 16
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 16


class InMemoryBookRepository:
    """Ersetzt SqlBookRepository (get/get_by_edition/save/list_overview)."""

    def __init__(self, *books: Book) -> None:
        self._books = {b.id: b for b in books}
        self.saved: list[UUID] = []

    def get(self, book_id: UUID) -> Book | None:
        return self._books.get(book_id)

    def get_by_edition(self, edition_id: UUID) -> Book | None:
        return next((b for b in self._books.values() if b.get_edition(edition_id)), None)

    def save(self, book: Book) -> None:
        self._books[book.id] = book
        self.saved.append(book.id)

    def list_overview(self) -> list[dict]:
        return [
            {
                "id": b.id,
                "title": b.title,
                "authors": ["Testautor"],
                "editions": [
                    {
                        "id": e.id,
                        "format": e.format.value,
                        "page_count": e.page_count,
                        "isbn": e.isbn,
                        "publisher": e.publisher,
                        "published_year": e.published_year,
                        "has_cover": e.cover is not None,
                    }
                    for e in b.editions
                ],
            }
            for b in sorted(self._books.values(), key=lambda b: b.title.lower())
        ]


class InMemoryCoverStorage:
    """Ersetzt LocalCoverStorage (Dateisystem)."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, file_name: str, data: bytes) -> None:
        self.files[file_name] = data

    def load(self, file_name: str) -> bytes | None:
        return self.files.get(file_name)

    def delete(self, file_name: str) -> None:
        self.files.pop(file_name, None)

class InMemoryCircleRepository:
    """Ersetzt SqlCircleRepository."""

    def __init__(self, *circles: ReadingCircle) -> None:
        self._circles = {c.id: c for c in circles}

    def get(self, circle_id: UUID) -> ReadingCircle | None:
        return self._circles.get(circle_id)

    def save(self, circle: ReadingCircle) -> None:
        self._circles[circle.id] = circle


class InMemoryEditionLookup:
    """Ersetzt SqlEditionLookup: liefert Werk und Seitenzahl einer Ausgabe."""

    def __init__(self, *editions: EditionRef) -> None:
        self._editions = {e.edition_id: e for e in editions}

    def find(self, edition_id: UUID) -> EditionRef | None:
        return self._editions.get(edition_id)


class InMemoryProgressRepository:
    """Ersetzt SqlProgressRepository."""

    def __init__(self, *progresses: ReadingProgress) -> None:
        self._progress = {(p.user_id, p.book_id): p for p in progresses}

    def get(self, user_id: UUID, book_id: UUID) -> ReadingProgress | None:
        return self._progress.get((user_id, book_id))

    def save(self, progress: ReadingProgress) -> None:
        self._progress[(progress.user_id, progress.book_id)] = progress


def make_edition(**overrides) -> Edition:
    data = {"id": uuid4(), "page_count": 1200, "format": EditionFormat.HARDCOVER}
    data.update(overrides)
    return Edition(**data)


def make_book(**overrides) -> Book:
    data = {
        "id": uuid4(),
        "title": "Der Herr der Ringe",
        "author_ids": [uuid4()],
        "editions": [make_edition()],
    }
    data.update(overrides)
    return Book(**data)
