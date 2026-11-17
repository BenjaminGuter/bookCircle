import pytest
from uuid import uuid4, UUID

# to-do : korrekte importpfade anpassen, wenn die Struktur geändert wird
from domain.exceptions import DomainError, ValidationError
from domain.identity import Email
from domain.catalog import ISBN
from domain.reading_circle import (
    ReadingCircle,
    ReadingPlan,
    ReadingProgressUpdated,
    BookFinished,
)
from domain.discussion import DiscussionThread
from domain.reading_progress import ReadingProgress


# =====================================================================
# Pytest Fixtures (beseitigt Code-Duplikation aus create_sample_circle)
# =====================================================================

@pytest.fixture
def sample_circle() -> tuple[ReadingCircle, UUID, UUID]:
    owner_id = uuid4()
    member_id = uuid4()
    circle = ReadingCircle.found(
        name="Sci-Fi Club",
        owner_id=owner_id,
        book_id=uuid4(),
        total_pages=10,
        reading_plan=ReadingPlan(start="2026-12-01", pages_per_week=2),
    )
    circle.join(member_id)
    circle.domain_events.clear()
    return circle, owner_id, member_id


# =====================================================================
# 1. ReadingCircle: Fortschritt & Domain Events (update_progress)
# =====================================================================

class TestReadingCircleProgress:
    # HAPPY PATH: Normaler Fortschritt löst Event aus
    def test_update_progress_happy_path(self, sample_circle):
        circle, _, member_id = sample_circle

        circle.update_progress(user_id=member_id, page=4)

        membership = circle.get_membership(member_id)
        assert membership.progress == 4
        assert any(
            isinstance(e, ReadingProgressUpdated) and e.page == 4
            for e in circle.domain_events
        )
        assert not any(
            isinstance(e, BookFinished) for e in circle.domain_events
        )

    # EDGE CASE: Erreichen der exakt letzten Seite triggert BookFinished
    def test_update_progress_exact_last_page_triggers_finished(self, sample_circle):
        circle, _, member_id = sample_circle

        circle.update_progress(user_id=member_id, page=10)

        assert circle.get_membership(member_id).progress == 10
        assert any(
            isinstance(e, BookFinished) and e.user_id == member_id
            for e in circle.domain_events
        )

    # EDGE CASE (NEU): Gleiche Seitenzahl erneut melden (Idempotenz)
    def test_update_progress_same_page_is_allowed(self, sample_circle):
        circle, _, member_id = sample_circle
        circle.update_progress(user_id=member_id, page=5)
        circle.domain_events.clear()

        circle.update_progress(user_id=member_id, page=5)

        assert circle.get_membership(member_id).progress == 5

    # NEGATIVE TEST: Fortschritt darf nicht unter Null, über total_pages oder rückwärts gehen
    def test_update_progress_invalid_page_raises_error(self, sample_circle):
        circle, _, member_id = sample_circle

        with pytest.raises(DomainError):
            circle.update_progress(user_id=member_id, page=-1)

        with pytest.raises(DomainError):
            circle.update_progress(user_id=member_id, page=11)

        # Neuer Negative-Case: Monotonie (Fortschritt darf nicht sinken)
        circle.update_progress(user_id=member_id, page=6)
        with pytest.raises(DomainError):
            circle.update_progress(user_id=member_id, page=5)

    # NEGATIVE TEST (NEU): Nicht-Mitglied darf keinen Fortschritt melden
    def test_update_progress_unknown_member_raises_error(self, sample_circle):
        circle, _, _ = sample_circle

        with pytest.raises(DomainError):
            circle.update_progress(user_id=uuid4(), page=3)


# =====================================================================
# 2. ReadingCircle: Mitgliedschaft & Gründer-Austrittsregel (join / leave)
# =====================================================================

class TestReadingCircleLeave:
    # HAPPY PATH: Reguläres Mitglied verlässt den Kreis jederzeit
    def test_regular_member_can_leave_anytime(self, sample_circle):
        circle, owner_id, member_id = sample_circle

        circle.leave(member_id)

        assert len(circle.memberships) == 1
        assert circle.memberships[0].user_id == owner_id

    # EDGE CASE: Gründer tritt aus, nachdem alle anderen gegangen sind
    def test_owner_can_leave_when_alone(self, sample_circle):
        circle, owner_id, member_id = sample_circle
        circle.leave(member_id)

        circle.leave(owner_id)  # Jetzt ist der Gründer allein -> erlaubt

        assert len(circle.memberships) == 0

    # NEGATIVE TEST: Gründer versucht auszutreten, während noch Mitglieder da sind
    def test_owner_cannot_leave_while_other_members_exist(self, sample_circle):
        circle, owner_id, _ = sample_circle

        with pytest.raises(
            DomainError, match="Gründer kann erst austreten, wenn er allein ist"
        ):
            circle.leave(owner_id)

    # NEGATIVE TEST (NEU): Doppelter Beitritt und Austritt eines Nicht-Mitglieds
    def test_duplicate_join_and_non_member_leave_rejected(self, sample_circle):
        circle, _, member_id = sample_circle

        with pytest.raises(DomainError):
            circle.join(member_id)

        with pytest.raises(DomainError):
            circle.leave(uuid4())


# =====================================================================
# 3. DiscussionThread: Spoiler-Schutz beim Lesen, Schreiben & Löschen
# =====================================================================

