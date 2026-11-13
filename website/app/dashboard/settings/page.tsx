"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { ThemeSelector } from "@/components/dashboard/ThemeSelector"
import { SkillToggles } from "@/components/dashboard/SkillToggles"
import { Shield, Sparkles, CreditCard, AlertTriangle } from "lucide-react"
import Link from "next/link"
import { PlanCheckoutModal } from "@/components/ui/PlanCheckoutModal"

export default function SettingsPage() {
  const [subscription, setSubscription] = useState<any>(null)
  const [profile, setProfile] = useState<any>(null)
  const [checkoutPlan, setCheckoutPlan] = useState<"student" | "lifetime" | null>(null)

  const reloadSubscription = () => {
    api.subscriptions.status().then(setSubscription).catch(() => {})
  }

  useEffect(() => {
    reloadSubscription()
    api.profile.get().then(setProfile).catch(() => {})
  }, [])

  const plan = subscription?.plan || "free"

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Settings & Configuration</h1>
        <p className="text-white/50 mt-1">Manage your account, visual themes, AI skills, and local runtime privacy.</p>
      </div>

      <div className="max-w-4xl space-y-8">
        {/* Visual Themes */}
        <ThemeSelector
          currentTheme={profile?.theme || "blob"}
          onThemeChanged={(newTheme) => setProfile((p: any) => ({ ...p, theme: newTheme }))}
        />

        {/* Autonomous AI Skills */}
        <SkillToggles />

        {/* Plan / Subscription */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-2">
            <CreditCard className="w-5 h-5 text-iris-400" />
            <h2 className="text-lg font-bold text-white">Current Plan</h2>
          </div>
          <p className="text-sm text-white/50 mb-4">
            You are currently on the <span className="text-white font-medium capitalize">{plan}</span> tier.
          </p>
          {plan === "free" && (
            <div className="flex items-center gap-4">
              <Button onClick={() => setCheckoutPlan("student")}>
                Upgrade to Student Pro (₹99/mo)
              </Button>
              <Button variant="outline" onClick={() => setCheckoutPlan("lifetime")}>
                Lifetime Access (₹999)
              </Button>
            </div>
          )}
          {plan === "student" && (
            <div className="space-y-2">
              <p className="text-sm text-cyan-400 font-medium">✓ Student Pro Active until {subscription?.end_date ? new Date(subscription.end_date).toLocaleDateString() : "Next Month"}</p>
              <Button variant="outline" size="sm" onClick={() => setCheckoutPlan("lifetime")}>
                Upgrade to Lifetime Sovereign (₹999)
              </Button>
            </div>
          )}
          {plan === "lifetime" && (
            <p className="text-sm text-emerald-400 font-medium">✓ Lifetime Pro access active — all premium modules unlocked permanently.</p>
          )}
        </Card>

        {/* Privacy */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-5 h-5 text-iris-400" />
            <h2 className="text-lg font-bold text-white">Local Zero-Trust Privacy</h2>
          </div>
          <p className="text-sm text-white/50 leading-relaxed">
            All your audio streams, conversation logs, embeddings, and workspace file accesses run strictly on your machine.
            Zero telemetry or conversation payloads ever leave your PC.
          </p>
        </Card>

        {/* Danger Zone */}
        <Card className="p-6 border-red-500/20 bg-red-950/10">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-bold text-white">Danger Zone</h2>
          </div>
          <p className="text-sm text-white/50 mb-4">
            Permanently delete your profile, erase local cache tokens, and disconnect your local engine.
          </p>
          <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/20 hover:text-red-300">
            Delete Account & Reset Data
          </Button>
        </Card>
      </div>

      {/* Plan Checkout & UPI QR Modal */}
      <PlanCheckoutModal
        isOpen={Boolean(checkoutPlan)}
        onClose={() => setCheckoutPlan(null)}
        planId={checkoutPlan || "student"}
        onSuccess={reloadSubscription}
      />
    </div>
  )
}
