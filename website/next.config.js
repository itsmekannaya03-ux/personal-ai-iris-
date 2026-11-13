/** @type {import('next').NextConfig} */
const BACKEND_PORT = process.env.BACKEND_PORT || "8001"
const ENGINE_PORT = process.env.ENGINE_PORT || "5743"

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Engine API (port 5743) — local AI features
      {
        source: "/api/chat",
        destination: `http://localhost:${ENGINE_PORT}/chat`,
      },
      {
        source: "/api/status",
        destination: `http://localhost:${ENGINE_PORT}/status`,
      },
      {
        source: "/api/memory",
        destination: `http://localhost:${ENGINE_PORT}/memory`,
      },
      {
        source: "/api/system",
        destination: `http://localhost:${ENGINE_PORT}/system`,
      },
      {
        source: "/api/conversation/:path*",
        destination: `http://localhost:${ENGINE_PORT}/conversation/:path*`,
      },

      // Cloud API (port 8001 by default, fallback configurable) — auth, subscriptions, downloads
      {
        source: "/api/:path*",
        destination: `http://localhost:${BACKEND_PORT}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
