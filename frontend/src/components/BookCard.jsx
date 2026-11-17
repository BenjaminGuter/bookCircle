import { useRef, useState } from 'react'
import { coverSrc, deleteCover, uploadCover } from '../api/books'

export default function BookCard({ book, isAdmin, onChanged }) {
  const fileInput = useRef(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [version, setVersion] = useState(0)

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
    if (file) run(() => uploadCover(book.id, file))
  }

  return (
    <article className="card">
      {book.cover_url ? (
        <img className="cover" src={coverSrc(book.id, version)} alt={`Cover von ${book.title}`} />
      ) : (
        <div className="cover placeholder">Kein Cover</div>
      )}
      <h3>{book.title}</h3>
      <p className="meta">
        {book.authors.join(', ') || 'Unbekannter Autor'} · {book.page_count} Seiten
      </p>

      {isAdmin && (
        <div className="admin">
          <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={handleFile} />
          <button disabled={busy} onClick={() => fileInput.current.click()}>
            {book.cover_url ? 'Cover ändern' : 'Cover hinzufügen'}
          </button>
          {book.cover_url && (
            <button disabled={busy} className="danger" onClick={() => run(() => deleteCover(book.id))}>
              Löschen
            </button>
          )}
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </article>
  )
}
