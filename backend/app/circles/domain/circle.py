from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from app.shared.errors import DomainError


@dataclass(frozen=True)
class ReadingPlan:
    """Value Object: ab wann und wie viele Seiten pro Woche."""
    start: date
    pages_per_week: int

    def __post_init__(self) -> None:
        if self.pages_per_week < 1:
            raise DomainError("Mindestens eine Seite pro Woche")


@dataclass
class Membership:
    user_id: UUID


@dataclass
class ReadingCircle:
    id: UUID
    name: str
    owner_id: UUID
    book_id: UUID
    memberships: dict[UUID, Membership] = field(default_factory=dict)
    reading_plan: ReadingPlan | None = None

    @classmethod
    def found(cls, name: str, owner_id: UUID, book_id: UUID) -> "ReadingCircle":
        if not name.strip():
            raise DomainError("Name darf nicht leer sein")
        circle = cls(uuid4(), name, owner_id, book_id)
        circle.memberships[owner_id] = Membership(owner_id)
        return circle

    def join(self, user_id: UUID) -> None:
        if user_id in self.memberships:
            raise DomainError("Bereits Mitglied")
        self.memberships[user_id] = Membership(user_id)

    def leave(self, user_id: UUID) -> None:
        if user_id not in self.memberships:
            raise DomainError("Kein Mitglied dieses Lesekreises")
        if user_id == self.owner_id and len(self.memberships) > 1:
            raise DomainError("Der Gründer kann erst austreten, wenn er allein ist")
        del self.memberships[user_id]

    def set_reading_plan(self, plan: ReadingPlan, by_user_id: UUID) -> None:
        if by_user_id != self.owner_id:
            raise DomainError("Nur der Gründer darf den Leseplan setzen")
        self.reading_plan = plan
