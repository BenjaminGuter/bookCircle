import { useState } from 'react'


export default function Login() {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setMessage('')
  }
  

  return (
    <section className="login">
      <section className="login-form">
        <h2>{mode === 'login' ? 'Login' : 'Registrieren'}</h2>

        <form className="login-form-fields" onSubmit={(event) => {}}>
          <label className="login-label" htmlFor="username">
            Benutzername
            <input
              className="login-input"
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>

          <label className="login-label" htmlFor="password">
            Passwort
            <input
              className="login-input"
              id="password"
              name="password"
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {message && <p className="login-message" role="status">{message}</p>}

          <button className="login-submit" type="submit" disabled={isLoading}>
            {isLoading
              ? 'Bitte warten...'
              : mode === 'login'
                ? 'Einloggen'
                : 'Registrieren'}
          </button>
        </form>

        <div className="login-mode" aria-label="Anmelde-Modus">
        
          {mode !== 'login' && (
            <button
              type="button"
              className="login-mode-button"
              onClick={() => switchMode('login')}
            >
              Einloggen
            </button>
          )}
          {mode !== 'register' && (             
              <button
                type="button"
                className="login-mode-button"
                onClick={() => switchMode('register')}
              >
                Registrieren
              </button>
          )}
        </div>
      </section>
    </section>
  )
} 

