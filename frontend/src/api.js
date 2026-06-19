const BASE = import.meta.env.VITE_API_URL

function today() {
  return new Date().toISOString().slice(0, 10)
}

function daysFromNow(n) {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d.toISOString().slice(0, 10)
}

export async function searchLocations(query) {
  const res = await fetch(`${BASE}/weather/locations?q=${encodeURIComponent(query)}&count=6`)
  if (!res.ok) throw new Error('Location search failed')
  return res.json()
}

export async function getRecords(limit = 50) {
  const res = await fetch(`${BASE}/weather/?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to load saved locations')
  return res.json()
}

export async function deleteRecord(id) {
  const res = await fetch(`${BASE}/weather/${id}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 404) throw new Error('Delete failed')
}

// Fetch a short Wikipedia summary — tries each part of the location name progressively
export async function fetchWikiSummary(locationName) {
  const parts = locationName
    .split(',')
    .map(p => p.trim())
    .filter(p => p.length >= 3)

  for (const part of parts) {
    try {
      const res = await fetch(
        `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(part)}`
      )
      if (!res.ok) continue
      const data = await res.json()
      if (data.type === 'disambiguation' || data.type === 'no-extract' || !data.extract) continue
      const extract = data.extract.length > 220
        ? data.extract.slice(0, 220).trimEnd() + '…'
        : data.extract
      return { title: data.title || part, extract }
    } catch {
      continue
    }
  }
  return null
}

// Creates a record and returns weather for today + next 5 days
export async function fetchWeather(location) {
  const res = await fetch(`${BASE}/weather/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      date_from: today(),
      date_to: daysFromNow(8),
    }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = body.detail
    if (Array.isArray(detail)) throw new Error(detail[0]?.msg || 'Invalid request')
    throw new Error(detail || `Request failed (${res.status})`)
  }

  return res.json()
}
