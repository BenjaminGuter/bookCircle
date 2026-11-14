# BookCircle – Domain-Driven Design und Event Storming

**Modul:** Moderne Softwareentwicklung **Projekt:** BookCircle – Plattform für Lesekreise mit kapitelbezogenen Diskussionen und Spoiler-Schutz **Team:** Jana-Kristin Petersen, Benjamin Guter, Maximilian Mozr Martens **Datum:** 12.11.2026

---

## Inhaltsverzeichnis

1. Event Storming  
2. Domänenmodell  
3. Bounded Contexts  
4. Entitäten und Aggregates  
5. Domain Services und Repositories  
6. Implementierungsstrategie

---

## 1\. Event Storming

### 1.1 Durchführung

Das Event Storming haben wir als Team am \[Datum\] mit \[Namen\] in Miro durchgeführt. Wir haben zuerst frei Domain Events gesammelt, sie chronologisch geordnet, anschließend Commands, Akteure, Aggregates und Policies ergänzt und offene Fragen als Hot Spots markiert.

![Abbildung 1: Event-Storming-Board in Miro](bilder/event-storming.png)

*Abbildung 1: Ergebnis der Event-Storming-Session (Miro-Board).*

**Legende der Sticky Notes**

| Farbe | Bedeutung |
| :---- | :---- |
| Orange | Domain Event (Vergangenheit) |
| Blau | Command (Aktion, die ein Event auslöst) |
| Gelb, klein | Akteur / Rolle |
| Gelb, groß | Aggregate |
| Lila | Policy („Wenn Event, dann Command“) |
| Pink | Hot Spot (offene Frage) |

### 1.2 Identifizierte Events in zeitlicher Reihenfolge

| Nr. | Phase | Domain Event | Command | Akteur | Aggregate |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | Identität | Nutzer registriert | Registrieren | Leser | User |
| 2 | Identität | Nutzer angemeldet | Anmelden | Leser | User |
| 3 | Katalog | Buch in Katalog aufgenommen | Buch anlegen | Admin / System | Book |
| 4 | Katalog | Kapitel zu Buch hinzugefügt | Kapitel anlegen | Admin / System | Book |
| 5 | Bibliothek | Regal erstellt | Regal anlegen | Leser | Shelf |
| 6 | Bibliothek | Buch zu Regal hinzugefügt | Buch ins Regal legen | Leser | Shelf |
| 7 | Bibliothek | Lesestatus geändert | Status setzen | Leser | Shelf |
| 8 | Bibliothek | Buch aus Regal entfernt | Buch entfernen | Leser | Shelf |
| 9 | Lesekreis | Lesekreis gegründet | Lesekreis gründen | Leser (Gründer) | ReadingCircle |
| 10 | Lesekreis | Leseplan festgelegt | Leseplan setzen | Gründer | ReadingCircle |
| 11 | Lesekreis | Mitglied beigetreten | Beitreten | Leser | ReadingCircle |
| 12 | Lesekreis | Mitglied ausgetreten | Austreten | Mitglied | ReadingCircle |
| 13 | Fortschritt | Buch fertig gelesen | (Folge von Nr. 7 beim letzten Kapitel) | System | ReadingCircle |
| 14 | Diskussion | Diskussions-Thread zu Kapitel eröffnet | Thread eröffnen | Mitglied | DiscussionThread |
| 15 | Diskussion | Beitrag veröffentlicht | Beitrag schreiben | Mitglied | DiscussionThread |
| 16 | Diskussion | Beitrag gelöscht | Beitrag löschen | Autor / Gründer | DiscussionThread |

1.3 Policies

- **P1:** Wenn *Lesefortschritt aktualisiert*, dann wird der bekannte Fortschritt des Mitglieds im Context Discussion aktualisiert. Dadurch werden zuvor verborgene Beiträge und Threads bis zu diesem Kapitel sichtbar.  
- **P2:** Wenn *Lesefortschritt aktualisiert* und das letzte Kapitel erreicht ist, dann entsteht das Event *Buch fertig gelesen*.  
- **P3:** Wenn *Buch fertig gelesen*, dann wird der Lesestatus des Buchs im Regal des Nutzers auf „Gelesen“ gesetzt (Übergang von Reading Circles zu Library).

### 1.4 Hot Spots und getroffene Entscheidungen

