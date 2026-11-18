# Übung 5: Tests für Reading

"""Reading: Lesefortschritt pro Nutzer und Buch"""

from uuid import uuid4

import pytest

from app.reading.domain.progress import (
    BookFinished,
    ReadingProgress,
    ReadingProgressChanged,
)
from app.shared.errors import DomainError


@pytest.fixture
def progress() -> ReadingProgress:
    return ReadingProgress.start(uuid4(), uuid4(), total_pages=200)


# ReadingProgress


@pytest.mark.parametrize("total", [0, -5])
def test_start_requires_at_least_one_page(total):
    with pytest.raises(DomainError):
        ReadingProgress.start(uuid4(), uuid4(), total_pages=total)


def test_start_at_page_zero(progress):
    assert progress.last_read_page == 0
    assert progress.position == 0
    assert progress.percentage() == 0
    assert progress.pull_events() == []


def test_advance_records_event_with_position(progress):
    progress.advance_to(50)
    [event] = progress.pull_events()
    assert isinstance(event, ReadingProgressChanged)
    assert (event.page, event.position) == (50, 250)
    assert progress.percentage() == 25


def test_percentage_is_100_only_on_last_page():
    progress = ReadingProgress.start(uuid4(), uuid4(), total_pages=2000)
    progress.advance_to(1999)
    assert progress.percentage() == 99
    progress.advance_to(2000)
    assert progress.percentage() == 100


def test_advance_cannot_go_backwards(progress):
    progress.advance_to(80)
    with pytest.raises(DomainError):
        progress.advance_to(79)
    assert progress.last_read_page == 80


@pytest.mark.parametrize("page", [-1, 201])
def test_pages_outside_book_are_rejected(progress, page):
    with pytest.raises(DomainError):
        progress.advance_to(page)
    with pytest.raises(DomainError):
        progress.correct_to(page)


def test_same_page_twice_records_no_event(progress):
    progress.advance_to(10)
    progress.pull_events()
    progress.advance_to(10)
    assert progress.pull_events() == []


def test_last_page_finishes_book_exactly_once(progress):
    progress.advance_to(200)
    progress.advance_to(200)
    events = progress.pull_events()
    assert [type(e) for e in events] == [ReadingProgressChanged, BookFinished]


def test_correct_to_may_go_backwards(progress):
    progress.advance_to(150)
    progress.correct_to(20)
    assert progress.last_read_page == 20
    assert progress.pull_events()[-1].page == 20


def test_finishing_again_after_correction_raises_book_finished_again(progress):
    # TODO: Aktuell löst das erneute Beenden nach einer Korrektur wieder
    # BookFinished aus. Wollen wir das so?
    progress.advance_to(200)
    progress.correct_to(199)
    progress.advance_to(200)
    finished = [e for e in progress.pull_events() if isinstance(e, BookFinished)]
    assert len(finished) == 2


def test_pull_events_empties_the_list(progress):
    progress.advance_to(1)
    assert len(progress.pull_events()) == 1
    assert progress.pull_events() == []
