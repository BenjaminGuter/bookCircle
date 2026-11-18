-- NUR ZUM AUSPROBIEREN: sichtbare Threads für einen Nutzer.
-- Im Backend macht das is_unlocked() (Spoiler-Regel), hier dieselbe exakte Ganzzahl-Rechnung ohne Rundung:
-- Leserseite * Thread.total_pages >= Thread.page * Leser.total_pages
-- Ben (Seite 60 von 250) sieht nur den Thread ab Seite 40. Maxi (kein Eintrag = Seite 0) sieht nichts.
-- Jana liest das Hardcover (310 Seiten): Thread ab Seite 100/250 gilt für sie ab Seite 124.
SELECT t.id, t.page, t.total_pages, t.title
FROM discussion.threads t
LEFT JOIN discussion.reader_progress rp
  ON rp.book_id = t.book_id AND rp.user_id = '22222222-2222-2222-2222-222222222222'
WHERE COALESCE(rp.page, 0) * t.total_pages >= t.page * COALESCE(rp.total_pages, 1)
ORDER BY t.page;

-- Lesestand der Mitglieder eines Lesekreises, mit der jeweiligen Ausgabe
-- (Prozent und "wer liegt zurück" berechnet das Backend)
SELECT u.display_name, e.format, COALESCE(p.last_read_page, 0) AS page, p.total_pages
FROM circles.reading_circles c
JOIN circles.memberships m ON m.circle_id = c.id
JOIN identity.users u ON u.id = m.user_id
LEFT JOIN reading.progress p ON p.user_id = m.user_id AND p.book_id = c.book_id
LEFT JOIN catalog.editions e ON e.id = p.edition_id
WHERE c.id = 'd0000000-0000-0000-0000-000000000001'
ORDER BY u.display_name;

-- Werke mit ihren Ausgaben und Covers
SELECT b.title, e.format, e.page_count, e.cover_file
FROM catalog.books b JOIN catalog.editions e ON e.book_id = b.id
ORDER BY b.title, e.page_count;