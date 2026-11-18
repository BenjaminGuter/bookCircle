from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Import-Pfad ggf. anpassen
from app.circles.domain.circle import Membership, ReadingCircle, ReadingPlan


class SqlReadingCircleRepository:
    """Implementiert das ReadingCircleRepository-Protocol aus der Domain (Fortschritt liegt im Context Reading, nicht mehr hier)."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, circle: ReadingCircle) -> None:
        self._s.execute(
            text("""INSERT INTO circles.reading_circles
                        (id, name, owner_id, book_id, plan_start, plan_percent_per_week)
                    VALUES (:id, :name, :owner, :book, :ps, :pp)"""),
            {"id": circle.id, "name": circle.name, "owner": circle.owner_id,
             "book": circle.book_id, **self._plan(circle)},
        )
        self._sync_memberships(circle)

    def save(self, circle: ReadingCircle) -> None:
        self._s.execute(
            text("""UPDATE circles.reading_circles
                    SET name = :name, plan_start = :ps, plan_percent_per_week = :pp WHERE id = :id"""),
            {"id": circle.id, "name": circle.name, **self._plan(circle)},
        )
        self._sync_memberships(circle)

    def get(self, circle_id: UUID) -> ReadingCircle | None:
        row = self._s.execute(
            text("""SELECT id, name, owner_id, book_id, plan_start, plan_percent_per_week
                    FROM circles.reading_circles WHERE id = :id"""),
            {"id": circle_id},
        ).one_or_none()
        if row is None:
            return None
        members = self._s.execute(
            text("SELECT user_id FROM circles.memberships WHERE circle_id = :id"),
            {"id": circle_id},
        ).all()
        plan = ReadingPlan(row.plan_start, row.plan_percent_per_week) if row.plan_start else None
        return ReadingCircle(
            id=row.id, name=row.name, owner_id=row.owner_id, book_id=row.book_id, reading_plan=plan,
            memberships={m.user_id: Membership(m.user_id) for m in members},
        )

    def list_by_member(self, user_id: UUID) -> list[ReadingCircle]:
        ids = self._s.execute(
            text("SELECT circle_id FROM circles.memberships WHERE user_id = :u"), {"u": user_id}
        ).scalars().all()
        return [c for i in ids if (c := self.get(i)) is not None]

    @staticmethod
    def _plan(circle: ReadingCircle) -> dict:
        p = circle.reading_plan
        return {"ps": p.start if p else None, "pp": p.percent_per_week if p else None}

    def _sync_memberships(self, circle: ReadingCircle) -> None:
        # entfernte Mitglieder löschen, vorhandene upserten
        self._s.execute(
            text("""DELETE FROM circles.memberships
                    WHERE circle_id = :c AND user_id <> ALL(CAST(:keep AS uuid[]))"""),
            {"c": circle.id, "keep": list(circle.memberships)},
        )
        for m in circle.memberships.values():
            self._s.execute(
                text("""INSERT INTO circles.memberships (circle_id, user_id)
                        VALUES (:c, :u) ON CONFLICT DO NOTHING"""),
                {"c": circle.id, "u": m.user_id},
            )