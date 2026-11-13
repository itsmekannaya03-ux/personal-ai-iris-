"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { 
  Download, 
  ArrowRight, 
  RefreshCw,
  Layers,
} from "lucide-react"
import Link from "next/link"

export default function DashboardPage() {
  const [profile, setProfile] = useState<any>(null)
  const [subscription, setSubscription] = useState<any>(null)
  const [engineStatus, setEngineStatus] = useState<any>(null)
  const [checking, setChecking] = useState(false)
  const [allExpanded, setAllExpanded] = useState(false)

  useEffect(() => {
    api.profile.get().then(setProfile).catch(() => {})
    api.subscriptions.status().then(setSubscription).catch(() => {})
    checkEngine()

    const handlePetalsState = (e: any) => {
      setAllExpanded(Boolean(e.detail?.allOpen))
    }
    window.addEventListener("iris-petals-state", handlePetalsState)
    return () => window.removeEventListener("iris-petals-state", handlePetalsState)
  }, [])

  const handleToggleAll = () => {
    window.dispatchEvent(new CustomEvent("iris-toggle-petals"))
  }

  async function checkEngine() {
    setChecking(true)
    try {
      const res = await fetch("/api/status", { signal: AbortSignal.timeout(1500) })
      if (res.ok) {
        const data = await res.json()
        setEngineStatus(data)
      } else {
        setEngineStatus(null)
      }
    } catch {
      setEngineStatus(null)
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="relative min-h-[calc(100vh-6rem)] flex flex-col justify-between">
      {/* Dashboard Foreground Content */}
      <div className="relative z-10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white drop-shadow-md">
              Welcome{profile?.name ? `, ${profile.name}` : ""}
            </h1>
            <p className="text-white/60 mt-1">
              {engineStatus
                ? `${engineStatus.ai_name} is running and ready.`
                : "Install IRIS on your machine to get started."}
            </p>
          </div>
          <div className="flex items-center gap-3 self-start sm:self-auto">
            {/* The single clean Expand / Retract button requested by the user */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleToggleAll}
              className="gap-2 bg-[#0c0e18]/60 backdrop-blur-xl border-white/15 hover:bg-white/10 text-white"
            >
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              {allExpanded ? "Retract All" : "Expand All"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={checkEngine}
              disabled={checking}
              className="gap-2 bg-[#0c0e18]/60 backdrop-blur-xl border-white/15 hover:bg-white/10 text-white"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
              {checking ? "Checking Engine..." : "Check Engine"}
            </Button>
          </div>
        </div>

        {/* Generous empty stage height so the rotating 3D flower and attached rotating petal nodes are completely open */}
        <div className="min-h-[460px] md:min-h-[520px] pointer-events-none" />

        {!engineStatus && (
          <Card className="p-8 text-center bg-[#0c0e18]/60 backdrop-blur-xl border-white/10 shadow-2xl mt-8">
            <Download className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Install IRIS on Your Machine</h2>
            <p className="text-white/60 mb-6 max-w-md mx-auto">
              Download the installer for your OS. One command, and your AI will be running locally in under 2 minutes.
            </p>
            <Link href="/dashboard/download">
              <Button size="lg" className="bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white shadow-xl shadow-cyan-500/20">
                Continue to Download
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </Card>
        )}

        {engineStatus && !profile?.name && (
          <Card className="p-6 mt-6 bg-[#0c0e18]/60 backdrop-blur-xl border-white/10 shadow-xl">
            <h2 className="font-semibold text-white mb-2">Complete Your Profile</h2>
            <p className="text-sm text-white/60 mb-4">
              Fill in your profile so your AI knows who you are.
            </p>
            <Link href="/dashboard/profile">
              <Button variant="outline" className="bg-white/[0.04] border-white/15 text-white">
                Go to Profile
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </div>
  )
}
