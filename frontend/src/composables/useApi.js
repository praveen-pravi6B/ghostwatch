// Thin wrapper around the GhostWatch API
const BASE = '/api'

async function request(method, path, body) {
  const opts = {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  }
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${method} ${path} → ${res.status}: ${text}`)
  }
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : null
}

export function useApi() {
  return {
    getStatus:     () => request('GET',    '/status'),
    getEvents:     (limit = 200) => request('GET', `/events?limit=${limit}`),
    collect:       () => request('POST',   '/collect'),
    investigate:   (limit = 50) => request('POST', `/investigate?limit=${limit}`),
    clearEvents:   () => request('DELETE', '/events'),
  }
}
