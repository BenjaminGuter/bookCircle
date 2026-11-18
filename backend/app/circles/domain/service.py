from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.circles.domain.circle import ReadingCircle


@dataclass(frozen=True)
class ProgressSnapshot:
    """Lesestand eines Mitglieds, aus dem Context Reading: Seite und Gesamtseiten SEINER Ausgabe."""
    user_id: UUID
    page: int
    total_pages: int


class CircleProgressService:
    """Domain Service: Auswertung über mehrere Mitglieder mit unterschiedlichen Ausgaben."""

    def group_progress(self, circle: ReadingCircle, progresses: Iterable[ProgressSnapshot]) -> dict[UUID, int]:
        """Prozent pro Mitglied (abgerundet). Wer noch nichts gelesen hat, steht bei 0."""
        by_user = {p.user_id: p for p in progresses}
        return {
            uid: (100 * by_user[uid].page // by_user[uid].total_pages) if uid in by_user else 0
            for uid in circle.memberships
        }

    def members_behind(
        self, circle: ReadingCircle, progresses: Iterable[ProgressSnapshot], today: date
    ) -> list[UUID]:
        """Mitglieder unter dem Soll-Stand des Leseplans. Exakter Ganzzahl-Vergleich ohne Rundung:
        page / total_pages < target / 100  <=>  page * 100 < target * total_pages."""
        if circle.reading_plan is None:
            return []
        target = circle.reading_plan.target_percent(today)
        by_user = {p.user_id: p for p in progresses}
        behind = []
        for uid in circle.memberships:
            p = by_user.get(uid)
            page, total = (p.page, p.total_pages) if p else (0, 1)
            if page * 100 < target * total:
                behind.append(uid)
        return behind