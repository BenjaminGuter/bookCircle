"""NUR FÜR DIE ENTWICKLUNG: vertraut dem Header X-User-Id und prüft nur die Rolle in der DB.
Jeder kann den Header setzen -> vor dem echten Einsatz durch Login/JWT ersetzen
(die Signatur `require_admin` kann gleich bleiben)."""
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.shared.database import get_session


def require_admin(
    x_user_id: UUID | None = Header(default=None),
    session: Session = Depends(get_session),
) -> UUID:
    if x_user_id is None:
        raise HTTPException(401, "Header X-User-Id fehlt")
    role = session.execute(
        text("SELECT role FROM identity.users WHERE id = :id"), {"id": x_user_id}
    ).scalar_one_or_none()
    if role != "admin":
        raise HTTPException(403, "Nur für Admins")
    return x_user_id
