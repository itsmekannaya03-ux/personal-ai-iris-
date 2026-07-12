/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Engine API (port 5743) — local AI features
      {
        source: "/api/chat",
        destination: "http://localhost:5743/chat",
      },
      {
        source: "/api/status",
        destination: "http://localhost:5743/status",
      },
      {
        source: "/api/memory",
        destination: "http://localhost:5743/memory",
      },
      {
        source: "/api/system",
        destination: "http://localhost:5743/system",
      },
      {
        source: "/api/profile",
        destination: "http://localhost:5743/profile",
      },
      // Cloud API (port 8000) — auth, subscriptions, downloads
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ]
  },
}

module.exports = nextConfig
