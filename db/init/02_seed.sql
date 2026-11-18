-- Testdaten. password_hash sind Platzhalter, KEINE echten Hashes (Login damit nicht möglich).
-- Verlag, Jahr und Seitenzahlen sind erfundene Beispielwerte.

INSERT INTO identity.users (id, email, display_name, password_hash, role) VALUES
 ('11111111-1111-1111-1111-111111111111', 'jana@example.com',      'Jana', 'dummy-hash', 'admin'),
 ('22222222-2222-2222-2222-222222222222', 'benjamin@example.com',  'Ben',  'dummy-hash', 'reader'),
 ('33333333-3333-3333-3333-333333333333', 'maximilian@example.com','Maxi', 'dummy-hash', 'reader');

INSERT INTO catalog.authors (id, name) VALUES
 ('a0000000-0000-0000-0000-000000000001', 'Arthur Conan Doyle'),
 ('a0000000-0000-0000-0000-000000000002', 'Franz Kafka');

-- Werke
INSERT INTO catalog.books (id, title) VALUES
 ('b0000000-0000-0000-0000-000000000001', 'Der Hund von Baskerville'),
 ('b0000000-0000-0000-0000-000000000002', 'Die Verwandlung');

INSERT INTO catalog.book_authors (book_id, author_id) VALUES
 ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001'),
 ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002');

-- Ausgaben: Baskerville als Taschenbuch (250 Seiten) und Hardcover (310 Seiten)
INSERT INTO catalog.editions (id, book_id, page_count, format, publisher, published_year) VALUES
 ('f1000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 250, 'paperback', NULL,            NULL),
 ('f1000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000001', 310, 'hardcover', 'Beispielverlag', 2020),
 ('f1000000-0000-0000-0000-000000000003', 'b0000000-0000-0000-0000-000000000002',  96, 'paperback', NULL,            NULL);

-- Library: Bens Regal (hängt am Werk)
INSERT INTO library.shelves (id, owner_id, name) VALUES
 ('c0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'Meine Bücher');
INSERT INTO library.shelf_entries (shelf_id, book_id, status) VALUES
 ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'reading'),
 ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', 'read');

-- Reading Circle "Krimi-Runde" liest das Werk, Leseplan: 10 % pro Woche
INSERT INTO circles.reading_circles (id, name, owner_id, book_id, plan_start, plan_percent_per_week) VALUES
 ('d0000000-0000-0000-0000-000000000001', 'Krimi-Runde',
  '11111111-1111-1111-1111-111111111111', 'b0000000-0000-0000-0000-000000000001', CURRENT_DATE, 10);

INSERT INTO circles.memberships (circle_id, user_id) VALUES
 ('d0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111'),
 ('d0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222'),
 ('d0000000-0000-0000-0000-000000000001', '33333333-3333-3333-3333-333333333333');

-- Reading: Jana liest das Hardcover (310 S.), Ben das Taschenbuch (250 S.), Maxi hat noch keinen Eintrag = Seite 0
INSERT INTO reading.progress (user_id, book_id, edition_id, last_read_page, total_pages) VALUES
 ('11111111-1111-1111-1111-111111111111', 'b0000000-0000-0000-0000-000000000001', 'f1000000-0000-0000-0000-000000000002', 149, 310),
 ('22222222-2222-2222-2222-222222222222', 'b0000000-0000-0000-0000-000000000001', 'f1000000-0000-0000-0000-000000000001',  60, 250),
 ('22222222-2222-2222-2222-222222222222', 'b0000000-0000-0000-0000-000000000002', 'f1000000-0000-0000-0000-000000000003',  96,  96);

-- Discussion: Read Model passend zu reading.progress (Kopie von Seite und Gesamtseiten)
INSERT INTO discussion.reader_progress (user_id, book_id, page, total_pages)
SELECT user_id, book_id, last_read_page, total_pages FROM reading.progress;

-- Threads gelten ab Seite 40 bzw. 100 einer Ausgabe mit 250 Seiten (Taschenbuch des Autors)
INSERT INTO discussion.threads (id, circle_id, book_id, page, total_pages, title) VALUES
 ('e0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',  40, 250, 'Der Fluch der Baskervilles'),
 ('e0000000-0000-0000-0000-000000000002', 'd0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 100, 250, 'Erste Verdächtige');

INSERT INTO discussion.posts (id, thread_id, author_id, text) VALUES
 ('f0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Wie glaubwürdig findet ihr die Legende?'),
 ('f0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'Ich bin noch skeptisch, klingt sehr nach Gruselgeschichte.'),
 ('f0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Mein Tipp: der Nachbar ist verdächtig.');