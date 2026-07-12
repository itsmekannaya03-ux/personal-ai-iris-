const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api"

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("igris_token") : null

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export const api = {
  auth: {
    signup: (data: { email: string; password: string; name: string }) =>
      request<{ token: string; user: any }>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      request<{ token: string; user: any }>("/auth/login", {
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
  },
  download: {
    getLink: async (os: string) => {
      const token = typeof window !== "undefined" ? localStorage.getItem("igris_token") : null
      const res = await fetch(`${API_BASE}/download/${os}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error("Download failed")
      const text = await res.text()
      const tokenMatch = text.match(/TOKEN="([^"]+)"/) || text.match(/installer\/([a-f0-9-]+)/)
      return { script: text, token: tokenMatch?.[1] || "" }
    },
  },
}
