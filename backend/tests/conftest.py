# Übung 5: gemeinsame Fixtures für alle Tests

"""Gemeinsame Fixtures. Die Fakes selbst liegen in tests/fakes.py."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.catalog.api.router import get_cover_service
from app.catalog.application.covers import ManageEditionCover
from app.catalog.domain.book import Book
from app.catalog.domain.edition import Edition
from app.main import app
from app.shared.auth import require_admin
from tests.fakes import InMemoryBookRepository, InMemoryCoverStorage, make_book


@pytest.fixture
def book() -> Book:
    return make_book()

@pytest.fixture
def edition(book) -> Edition:
    """Die (einzige) Ausgabe des Test-Buchs. Cover hängen an der Ausgabe."""
    return book.editions[0]


@pytest.fixture
def books(book) -> InMemoryBookRepository:
    return InMemoryBookRepository(book)


@pytest.fixture
def storage() -> InMemoryCoverStorage:
    return InMemoryCoverStorage()


@pytest.fixture
def cover_service(books, storage) -> ManageEditionCover:
    return ManageEditionCover(books, storage)


@pytest.fixture
def api(cover_service):
    """TestClient, bei dem Datenbank und Login durch Fakes ersetzt sind."""
    app.dependency_overrides[get_cover_service] = lambda: cover_service
    app.dependency_overrides[require_admin] = lambda: uuid4()
    yield TestClient(app)
    app.dependency_overrides.clear()
