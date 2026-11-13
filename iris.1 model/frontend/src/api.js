const API_BASE = '/api'

export async function chat(message, useVoice = false, isVoice = false) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, voice: useVoice, is_voice: isVoice }),
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

export async function stopVoice() {
  try {
    const res = await fetch(`${API_BASE}/voice/stop`, { method: 'POST' })
    return await res.json()
  } catch {
    return { status: 'error', speaking: false }
  }
}

export async function getVisionLast() {
  const res = await fetch(`${API_BASE}/vision/last`)
  if (!res.ok) throw new Error(`Vision error: ${res.status}`)
  return res.json()
}

export async function getCameraDevices() {
  try {
    const res = await fetch(`${API_BASE}/camera/devices`)
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function switchCamera(cameraId) {
  const res = await fetch(`${API_BASE}/camera/switch?camera_id=${cameraId}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Camera switch error: ${res.status}`)
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

export async function getConversationHistory() {
  try {
    const res = await fetch(`${API_BASE}/conversation/history`)
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function clearConversationSession() {
  try {
    const res = await fetch(`${API_BASE}/conversation/new-session`, { method: 'POST' })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getProactiveEvents(sinceId = 0) {
  try {
    const res = await fetch(`${API_BASE}/proactive/events?since_id=${sinceId}`)
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function simulateEmotion(emotion) {
  try {
    const res = await fetch(`${API_BASE}/emotion/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emotion }),
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getTodos() {
  try {
    const res = await fetch(`${API_BASE}/todos`)
    if (!res.ok) return { todos: [] }
    return res.json()
  } catch {
    return { todos: [] }
  }
}

export async function createTodo(task, remindInSeconds = null) {
  const res = await fetch(`${API_BASE}/todos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, remind_in_seconds: remindInSeconds }),
  })
  if (!res.ok) throw new Error(`Todo create error: ${res.status}`)
  return res.json()
}

export async function toggleTodo(todoId, completed = null) {
  const res = await fetch(`${API_BASE}/todos/${encodeURIComponent(todoId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed }),
  })
  if (!res.ok) throw new Error(`Todo toggle error: ${res.status}`)
  return res.json()
}

export async function deleteTodo(todoId) {
  const res = await fetch(`${API_BASE}/todos/${encodeURIComponent(todoId)}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`Todo delete error: ${res.status}`)
  return res.json()
}

export async function getPresenceHudState() {
  try {
    const res = await fetch(`${API_BASE}/presence/hud-state`)
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function resetPresence() {
  const res = await fetch(`${API_BASE}/presence/reset`, { method: 'POST' })
  if (!res.ok) throw new Error(`Presence reset error: ${res.status}`)
  return res.json()
}

export async function reEnrollFace(name = 'Commander') {
  const res = await fetch(`${API_BASE}/presence/re-enroll`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error(`Face re-enroll error: ${res.status}`)
  return res.json()
}

export async function clearAllTodos() {
  const res = await fetch(`${API_BASE}/todos/clear`, { method: 'POST' })
  if (!res.ok) throw new Error(`Todos clear error: ${res.status}`)
  return res.json()
}