| Offene Frage | Entscheidung |
| :---- | :---- |
| Darf der Lesefortschritt sinken? | Ja, der Lesefortschritt kann auch sinken.&nbsp; |
| Gilt der Spoiler-Schutz auch für Thread-Titel? | Ja, der gesamte Thread ist bis zum Erreichen des Kapitels verborgen. Evtl. über Warnung und Abfragebestätigung kann es sichtbar gemacht werden. |
| Darf man in einem Thread schreiben, dessen Kapitel man noch nicht erreicht hat? | Nein. |
| Wer darf Lesekreise moderieren? | Zunächst nur der Gründer und Admins. |
| Woher stammen die Kapitelinformationen? | Zunächst manuelle Pflege im Katalog. Eine externe Datenquelle wäre später über eine Anti-Corruption-Schicht anzubinden. |

---

## 2\. Domänenmodell

Aus den Events leiten wir folgende Kernkonzepte ab.

- **Entitäten:** User, Book, Chapter, Author, ShelfEntry, Membership, Post  
- **Value Objects:** Email, ISBN, ReadingStatus, ReadingPlan  
- **Aggregate Roots:** User, Book, Author, Shelf, ReadingCircle, DiscussionThread  
- **Read Model:** MemberProgress (im Context Discussion)

![Abbildung 2: Klassendiagramm des Domänenmodells](bilder/klassendiagramm.png)

*Abbildung 2: Domänenmodell als Klassendiagramm, gruppiert nach Bounded Contexts. Verweise zwischen Contexts bestehen nur über IDs (z. B. `book_id`, `owner_id`) und sind deshalb nicht als Linien eingezeichnet.*

**Notation:** Eine Linie mit gefüllter Raute (Komposition) bedeutet, dass ein Objekt nur innerhalb seines Aggregates existiert. Ein einfacher Pfeil bedeutet, dass eine Klasse ein Value Object verwendet.

---

## 3\. Bounded Contexts

### 3.1 Übersicht

| Context | Verantwortung | Zentrale Begriffe | Subdomain |
| :---- | :---- | :---- | :---- |
| Identity | Registrierung, Login, Nutzerprofil | User, Email | Generic |
| Catalog | Bücher, Autoren und Kapitel, Suche und Filter | Book, Author, Chapter | Supporting |
| Library | Persönliche Regale und Lesestatus | Shelf, ShelfEntry, ReadingStatus | Supporting |
| Reading Circles | Lesekreise, Mitgliedschaften, Leseplan, Fortschritt | ReadingCircle, Membership | **Core** |
| Discussion | Kapitelbezogene Threads und Beiträge mit Spoiler-Schutz | DiscussionThread, Post | **Core** |

**Begründung der Trennung:** Der Begriff „Mitglied“ hat in den Contexts unterschiedliche Bedeutungen. In Reading Circles ist ein Mitglied jemand mit Fortschritt und Leseplan. In Discussion ist es jemand, der bis Kapitel *n* gelesen hat und deshalb Beiträge sehen darf. Beide Modelle haben eigene Regeln und ändern sich aus unterschiedlichen Gründen. Die Kern-Subdomains Reading Circles und Discussion enthalten die fachliche Besonderheit von BookCircle (kapitelbezogener Spoiler-Schutz), die übrigen Contexts sind unterstützend oder generisch.

### 3.2 Context Map

![Abbildung 3: Context Map](bilder/context-map.png)

*Abbildung 3: Beziehungen zwischen den Bounded Contexts.*

| Upstream | Downstream | Beziehung | Austausch |
| :---- | :---- | :---- | :---- |
| Identity | Library, Reading Circles, Discussion | Open Host Service (Published Language: `UserId`) | UserId (UUID) |
| Catalog | Library, Reading Circles | Customer/Supplier | BookId, Kapitelanzahl |
| Reading Circles | Discussion | Customer/Supplier über Events | Event *Lesefortschritt aktualisiert* |
| Reading Circles | Library | Customer/Supplier über Events | Event *Buch fertig gelesen* |

Discussion hält ein eigenes **Read Model** `MemberProgress(circle_id, user_id, chapter)`, das per Event aktualisiert wird. Dadurch muss Discussion nicht direkt bei Reading Circles nachfragen und bleibt unabhängig testbar.

---

## 4\. Entitäten und Aggregates

### 4.1 Identity

**User** (Aggregate Root)

