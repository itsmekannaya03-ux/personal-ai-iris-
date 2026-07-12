"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"

export default function SettingsPage() {
  const [subscription, setSubscription] = useState<any>(null)

  useEffect(() => {
    api.subscriptions.status().then(setSubscription).catch(() => {})
  }, [])

  const plan = subscription?.plan || "free"

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-white/50 mt-1">Manage your account and subscription.</p>
      </div>

      <div className="max-w-2xl space-y-6">
        <Card className="p-6">
          <h2 className="font-semibold mb-1">Current Plan</h2>
          <p className="text-sm text-white/50 mb-4">
            You are on the <span className="text-white capitalize">{plan}</span> plan.
          </p>
          {plan === "free" && (
            <Button onClick={() => window.location.href = "/pricing"}>
              Upgrade to Pro
            </Button>
          )}
          {plan === "student" && (
            <p className="text-sm text-igris-400">Active until {subscription?.end_date || "N/A"}</p>
          )}
          {plan === "lifetime" && (
            <p className="text-sm text-igris-400">Lifetime access — thank you!</p>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="font-semibold mb-1">Privacy</h2>
          <p className="text-sm text-white/50">
            All your data is stored locally on your machine. We do not store or have access to your conversations, files, or personal information beyond what you provide in your profile.
          </p>
        </Card>

        <Card className="p-6">
          <h2 className="font-semibold mb-1">Danger Zone</h2>
          <p className="text-sm text-white/50 mb-4">
            Permanently delete your account and all associated data.
          </p>
          <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10">
            Delete Account
          </Button>
        </Card>
      </div>
    </div>
  )
}
