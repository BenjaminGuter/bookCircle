-- BookCircle: ein Postgres-Schema pro Bounded Context.
-- Zwischen Contexts gibt es bewusst KEINE Foreign Keys (Verweise nur per ID,
-- siehe DDD-Doku). Innerhalb eines Aggregates schon (Komposition -> ON DELETE CASCADE).

CREATE SCHEMA identity;
CREATE SCHEMA catalog;
CREATE SCHEMA library;
CREATE SCHEMA reading;
CREATE SCHEMA circles;
CREATE SCHEMA discussion;

-- ───────── Identity ─────────
CREATE TABLE identity.users (
    id            uuid PRIMARY KEY,
    email         text NOT NULL,
    display_name  text NOT NULL CHECK (length(trim(display_name)) > 0),
    password_hash text NOT NULL,
    role          text NOT NULL DEFAULT 'reader' CHECK (role IN ('reader', 'admin')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);
CREATE UNIQUE INDEX users_email_uq ON identity.users (lower(email));

-- ───────── Catalog ─────────
CREATE TABLE catalog.authors (
    id   uuid PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE catalog.books (
    id    uuid PRIMARY KEY,
    title text NOT NULL,
    page_count int NOT NULL CHECK (page_count >= 1),   -- Seitenzahl, Grundlage für den Spoiler-Schutz
    isbn  text UNIQUE CHECK (isbn IS NULL OR isbn ~ '^[0-9]{10}([0-9]{3})?$'),
    -- Cover: Datei liegt im Volume (COVER_DIR), hier nur die Metadaten. Beide NULL = kein Cover.
    cover_file         text,
    cover_content_type text CHECK (cover_content_type IN ('image/jpeg', 'image/png', 'image/webp')),
    CHECK ((cover_file IS NULL) = (cover_content_type IS NULL))
);
CREATE INDEX books_title_idx ON catalog.books (lower(title));

-- Book verweist per ID auf Autoren (Autoren sind eigenes Aggregate -> kein FK auf authors nötig,
-- hier aber unproblematisch, da beides im selben Context liegt)
CREATE TABLE catalog.book_authors (
    book_id   uuid NOT NULL REFERENCES catalog.books(id) ON DELETE CASCADE,
    author_id uuid NOT NULL REFERENCES catalog.authors(id),
    PRIMARY KEY (book_id, author_id)
);

-- ───────── Library ─────────
CREATE TYPE library.reading_status AS ENUM ('want_to_read', 'reading', 'read');

CREATE TABLE library.shelves (
    id       uuid PRIMARY KEY,
    owner_id uuid NOT NULL,                 -- identity.users.id (nur ID)
    name     text NOT NULL,
    UNIQUE (owner_id, name)                 -- Sicherheitsnetz; Regel liegt im Application Service
);

CREATE TABLE library.shelf_entries (
    shelf_id uuid NOT NULL REFERENCES library.shelves(id) ON DELETE CASCADE,
    book_id  uuid NOT NULL,                 -- catalog.books.id (nur ID)
    status   library.reading_status NOT NULL DEFAULT 'want_to_read',
    added_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (shelf_id, book_id)         -- ein Buch höchstens einmal pro Regal
);

-- ───────── Reading Progress (eigener Context, unabhängig vom Lesekreis) ─────────
-- Aggregate ReadingProgress: ein Eintrag pro Nutzer und Buch. Kein Eintrag = noch nicht begonnen (Seite 0).
CREATE TABLE reading.progress (
    user_id           uuid NOT NULL,        -- identity.users.id
    book_id           uuid NOT NULL,        -- catalog.books.id
    last_read_page int  NOT NULL DEFAULT 0 CHECK (last_read_page >= 0),
    total_pages       int  NOT NULL CHECK (total_pages >= 1),  -- Snapshot von catalog.books.page_count
    updated_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, book_id),
    -- Position im Buch in Promille (0..1000), ausgabenunabhängig. Gleiche Abrundung wie to_position() im Domain-Code.
    position          int GENERATED ALWAYS AS ((last_read_page * 1000) / total_pages) STORED,
    CHECK (last_read_page <= total_pages)
);

-- ───────── Reading Circles ─────────
CREATE TABLE circles.reading_circles (
    id                    uuid PRIMARY KEY,
    name                  text NOT NULL,
    owner_id              uuid NOT NULL,    -- identity.users.id
    book_id               uuid NOT NULL,    -- catalog.books.id
    -- Value Object ReadingPlan (beide NULL oder beide gesetzt)
    plan_start            date,
    plan_pages_per_week int CHECK (plan_pages_per_week > 0),
    created_at            timestamptz NOT NULL DEFAULT now(),
    CHECK ((plan_start IS NULL) = (plan_pages_per_week IS NULL))
);

CREATE TABLE circles.memberships (
    circle_id uuid NOT NULL REFERENCES circles.reading_circles(id) ON DELETE CASCADE,
    user_id   uuid NOT NULL,                -- identity.users.id
    joined_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (circle_id, user_id)        -- Nutzer nur einmal Mitglied
);
CREATE INDEX memberships_user_idx ON circles.memberships (user_id);  -- list_by_member

-- ───────── Discussion ─────────
CREATE TABLE discussion.threads (
    id         uuid PRIMARY KEY,
    circle_id  uuid NOT NULL,               -- circles.reading_circles.id
    book_id    uuid NOT NULL,               -- catalog.books.id (für den Spoiler-Abgleich)
    position   int  NOT NULL CHECK (position BETWEEN 1 AND 1000),  -- Spoiler-Schwelle in Promille
    title      text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX threads_circle_idx ON discussion.threads (circle_id, position);

CREATE TABLE discussion.posts (
    id         uuid PRIMARY KEY,
    thread_id  uuid NOT NULL REFERENCES discussion.threads(id) ON DELETE CASCADE,
    author_id  uuid NOT NULL,               -- identity.users.id
    text       text NOT NULL CHECK (length(trim(text)) > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX posts_thread_idx ON discussion.posts (thread_id, created_at);

-- Read Model ReaderProgress, per Event ReadingProgressChanged (Feld position) aus dem Context Reading gepflegt
CREATE TABLE discussion.reader_progress (
    user_id uuid NOT NULL,
    book_id uuid NOT NULL,
    position int NOT NULL CHECK (position BETWEEN 0 AND 1000),
    PRIMARY KEY (user_id, book_id)
);
