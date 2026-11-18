#Übung 5: In-Memory-Ersatz für Datenbank und Dateispeicher, damit die Tests ohne PostgreSQL laufen

"""In-Memory-Ersatz für Datenbank und Dateisystem (Übung 5 mit In-Memory-Repository)

Die Anwendung nutzt im Betrieb PostgreSQL. Die Tests prüfen die fachlichen Regeln
und brauchen dafür keine Datenbank.
"""

from uuid import UUID, uuid4

from app.catalog.domain.book import Book

# Kleinste gültige Bilddateien: nur die "Magic Bytes", an denen der Typ erkannt wird
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 16
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 16
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 16


class InMemoryBookRepository:
    """Ersetzt SqlBookRepository (get/save/list_overview)."""

    def __init__(self, *books: Book) -> None:
        self._books = {b.id: b for b in books}
        self.saved: list[UUID] = []

    def get(self, book_id: UUID) -> Book | None:
        return self._books.get(book_id)

    def save(self, book: Book) -> None:
        self._books[book.id] = book
        self.saved.append(book.id)

    def list_overview(self) -> list[dict]:
        return [
            {
                "id": b.id,
                "title": b.title,
                "page_count": b.page_count,
                "isbn": b.isbn,
                "authors": ["Testautor"],
                "has_cover": b.cover is not None,
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


def make_book(**overrides) -> Book:
    data = {
        "id": uuid4(),
        "title": "Der Herr der Ringe",
        "page_count": 1200,
        "author_ids": [uuid4()],
    }
    data.update(overrides)
    return Book(**data)
