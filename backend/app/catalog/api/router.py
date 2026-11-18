from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.catalog.application.covers import ManageEditionCover
from app.catalog.domain.cover import MAX_COVER_BYTES
from app.catalog.infrastructure.local_cover_storage import LocalCoverStorage
from app.catalog.infrastructure.sql_book_repository import SqlBookRepository
from app.shared.auth import require_admin
from app.shared.database import get_session

# Fachliche Fehler (NotFoundError -> 404, DomainError -> 422) werden zentral
# in app/shared/error_handlers.py in HTTP-Antworten übersetzt.
router = APIRouter(tags=["catalog"])


def get_cover_service(session: Session = Depends(get_session)) -> ManageEditionCover:
    return ManageEditionCover(SqlBookRepository(session), LocalCoverStorage())


@router.get("/books")
def list_books(session: Session = Depends(get_session)):
    """Werke mit ihren Ausgaben. cover_url ist null, wenn die Ausgabe kein Cover hat."""
    return [
        {
            "id": b["id"], "title": b["title"], "authors": b["authors"],
            "editions": [
                {
                    "id": e["id"], "format": e["format"], "page_count": e["page_count"],
                    "isbn": e["isbn"], "publisher": e["publisher"], "published_year": e["published_year"],
                    "cover_url": f"/editions/{e['id']}/cover" if e["has_cover"] else None,
                }
                for e in b["editions"]
            ],
        }
        for b in SqlBookRepository(session).list_overview()
    ]


@router.get("/editions/{edition_id}/cover")
def get_cover(edition_id: UUID, service: ManageEditionCover = Depends(get_cover_service)):
    data, content_type = service.get_cover(edition_id)
    # no-cache: Browser fragen nach, damit ein geändertes Cover sofort sichtbar ist
    return Response(content=data, media_type=content_type, headers={"Cache-Control": "no-cache"})


@router.put("/editions/{edition_id}/cover")
def put_cover(
    edition_id: UUID,
    file: UploadFile = File(...),
    _admin: UUID = Depends(require_admin),
    service: ManageEditionCover = Depends(get_cover_service),
):
    data = file.file.read(MAX_COVER_BYTES + 1)  # nie mehr als Limit + 1 Byte einlesen
    service.set_cover(edition_id, data)
    return {"cover_url": f"/editions/{edition_id}/cover"}


@router.delete("/editions/{edition_id}/cover", status_code=204)
def delete_cover(
    edition_id: UUID,
    _admin: UUID = Depends(require_admin),
    service: ManageEditionCover = Depends(get_cover_service),
):
    service.remove_cover(edition_id)
