"use client"

import { useState } from "react"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { Check, Sparkles, Terminal, Activity, Waves, Radio, CircleDot } from "lucide-react"
import { api } from "@/lib/api"

export interface ThemeOption {
  id: string
  name: string
  description: string
  icon: typeof Sparkles
  accentColor: string
  previewClass: string
}

export const THEMES: ThemeOption[] = [
  {
    id: "blob",
    name: "Liquid Blob",
    description: "Reactive fluid orb with pulsing organic energy aura",
    icon: Sparkles,
    accentColor: "from-indigo-500 to-purple-600",
    previewClass: "rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 shadow-[0_0_25px_rgba(99,102,241,0.5)] animate-pulse",
  },
  {
    id: "terminal",
    name: "Cyber Terminal",
    description: "Matrix phosphor green HUD with scanlines and monospaced telemetry",
    icon: Terminal,
    accentColor: "from-emerald-500 to-teal-700",
    previewClass: "rounded-md bg-emerald-950/80 border border-emerald-500/60 shadow-[0_0_20px_rgba(16,185,129,0.3)] font-mono text-[10px] text-emerald-400 flex items-center justify-center",
  },
  {
    id: "voice_bar",
    name: "Voice Spectrum",
    description: "Dynamic multi-channel audio equalizer bars responding to speech",
    icon: Activity,
    accentColor: "from-blue-500 to-cyan-400",
    previewClass: "flex items-end justify-center gap-1 h-10 py-1",
  },
  {
    id: "drum_waves",
    name: "Drum Waves",
    description: "Concentric sonic ripples vibrating with acoustic voice cadence",
    icon: Waves,
    accentColor: "from-pink-500 to-rose-600",
    previewClass: "relative flex items-center justify-center",
  },
  {
    id: "hologram_orb",
    name: "Hologram Orb",
    description: "3D geometric holographic wireframe with gyro rotation",
    icon: Radio,
    accentColor: "from-sky-400 to-indigo-600",
    previewClass: "rounded-full border-2 border-sky-400/80 bg-sky-950/40 shadow-[0_0_20px_rgba(56,189,248,0.4)] flex items-center justify-center",
  },
  {
    id: "minimal_dot",
    name: "Minimal Dot",
    description: "Ultra-clean ambient breathing indicator for zero-distraction focus",
    icon: CircleDot,
    accentColor: "from-white to-gray-400",
    previewClass: "w-5 h-5 rounded-full bg-white shadow-[0_0_15px_rgba(255,255,255,0.7)] animate-ping",
  },
]

interface ThemeSelectorProps {
  currentTheme?: string
  onThemeChanged?: (newTheme: string) => void
}

export function ThemeSelector({ currentTheme = "blob", onThemeChanged }: ThemeSelectorProps) {
  const [selected, setSelected] = useState(currentTheme)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState("")

  async function handleApplyTheme(themeId: string) {
    setSelected(themeId)
    onThemeChanged?.(themeId)
    if (typeof window !== "undefined") {
      localStorage.setItem("iris_theme", themeId)
      window.dispatchEvent(new CustomEvent("iris-theme-change", { detail: { theme: themeId } }))
    }
    setSaving(true)
    setError("")
    try {
      await api.profile.update({ theme: themeId })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err: any) {
      setError(err?.message || "Failed to update theme.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-iris-400" />
            Visual Themes
          </h2>
          <p className="text-sm text-white/50 mt-1">
            Customize the appearance of IRIS on your desktop overlay and web interfaces.
          </p>
        </div>
        {saved && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Check className="w-3.5 h-3.5" />
            Theme Saved
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {THEMES.map((theme) => {
          const isSelected = selected === theme.id
          const Icon = theme.icon

          return (
            <button
              key={theme.id}
              type="button"
              onClick={() => handleApplyTheme(theme.id)}
              disabled={saving}
              className={`relative text-left p-4 rounded-xl border transition-all duration-75 active:scale-[0.98] select-none cursor-pointer group flex flex-col justify-between ${
                isSelected
                  ? "bg-iris-950/40 border-iris-500 shadow-[0_0_20px_rgba(99,102,241,0.25)] ring-1 ring-iris-500"
                  : "bg-white/[0.02] border-white/5 hover:border-white/20 hover:bg-white/[0.04]"
              }`}
            >
              {/* Mini visual mockup box */}
              <div className="w-full h-24 rounded-lg bg-black/50 border border-white/5 mb-3 flex items-center justify-center overflow-hidden relative">
                {theme.id === "blob" && (
                  <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 blur-[2px] shadow-[0_0_25px_rgba(99,102,241,0.8)] animate-pulse" />
                )}

                {theme.id === "terminal" && (
                  <div className="text-[11px] font-mono text-emerald-400 text-center leading-tight tracking-wider">
                    <span className="text-emerald-500">&gt; IRIS_OS:</span> ONLINE<br />
                    <span className="text-white/40">SYS: 64-BIT SECURE</span>
                  </div>
                )}

                {theme.id === "voice_bar" && (
                  <div className="flex items-end gap-1 h-8">
                    {[40, 75, 100, 60, 90, 50, 80].map((h, i) => (
                      <span
                        key={i}
                        className="w-1.5 bg-gradient-to-t from-blue-600 to-cyan-400 rounded-t"
                        style={{ height: `${h}%` }}
                      />
                    ))}
                  </div>
                )}

                {theme.id === "drum_waves" && (
                  <div className="relative flex items-center justify-center">
                    <div className="w-14 h-14 rounded-full border border-pink-500/30 animate-ping" />
                    <div className="absolute w-8 h-8 rounded-full border border-pink-400/60" />
                    <div className="absolute w-3 h-3 rounded-full bg-pink-500" />
                  </div>
                )}

                {theme.id === "hologram_orb" && (
                  <div className="w-12 h-12 rounded-full border-2 border-dashed border-sky-400/70 bg-sky-950/40 shadow-[0_0_15px_rgba(56,189,248,0.5)] flex items-center justify-center">
                    <div className="w-6 h-6 rounded-full border border-sky-300/60" />
                  </div>
                )}

                {theme.id === "minimal_dot" && (
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-white shadow-[0_0_12px_rgba(255,255,255,0.9)]" />
                    <span className="text-xs text-white/50 font-mono">STANDBY</span>
                  </div>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${isSelected ? "text-iris-400" : "text-white/40"}`} />
                    <h3 className="font-semibold text-sm text-white">{theme.name}</h3>
                  </div>
                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-iris-600 flex items-center justify-center">
                      <Check className="w-3 h-3 text-white" />
                    </div>
                  )}
                </div>
                <p className="text-xs text-white/40 leading-relaxed">{theme.description}</p>
              </div>
            </button>
          )
        })}
      </div>
    </Card>
  )
}

