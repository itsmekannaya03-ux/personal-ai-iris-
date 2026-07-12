"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function CallbackPage() {
  const router = useRouter()

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get("session_id")
    if (sessionId) {
      router.push("/dashboard/download")
    } else {
      router.push("/pricing")
    }
  }, [router])

  return (
    <div className="min-h-screen grid-bg flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 rounded-lg bg-igris-600 flex items-center justify-center mx-auto mb-4 animate-pulse">
          <span className="text-white font-bold">I</span>
        </div>
        <p className="text-white/50">Processing your payment...</p>
      </div>
    </div>
  )
}
