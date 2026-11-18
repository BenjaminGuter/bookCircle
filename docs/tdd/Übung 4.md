# 1\. Überprüfung und Optimierung der Implementierungsstrategie

Im Folgenden wurde unser Domain Modell an Gemini gegeben um es zu analysieren. Es wurden folgende Punkte bemängelt:

## 1.1 LLM Analyse

### 1.1.1 Inkonsistente Einheiten (Kapitel vs. Seiten):&nbsp;

Deine Attribute sprechen von `ChapterNumber` und `totalChapters`, deine Methoden (`advance_to(page)`, `correct_to(page)`) erwarten jedoch **Seiten (`page`)**. Das führt zu Verwirrung und Rechenfehlern bei der Prozentangabe. Entscheide dich konsequent für eine Einheit (z. B. `currentPage` / `totalPages` oder passe die Methoden auf `chapter` an) – oder kapsle den Fortschritt direkt in ein eigenes **Value Object** (z. B. `Progress(current, total)`).

### 1.1.2 Fehlende/Unklare Fachliche Invarianten:&nbsp;

Deine aktuelle Formulierung beschreibt eher _wann_ etwas berechnet wird,nicht _was immer wahr sein muss_. Echte DDD-Invarianten für dieses Aggregate wären:

- `currentPage` darf niemals kleiner als `0` sein.
- `currentPage` darf `totalPages` nicht überschreiten.
- Bei `advance_to(newPage)` muss gelten: `newPage >= currentPage` (das unterscheidet die Methode erst fachlich sinnvoll von `correct_to()`, wo auch ein Zurückspringen erlaubt ist).

### 1.1.3 Fehlende Identität der Aggregate Root:&nbsp;

Als Aggregate Root benötigt `ReadingProgress` eine eigene Identität (z. B.`ReadingProgressID`), sofern die Kombination aus `UserID` und `BookID` nicht explizit als zusammengesetzter Primärschlüssel definiert ist. Zudem sollten `UserID` und `BookID` als Referenzen (Value Objects) statt als direkte Objektreferenzen gehalten werden, um die Aggregate sauber voneinander zu entkoppeln.

### 1.1.4 Beziehungskardinalität prüfen:&nbsp;

Ein Buch kann von _vielen_ Nutzer:innen gelesen werden und eine Nutzer:in liest *viele*Bücher. `ReadingProgress` ist somit die Auflösungstabelle einer **n:m-Beziehung** zwischen `User` und `Book` – jedes `ReadingProgress`\-Objekt referenziert genau einen User und genau ein Buch (jeweils 1:1 aus Sicht des Fortschritts, aber 1:n aus Sicht von User und Book).

### 1.1.5 Ubiquitous Language & Naming:&nbsp;

Achte auf einheitliche Schreibweisen im Code/Modell: `UserID` (PascalCase) vs.`totalChapters` (camelCase) vs. `advance_to` (snake_case). Ein einheitlicher Stil erhöht die Lesbarkeit im Team enorm.

### 1.1.6 Event-Inkonsistenz im ReadingCircle (4.4):

`ReadingCircle` wirft die Events `ReadingProgressUpdated` und `BookFinished`. Da `ReadingCircle` aber primär für die Gruppenorganisation zuständig ist, wäre ein Event wie `MemberProgressUpdated` fachlich präziser, um Verwechslungen mit dem separaten `ReadingProgress`\-Aggregate (4.6) zu vermeiden.

## 1.2 Ergebnis

Die LLM Analyse zeigt einige Schwächen von unserem DDD-Modell. Als low-hanging fruit können wir hier zuerst die Einhaltung der Namenskonventionen gewährleisten. Darüber hinaus schlichen sich in unseren Gedanken zum Reading-Progress einige Fehler ein. Die Invariante war falsch ausgelegt und die Datenbankbeziehung wird nun als 1:n Beziehung der User zum Readingprogress gelesen. Die Gedanken zur Benennung der Events im Reading Circle und dem normalen Lesen der Userinnen werden aufgegriffen und umgesetzt. Hier handelt es sich um zwei unterschiedliche Fortschritts-Formen, welche durch die ähnliche Benennung nicht gut auseinanderzuhalten wären.

