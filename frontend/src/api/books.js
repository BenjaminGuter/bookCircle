import { API_BASE, request } from './client'

export const getHealth = () => request('/health/db')

// Werke mit ihren Ausgaben: [{ id, title, authors, editions: [{ id, format, page_count, cover_url, ... }] }]
export const listBooks = () => request('/books')

// Cover gehören zur Ausgabe (nicht zum Werk). version erzwingt ein Neuladen nach Upload/Löschen.
export const coverSrc = (editionId, version = 0) => `${API_BASE}/editions/${editionId}/cover?v=${version}`

// Nur Admin. Hinzufügen und Ändern sind dieselbe Operation.
export function uploadCover(editionId, file) {
  const form = new FormData()
  form.append('file', file)
  return request(`/editions/${editionId}/cover`, { method: 'PUT', body: form })
}

// Nur Admin
export const deleteCover = (editionId) => request(`/editions/${editionId}/cover`, { method: 'DELETE' })