class TestDiscussionSpoilerProtection:
    # HAPPY PATH: Nutzer mit höherem Fortschritt darf posten und lesen
    def test_add_and_read_post_with_sufficient_progress(self):
        thread = DiscussionThread.open(
            circle_id=uuid4(), page=5, title="Seite 5 Twist!"
        )
        author_id = uuid4()

        thread.add_post(
            author_id=author_id, text="Was für ein Ende!", author_progress=7
        )
        visible = thread.visible_posts(viewer_progress=6)

        assert len(visible) == 1
        assert visible[0].text == "Was für ein Ende!"

    # EDGE CASE: Exakter Gleichstand (progress == page) muss erlaubt sein
    def test_boundary_exact_page_match_allows_reading_and_writing(self):
        thread = DiscussionThread.open(
            circle_id=uuid4(), page=5, title="Seite 5 Twist!"
        )

        thread.add_post(
            author_id=uuid4(), text="Gerade beendet!", author_progress=5
        )
        visible = thread.visible_posts(viewer_progress=5)

        assert len(visible) == 1

    # NEGATIVE TEST: Geringerer Fortschritt blockiert Schreiben & blendet Posts aus
    def test_insufficient_progress_blocks_posting_and_hides_posts(self):
        thread = DiscussionThread.open(
            circle_id=uuid4(), page=5, title="Seite 5 Twist!"
        )
        thread.add_post(author_id=uuid4(), text="Spoiler!", author_progress=5)

        # Lesen liefert leere Liste (kein Spoiler)
        assert thread.visible_posts(viewer_progress=4) == []

        # Schreiben wirft DomainError
        with pytest.raises(
            DomainError, match="Fortschritt reicht für diese Seite nicht aus"
        ):
            thread.add_post(
                author_id=uuid4(), text="Darf ich noch nicht", author_progress=4
            )

    # NEGATIVE TEST (NEU): Leerer Post (nur Whitespace) & unbefugtes Löschen
    def test_empty_post_and_unauthorized_deletion_rejected(self):
        thread = DiscussionThread.open(
            circle_id=uuid4(), page=5, title="Seite 5 Twist!"
        )
        author_id = uuid4()

        with pytest.raises((DomainError, ValidationError)):
            thread.add_post(author_id=author_id, text="   \n  ", author_progress=5)

        thread.add_post(author_id=author_id, text="Gültiger Text", author_progress=5)
        post_id = thread.posts[0].id

        with pytest.raises(DomainError):
            thread.delete_post(post_id=post_id, by_user_id=uuid4())


# =====================================================================
# 4. ReadingProgress: Vorwärts-Lesen vs. Korrektur (advance_to, correct_to)
# =====================================================================

class TestReadingProgress:
    # HAPPY PATH: Fortschritt vorwärts bewegen und Prozentwert prüfen
    def test_advance_to_increases_progress_and_calculates_percentage(self):
        rp = ReadingProgress(
            user_id=uuid4(), book_id=uuid4(), current_page=0, total_pages=200
        )

        rp.advance_to(50)

        assert rp.current_page == 50
        assert rp.percentage() == 25.0

    # EDGE CASE: Zurücksetzen auf 0 und Maximum über correct_to erlaubt
    def test_correct_to_allows_resetting_to_zero_and_max_page(self):
        rp = ReadingProgress(
            user_id=uuid4(), book_id=uuid4(), current_page=120, total_pages=200
        )

        rp.correct_to(0)
        assert rp.current_page == 0

        rp.correct_to(200)
        assert rp.current_page == 200
        assert rp.percentage() == 100.0

    # NEGATIVE TEST: advance_to darf nicht rückwärts gehen und total_pages nicht überschreiten
    def test_advance_to_rejects_backward_or_overflow_pages(self):
        rp = ReadingProgress(
            user_id=uuid4(), book_id=uuid4(), current_page=100, total_pages=200
        )

        with pytest.raises(DomainError):
            rp.advance_to(99)   # Rückwärts verboten

        with pytest.raises(DomainError):
            rp.advance_to(201)  # Über total_pages verboten

    # NEGATIVE TEST (NEU): Ungültige Initialwerte (total_pages <= 0 oder negative Seiten)
    @pytest.mark.parametrize(
        "current,total",
        [
            (0, 0),
            (0, -5),
            (-1, 100),
            (101, 100),
        ],
    )
    def test_invalid_initialization_raises_error(self, current, total):
        with pytest.raises((DomainError, ValidationError)):
            ReadingProgress(
                user_id=uuid4(), book_id=uuid4(), current_page=current, total_pages=total
            )


# =====================================================================
# 5. Value Objects: Regex-Validierung (Email & ISBN)
# =====================================================================

class TestValueObjectValidation:
    @pytest.mark.parametrize(
        "valid_email",
        [
            "anna@example.com",                # Happy Path
            "max.mustermann+books@sub.uni.de", # Edge Case: Subdomain & Plus-Tag
        ],
    )
    def test_email_valid(self, valid_email):
        assert Email(valid_email).value == valid_email

    @pytest.mark.parametrize(
        "invalid_email",
        [
            "",                  # Leer
            "anna@localhost",    # Fehlende Top-Level-Domain
            "anna @example.com", # Leerzeichen
            "@example.com",      # Fehlender Local-Part
        ],
    )
    def test_email_invalid(self, invalid_email):
        with pytest.raises(ValidationError):
            Email(invalid_email)

    @pytest.mark.parametrize(
        "isbn_input,is_valid",
        [
            ("978-3-16-148410-0", True),  # Happy Path: ISBN-13 mit Bindestrichen
            ("0-306-40615-2", True),      # Happy Path: ISBN-10
            ("043942089X", True),         # Edge Case: ISBN-10 mit 'X' als Prüfziffer
            ("978316148410", False),      # Negative: Nur 12 Stellen
            ("978-3-16-148410-X", False), # Negative: 'X' nur bei ISBN-10 erlaubt
        ],
    )
    def test_isbn_validation(self, isbn_input, is_valid):
        if is_valid:
            assert ISBN(isbn_input).value == isbn_input
        else:
            with pytest.raises(ValidationError):
                ISBN(isbn_input)