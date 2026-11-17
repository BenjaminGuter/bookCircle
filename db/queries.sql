-- Spoiler-Schutz: sichtbare Threads für einen Nutzer
-- Ben (Position 240) sieht nur den Thread ab 160. Maxi (kein Eintrag = 0) sieht nichts.
SELECT t.id, t.position, t.title
FROM discussion.threads t
LEFT JOIN discussion.reader_progress rp
  ON rp.book_id = t.book_id AND rp.user_id = '22222222-2222-2222-2222-222222222222'
WHERE t.position <= COALESCE(rp.position, 0)
ORDER BY t.position;

-- Wer im Lesekreis liegt hinter Position 400? (CircleProgressService.members_behind)
SELECT u.display_name, COALESCE(p.position, 0) AS position
FROM circles.reading_circles c
JOIN circles.memberships m ON m.circle_id = c.id
JOIN identity.users u ON u.id = m.user_id
LEFT JOIN reading.progress p ON p.user_id = m.user_id AND p.book_id = c.book_id
WHERE c.id = 'd0000000-0000-0000-0000-000000000001'
  AND COALESCE(p.position, 0) < 400;

-- Cover-Metadaten der Bücher
SELECT title, cover_file, cover_content_type FROM catalog.books;