- Attribute: `id`, `email: Email`, `display_name`, `password_hash`, `created_at`  
- Methoden: `register(...)`, `change_password(...)`, `rename(...)`  
- Invarianten: E-Mail-Format gültig, Anzeigename nicht leer  
- Beziehungen: verwendet das Value Object `Email`

### 4.2 Catalog

**Book** (Aggregate Root) mit **Chapter** (Entity)

- Attribute Book: `id`, `title`, `isbn: ISBN | None`, `author_ids: list[UUID]`, `chapters: list[Chapter]`  
- Attribute Chapter: `number`, `title`  
- Methoden: `add_chapter(title)`, `rename(title)`  
- Invarianten: Kapitelnummern lückenlos ab 1, mindestens ein Autor  
- Beziehungen: Book enthält 1..\* Chapter (Komposition), verweist auf Autoren per ID

**Author** (Aggregate Root)

- Attribute: `id`, `name`  
- Methoden: `rename(name)`

### 4.3 Library

**Shelf** (Aggregate Root) mit **ShelfEntry** (Entity)

- Attribute Shelf: `id`, `owner_id`, `name`, `entries: list[ShelfEntry]`  
- Attribute ShelfEntry: `book_id`, `status: ReadingStatus`, `added_at`  
- Methoden: `add_book(book_id)`, `remove_book(book_id)`, `change_status(book_id, status)`  
- Invarianten: ein Buch höchstens einmal pro Regal. Die Eindeutigkeit des Regalnamens pro Nutzer wird im Application Service über das Repository geprüft.  
- Beziehungen: Shelf enthält 0..\* ShelfEntry (Komposition), verweist auf User und Book per ID

### 4.4 Reading Circles

**ReadingCircle** (Aggregate Root) mit **Membership** (Entity)

- Attribute ReadingCircle: `id`, `name`, `owner_id`, `book_id`, `total_chapters`, `memberships`, `reading_plan: ReadingPlan`  
- Attribute Membership: `user_id`, `progress: int`, `joined_at`  
- Value Object ReadingPlan: `start`, `chapters_per_week`  
- Methoden: `found(...)`, `join(user_id)`, `leave(user_id)`, `update_progress(user_id, chapter)`, `set_reading_plan(plan)`  
- Invarianten: Fortschritt zwischen 0 und `total_chapters` und nie sinkend, Nutzer nur einmal Mitglied, der Gründer kann erst austreten, wenn er allein im Lesekreis ist  
- Events: `ReadingProgressUpdated`, `BookFinished`  
- Beziehungen: ReadingCircle enthält 1..\* Membership (Komposition), verweist auf Book und User per ID

### 4.5 Discussion

**DiscussionThread** (Aggregate Root) mit **Post** (Entity)

- Attribute DiscussionThread: `id`, `circle_id`, `chapter`, `title`, `posts: list[Post]`  
- Attribute Post: `id`, `author_id`, `text`, `created_at`  
- Methoden: `open(...)`, `add_post(author_id, text, author_progress)`, `visible_posts(viewer_progress)`, `delete_post(post_id, by_user_id)`  
- Invarianten: Schreiben und Lesen nur mit Fortschritt ≥ Kapitel des Threads  
- Read Model: `MemberProgress(circle_id, user_id, chapter)`  
- Beziehungen: DiscussionThread enthält 0..\* Post (Komposition), verweist auf ReadingCircle per ID

### 4.6 Begründung der Aggregate-Grenzen

Ein Aggregate wird in einer Transaktion geändert und schützt seine eigenen Invarianten. Ein Lesekreis mit seinen Mitgliedschaften bildet eine Einheit, weil der Fortschritt dort konsistent sein muss. Ein Thread mit seinen Beiträgen bildet ebenfalls eine Einheit. Zwischen Aggregates wird ausschließlich per ID verwiesen, damit sie unabhängig voneinander geladen und gespeichert werden können.

---

## 5\. Domain Services und Repositories

### 5.1 Domain Services

Domain Services enthalten Fachlogik, die nicht natürlich zu einer einzelnen Entity gehört. Application Services (Use Cases) orchestrieren nur den Ablauf und enthalten keine Fachregeln.

