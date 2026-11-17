import { useCallback, useEffect, useState } from 'react'
import { getHealth, listBooks } from './api/books'
import { setDevUser } from './api/client'
import BookCard from './components/BookCard'

// NUR FÜR DIE ENTWICKLUNG: Test-Nutzer aus db/init/02_seed.sql, bis es ein echtes Login gibt.
const DEV_USERS = [
  { id: '', label: 'Nicht angemeldet', admin: false },
  { id: '11111111-1111-1111-1111-111111111111', label: 'Jana (Admin)', admin: true },
  { id: '22222222-2222-2222-2222-222222222222', label: 'Ben (Leser)', admin: false },
  { id: '33333333-3333-3333-3333-333333333333', label: 'Maxi (Leser)', admin: false },
]

export default function App() {
  const [books, setBooks] = useState([])
  const [loadError, setLoadError] = useState(null)
  const [dbOk, setDbOk] = useState(null)
  const [userId, setUserId] = useState('')

  const user = DEV_USERS.find((u) => u.id === userId) ?? DEV_USERS[0]

  const loadBooks = useCallback(async () => {
    try {
      setBooks(await listBooks())
      setLoadError(null)
    } catch (e) {
      setLoadError(e.message)
    }
  }, [])

  useEffect(() => {
    getHealth()
      .then(() => setDbOk(true))
      .catch(() => setDbOk(false))
    listBooks()
      .then(setBooks)
      .catch((e) => setLoadError(e.message))
  }, [])

  function changeUser(event) {
    setUserId(event.target.value)
    setDevUser(event.target.value || null)
  }

  return (
    <main>
      <header>
        <h1>BookCircle</h1>
        <span className={`status ${dbOk === null ? '' : dbOk ? 'ok' : 'bad'}`}>
          {dbOk === null ? 'Backend prüfen …' : dbOk ? 'Backend verbunden' : 'Backend nicht erreichbar'}
        </span>
        <label className="user">
          Dev-Nutzer:
          <select value={userId} onChange={changeUser}>
            {DEV_USERS.map((u) => (
              <option key={u.id} value={u.id}>{u.label}</option>
            ))}
          </select>
        </label>
      </header>

      {loadError && <p className="error">Bücher konnten nicht geladen werden: {loadError}</p>}

      <section className="grid">
        {books.map((book) => (
          <BookCard key={book.id} book={book} isAdmin={user.admin} onChanged={loadBooks} />
        ))}
      </section>
    </main>
  )
}