# 2\. LLm \- Testfälle

## 2.1 Prompt:

Du entwickelst eine Anwendung zum gemeinsamen Teilen und lesen von Büchern. Zum Testing solltest du bitte folgendes tun:

o Happy-Path-Tests

o Edge-Cases (Grenzfälle)

o Negative Tests (ungültige Eingaben)

Im Folgenden erhältst du unsere Entitäten und Aggregates. Bewerte diese und schlage mir für die kritischsten Funktionen jeweils einen Python test Case.

\[Entitäten und Aggregates aus DDD-3\]

## 2.2 Lösungsvorschläge & Code

### **2.2.3 Kritischste Funktionen & Python Test Cases (`pytest`)**

Die kritischsten Stellen im System sind **komplexe Zustandsübergänge mit mehreren Invarianten** sowie **Berechtigungs- und Spoiler-Grenzen**. Nachfolgend findest du für die 4 kritischsten Aggregate jeweils eine Test-Suite mit **Happy Path**, **Edge Case** und **Negative Test**.

_(Annahme: Fachliche Regelverstöße werfen eine spezifische `DomainError`\-Exception.)_

#### **A. ReadingCircle: Fortschritt & Events (`update_progress`)**

_Warum kritisch?_ Hier greifen gleich drei Regeln: Obergrenze (`total_chapters`), Monotonie (kein Zurückfallen) und das Auslösen der Domain Events (`ReadingProgressUpdated`, `BookFinished`).

Python

```py
import pytest
from uuid import uuid4
from domain.reading_circle import ReadingCircle, ReadingPlan, ReadingProgressUpdated, BookFinished
from domain.exceptions import DomainError

def create_sample_circle(total_chapters: int = 10):
    owner_id = uuid4()
    member_id = uuid4()
    circle = ReadingCircle.found(
        name="Sci-Fi Club",
        owner_id=owner_id,
        book_id=uuid4(),
        total_chapters=total_chapters,
        reading_plan=ReadingPlan(start="2026-12-01", chapters_per_week=2)
    )
    circle.join(member_id)
    return circle, owner_id, member_id

class TestReadingCircleProgress:
    # 1. HAPPY PATH: Normaler Fortschritt löst Event aus
    def test_update_progress_happy_path(self):
        circle, _, member_id = create_sample_circle(total_chapters=10)

        circle.update_progress(user_id=member_id, chapter=4)

        membership = circle.get_membership(member_id)
        assert membership.progress == 4
        assert any(isinstance(e, ReadingProgressUpdated) and e.chapter == 4 for e in circle.domain_events)
        assert not any(isinstance(e, BookFinished) for e in circle.domain_events)

    # 2. EDGE CASE: Erreichen des exakt letzten Kapitels triggert BookFinished
    def test_update_progress_exact_last_chapter_triggers_finished(self):
        circle, _, member_id = create_sample_circle(total_chapters=10)

        circle.update_progress(user_id=member_id, chapter=10)

        assert circle.get_membership(member_id).progress == 10
        assert any(isinstance(e, BookFinished) and e.user_id == member_id for e in circle.domain_events)

    # 3. NEGATIVE TEST: Fortschritt darf nicht sinken (Monotonie-Invariante)
    def test_update_progress_cannot_decrease(self):
        circle, _, member_id = create_sample_circle(total_chapters=10)
        circle.update_progress(user_id=member_id, chapter=5)

        with pytest.raises(DomainError, match="Fortschritt darf nicht sinken"):
            circle.update_progress(user_id=member_id, chapter=4)
```

B. ReadingCircle: Gründer-Austrittsregel (`leave`)

