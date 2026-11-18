# Übung 5: Tests für Discussion. Haben die leeren Beiträge/Titel gefunden.

"""Discussion: Threads an einer Buchstelle (Promille) mit Spoiler-Schutz"""

from uuid import uuid4

import pytest

from app.discussion.domain.thread import DiscussionThread, is_unlocked
from app.shared.errors import DomainError


def open_thread(position=400, author_position=500, title="Der Verrat"):
    return DiscussionThread.open(uuid4(), uuid4(), position, title, author_position)


# Spoiler-Regel


@pytest.mark.parametrize(
    ("thread_position", "viewer_position", "expected"),
    [
        (300, 500, True),  # schon weiter
        (500, 500, True),  # Grenzwert: genau an der Stelle
        (501, 500, False),  # Grenzwert: eine Promille zu früh
        (1, 0, False),  # noch nicht begonnen
        (1000, 1000, True),  # Buch beendet
    ],
)
def test_is_unlocked(thread_position, viewer_position, expected):
    assert is_unlocked(thread_position, viewer_position) is expected


# Thread eröffnen

@pytest.mark.parametrize("position", [0, -1, 1001])
def test_position_must_be_between_1_and_1000(position):
    with pytest.raises(DomainError):
        open_thread(position=position, author_position=1000)


@pytest.mark.parametrize("position", [1, 1000])
def test_position_boundaries_are_allowed(position):
    assert open_thread(position=position, author_position=1000).position == position


def test_thread_only_at_already_read_position():
    with pytest.raises(DomainError):
        open_thread(position=600, author_position=599)


@pytest.mark.parametrize("title", ["", "   "])
def test_title_must_not_be_empty(title):
    with pytest.raises(DomainError):
        open_thread(title=title)


def test_title_is_trimmed():
    assert open_thread(title="  Kapitel 3  ").title == "Kapitel 3"


# Beiträge


def test_reader_far_enough_sees_posts():
    thread = open_thread(position=400)
    thread.add_post(uuid4(), "Hab ich nicht kommen sehen!", author_position=400)
    assert [p.text for p in thread.visible_posts(viewer_position=400)] == [
        "Hab ich nicht kommen sehen!"
    ]


def test_reader_not_far_enough_sees_nothing():
    thread = open_thread(position=400)
    thread.add_post(uuid4(), "Spoiler", author_position=900)
    assert thread.visible_posts(viewer_position=399) == []


def test_cannot_post_before_reaching_position():
    thread = open_thread(position=400)
    with pytest.raises(DomainError):
        thread.add_post(uuid4(), "Zu früh", author_position=399)
    assert thread.posts == []


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_post_is_rejected(text):
    thread = open_thread()
    with pytest.raises(DomainError):
        thread.add_post(uuid4(), text, author_position=1000)


def test_post_text_is_trimmed():
    thread = open_thread()
    assert thread.add_post(uuid4(), "  Hallo  ", author_position=1000).text == "Hallo"


def test_visible_posts_returns_copy():
    """Wer die zurückgegebene Liste verändert, darf den Thread nicht verändern."""
    thread = open_thread(position=1)
    thread.add_post(uuid4(), "Text", author_position=1)
    thread.visible_posts(viewer_position=1).clear()
    assert len(thread.posts) == 1
