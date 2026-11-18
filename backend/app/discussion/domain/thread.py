from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.shared.book_position import MAX_POSITION
from app.shared.errors import DomainError


def is_unlocked(thread_position: int, viewer_position: int) -> bool:
    """Die einzige Stelle der Spoiler-Regel (Positionen in Promille)."""
    return viewer_position >= thread_position


@dataclass
class Post:
    id: UUID
    author_id: UUID
    text: str
    created_at: datetime


@dataclass
class DiscussionThread:
    id: UUID
    circle_id: UUID
    book_id: UUID
    position: int
    title: str
    posts: list[Post] = field(default_factory=list)

    @classmethod
    def open(cls, circle_id: UUID, book_id: UUID, position: int, title: str, author_position: int):
        if not 1 <= position <= MAX_POSITION:
            raise DomainError(f"Position muss zwischen 1 und {MAX_POSITION} liegen")
        if not is_unlocked(position, author_position):
            raise DomainError("Thread kann nur an einer bereits gelesenen Stelle eröffnet werden")
        # Leere Titel ablehnen (FEHLERBEHEBUNG)
        # Grund: Ein Thread ohne Titel war möglich. Gefunden durch test_discussion.py (Übung 5)
        if not title.strip():
            raise DomainError("Titel darf nicht leer sein")
        return cls(uuid4(), circle_id, book_id, position, title.strip())

    def add_post(self, author_id: UUID, text: str, author_position: int) -> Post:
        if not is_unlocked(self.position, author_position):
            raise DomainError("Diese Stelle ist noch nicht gelesen")
        # Leere Beiträge ablehnen (FEHLERBEHEBUNG)
        # Grund: Leere Beiträge ("" oder nur Leerzeichen) waren möglich.
        # LLM-Tests aus Übung 4 forderten die Regel, sie ging bei der Umsetzung verloren.
        if not text.strip():
            raise DomainError("Beitrag darf nicht leer sein")
        post = Post(uuid4(), author_id, text.strip(), datetime.now(timezone.utc))
        self.posts.append(post)
        return post

    def visible_posts(self, viewer_position: int) -> list[Post]:
        if not is_unlocked(self.position, viewer_position):
            return []
        return list(self.posts)