_Warum kritisch?_ Ein verwaister Lesekreis ohne aktiven Gründer würde das Aggregate in einen ungültigen Zustand überführen.

Python

```py
class TestReadingCircleLeave:
    # 1. HAPPY PATH: Reguläres Mitglied verlässt den Kreis jederzeit
    def test_regular_member_can_leave_anytime(self):
        circle, owner_id, member_id = create_sample_circle()

        circle.leave(member_id)

        assert len(circle.memberships) == 1
        assert circle.memberships[0].user_id == owner_id

    # 2. EDGE CASE: Gründer tritt aus, nachdem alle anderen gegangen sind
    def test_owner_can_leave_when_alone(self):
        circle, owner_id, member_id = create_sample_circle()
        circle.leave(member_id)

        circle.leave(owner_id)  # Jetzt ist der Gründer allein -> erlaubt

        assert len(circle.memberships) == 0

    # 3. NEGATIVE TEST: Gründer versucht auszutreten, während noch Mitglieder da sind
    def test_owner_cannot_leave_while_other_members_exist(self):
        circle, owner_id, _ = create_sample_circle()

        with pytest.raises(DomainError, match="Gründer kann erst austreten, wenn er allein ist"):
            circle.leave(owner_id)
```

C. DiscussionThread: Spoiler-Schutz beim Lesen & Schreiben (`add_post`, `visible_posts`)

_Warum kritisch?_ Kernfeature der Anwendung. Wenn die Grenzwerte (`progress == chapter` vs. `progress < chapter`) falsch implementiert sind, werden Nutzer gespoilert.

Python

```py
from domain.discussion import DiscussionThread

class TestDiscussionSpoilerProtection:
    # 1. HAPPY PATH: Nutzer mit höherem Fortschritt darf posten und lesen
    def test_add_and_read_post_with_sufficient_progress(self):
        thread = DiscussionThread.open(circle_id=uuid4(), chapter=5, title="Kapitel 5 Twist!")
        author_id = uuid4()

        thread.add_post(author_id=author_id, text="Was für ein Ende!", author_progress=7)
        visible = thread.visible_posts(viewer_progress=6)

        assert len(visible) == 1
        assert visible[0].text == "Was für ein Ende!"

    # 2. EDGE CASE: Exakter Gleichstand (progress == chapter) muss erlaubt sein
    def test_boundary_exact_chapter_match_allows_reading_and_writing(self):
        thread = DiscussionThread.open(circle_id=uuid4(), chapter=5, title="Kapitel 5 Twist!")

        thread.add_post(author_id=uuid4(), text="Gerade beendet!", author_progress=5)
        visible = thread.visible_posts(viewer_progress=5)

        assert len(visible) == 1

    # 3. NEGATIVE TEST: Nutzer mit geringerem Fortschritt wird beim Schreiben blockiert & sieht keine Posts
    def test_insufficient_progress_blocks_posting_and_hides_posts(self):
        thread = DiscussionThread.open(circle_id=uuid4(), chapter=5, title="Kapitel 5 Twist!")
        thread.add_post(author_id=uuid4(), text="Spoiler!", author_progress=5)

        # Lesen liefert leere Liste (kein Spoiler)
        assert thread.visible_posts(viewer_progress=4) == []

        # Schreiben wirft DomainError
        with pytest.raises(DomainError, match="Fortschritt reicht für dieses Kapitel nicht aus"):
            thread.add_post(author_id=uuid4(), text="Darf ich noch nicht", author_progress=4)
```

D. ReadingProgress: Vorwärts-Lesen vs. Korrektur (`advanceTo`, `correctTo`)

_Warum kritisch?_ Die Trennung zweier Methoden für denselben Wert (`currentPage`) mit unterschiedlichen Invarianten ist fehleranfällig (insbesondere bei Seite 0 und `totalPages`).

Python

