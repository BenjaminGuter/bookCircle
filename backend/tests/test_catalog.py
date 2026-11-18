# Übung 5: Tests für Catalog

"""Catalog: Buch, Cover-Value-Object, Cover-Use-Case und Dateispeicher"""

from uuid import uuid4

import pytest

from app.catalog.application.covers import detect_image_type
from app.catalog.domain.cover import MAX_COVER_BYTES, CoverImage
from app.catalog.infrastructure.local_cover_storage import LocalCoverStorage
from app.shared.errors import DomainError, NotFoundError
from tests.fakes import JPEG, PNG, WEBP, make_book

# --- Book -----------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [{"title": ""}, {"title": "   "}, {"page_count": 0}, {"author_ids": []}],
)
def test_invalid_books_are_rejected(overrides):
    with pytest.raises(DomainError):
        make_book(**overrides)


def test_set_cover_returns_previous_cover():
    book = make_book()
    first = CoverImage("a.jpg", "image/jpeg")
    second = CoverImage("b.png", "image/png")
    assert book.set_cover(first) is None
    assert book.set_cover(second) == first
    assert book.remove_cover() == second
    assert book.remove_cover() is None


def test_cover_only_allows_images():
    with pytest.raises(DomainError):
        CoverImage("datei.pdf", "application/pdf")


# Bildtyp-Erkennung

@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (JPEG, "image/jpeg"),
        (PNG, "image/png"),
        (WEBP, "image/webp"),
        (b"GIF89a" + b"0" * 10, None),
        (b"RIFF\x00\x00\x00\x00WAVE", None),  # RIFF, aber kein WebP
        (b"%PDF-1.7", None),
        (b"", None),
    ],
)
def test_detect_image_type(data, expected):
    assert detect_image_type(data) == expected


# Use Case ManageBookCover


def test_set_cover_stores_file_and_updates_book(cover_service, book, books, storage):
    cover = cover_service.set_cover(book.id, PNG)
    assert cover.content_type == "image/png"
    assert cover.file_name.startswith(str(book.id))
    assert cover.file_name.endswith(".png")
    assert storage.files[cover.file_name] == PNG
    assert books.get(book.id).cover == cover


def test_replacing_cover_deletes_old_file(cover_service, book, storage):
    old = cover_service.set_cover(book.id, JPEG)
    new = cover_service.set_cover(book.id, PNG)
    assert old.file_name not in storage.files
    assert list(storage.files) == [new.file_name]


@pytest.mark.parametrize(
    "data",
    [b"", b"keinBild" * 10, b"\xff\xd8\xff" + b"0" * MAX_COVER_BYTES],
    ids=["empty", "not an image", "too large"],
)
def test_invalid_upload_changes_nothing(cover_service, book, books, storage, data):
    with pytest.raises(DomainError):
        cover_service.set_cover(book.id, data)
    assert storage.files == {}
    assert books.saved == []


def test_cover_exactly_at_size_limit_is_accepted(cover_service, book):
    data = JPEG[:4] + b"0" * (MAX_COVER_BYTES - 4)
    assert cover_service.set_cover(book.id, data).content_type == "image/jpeg"


def test_unknown_book(cover_service, storage):
    with pytest.raises(NotFoundError):
        cover_service.set_cover(uuid4(), PNG)
    with pytest.raises(NotFoundError):
        cover_service.remove_cover(uuid4())
    with pytest.raises(NotFoundError):
        cover_service.get_cover(uuid4())
    assert storage.files == {}


def test_get_cover_returns_data_and_type(cover_service, book):
    cover_service.set_cover(book.id, WEBP)
    assert cover_service.get_cover(book.id) == (WEBP, "image/webp")


def test_get_cover_without_cover(cover_service, book):
    with pytest.raises(NotFoundError):
        cover_service.get_cover(book.id)


def test_get_cover_when_file_is_missing(cover_service, book, storage):
    cover = cover_service.set_cover(book.id, PNG)
    storage.delete(cover.file_name)  # Datei z. B. manuell gelöscht
    with pytest.raises(NotFoundError):
        cover_service.get_cover(book.id)


def test_remove_cover(cover_service, book, books, storage):
    cover_service.set_cover(book.id, PNG)
    cover_service.remove_cover(book.id)
    assert storage.files == {}
    assert books.get(book.id).cover is None


def test_remove_cover_without_cover_does_nothing(cover_service, book, books):
    cover_service.remove_cover(book.id)
    assert books.saved == []


# LocalCoverStorage (Dateisystem, mit temporärem Ordner)


def test_local_storage_roundtrip(tmp_path):
    storage = LocalCoverStorage(str(tmp_path / "covers"))
    storage.save("bild.png", PNG)
    assert storage.load("bild.png") == PNG
    assert not list((tmp_path / "covers").glob("*.tmp"))  # keine Reste
    storage.delete("bild.png")
    assert storage.load("bild.png") is None
    storage.delete("bild.png")  # zweites Löschen ist kein Fehler


@pytest.mark.parametrize("name", ["../geheim.txt", "sub/bild.png", "/etc/passwd"])
def test_local_storage_rejects_paths(tmp_path, name):
    """Schutz gegen Path Traversal: nur reine Dateinamen sind erlaubt."""
    storage = LocalCoverStorage(str(tmp_path))
    with pytest.raises(ValueError, match="Ungültiger Dateiname"):
        storage.save(name, PNG)
    with pytest.raises(ValueError, match="Ungültiger Dateiname"):
        storage.load(name)
