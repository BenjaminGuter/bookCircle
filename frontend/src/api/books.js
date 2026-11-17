import { API_BASE, request } from './client'

export const getHealth = () => request('/health/db')

export const listBooks = () => request('/books')

// Cover-URL für <img>. version erzwingt ein Neuladen nach Upload/Löschen.
export const coverSrc = (bookId, version = 0) => `${API_BASE}/books/${bookId}/cover?v=${version}`

// Nur Admin. Hinzufügen und Ändern sind dieselbe Operation.
export function uploadCover(bookId, file) {
  const form = new FormData()
  form.append('file', file)
  return request(`/books/${bookId}/cover`, { method: 'PUT', body: form })
}

// Nur Admin
export const deleteCover = (bookId) => request(`/books/${bookId}/cover`, { method: 'DELETE' })
