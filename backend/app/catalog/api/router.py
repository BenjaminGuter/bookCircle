from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.catalog.application.covers import ManageBookCover
from app.catalog.domain.cover import MAX_COVER_BYTES
from app.catalog.infrastructure.local_cover_storage import LocalCoverStorage
from app.catalog.infrastructure.sql_book_repository import SqlBookRepository
from app.shared.auth import require_admin
from app.shared.database import get_session
from app.shared.errors import DomainError, NotFoundError

router = APIRouter(prefix="/books", tags=["catalog"])


def get_cover_service(session: Session = Depends(get_session)) -> ManageBookCover:
    return ManageBookCover(SqlBookRepository(session), LocalCoverStorage())


@router.get("")
def list_books(session: Session = Depends(get_session)):
    """Buchliste fürs Frontend. cover_url ist null, wenn kein Cover vorhanden ist."""
    books = SqlBookRepository(session).list_overview()
    return [
        {
            "id": b["id"], "title": b["title"], "page_count": b["page_count"],
            "isbn": b["isbn"], "authors": b["authors"],
            "cover_url": f"/books/{b['id']}/cover" if b["has_cover"] else None,
        }
        for b in books
    ]


@router.get("/{book_id}/cover")
def get_cover(book_id: UUID, service: ManageBookCover = Depends(get_cover_service)):
    try:
        data, content_type = service.get_cover(book_id)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    # no-cache: Browser fragen nach, damit ein geändertes Cover sofort sichtbar ist
    return Response(content=data, media_type=content_type, headers={"Cache-Control": "no-cache"})


@router.put("/{book_id}/cover")
def put_cover(
    book_id: UUID,
    file: UploadFile = File(...),
    _admin: UUID = Depends(require_admin),
    service: ManageBookCover = Depends(get_cover_service),
):
    data = file.file.read(MAX_COVER_BYTES + 1)  # nie mehr als Limit + 1 Byte einlesen
    try:
        service.set_cover(book_id, data)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except DomainError as e:
        raise HTTPException(422, str(e))
    return {"cover_url": f"/books/{book_id}/cover"}


@router.delete("/{book_id}/cover", status_code=204)
def delete_cover(
    book_id: UUID,
    _admin: UUID = Depends(require_admin),
    service: ManageBookCover = Depends(get_cover_service),
):
    try:
        service.remove_cover(book_id)
    except NotFoundError as e:
        raise HTTPException(404, str(e))