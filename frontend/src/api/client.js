// Zentraler API-Client. Alle Aufrufe ans Backend laufen hier durch,
// damit Basis-URL, Fehlerbehandlung und (später) Login an einer Stelle liegen.

export const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

// NUR FÜR DIE ENTWICKLUNG: Das Backend erkennt Nutzer aktuell am Header X-User-Id.
// Wird durch ein echtes Login (Token im Authorization-Header) ersetzt, die Stelle bleibt dieselbe.
let devUserId = null
export function setDevUser(id) {
  devUserId = id
}

export async function request(path, options = {}) {
  const headers = { ...(options.headers ?? {}) }
  if (devUserId) headers['X-User-Id'] = devUserId

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      // Antwort war kein JSON, dann bleibt der Statustext
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return null
  return res.json()
}