| Service | Context | Methoden | Zweck |
| :---- | :---- | :---- | :---- |
| SpoilerPolicy | Discussion | `is_unlocked(chapter, viewer_progress)`, `filter_threads(threads, viewer_progress)` | Zentrale Sichtbarkeitsregel, auch für Abfragen über mehrere Threads |
| CircleProgressService | Reading Circles | `group_progress(circle)`, `members_behind(circle, chapter)` | Auswertung über mehrere Mitgliedschaften hinweg |

Technische Ports wie der `PasswordHasher` (Identity) sind Schnittstellen in der Domain-Schicht, deren Implementierung in der Infrastruktur liegt. Sie sind keine Domain Services.

### 5.2 Repositories

Pro Aggregate Root gibt es ein Repository. Die Interfaces liegen in der Domain-Schicht, die Implementierungen in der Infrastruktur.

| Repository | Context | Methoden |
| :---- | :---- | :---- |
| UserRepository | Identity | `add(user)`, `get(id)`, `get_by_email(email)` |
| BookRepository | Catalog | `add(book)`, `get(id)`, `search(query, filters)`, `save(book)` |
| AuthorRepository | Catalog | `add(author)`, `get(id)` |
| ShelfRepository | Library | `add(shelf)`, `get(id)`, `list_by_owner(user_id)`, `save(shelf)` |
| ReadingCircleRepository | Reading Circles | `add(circle)`, `get(id)`, `list_by_member(user_id)`, `save(circle)` |
| DiscussionThreadRepository | Discussion | `add(thread)`, `get(id)`, `list_by_circle(circle_id)`, `save(thread)` |
| MemberProgressRepository | Discussion | `get(circle_id, user_id)`, `upsert(circle_id, user_id, chapter)` |

Auf Entities innerhalb eines Aggregates (z. B. `Post`, `Membership`) wird nie direkt zugegriffen.

---

## 6\. Implementierungsstrategie

### 6.1 Prinzipien

1. **Domain zuerst, Framework zuletzt.** Der Domain-Code ist reines Python (Dataclasses) ohne Imports von FastAPI oder SQLAlchemy.  
2. **Ein Package pro Bounded Context**, intern in die Schichten `domain`, `application`, `infrastructure` und `api` gegliedert. Abhängigkeiten zeigen nur nach innen.  
3. **Repositories als Protocol** in der Domain. Zum Testen gibt es In-Memory-Implementierungen, später SQLAlchemy.  
4. **Domain Events** werden im Aggregate gesammelt und nach dem Speichern von einem einfachen In-Process-Event-Bus an andere Contexts verteilt, etwa `ReadingProgressUpdated` an Discussion.  
5. **Test-driven:** zuerst der Domain-Unit-Test, dann die Implementierung.

### 6.2 Ordnerstruktur (Backend)

```
backend/app/
  identity/
  catalog/
  library/
  circles/
    domain/          # Entities, Value Objects, Events, Repository-Protocol, Domain Services
    application/     # Use Cases
    infrastructure/  # SQLAlchemy- und In-Memory-Repositories
    api/             # FastAPI-Router, Pydantic-Schemas
  discussion/
  shared/            # Event-Bus, DomainEvent-Basisklasse, DomainError
  main.py
```

### 6.3 Teststrategie

| Ebene | Gegenstand | Umsetzung |
| :---- | :---- | :---- |
| Domain-Unit-Tests | Invarianten und Methoden der Aggregates | pytest, ohne Datenbank und Framework |
| Application-Tests | Use Cases | pytest mit In-Memory-Repositories |
| Integrationstests | SQLAlchemy-Repositories | pytest mit Test-Datenbank |
| API-Tests | HTTP-Endpunkte | FastAPI TestClient |

Die CI-Pipeline führt `pytest` bei jedem Push aus.

### 6.4 Beispiel: Domain Model in Python

Die Beispiele setzen Python ab Version 3.10 voraus (`kw_only` bei Dataclasses).

**Aggregate ReadingCircle mit Domain Events (`circles/domain`)**

