# Buchstelle in Promille als gemeinsames Konzept (Shared Kernel).
# Grund: Die Zahl 1000 stand unbenannt in reading und discussion (Magic Number, CCD).

"""Buchstelle in Promille: gemeinsames Konzept von Reading und Discussion.

Eine Stelle im Buch wird in Promille angegeben (0 = nicht begonnen, 1000 = fertig).
So lassen sich Ausgaben mit unterschiedlicher Seitenzahl vergleichen: Seite 150
von 300 und Seite 250 von 500 sind dieselbe Stelle (500).

Die Umrechnung muss zur generierten Spalte in der Datenbank passen.
"""

MAX_POSITION = 1000


def to_position(page: int, total_pages: int) -> int:
    """Seite -> Position in Promille (0..1000), ganzzahlig abgerundet."""
    return page * MAX_POSITION // total_pages


def to_page(position: int, total_pages: int) -> int:
    """Position -> Seite in einer bestimmten Ausgabe (für die Anzeige)."""
    return (position * total_pages + MAX_POSITION // 2) // MAX_POSITION
