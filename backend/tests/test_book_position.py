# Übung 5: Tests für die Umrechnung von Seite zu Promille (shared/book_position.py).

"""Buchstelle in Promille: Umrechnung Seite zu Position (shared/book_position.py)."""

import pytest

from app.shared.book_position import MAX_POSITION, to_page, to_position


@pytest.mark.parametrize(
    ("page", "total", "expected"),
    [
        (0, 200, 0),  # nicht begonnen
        (200, 200, 1000),  # fertig
        (100, 200, 500),  # Hälfte
        (1, 3, 333),  # 333,3 wird abgerundet
        (2, 3, 666),  # 666,7 wird ebenfalls abgerundet
        (1, 2000, 0),  # 0,5 Promille zählt noch nicht
        (1999, 2000, 999),  # kurz vor Schluss: nie schon "fertig"
    ],
)
def test_to_position(page, total, expected):
    assert to_position(page, total) == expected


@pytest.mark.parametrize(
    ("position", "total", "expected"),
    [(0, 300, 0), (1000, 300, 300), (500, 300, 150), (333, 3, 1)],
)
def test_to_page(position, total, expected):
    assert to_page(position, total) == expected


def test_same_position_in_different_editions():
    """Promille-Idee: Seite 150 von 300 und Seite 250 von 500
    sind dieselbe Stelle im Buch."""
    assert to_position(150, 300) == to_position(250, 500) == 500


def test_full_book_is_max_position():
    assert to_position(321, 321) == MAX_POSITION
    assert to_page(MAX_POSITION, 321) == 321


@pytest.mark.parametrize("total", [1001, 1500, 2000, 4999])
def test_only_last_page_reaches_max_position(total):
    """Spoiler-Schutz: Auf der vorletzten Seite ist das Buchende nie freigeschaltet."""
    assert to_position(total - 1, total) < MAX_POSITION
    assert to_position(total, total) == MAX_POSITION
