import { useCallback, useEffect, useState } from 'react'
import { getHealth, listBooks } from './api/books'
import { setDevUser } from './api/client'
import BookCard from './components/BookCard'
import version from '../package.json'
import heroImage from '../../img/mohammadreza-charkhgard-UolPvs1rBk8-unsplash.jpg'

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
      <header id="global-header" >
        <section className="navigation-elements">
          <h1>BookCircle</h1>
          <p>Lesekreise</p>
          <p>Bücher</p>
          {user.admin && <button className="admin" onClick={() => {}}>Buch hinzufügen</button>}
          <button onClick={() => {}}>Login</button>
        </section>
        </header>

      {loadError && <p className="error">Bücher konnten nicht geladen werden: {loadError}</p>}
      <section className="hero" style={{ background: `url(${heroImage}) center / cover`}}>
        <h2 className="hero-title">Willkommen bei BookCircle</h2>
      </section>
      <section>
        <h2 className="section-title">Aktuelle Bücher</h2>
        <section className="grid book-list">
          {books.map((book) => (
            <BookCard key={book.id} book={book} isAdmin={user.admin} onChanged={loadBooks} />
          ))}
        </section>
      </section>
      <section className="devTools" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'fixed', bottom: 0, left: 0, right: 0, padding: '1rem 10rem', backgroundColor: '#CBC0AD', }}>
        <span className="devTools" style={{ fontWeight: 'bold' }}> Dev-Tools</span>
        <span className="version">Version: {version.version}
        </span>
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
      </section>
    </main>
  )
}