```py
from domain.reading_progress import ReadingProgress

class TestReadingProgress:
    # 1. HAPPY PATH: Fortschritt vorwärts bewegen und Prozentwert prüfen
    def test_advance_to_increases_progress_and_calculates_percentage(self):
        rp = ReadingProgress(user_id=uuid4(), book_id=uuid4(), current_page=0, total_pages=200)

        rp.advance_to(50)

        assert rp.current_page == 50
        assert rp.percentage() == 25.0

    # 2. EDGE CASE: Zurücksetzen auf 0 über correctTo erlaubt, während advanceTo scheitert
    def test_correct_to_allows_resetting_to_zero_and_max_page(self):
        rp = ReadingProgress(user_id=uuid4(), book_id=uuid4(), current_page=120, total_pages=200)

        rp.correct_to(0)
        assert rp.current_page == 0

        rp.correct_to(200)
        assert rp.current_page == 200
        assert rp.percentage() == 100.0

    # 3. NEGATIVE TEST: advanceTo darf nicht rückwärts gehen und totalPages nicht überschreiten
    def test_advance_to_rejects_backward_or_overflow_pages(self):
        rp = ReadingProgress(user_id=uuid4(), book_id=uuid4(), current_page=100, total_pages=200)

        with pytest.raises(DomainError):
            rp.advance_to(99)   # Rückwärts verboten

        with pytest.raises(DomainError):
            rp.advance_to(201)  # Über totalPages verboten
```

&nbsp;

## 2.3 Kritische Bewertung der Tests

Die generierten Tests stellen jeweils einen der geforderten Aspekte dar. Es gibt somit zu jedem, vom LLM als kritisch bewerteten Aspekt drei Tests, die gemacht werden können.

### 2.3.1 A) Reading Circle update Progress

Das LLM sieht hier Grund zur Annahme, dass der Fortschritt des Programms nicht sinken darf. Dies ist jedoch nicht unbedingt der Fall. Ein Reading Circle darf durchaus, auch wenn es untypisch ist, negativen Fortschritt haben. Ein sinnvollerer negativer Test wäre, was passiert, wenn man eine Seitenzahl in den Progress eingibt, die nicht existiert. Eine negative oder zu große Zahl.

### 2.3.2 B) Verwaister Lesekreis

Diese Tests sind umfassend und sinnvoll. Hier ist eine Logik zu etablieren, wie mit einem Verschwinden der Gründer:in umzugehen ist, welcher Person dann die Rechte zu fallen, oder ob diese nur durch Admins weiter verwaltet werden können. Kann ein leerer Lesekreis weiter bestehen?

### 2.3.3 C) Spoiler Schutz

Die Vorgeschlagenen Tests sind auch hier sinnvoll. Ein weiterer Test, welcher als Negativ-Test geeignet sein könnte, wäre zu testen, wie das System mit negativen Seitenzahlen umgeht. Wenn es beispielsweise einen Vorzeichenfehler gibt.

### 2.3.4 D) advance-to und correct-to

Diese Methoden haben wir getrennt, um eindeutige Methodenaufrufe für Fort- und Rückschritte im Buch zu definieren. Daher ist der Test, ob die jeweiligen Methoden eine inverse Operation erlauben, sehr sinnvoll. Auch hier sollte getestet werden, ob die Seitenzahlen jeweils im erlaubten Spektrum bleiben. Dass keine Vorzeichenfehler entstehen können, oder Personen auf Seite 300 von 250 sein können.

&nbsp;

## 2.4 RegEx

Vom LLM vorgeschlagene Regular Expressions:

```py
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
DISPLAY_NAME_PATTERN = re.compile(r"^(?!\s*$)[a-zA-Z0-9äöüÄÖÜßàéèêîôûç _-]{2,50}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#._-])[A-Za-z\d@$!%*?&#._-]{10,128}$")
ISBN_PATTERN = re.compile(r"^(?:(?=.{17}$)97[89][-]?(?:[0-9][- ]?){9}[0-9]|(?=.{13}$)(?:[0-9][- ]?){9}[0-9Xx]|97[89][0-9]{10}|[0-9]{9}[0-9Xx])$")
SINGLE_LINE_TITLE_PATTERN = re.compile(r"^(?!\s*$)[^\r\n]{1,150}$")
POST_TEXT_PATTERN = re.compile(r"^(?!\s*$).{1,5000}$", re.DOTALL)
```

