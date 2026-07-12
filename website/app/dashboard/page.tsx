"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Cpu, HardDrive, Wifi, Activity, Download, ArrowRight, CheckCircle2, XCircle } from "lucide-react"
import Link from "next/link"

export default function DashboardPage() {
  const [profile, setProfile] = useState<any>(null)
  const [subscription, setSubscription] = useState<any>(null)
  const [engineStatus, setEngineStatus] = useState<any>(null)

  useEffect(() => {
    api.profile.get().then(setProfile).catch(() => {})
    api.subscriptions.status().then(setSubscription).catch(() => {})
    checkEngine()
  }, [])

  async function checkEngine() {
    try {
      const res = await fetch("/api/status")
      if (res.ok) {
        const data = await res.json()
        setEngineStatus(data)
      }
    } catch {}
  }

  const plan = subscription?.plan || "free"

  const stats = [
    {
      icon: Cpu,
      label: "AI Engine",
      value: engineStatus ? `${engineStatus.ai_name} (${engineStatus.model})` : "Not Installed",
      status: engineStatus ? "ready" : "pending",
      detail: engineStatus ? `Mode: ${engineStatus.mode}` : "Install to get started",
    },
    {
      icon: HardDrive,
      label: "Memory",
      value: engineStatus ? `${engineStatus.memory.short_term} ST / ${engineStatus.memory.long_term} LT / ${engineStatus.memory.deep} Deep` : "—",
      status: engineStatus?.memory ? "ready" : "pending",
      detail: "3-tier memory system",
    },
    {
      icon: Wifi,
      label: "Connection",
      value: engineStatus?.online ? "Online" : "Offline",
      status: engineStatus?.online ? "ready" : "pending",
      detail: engineStatus?.online ? "Engine responding" : "Engine not reachable",
    },
    {
      icon: Activity,
      label: "Plan",
      value: plan.charAt(0).toUpperCase() + plan.slice(1),
      status: plan === "free" ? "pending" : "ready",
      detail: plan === "free" ? "Upgrade for full features" : "All features active",
    },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">
          Welcome{profile?.name ? `, ${profile.name}` : ""}
        </h1>
        <p className="text-white/50 mt-1">
          {engineStatus
            ? `${engineStatus.ai_name} is running and ready.`
            : "Install IGRIS on your machine to get started."}
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {stats.map((stat) => (
          <Card key={stat.label} className="p-4">
            <div className="flex items-center justify-between mb-3">
              <stat.icon className="w-4 h-4 text-white/40" />
              {stat.status === "ready" ? (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-yellow-500" />
              )}
            </div>
            <p className="text-sm font-semibold leading-tight">{stat.value}</p>
            <p className="text-xs text-white/40 mt-1">{stat.detail}</p>
          </Card>
        ))}
      </div>

      {!engineStatus && (
        <Card className="p-8 text-center">
          <Download className="w-12 h-12 text-igris-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Install IGRIS on Your Machine</h2>
          <p className="text-white/50 mb-6 max-w-md mx-auto">
            Download the installer for your OS. One command, and your AI will be running locally in under 2 minutes.
          </p>
          <Link href="/dashboard/download">
            <Button size="lg">
              Continue to Download
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </Card>
      )}

      {engineStatus && !profile?.name && (
        <Card className="p-6 mt-6">
          <h2 className="font-semibold mb-2">Complete Your Profile</h2>
          <p className="text-sm text-white/50 mb-4">
            Fill in your profile so your AI knows who you are.
          </p>
          <Link href="/dashboard/profile">
            <Button variant="outline">
              Go to Profile
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </Card>
      )}
    </div>
  )
}
