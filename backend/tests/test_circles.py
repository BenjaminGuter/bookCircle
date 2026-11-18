# Übung 5: Tests für Circles

"""Circles: Lesekreise, Mitgliedschaften und Leseplan"""

from datetime import date
from uuid import uuid4

import pytest

from app.circles.application.join_circle import JoinCircle
from app.circles.domain.circle import ReadingCircle, ReadingPlan
from app.circles.domain.service import CircleProgressService, ProgressSnapshot
from app.reading.domain.progress import EditionRef, ReadingProgress
from app.shared.errors import DomainError, NotFoundError
from tests.fakes import InMemoryCircleRepository, InMemoryEditionLookup, InMemoryProgressRepository


@pytest.fixture
def circle_with_member():
    owner, member = uuid4(), uuid4()
    circle = ReadingCircle.found("Sci-Fi Club", owner, uuid4())
    circle.join(member)
    return circle, owner, member


@pytest.mark.parametrize("name", ["", "   "])
def test_name_must_not_be_empty(name):
    with pytest.raises(DomainError):
        ReadingCircle.found(name, uuid4(), uuid4())


def test_founder_is_first_member():
    owner = uuid4()
    circle = ReadingCircle.found("Krimi-Runde", owner, uuid4())
    assert list(circle.memberships) == [owner]
    assert circle.owner_id == owner
    assert circle.reading_plan is None


def test_join_twice_is_rejected(circle_with_member):
    circle, owner, member = circle_with_member
    with pytest.raises(DomainError):
        circle.join(member)
    with pytest.raises(DomainError):
        circle.join(owner)


def test_member_can_leave_and_rejoin(circle_with_member):
    circle, _, member = circle_with_member
    circle.leave(member)
    assert member not in circle.memberships
    circle.join(member)
    assert member in circle.memberships


def test_non_member_cannot_leave(circle_with_member):
    circle, _, _ = circle_with_member
    with pytest.raises(DomainError):
        circle.leave(uuid4())


def test_owner_cannot_leave_while_others_remain(circle_with_member):
    circle, owner, _ = circle_with_member
    with pytest.raises(DomainError):
        circle.leave(owner)
    assert owner in circle.memberships


def test_owner_can_leave_when_alone(circle_with_member):
    circle, owner, member = circle_with_member
    circle.leave(member)
    circle.leave(owner)
    assert circle.memberships == {}


# Leseplan


@pytest.mark.parametrize("percent", [0, -1, 101])
def test_reading_plan_percent_must_be_between_1_and_100(percent):
    with pytest.raises(DomainError):
        # Leseplan in Prozent pro Woche
        ReadingPlan(date(2026, 12, 1), percent)

@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2026, 11, 30), 0),  # vor dem Start
        (date(2026, 12, 1), 0),  # Starttag: noch keine volle Woche
        (date(2026, 12, 7), 0),  # 6 Tage
        (date(2026, 12, 8), 30),  # 1 volle Woche
        (date(2026, 12, 22), 90),  # 3 Wochen
        (date(2026, 12, 29), 100),  # 4 Wochen wären 120 -> höchstens 100
    ],
)
def test_target_percent_counts_full_weeks(today, expected):
    assert ReadingPlan(date(2026, 12, 1), 30).target_percent(today) == expected


def test_only_owner_sets_reading_plan(circle_with_member):
    circle, owner, member = circle_with_member
    plan = ReadingPlan(date(2026, 12, 1), 50)
    with pytest.raises(DomainError):
        circle.set_reading_plan(plan, by_user_id=member)
    assert circle.reading_plan is None
    circle.set_reading_plan(plan, by_user_id=owner)
    assert circle.reading_plan == plan

# Gruppenfortschritt (CircleProgressService): Mitglieder mit unterschiedlichen Ausgaben


def test_group_progress_in_percent_per_member(circle_with_member):
    circle, owner, member = circle_with_member
    progresses = [ProgressSnapshot(owner, 150, 300)]  # member hat noch nichts gelesen
    assert CircleProgressService().group_progress(circle, progresses) == {owner: 50, member: 0}


def test_group_progress_rounds_down(circle_with_member):
    circle, owner, member = circle_with_member
    progresses = [ProgressSnapshot(owner, 1999, 2000), ProgressSnapshot(member, 1, 3)]
    assert CircleProgressService().group_progress(circle, progresses) == {owner: 99, member: 33}