&nbsp;

Die vom LLM Vorgeschlagenen Regular Expressions erfüllen nach erstmaligem Testing die Anforderungen an die Validierungslogik. Insbesondere Komplizierte Regular Expressions wie die für das ISBN Pattern lassen sich schneller mit Unterstützung durch LLMs schreiben, als in Eigenarbeit.

# 4\. Test Refaktorisierung

## 4.1 LLM Vorschläge

Zusätzliche Edge-Cases & Fehlerbedingungen:

**Nicht-Mitglieder im `ReadingCircle`:** Was passiert, wenn ein `user_id` Fortschritt melden (`update_progress`) oder austreten (`leave`) will, der gar kein Mitglied ist?

**Doppelter Beitritt (`join`):** Ein Nutzer tritt dem Lesekreis zweimal bei (Invariante: „Nutzer nur einmal Mitglied“).

**Ungültige Initialisierung:** `ReadingProgress` mit `total_pages <= 0` oder `current_page < 0` bzw. `current_page > total_pages`.

**Post-Löschung & leerer Text:** `delete_post` durch einen Unbefugten oder für eine nicht existierende `post_id` sowie `add_post`mit reinem Whitespace (`" \n "`).

Identifizierte Code-Smells (in der bisherigen Testsuite & Implementierung):

**Magic Numbers & Duplizierter Setup-Code:** Statt `create_sample_circle()` manuell in fast jedem Test aufzurufen, sollte eine echte `@pytest.fixture` verwendet werden.  
test_domain_v2.py

**Inkonsistente Rest-Begriffe:** Durch das Suchen-und-Ersetzen entstanden grammatikalische Unsauberkeiten in Kommentaren/Strings (z. B. _„letzten Seites“_, _„dieses Seite“_).  
test_domain_v2.py

**Sprach-/Feature-Hinweis (Python vs. Java):** In der Aufgabenstellung werden „Java-Features“ erwähnt – da euer Projekt in **Python** umgesetzt ist, wenden wir stattdessen idiomatische **Python-Features** an (`@pytest.fixture`, `@dataclass(frozen=True)`, Type Hints, `re.fullmatch` statt `re.match`).  
Bildschirmfoto 2026-11-16 um 22.24.21.png+ 1

**Over-Engineering (abgelehntes Refactoring):** Eine Auslagerung der Testdaten in externe JSON-Dateien wäre für diese kompakte Domain-Testsuite überdimensioniert und würde die Lesbarkeit verschlechtern.

&nbsp;

## 4.2 Umgesetzte Änderungen

Code-Smells behoben:

- Der ungenutzte Import `from fastapi.testclient import TestClient` wurde entfernt (reine Domain-Unit-Tests benötigen keinen HTTP-Client).
- Die manuelle Hilfsfunktion `create_sample_circle()` wurde in eine echte `@pytest.fixture` (`sample_circle`) mit Type Hints (`tuple[ReadingCircle, UUID, UUID]`) umgewandelt, um Setup-Duplikation zu beseitigen.
- Grammatikalische Restfehler aus der Umstellung von Kapiteln auf Seiten (_„letzten Seites“_, _„dieses Seite“_) wurden in den Kommentaren und Fehlermeldungen korrigiert.

Neue Edge-Cases & Fehlerbedingungen ergänzt:

