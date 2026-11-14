from fastapi.testclient import TestClient

import pytest
from uuid import uuid4
from app.main import app
from app.spoiler import is_visible

client = TestClient(app)




# ==========================================
# 1. IDENTITY – USER
# ==========================================

def test_register_user_with_invalid_email():
    with pytest.raises(ValueError):
        User.register(
            email="invalid-email",
            display_name="Max",
            password="SecurePassword123"
        )


def test_register_user_with_empty_display_name():
    with pytest.raises(ValueError):
        User.register(
            email="max@example.com",
            display_name="",
            password="SecurePassword123"
        )


# ==========================================
# 2. CATALOG – BOOK / CHAPTER
# ==========================================

def test_book_chapters_are_numbered_consecutively():
    book = Book(
        id=uuid4(),
        title="Clean Architecture",
        isbn=None,
        author_ids=[uuid4()],
        chapters=[
            Chapter(number=1, title="Introduction"),
            Chapter(number=2, title="Architecture"),
        ]
    )

    book.add_chapter("Design Principles")

    assert len(book.chapters) == 3
    assert book.chapters[2].number == 3


def test_book_rejects_chapter_number_gap():
    with pytest.raises(ValueError):
        Book(
            id=uuid4(),
            title="Clean Architecture",
            isbn=None,
            author_ids=[uuid4()],
            chapters=[
                Chapter(number=1, title="Introduction"),
                Chapter(number=3, title="Architecture"),
            ]
        )


def test_book_requires_at_least_one_author():
    with pytest.raises(ValueError):
        Book(
            id=uuid4(),
            title="Clean Architecture",
            isbn=None,
            author_ids=[],
            chapters=[
                Chapter(number=1, title="Introduction")
            ]
        )


# ==========================================
# 3. LIBRARY – SHELF
# ==========================================

def test_book_cannot_be_added_twice_to_shelf():
    book_id = uuid4()

    shelf = Shelf(
        id=uuid4(),
        owner_id=uuid4(),
        name="Meine Bücher",
        entries=[]
    )

    shelf.add_book(book_id)

    with pytest.raises(ValueError):
        shelf.add_book(book_id)

    assert len(shelf.entries) == 1


def test_book_can_be_removed_from_shelf():
    book_id = uuid4()

    shelf = Shelf(
        id=uuid4(),
        owner_id=uuid4(),
        name="Meine Bücher",
        entries=[]
    )

    shelf.add_book(book_id)
    shelf.remove_book(book_id)

    assert len(shelf.entries) == 0


def test_reading_status_can_be_changed():
    book_id = uuid4()

    shelf = Shelf(
        id=uuid4(),
        owner_id=uuid4(),
        name="Meine Bücher",
        entries=[]
    )

    shelf.add_book(book_id)
    shelf.change_status(book_id, ReadingStatus.READING)

    assert shelf.entries[0].status == ReadingStatus.READING


# ==========================================
# 4. READING CIRCLES
# ==========================================

def test_reading_progress_cannot_decrease():
    user_id = uuid4()

    circle = ReadingCircle.found(
        name="Book Club",
        owner_id=user_id,
        book_id=uuid4(),
        total_chapters=20
    )

    circle.update_progress(user_id, 10)

    with pytest.raises(ValueError):
        circle.update_progress(user_id, 8)

    assert circle.memberships[0].progress == 10


def test_reading_progress_cannot_exceed_total_chapters():
    user_id = uuid4()

    circle = ReadingCircle.found(
        name="Book Club",
        owner_id=user_id,
        book_id=uuid4(),
        total_chapters=20
    )

    with pytest.raises(ValueError):
        circle.update_progress(user_id, 21)


def test_reading_progress_allows_zero():
    user_id = uuid4()

    circle = ReadingCircle.found(
        name="Book Club",
        owner_id=user_id,
        book_id=uuid4(),
        total_chapters=20
    )

    circle.update_progress(user_id, 0)

    assert circle.memberships[0].progress == 0


