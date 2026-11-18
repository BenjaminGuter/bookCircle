from typing import Protocol
from uuid import UUID, uuid4

from app.catalog.domain.book import Book
from app.catalog.domain.cover import ALLOWED_TYPES, MAX_COVER_BYTES, CoverImage, CoverStorage
from app.shared.errors import DomainError, NotFoundError


class BookRepository(Protocol):
    def get_by_edition(self, edition_id: UUID) -> Book | None: ...
    def save(self, book: Book) -> None: ...


def detect_image_type(data: bytes) -> str | None:
    """Typ anhand der ersten Bytes bestimmen. Dem vom Client gesendeten Content-Type wird nicht getraut."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


class ManageEditionCover:
    """Cover einer Ausgabe hinzufügen/ändern/löschen/laden. Der Zugriff läuft über das Aggregate Book."""

    def __init__(self, books: BookRepository, storage: CoverStorage) -> None:
        self._books = books
        self._storage = storage

    def _load(self, edition_id: UUID):
        book = self._books.get_by_edition(edition_id)
        edition = book.get_edition(edition_id) if book else None
        if book is None or edition is None:
            raise NotFoundError("Ausgabe nicht gefunden")
        return book, edition

    def set_cover(self, edition_id: UUID, data: bytes) -> CoverImage:
        """Hinzufügen und Ändern sind dieselbe Operation."""
        if not data:
            raise DomainError("Leere Datei")
        if len(data) > MAX_COVER_BYTES:
            raise DomainError("Bild zu groß (max. 2 MB)")
        content_type = detect_image_type(data)
        if content_type is None:
            raise DomainError("Nur JPEG, PNG oder WebP erlaubt")
        book, edition = self._load(edition_id)
        # Dateiname wird serverseitig erzeugt, nie aus der Eingabe übernommen
        cover = CoverImage(f"{edition_id}-{uuid4().hex}{ALLOWED_TYPES[content_type]}", content_type)
        self._storage.save(cover.file_name, data)
        old = edition.set_cover(cover)
        self._books.save(book)
        if old is not None:
            self._storage.delete(old.file_name)
        return cover

    def remove_cover(self, edition_id: UUID) -> None:
        book, edition = self._load(edition_id)
        old = edition.remove_cover()
        if old is None:
            return
        self._books.save(book)
        self._storage.delete(old.file_name)

    def get_cover(self, edition_id: UUID) -> tuple[bytes, str]:
        _, edition = self._load(edition_id)
        if edition.cover is None:
            raise NotFoundError("Kein Cover vorhanden")
        data = self._storage.load(edition.cover.file_name)
        if data is None:
            raise NotFoundError("Cover-Datei fehlt")
        return data, edition.cover.content_type