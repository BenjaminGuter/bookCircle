import { useRef, useState } from 'react'
import { coverSrc, deleteCover, uploadCover } from '../api/books'

const FORMAT_LABELS = { paperback: 'Taschenbuch', hardcover: 'Hardcover', ebook: 'E-Book' }

export default function BookCard({ book, isAdmin, onChanged }) {
  const fileInput = useRef(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [version, setVersion] = useState(0)
  const [editionId, setEditionId] = useState(book.editions[0].id)

  // Die gewählte Ausgabe bestimmt Cover und Seitenzahl
  const edition = book.editions.find((e) => e.id === editionId) ?? book.editions[0]

  async function run(action) {
    setBusy(true)
    setError(null)
    try {
      await action()
      setVersion((v) => v + 1)
      await onChanged()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  function handleFile(event) {
    const file = event.target.files[0]
    event.target.value = '' // gleiche Datei erneut wählbar
    if (file) run(() => uploadCover(edition.id, file))
  }

  return (
    <article className="card">
      {edition.cover_url ? (
        <img className="cover" src={coverSrc(edition.id, version)} alt={`Cover von ${book.title}`} />
      ) : (
        <div className="cover placeholder">Kein Cover</div>
      )}
      <h3>{book.title}</h3>
      <p className="meta">{book.authors.join(', ') || 'Unbekannter Autor'}</p>

      <select
        className="edition"
        aria-label="Ausgabe"
        value={edition.id}
        onChange={(e) => setEditionId(e.target.value)}
      >
        {book.editions.map((e) => (
          <option key={e.id} value={e.id}>
            {FORMAT_LABELS[e.format] ?? e.format} · {e.page_count} Seiten
          </option>
        ))}
      </select>
      {(edition.publisher || edition.published_year) && (
        <p className="meta">{[edition.publisher, edition.published_year].filter(Boolean).join(', ')}</p>
      )}

      {isAdmin && (
        <div className="admin">
          <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={handleFile} />
          <button disabled={busy} onClick={() => fileInput.current.click()}>
            {edition.cover_url ? 'Cover ändern' : 'Cover hinzufügen'}
          </button>
          {edition.cover_url && (
            <button disabled={busy} className="danger" onClick={() => run(() => deleteCover(edition.id))}>
              Löschen
            </button>
          )}
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </article>
  )
}