def test_user_cannot_join_circle_twice():
    owner_id = uuid4()
    member_id = uuid4()

    circle = ReadingCircle.found(
        name="Book Club",
        owner_id=owner_id,
        book_id=uuid4(),
        total_chapters=20
    )

    circle.join(member_id)

    with pytest.raises(ValueError):
        circle.join(member_id)


def test_circle_owner_cannot_leave_while_members_exist():
    owner_id = uuid4()
    member_id = uuid4()

    circle = ReadingCircle.found(
        name="Book Club",
        owner_id=owner_id,
        book_id=uuid4(),
        total_chapters=20
    )

    circle.join(member_id)

    with pytest.raises(ValueError):
        circle.leave(owner_id)

    assert any(
        membership.user_id == owner_id
        for membership in circle.memberships
    )


def test_book_finished_event_emitted_only_once():
    user_id = uuid4()

    circle = ReadingCircle.found(
        name="Book Club",
        owner_id=user_id,
        book_id=uuid4(),
        total_chapters=20
    )

    circle.update_progress(user_id, 20)
    circle.update_progress(user_id, 20)

    events = [
        event for event in circle.events
        if isinstance(event, BookFinished)
    ]

    assert len(events) == 1


# ==========================================
# 5. DISCUSSION – DISCUSSION THREAD
# ==========================================

def test_user_cannot_see_posts_from_unread_chapters():
    thread = DiscussionThread.open(
        circle_id=uuid4(),
        chapter=10,
        title="Diskussion über Kapitel 10"
    )

    thread.add_post(
        author_id=uuid4(),
        text="Interessante Wendung!",
        author_progress=12
    )

    visible_posts = thread.visible_posts(
        viewer_progress=8
    )

    assert len(visible_posts) == 0


def test_user_can_see_posts_when_progress_is_sufficient():
    thread = DiscussionThread.open(
        circle_id=uuid4(),
        chapter=10,
        title="Diskussion über Kapitel 10"
    )

    thread.add_post(
        author_id=uuid4(),
        text="Interessante Wendung!",
        author_progress=12
    )

    visible_posts = thread.visible_posts(
        viewer_progress=10
    )

    assert len(visible_posts) == 1


def test_user_cannot_post_if_progress_is_insufficient():
    thread = DiscussionThread.open(
        circle_id=uuid4(),
        chapter=10,
        title="Diskussion über Kapitel 10"
    )

    with pytest.raises(ValueError):
        thread.add_post(
            author_id=uuid4(),
            text="Ich kenne den Inhalt noch nicht.",
            author_progress=8
        )

    assert len(thread.posts) == 0


def test_user_cannot_delete_post_of_another_user():
    author_id = uuid4()
    attacker_id = uuid4()

    thread = DiscussionThread.open(
        circle_id=uuid4(),
        chapter=5,
        title="Diskussion"
    )

    thread.add_post(
        author_id=author_id,
        text="Mein Beitrag",
        author_progress=5
    )

    post_id = thread.posts[0].id

    with pytest.raises(PermissionError):
        thread.delete_post(
            post_id=post_id,
            by_user_id=attacker_id
        )

    assert len(thread.posts) == 1


def test_user_can_delete_own_post():
    author_id = uuid4()

    thread = DiscussionThread.open(
        circle_id=uuid4(),
        chapter=5,
        title="Diskussion"
    )

    thread.add_post(
        author_id=author_id,
        text="Mein Beitrag",
        author_progress=5
    )

    post_id = thread.posts[0].id

    thread.delete_post(
        post_id=post_id,
        by_user_id=author_id
    )

    assert len(thread.posts) == 0


def test_empty_post_is_rejected():
    thread = DiscussionThread.open(
        circle_id=uuid4(),
        chapter=5,
        title="Diskussion"
    )

    with pytest.raises(ValueError):
        thread.add_post(
            author_id=uuid4(),
            text="",
            author_progress=5
        )

    assert len(thread.posts) == 0