```py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class DomainError(Exception):
    pass


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, kw_only=True)
class ReadingProgressUpdated(DomainEvent):
    circle_id: UUID
    user_id: UUID
    chapter: int


@dataclass(frozen=True, kw_only=True)
class BookFinished(DomainEvent):
    circle_id: UUID
    user_id: UUID
    book_id: UUID


@dataclass
class Membership:
    user_id: UUID
    progress: int = 0


@dataclass
class ReadingCircle:
    id: UUID
    name: str
    owner_id: UUID
    book_id: UUID
    total_chapters: int
    memberships: dict[UUID, Membership] = field(default_factory=dict)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def found(cls, name: str, owner_id: UUID, book_id: UUID, total_chapters: int):
        if total_chapters < 1:
            raise DomainError('Ein Buch braucht mindestens ein Kapitel')
        circle = cls(uuid4(), name, owner_id, book_id, total_chapters)
        circle.memberships[owner_id] = Membership(owner_id)
        return circle

    def join(self, user_id: UUID) -> None:
        if user_id in self.memberships:
            raise DomainError('Bereits Mitglied')
        self.memberships[user_id] = Membership(user_id)

    def leave(self, user_id: UUID) -> None:
        if user_id not in self.memberships:
            raise DomainError('Kein Mitglied dieses Lesekreises')
        if user_id == self.owner_id and len(self.memberships) > 1:
            raise DomainError('Der Gründer kann erst austreten, wenn er allein ist')
        del self.memberships[user_id]

    def update_progress(self, user_id: UUID, chapter: int) -> None:
        membership = self.memberships.get(user_id)
        if membership is None:
            raise DomainError('Kein Mitglied dieses Lesekreises')
        if not 0 <= chapter <= self.total_chapters:
            raise DomainError('Kapitel außerhalb des Buchs')
        if chapter < membership.progress:
            raise DomainError('Fortschritt darf nicht sinken')
        membership.progress = chapter
        self._events.append(
            ReadingProgressUpdated(circle_id=self.id, user_id=user_id, chapter=chapter)
        )
        if chapter == self.total_chapters:
            self._events.append(
                BookFinished(circle_id=self.id, user_id=user_id, book_id=self.book_id)
            )

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events
```

**Aggregate DiscussionThread mit Spoiler-Regel (`discussion/domain`)**

```py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


def is_unlocked(chapter: int, viewer_progress: int) -> bool:
    return viewer_progress >= chapter


@dataclass
class Post:
    id: UUID
    author_id: UUID
    text: str
    created_at: datetime


@dataclass
class DiscussionThread:
    id: UUID
    circle_id: UUID
    chapter: int
    title: str
    posts: list[Post] = field(default_factory=list)

    def add_post(self, author_id: UUID, text: str, author_progress: int) -> Post:
        if not is_unlocked(self.chapter, author_progress):
            raise DomainError('Kapitel noch nicht gelesen')
        post = Post(uuid4(), author_id, text, datetime.now(timezone.utc))
        self.posts.append(post)
        return post

    def visible_posts(self, viewer_progress: int) -> list[Post]:
        if not is_unlocked(self.chapter, viewer_progress):
            return []
        return list(self.posts)
```

Die Funktion `is_unlocked` ist die einzige Stelle, an der die Spoiler-Regel steht. Sie wird sowohl vom Aggregate als auch vom Domain Service `SpoilerPolicy` verwendet.

**Beispiel-Tests (`tests/circles/test_circle.py`)**

```py
import pytest
from uuid import uuid4


def make_circle():
    return ReadingCircle.found('Krimi-Runde', uuid4(), uuid4(), total_chapters=10)


def test_progress_emits_event():
    circle = make_circle()
    circle.update_progress(circle.owner_id, 3)
    events = circle.pull_events()
    assert len(events) == 1 and events[0].chapter == 3


def test_progress_cannot_decrease():
    circle = make_circle()
    circle.update_progress(circle.owner_id, 5)
    with pytest.raises(DomainError):
        circle.update_progress(circle.owner_id, 4)


def test_last_chapter_finishes_book():
    circle = make_circle()
    circle.update_progress(circle.owner_id, 10)
    assert any(isinstance(e, BookFinished) for e in circle.pull_events())
```

### 6.5 Vorgehen in der Implementierung

1. Package-Struktur anlegen, `shared/` mit `DomainEvent`, `DomainError` und Event-Bus.  
2. Context **Reading Circles** per Test-driven Development umsetzen, da er den Kern der Anwendung bildet.  
3. Context **Discussion** mit dem Spoiler-Schutz ergänzen und per Event an den Fortschritt anbinden.  
4. In-Memory-Repositories bereitstellen, danach FastAPI-Router und SQLAlchemy-Repositories.  
5. Die übrigen Contexts (Identity, Catalog, Library) folgen nach demselben Schema.