# Kennzahlen für die Doku von Übung 5

Gemessen am 18.11.2026. „Vorher“ = Repo-Stand `637a8ac`, „Nachher“ = mit allen Änderungen durch Übung 5.
Python-Werkzeuge statt der Java-Werkzeuge aus dem Skript: `radon` (McCabe, Halstead, Rohmetriken), `lizard` (Parameter, Länge), `ruff` (Regelverletzungen, wie Checkstyle/PMD), `pytest-cov` (wie JaCoCo), eigener Architekturtest (wie JDepend).

## Aufgabe 1: Einfache Metriken (MET 5.4, 5.5)

| Metrik | Vorher | Nachher | Einordnung laut Kursmaterial |
|---|---|---|---|
| Quellcodezeilen (SLOC, nur `app/`) | 536 | 541 | – |
| Funktionen/Methoden/Klassen | 86 | 86 | – |
| McCabe, Durchschnitt | 1,93 (A) | 1,92 (A) | Sonar zählt Funktionen ab 8 als Schuld (MET 5.10); höchster Wert bei uns: 4 |
| Funktionen über McCabe 5 (radon ≥ B) | 0 | 0 | – |
| Kommentaranteil | 3 % | 4 % | Faustregel im Kurs: 30–60 % (MET 5.4) |
| Parameter > 4 (lizard) | 1 × `DiscussionThread.open` (6, davon 5 echte) | unverändert | Kursmaterial nennt eine Obergrenze für Parameter als Regel (MET 5.7) |
| Halstead Difficulty, höchste Datei | `circles/domain/circle.py` 4,78 | unverändert | Absolute Werte unwichtig, nur Größenordnungssprünge (MET 5.5) |

