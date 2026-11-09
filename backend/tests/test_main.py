from fastapi.testclient import TestClient

from app.main import app
from app.spoiler import is_visible

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404():
    response = client.get("/gibt-es-nicht")
    assert response.status_code == 404


def test_spoiler_visibility():
    assert is_visible(post_chapter=3, reader_chapter=5) is True
    assert is_visible(post_chapter=3, reader_chapter=3) is True
    assert is_visible(post_chapter=7, reader_chapter=2) is False