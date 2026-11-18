# Übung 5: Tests für alle Endpunkte ohne echte Datenbank

"""API: Endpunkte des Catalog-Routers und Admin-Prüfung, ohne echte Datenbank."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.catalog.api import router as catalog_router
from app.main import app
from app.shared.auth import require_admin
from app.shared.database import get_session
from tests.fakes import JPEG, PNG, InMemoryBookRepository


class FakeSession:
    """Liefert für jede Abfrage ein festes Ergebnis (z. B. die Rolle eines Users)."""

    def __init__(self, scalar=None) -> None:
        self._scalar = scalar
        self.queries: list[str] = []

    def execute(self, statement, params=None):
        self.queries.append(str(statement))
        return SimpleNamespace(scalar_one_or_none=lambda: self._scalar)


# Health


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_health_db_runs_a_query():
    session = FakeSession()
    app.dependency_overrides[get_session] = lambda: session
    try:
        response = TestClient(app).get("/health/db")
    finally:
        app.dependency_overrides.clear()
    assert response.json() == {"db": "ok"}
    assert session.queries == ["SELECT 1"]


# Buchliste


def test_list_books_returns_editions_with_cover_url(api, book, edition, books, monkeypatch, cover_service):
    cover_service.set_cover(edition.id, PNG)
    monkeypatch.setattr(catalog_router, "SqlBookRepository", lambda session: books)
    app.dependency_overrides[get_session] = lambda: None

    [entry] = api.get("/books").json()

    assert entry["title"] == book.title
    assert entry["authors"] == ["Testautor"]
    [listed] = entry["editions"]
    assert listed["id"] == str(edition.id)
    assert listed["page_count"] == edition.page_count
    assert listed["format"] == "hardcover"
    assert listed["cover_url"] == f"/editions/{edition.id}/cover"


def test_list_books_without_cover(api, book, monkeypatch):
    repo = InMemoryBookRepository(book)
    monkeypatch.setattr(catalog_router, "SqlBookRepository", lambda session: repo)
    app.dependency_overrides[get_session] = lambda: None
    assert api.get("/books").json()[0]["editions"][0]["cover_url"] is None


# Cover-Endpunkte

def test_upload_and_download_cover(api, edition):
    response = api.put(f"/editions/{edition.id}/cover", files={"file": ("x.png", PNG)})
    assert response.status_code == 200
    assert response.json() == {"cover_url": f"/editions/{edition.id}/cover"}

    response = api.get(f"/editions/{edition.id}/cover")
    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-cache"


def test_content_type_of_client_is_ignored(api, edition):
    """Der Server erkennt den Typ an den Bytes, nicht an der Angabe des Browsers."""
    api.put(f"/editions/{edition.id}/cover", files={"file": ("x.png", JPEG, "image/png")})
    assert api.get(f"/editions/{edition.id}/cover").headers["content-type"] == "image/jpeg"


def test_upload_invalid_file_returns_422(api, edition):
    response = api.put(f"/editions/{edition.id}/cover", files={"file": ("x.txt", b"kein Bild")})
    assert response.status_code == 422


def test_error_response_format(api, edition):
    """Zentrale Fehlerbehandlung: gleiches Format wie FastAPIs HTTPException."""
    response = api.get(f"/editions/{uuid4()}/cover")
    assert response.json() == {"detail": "Ausgabe nicht gefunden"}
    response = api.put(f"/editions/{edition.id}/cover", files={"file": ("x.png", b"")})
    assert response.json() == {"detail": "Leere Datei"}


def test_cover_for_unknown_edition_returns_404(api):
    unknown = uuid4()
    assert api.get(f"/editions/{unknown}/cover").status_code == 404
    assert (
        api.put(f"/editions/{unknown}/cover", files={"file": ("x.png", PNG)}).status_code
        == 404
    )
    assert api.delete(f"/editions/{unknown}/cover").status_code == 404


def test_delete_cover(api, edition):
    api.put(f"/editions/{edition.id}/cover", files={"file": ("x.png", PNG)})
    assert api.delete(f"/editions/{edition.id}/cover").status_code == 204
    assert api.get(f"/editions/{edition.id}/cover").status_code == 404


def test_invalid_uuid_returns_422(api):
    assert api.get("/editions/keine-uuid/cover").status_code == 422


# Admin-Prüfung (require_admin)

def test_missing_header_returns_401():
    with pytest.raises(HTTPException) as error:
        require_admin(x_user_id=None, session=FakeSession())
    assert error.value.status_code == 401


@pytest.mark.parametrize("role", ["user", None], ids=["regular user", "unknown role"])
def test_non_admin_returns_403(role):
    with pytest.raises(HTTPException) as error:
        require_admin(x_user_id=uuid4(), session=FakeSession(scalar=role))
    assert error.value.status_code == 403


def test_admin_is_accepted():
    user_id = uuid4()
    assert (
        require_admin(x_user_id=user_id, session=FakeSession(scalar="admin")) == user_id
    )


def test_upload_without_admin_header_is_rejected(cover_service, edition):
    """Ohne Override greift die echte Prüfung: kein Header, kein Upload."""
    app.dependency_overrides[catalog_router.get_cover_service] = lambda: cover_service
    app.dependency_overrides[get_session] = lambda: FakeSession()
    try:
        response = TestClient(app).put(
            f"/editions/{edition.id}/cover", files={"file": ("x.png", PNG)}
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401