**Diskussionspunkte:**
- **Ungenutzter Code: `to_page()`:** Das Kursmaterial fordert „Kill Useless Code“ (CCD 6.4), ebenso das Prinzip YAGNI („You Ain't Gonna Need It“). Die Funktion ist aber klein, getestet und für eine konkret geplante Anzeige gedacht. Sie bleibt deshalb und ist als Schuld vermerkt (Aufgabe 3). Regeln aus dem Kurs müssen abgewogen werden.
- **Kommentaranteil 4 % statt 30–60 %:** Die Faustregel aus MET widerspricht CCD („Delete Useless Comments“, sprechende Namen statt Kommentare). Der Code nutzt sprechende Namen und Docstrings an Klassen und Funktionen. Kommentare nur einzufügen, um die Metrik zu erfüllen, wäre nicht sinnvoll. Ein gutes Beispiel für „Gute Metriken sind nicht gleich gute Qualität“ (MET 5.3).
- **McCabe und Halstead haben sich kaum verändert.** Der Code war schon einfach, die Refactorings betrafen Duplikate und Magic Numbers, die diese Metriken nicht erfassen.
- **`DiscussionThread.open` mit 5 echten Parametern** (`lizard` zählt `cls` mit): `book_id` ließe sich aus dem Lesekreis ableiten. Nicht geändert, weil die Datenbank den Wert pro Thread speichert. Als Schuld dokumentiert.

## Aufgabe 2: Coverage (MET 5.6, CCD 6.5.3)

| | Vorher | Nachher |
|---|---|---|
| Tests in der CI | 2 | 114 |
| Zweigabdeckung gesamt | 23 % | 84 % |
| ohne SQL-Repositories und DB-Verbindung | – | 99 % |
| `circles`, `discussion`, `reading` (Domain) | je 0 % | je 100 % |
| `catalog/application/covers.py` | 17 % | 100 % |

Gemessen wird **Zweigabdeckung** (Branch Coverage), entsprechend der „Conditional Coverage“ (CCD 6.5.3). Ungetestet bleiben `infrastructure/sql_*.py` und `shared/database.py`, weil sie eine echte PostgreSQL brauchen.

**Fehler, die die neuen Tests gefunden haben:**
- Leere Beiträge und leere Thread-Titel wurden akzeptiert.
- **Spoiler-Schutz:** Die Promille-Position wurde ab 0,5 aufgerundet. Bei Seite 1999 von 2000 ergab das schon 1000, damit waren Threads zum Buchende sichtbar, und die Anzeige stand auf 100 %. Gefunden über Grenzwerttests, korrigiert durch Abrunden in Code und Datenbank (mit Team abgestimmt). Ein Beispiel dafür, dass 100 % Abdeckung allein nichts garantiert: Unsere ersten Tests für `to_position()` deckten die Funktion bereits vollständig ab und bestanden, weil sie das Runden als erwartetes Verhalten festhielten (`(2, 3, 667)  # aufgerundet`). Erst die fachliche Frage „Darf ein Buch vor der letzten Seite als fertig gelten?“ hat den Fehler sichtbar gemacht.

**Aufgefallenes Verhalten (Team muss noch entscheiden):** Nach `correct_to()` unter die letzte Seite und erneutem Beenden wird `BookFinished` ein zweites Mal ausgelöst.

## Aufgabe 3: Regelverletzungen und Technical Debt (MET 5.7, 5.10, CCD 6.5.10)

**ruff** (Regeln E, F, W, B, UP, SIM, PT, N, C90, I): 60 Befunde vorher, 44 nachher.

| Regel | Vorher | Nachher | Bewertung |
|---|---|---|---|
| E501 Zeile zu lang | 31 | 26 | Gering. Rest im bestehenden Code. |
| B008 Funktionsaufruf als Standardwert | 11 | 11 | **Fehlalarm:** `Depends()` ist bei FastAPI so vorgesehen. Regel für den Router abschalten. |
| B904 `raise` ohne `from` | 4 | 0 | Durch die zentrale Fehlerbehandlung entfallen |
| W291/W292/I001 Formatierung | 10 | 5 | Gering, mit `ruff --fix` behebbar |
| UP017 `timezone.utc` | 2 | 2 | Gering |
| PT006 | 2 | 0 | Entfallen mit `test_llm.py` |

**Kopplung (Skript MET 5.8.1: Ca, Ce, I = Ce / (Ca + Ce)):**

| Paket | Ca | Ce | I |
|---|---|---|---|
| `shared` | 5 | 0 | 0,00 (stabil) |
| `catalog` | 1 | 1 | 0,50 |
| `circles`, `discussion`, `reading` | 0 | 1 | 1,00 |
| `main` | 0 | 2 | 1,00 |

Keine Zyklen. Instabile Pakete hängen nur vom stabilsten Paket ab (Stable Dependencies Principle, CCD 6.7). Das prüft jetzt `test_architecture.py` bei jedem Build.

**Weitere technische Schulden (nach Schweregrad):**

| Schulden | Schweregrad | Maßnahme |
|---|---|---|
| Login per Header `X-User-Id`: Jeder kann sich als Admin ausgeben | Kritisch | Echten Login (z. B. JWT) einbauen, bevor die App erreichbar ist |
| SQL-Repositories ohne Tests | Hoch | Tests gegen echte PostgreSQL in der CI (kommt später?) |
| Versionen in `requirements.txt` nicht festgelegt | Mittel | Versionen festlegen (Build-Management-Übung kommt noch?) |
| Veralteter TestClient (`httpx`-Warnung von Starlette) | Mittel | Auf `httpx2` umstellen, sobald FastAPI es unterstützt? |
| Nicht umgesetzt aus Übung 4: Klassen `Email`/`ISBN`, Beiträge löschen | Mittel | Im Team entscheiden, ob und wann nachgeholt |
| `DiscussionThread.open` mit 5 Parametern | Gering | Siehe Aufgabe 1 |
| `to_page()` in `shared/book_position.py` wird nur von Tests genutzt (ungenutzter Code, schon im Ausgangsstand) | Gering | Behalten: vorgesehen für den Spoiler-Platzhalter („Enthält Inhalte aus Seite …“), der die Thread-Position in die Seite der eigenen Ausgabe umrechnen muss. Entfernen, falls die Anzeige anders gelöst wird. |
| 26 zu lange Zeilen, 5 Formatierungsbefunde | Gering | `ruff format` / `ruff --fix` |

**Behoben:** Rundungsfehler im Spoiler-Schutz, doppelte Spoiler-Regel, Magic Number 1000, dreifach duplizierter `try/except`-Block, abgewählte und ausgelassene Tests in der CI.
