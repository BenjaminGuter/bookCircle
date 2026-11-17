-- Testdaten. password_hash sind Platzhalter, KEINE echten Hashes (Login damit nicht möglich).
-- Seitenzahlen sind Beispielwerte (hängen von der Ausgabe ab).

INSERT INTO identity.users (id, email, display_name, password_hash, role) VALUES
 ('11111111-1111-1111-1111-111111111111', 'jana@example.com',      'Jana', 'dummy-hash', 'admin'),
 ('22222222-2222-2222-2222-222222222222', 'benjamin@example.com',  'Ben',  'dummy-hash', 'reader'),
 ('33333333-3333-3333-3333-333333333333', 'maximilian@example.com','Maxi', 'dummy-hash', 'reader');

INSERT INTO catalog.authors (id, name) VALUES
 ('a0000000-0000-0000-0000-000000000001', 'Arthur Conan Doyle'),
 ('a0000000-0000-0000-0000-000000000002', 'Franz Kafka');

INSERT INTO catalog.books (id, title, page_count, isbn) VALUES
 ('b0000000-0000-0000-0000-000000000001', 'Der Hund von Baskerville', 250, NULL),
 ('b0000000-0000-0000-0000-000000000002', 'Die Verwandlung',           96, NULL);

INSERT INTO catalog.book_authors (book_id, author_id) VALUES
 ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001'),
 ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002');

-- Library: Bens Regal
INSERT INTO library.shelves (id, owner_id, name) VALUES
 ('c0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'Meine Bücher');
INSERT INTO library.shelf_entries (shelf_id, book_id, status) VALUES
 ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'reading'),
 ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', 'read');

-- Reading Circle "Krimi-Runde"
INSERT INTO circles.reading_circles (id, name, owner_id, book_id, plan_start, plan_pages_per_week) VALUES
 ('d0000000-0000-0000-0000-000000000001', 'Krimi-Runde',
  '11111111-1111-1111-1111-111111111111', 'b0000000-0000-0000-0000-000000000001', CURRENT_DATE, 50);

INSERT INTO circles.memberships (circle_id, user_id) VALUES
 ('d0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111'),
 ('d0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222'),
 ('d0000000-0000-0000-0000-000000000001', '33333333-3333-3333-3333-333333333333');

-- Reading: Fortschritt pro Nutzer und Buch (Maxi hat noch keinen Eintrag = Seite 0)
INSERT INTO reading.progress (user_id, book_id, last_read_page, total_pages) VALUES
 ('11111111-1111-1111-1111-111111111111', 'b0000000-0000-0000-0000-000000000001', 120, 250),
 ('22222222-2222-2222-2222-222222222222', 'b0000000-0000-0000-0000-000000000001',  60, 250),
 ('22222222-2222-2222-2222-222222222222', 'b0000000-0000-0000-0000-000000000002',  96,  96);

-- Discussion: Read Model passend zu reading.progress
INSERT INTO discussion.reader_progress (user_id, book_id, position)
SELECT user_id, book_id, position FROM reading.progress;

-- Position = Seite / Gesamtseiten * 1000 (Seite 40 von 250 = 160, Seite 100 von 250 = 400)
INSERT INTO discussion.threads (id, circle_id, book_id, position, title) VALUES
 ('e0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 160, 'Der Fluch der Baskervilles'),
 ('e0000000-0000-0000-0000-000000000002', 'd0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 400, 'Erste Verdächtige');

INSERT INTO discussion.posts (id, thread_id, author_id, text) VALUES
 ('f0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Wie glaubwürdig findet ihr die Legende?'),
 ('f0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'Ich bin noch skeptisch, klingt sehr nach Gruselgeschichte.'),
 ('f0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Mein Tipp: der Nachbar ist verdächtig.');
