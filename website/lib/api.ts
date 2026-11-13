const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api"
let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

function getTokens() {
  if (typeof window === "undefined") return { token: null, refresh: null }
  return {
    token: localStorage.getItem("iris_token"),
    refresh: localStorage.getItem("iris_refresh"),
  }
}

function setTokens(token: string, refresh: string) {
  localStorage.setItem("iris_token", token)
  localStorage.setItem("iris_refresh", refresh)
}

function clearTokens() {
  localStorage.removeItem("iris_token")
  localStorage.removeItem("iris_refresh")
}

async function refreshAccessToken(): Promise<string> {
  const { refresh } = getTokens()
  if (!refresh) throw new Error("No refresh token")

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  })

  if (!res.ok) {
    clearTokens()
    throw new Error("Session expired")
  }

  const data = await res.json()
  setTokens(data.token, data.refresh_token)
  return data.token
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { token } = getTokens()

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  let res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (res.status === 401 && token) {
    if (!isRefreshing) {
      isRefreshing = true
      try {
        const newToken = await refreshAccessToken()
        isRefreshing = false
        refreshQueue.forEach((cb) => cb(newToken))
        refreshQueue = []

        headers["Authorization"] = `Bearer ${newToken}`
        res = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers,
        })
      } catch {
        isRefreshing = false
        refreshQueue = []
        clearTokens()
        if (typeof window !== "undefined") {
          window.location.href = "/login"
        }
        throw new Error("Session expired")
      }
    } else {
      const newToken = await new Promise<string>((resolve) => {
        refreshQueue.push(resolve)
      })
      headers["Authorization"] = `Bearer ${newToken}`
      res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      })
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

type ChatResponse = { response: string }
type ConversationStatus = {
  tokens_used: number
  max_tokens: number
  ratio: number
  status: "ok" | "warning" | "critical"
  message: string
  message_count: number
}
type SessionResult = {
  summary: string | null
  message_count_cleared: number
  status: string
}

async function directFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  auth: {
    signup: (data: { email: string; password: string; name: string }) =>
      request<{ token: string; refresh_token: string; user: any }>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      request<{ token: string; refresh_token: string; user: any }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    me: () => request<any>("/auth/me"),
  },
  profile: {
    get: () => request<any>("/profile"),
    update: (data: any) =>
      request<any>("/profile", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
  },
  subscriptions: {
    create: (plan: string) =>
      request<{ url: string }>("/subscriptions/create", {
        method: "POST",
        body: JSON.stringify({ plan }),
      }),
    status: () => request<any>("/subscriptions/status"),
    verifyQr: (plan: string, utr?: string) =>
      request<any>("/subscriptions/verify-qr", {
        method: "POST",
        body: JSON.stringify({ plan, utr }),
      }),
  },
  download: {
    getLink: async (os: string) => {
      const { token } = getTokens()
      const res = await fetch(`${API_BASE}/download/${os}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error("Download failed")
      const text = await res.text()
      const tokenMatch = text.match(/TOKEN="([^"]+)"/) || text.match(/installer\/([a-f0-9-]+)/)
      return { script: text, token: tokenMatch?.[1] || "" }
    },
  },
  chat: {
    send: (message: string) =>
      directFetch<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
      }),
    status: () =>
      directFetch<ConversationStatus>("/conversation/status"),
    newSession: (keepSummary = true) =>
      directFetch<SessionResult>("/conversation/new-session", {
        method: "POST",
        body: JSON.stringify({ keep_summary: keepSummary }),
      }),
    summary: () =>
      directFetch<{ summary: string }>("/conversation/summary"),
    setMaxTokens: (maxTokens: number) =>
      directFetch<{ max_tokens: number; status: string }>("/conversation/max-tokens", {
        method: "POST",
        body: JSON.stringify({ max_tokens: maxTokens }),
      }),
  },
}