- `ReadingCircle`: Idempotenz bei gleicher Seitenzahl (`page == current_page`), Monotonie-Prüfung (Fortschritt sinkt von 6 auf 5), Fortschrittsmeldung durch Nicht-Mitglieder sowie doppelter Beitritt (`join`) / Austritt eines Nicht-Mitglieds (`leave`).
- `DiscussionThread`: Ablehnung von leeren Posts (nur Whitespace) und unbefugtes Löschen fremder Beiträge (`delete_post`).
- `ReadingProgress`: Parametrisierte Prüfung ungültiger Initialwerte (`total_pages <= 0`, `current_page < 0`, `current_page > total_pages`).

## 4.3 Ergebnis

Im Rahmen der Refaktorisierung wurde der ungenutzte `TestClient`\-Import entfernt und die manuelle Setup-Funktion `create_sample_circle` durch eine typisierte `@pytest.fixture` (`sample_circle`) ersetzt, um Code-Duplikation und unnötige Abhängigkeiten abzubauen. Zudem wurden sprachliche Überbleibsel aus der Umstellung auf Seiten bereinigt und die Testsuite um zentrale Randfälle wie idempotente Fortschrittsmeldungen, sinkende Seitenzahlen, doppelte Beitritte, Whitespace-only-Posts, unberechtigte Post-Löschungen sowie ungültige Initialwerte (`total_pages <= 0`) erweitert. Nicht umgesetzt wurde der Vorschlag aus der Aufgabenstellung zur Nutzung spezieller Java-Features, da das Projekt in Python implementiert ist und stattdessen idiomatische Python-Muster (Fixtures, Type Hints, `@pytest.mark.parametrize`) zum Einsatz kamen. Ebenfalls verworfen wurde eine Auslagerung der Testdaten in externe JSON-Dateien, da dies bei reinen Domain-Unit-Tests unnötige Komplexität erzeugt und die direkte Lesbarkeit der Assertions verschlechtert hätte.

# 5\. Modularer Aufbau und CI/CD

### **1\. Modularer Aufbau & Testbarkeit nach Bounded Contexts**

- **Strikte Trennung nach Fachdomänen:** Jeder Bounded Context (_Identity_, _Catalog_, _Reading Circles_, _Discussion_, _Reading Progress_) ist in eigene Module und isolierte Testklassen gekapselt.  
  test_domain_refactored.py
- **Lose Kopplung über IDs:** Da die Aggregate ausschließlich über Value Objects und IDs (`user_id`, `circle_id`) statt über direkte Objektreferenzen verbunden sind, lassen sich die fachlichen Invarianten jedes Kontexts völlig isoliert und ohne aufwendige Datenbank- oder Netzwerk-Mocks testen.  
  test_domain_refactored.py
- **Saubere Test-Architektur:** Wiederkehrende Initialisierungen sind in `@pytest.fixture` (`sample_circle`) ausgelagert, während Eingabevalidierungen über `@pytest.mark.parametrize` gebündelt und übersichtlich gehalten werden.  
  test_domain_refactored.py

### **2\. Ablauf der automatisierten CI-Pipeline (`CI.yml`)**

1. **Auslöser (Trigger):** Die GitHub-Actions-Pipeline startet automatisch bei jedem `push` auf den `main`\-Branch sowie bei jedem `pull_request`.
2. **Umgebung & Setup:** Auf einem `ubuntu-latest`\-Runner wechselt der Job in das `Backend-Verzeichnis,` richtet Python 3.14 (inklusive `pip`\-Cache) ein und installiert alle Pakete aus der `requirements.txt`.
3. **Build-Check:** Vor den Tests verifiziert ein Smoke-Test (`python -c "from app.main import app"`), dass die FastAPI-Anwendung ohne Import- oder Syntaxfehler geladen werden kann.
4. **Testausführung (`pytest`):** Anschließend führt `pytest -v` alle Tests automatisiert aus. Über `--ignore=tests/test_llm.py` und `--deselect ...` werden zwei bekannte Baustellen vorübergehend übersprungen, bis die Anpassungen an der Domänenstruktur abgeschlossen sind.

&nbsp;
