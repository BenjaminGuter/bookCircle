# Übung 5: Tests für Catalog

"""Catalog: Buch, Cover-Value-Object, Cover-Use-Case und Dateispeicher"""

from uuid import uuid4

import pytest

from app.catalog.application.covers import ManageEditionCover, detect_image_type
from app.catalog.domain.cover import MAX_COVER_BYTES, CoverImage
from app.catalog.domain.edition import EditionFormat
from app.catalog.infrastructure.local_cover_storage import LocalCoverStorage
from app.shared.errors import DomainError, NotFoundError
from tests.fakes import JPEG, PNG, WEBP, InMemoryBookRepository, make_book, make_edition

# Book (Werk) und Edition (Ausgabe)


@pytest.mark.parametrize(
    "overrides",
    [{"title": ""}, {"title": "   "}, {"author_ids": []}, {"editions": []}],
    ids=["empty title", "blank title", "no author", "no edition"],
)

def test_invalid_books_are_rejected(overrides):
    with pytest.raises(DomainError):
        make_book(**overrides)

def test_edition_ids_must_be_unique():
    edition = make_edition()
    with pytest.raises(DomainError):
        make_book(editions=[edition, edition])


@pytest.mark.parametrize(
    "overrides",
    [{"page_count": 0}, {"isbn": "123"}, {"isbn": "978-3-16-148410-0"}, {"published_year": 999}],
    ids=["no pages", "isbn too short", "isbn with dashes", "year too early"],
)
def test_invalid_editions_are_rejected(overrides):
    with pytest.raises(DomainError):
        make_edition(**overrides)


@pytest.mark.parametrize("isbn", ["3161484100", "9783161484100"], ids=["isbn-10", "isbn-13"])
def test_valid_isbn(isbn):
    assert make_edition(isbn=isbn).isbn == isbn


def test_add_and_get_edition():
    book = make_book()
    ebook = make_edition(format=EditionFormat.EBOOK, page_count=900)
    book.add_edition(ebook)
    assert book.get_edition(ebook.id) == ebook
    assert book.get_edition(uuid4()) is None


def test_add_edition_twice_is_rejected():
    book = make_book()
    with pytest.raises(DomainError):
        book.add_edition(book.editions[0])


def test_isbn_must_be_unique_within_book():
    book = make_book(editions=[make_edition(isbn="3161484100")])
    with pytest.raises(DomainError):
        book.add_edition(make_edition(isbn="3161484100"))


def test_set_cover_returns_previous_cover():
    edition = make_edition()
    first = CoverImage("a.jpg", "image/jpeg")
    second = CoverImage("b.png", "image/png")
    assert edition.set_cover(first) is None
    assert edition.set_cover(second) == first
    assert edition.remove_cover() == second
    assert edition.remove_cover() is None


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


# Use Case ManageEditionCover


def test_set_cover_stores_file_and_updates_book(cover_service, book, edition, books, storage):
    cover = cover_service.set_cover(edition.id, PNG)
    assert cover.content_type == "image/png"
    assert cover.file_name.startswith(str(edition.id))
    assert cover.file_name.endswith(".png")
    assert storage.files[cover.file_name] == PNG
    assert books.get(book.id).get_edition(edition.id).cover == cover


def test_replacing_cover_deletes_old_file(cover_service, edition, storage):
    old = cover_service.set_cover(edition.id, JPEG)
    new = cover_service.set_cover(edition.id, PNG)
    assert old.file_name not in storage.files
    assert list(storage.files) == [new.file_name]


@pytest.mark.parametrize(
    "data",
    [b"", b"keinBild" * 10, b"\xff\xd8\xff" + b"0" * MAX_COVER_BYTES],
    ids=["empty", "not an image", "too large"],
)
def test_invalid_upload_changes_nothing(cover_service, edition, books, storage, data):
    with pytest.raises(DomainError):
        cover_service.set_cover(edition.id, data)
    assert storage.files == {}
    assert books.saved == []


def test_cover_exactly_at_size_limit_is_accepted(cover_service, edition):
    data = JPEG[:4] + b"0" * (MAX_COVER_BYTES - 4)
    assert cover_service.set_cover(edition.id, data).content_type == "image/jpeg"


def test_unknown_edition(cover_service, storage):
    with pytest.raises(NotFoundError):
        cover_service.set_cover(uuid4(), PNG)
    with pytest.raises(NotFoundError):
        cover_service.remove_cover(uuid4())
    with pytest.raises(NotFoundError):
        cover_service.get_cover(uuid4())
    assert storage.files == {}


def test_get_cover_returns_data_and_type(cover_service, edition):
    cover_service.set_cover(edition.id, WEBP)
    assert cover_service.get_cover(edition.id) == (WEBP, "image/webp")


def test_get_cover_without_cover(cover_service, edition):
    with pytest.raises(NotFoundError):
        cover_service.get_cover(edition.id)


def test_get_cover_when_file_is_missing(cover_service, edition, storage):
    cover = cover_service.set_cover(edition.id, PNG)
    storage.delete(cover.file_name)  # Datei z. B. manuell gelöscht
    with pytest.raises(NotFoundError):
        cover_service.get_cover(edition.id)


def test_remove_cover(cover_service, edition, books, storage):
    cover_service.set_cover(edition.id, PNG)
    cover_service.remove_cover(edition.id)
    assert storage.files == {}
    assert books.get_by_edition(edition.id).get_edition(edition.id).cover is None


def test_cover_belongs_to_one_edition_only(storage):
    """Zwei Ausgaben desselben Werks haben getrennte Cover."""
    hardcover, ebook = make_edition(), make_edition(format=EditionFormat.EBOOK)
    book = make_book(editions=[hardcover, ebook])
    service = ManageEditionCover(InMemoryBookRepository(book), storage)
    service.set_cover(hardcover.id, PNG)
    assert hardcover.cover is not None
    assert ebook.cover is None
    with pytest.raises(NotFoundError):
        service.get_cover(ebook.id)


def test_remove_cover_without_cover_does_nothing(cover_service, edition, books):
    cover_service.remove_cover(edition.id)
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
