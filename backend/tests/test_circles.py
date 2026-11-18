# Übung 5: Tests für Circles

"""Circles: Lesekreise, Mitgliedschaften und Leseplan"""

from datetime import date
from uuid import uuid4

import pytest

from app.circles.domain.circle import ReadingCircle, ReadingPlan
from app.shared.errors import DomainError


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


@pytest.mark.parametrize("pages", [0, -1])
def test_reading_plan_needs_at_least_one_page(pages):
    with pytest.raises(DomainError):
        ReadingPlan(date(2026, 12, 1), pages)


def test_only_owner_sets_reading_plan(circle_with_member):
    circle, owner, member = circle_with_member
    plan = ReadingPlan(date(2026, 12, 1), 50)
    with pytest.raises(DomainError):
        circle.set_reading_plan(plan, by_user_id=member)
    assert circle.reading_plan is None
    circle.set_reading_plan(plan, by_user_id=owner)
    assert circle.reading_plan == plan
