from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

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
        if not 1 <= position <= 1000:
            raise DomainError("Position muss zwischen 1 und 1000 liegen")
        if not is_unlocked(position, author_position):
            raise DomainError("Thread kann nur an einer bereits gelesenen Stelle eröffnet werden")
        return cls(uuid4(), circle_id, book_id, position, title)

    def add_post(self, author_id: UUID, text: str, author_position: int) -> Post:
        if not is_unlocked(self.position, author_position):
            raise DomainError("Diese Stelle ist noch nicht gelesen")
        post = Post(uuid4(), author_id, text, datetime.now(timezone.utc))
        self.posts.append(post)
        return post

    def visible_posts(self, viewer_position: int) -> list[Post]:
        if not is_unlocked(self.position, viewer_position):
            return []
        return list(self.posts)
