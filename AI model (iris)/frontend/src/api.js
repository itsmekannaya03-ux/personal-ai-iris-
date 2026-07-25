const API_BASE = '/api'

export async function chat(message, useVoice = false) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, voice: useVoice }),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function getStatus() {
  const res = await fetch(`${API_BASE}/status`)
  if (!res.ok) throw new Error(`Status error: ${res.status}`)
  return res.json()
}

export async function getVoiceInfo() {
  const res = await fetch(`${API_BASE}/voice/info`)
  if (!res.ok) throw new Error(`Voice info error: ${res.status}`)
  return res.json()
}

export async function storeMemory(key, value) {
  const res = await fetch(`${API_BASE}/memory/store`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, value }),
  })
  if (!res.ok) throw new Error(`Memory store error: ${res.status}`)
  return res.json()
}

export async function recallMemory(key) {
  const res = await fetch(`${API_BASE}/memory/recall/${encodeURIComponent(key)}`)
  if (!res.ok) {
    if (res.status === 404) return null
    throw new Error(`Memory recall error: ${res.status}`)
  }
  return res.json()
}