def test_members_behind_without_plan(circle_with_member):
    circle, _, _ = circle_with_member
    assert CircleProgressService().members_behind(circle, [], date(2026, 12, 15)) == []


def test_members_behind_compares_exactly(circle_with_member):
    """Soll nach 2 Wochen: 20 %. Exakt 20 % (60 von 300) ist nicht im Rückstand,
    knapp darunter (99 von 500 = 19,8 %) schon, auch wenn gerundet 20 % herauskäme."""
    circle, owner, member = circle_with_member
    circle.set_reading_plan(ReadingPlan(date(2026, 12, 1), 10), by_user_id=owner)
    progresses = [ProgressSnapshot(owner, 60, 300), ProgressSnapshot(member, 99, 500)]
    assert CircleProgressService().members_behind(circle, progresses, date(2026, 12, 15)) == [member]


def test_member_without_progress_is_behind(circle_with_member):
    circle, owner, member = circle_with_member
    circle.set_reading_plan(ReadingPlan(date(2026, 12, 1), 10), by_user_id=owner)
    progresses = [ProgressSnapshot(owner, 300, 300)]
    assert CircleProgressService().members_behind(circle, progresses, date(2026, 12, 15)) == [member]


# Use Case JoinCircle: Beitritt mit der eigenen Ausgabe


@pytest.fixture
def join_setup():
    """Lesekreis zu einem Werk mit zwei Ausgaben (300 und 600 Seiten)."""
    book_id = uuid4()
    circle = ReadingCircle.found("Krimi-Runde", uuid4(), book_id)
    paperback = EditionRef(uuid4(), book_id, 300)
    hardcover = EditionRef(uuid4(), book_id, 600)
    circles = InMemoryCircleRepository(circle)
    progress = InMemoryProgressRepository()
    use_case = JoinCircle(circles, InMemoryEditionLookup(paperback, hardcover), progress)
    return use_case, circle, paperback, hardcover, progress


def test_join_starts_progress_with_chosen_edition(join_setup):
    use_case, circle, paperback, _, progress = join_setup
    user = uuid4()
    events = use_case.execute(circle.id, user, paperback.edition_id)
    assert user in circle.memberships
    started = progress.get(user, circle.book_id)
    assert (started.edition_id, started.total_pages, started.last_read_page) == (paperback.edition_id, 300, 0)
    assert events == []


def test_join_with_other_edition_keeps_share(join_setup):
    """Wer das Buch schon liest, behält seinen Anteil: Seite 150 von 300 = Seite 300 von 600."""
    use_case, circle, paperback, hardcover, progress = join_setup
    user = uuid4()
    existing = ReadingProgress.start(user, paperback)
    existing.advance_to(150)
    existing.pull_events()
    progress.save(existing)

    [event] = use_case.execute(circle.id, user, hardcover.edition_id)

    assert (existing.total_pages, existing.last_read_page) == (600, 300)
    assert (event.page, event.total_pages) == (300, 600)


def test_join_unknown_circle_or_edition(join_setup):
    use_case, circle, paperback, _, _ = join_setup
    with pytest.raises(NotFoundError):
        use_case.execute(uuid4(), uuid4(), paperback.edition_id)
    with pytest.raises(NotFoundError):
        use_case.execute(circle.id, uuid4(), uuid4())


def test_join_with_edition_of_other_book_is_rejected(join_setup):
    use_case, circle, _, _, progress = join_setup
    foreign = EditionRef(uuid4(), uuid4(), 200)
    use_case._editions = InMemoryEditionLookup(foreign)
    user = uuid4()
    with pytest.raises(DomainError):
        use_case.execute(circle.id, user, foreign.edition_id)
    assert user not in circle.memberships
    assert progress.get(user, circle.book_id) is None


def test_join_twice_is_rejected_and_progress_unchanged(join_setup):
    use_case, circle, paperback, hardcover, progress = join_setup
    user = uuid4()
    use_case.execute(circle.id, user, paperback.edition_id)
    with pytest.raises(DomainError):
        use_case.execute(circle.id, user, hardcover.edition_id)
    assert progress.get(user, circle.book_id).edition_id == paperback.edition_id
