// Base URL of the ORCA Python backend.
// For local dev this points at the local FastAPI server.
// For production set VITE_API_BASE_URL (e.g. https://your-backend-host.com) in the Vercel env.
const DEFAULT_BASE = 'http://127.0.0.1:8000'
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE).replace(/\/+$/, '')

export async function askOrca(message, conversationId, location = null) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId || null,
      location: location || null,
    }),
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const text = await response.text()
      if (text) detail = text
    } catch (_) {
      /* ignore */
    }
    const err = new Error(detail)
    err.status = response.status
    throw err
  }

  return response.json()
}
