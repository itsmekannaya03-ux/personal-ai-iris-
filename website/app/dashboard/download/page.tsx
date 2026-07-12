"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useState, useEffect } from "react"
import { Monitor, Apple, Terminal, Copy, Check, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

const osInfo = {
  windows: { name: "Windows", icon: Monitor, lang: "powershell" },
  mac: { name: "macOS", icon: Apple, lang: "sh" },
  linux: { name: "Linux", icon: Terminal, lang: "sh" },
}

export default function DownloadPage() {
  const [selected, setSelected] = useState<"windows" | "mac" | "linux">("windows")
  const [token, setToken] = useState("")
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (typeof window === "undefined") return
    const ua = navigator.userAgent
    if (ua.includes("Win")) setSelected("windows")
    else if (ua.includes("Mac")) setSelected("mac")
    else setSelected("linux")
  }, [])

  async function generateToken() {
    setLoading(true)
    try {
      const res = await api.download.getLink(selected)
      setToken(res.token)
    } catch {
      setToken("")
    }
    setLoading(false)
  }

  useEffect(() => { generateToken() }, [selected])

  const os = osInfo[selected]
  const installUrl = token
    ? `https://igris.ai/api/install/script/${selected}/${token}`
    : ""

  const command =
    selected === "windows"
      ? `curl -fsSL "${installUrl}" | iex`
      : `curl -fsSL "${installUrl}" | sh`

  async function copyCommand() {
    await navigator.clipboard.writeText(command)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Download IGRIS</h1>
        <p className="text-white/50 mt-1">Choose your OS and run the install command in your terminal.</p>
      </div>

      {/* OS Selector */}
      <div className="flex gap-3 mb-8">
        {(Object.entries(osInfo) as [keyof typeof osInfo, typeof os][]).map(([key, info]) => (
          <button
            key={key}
            onClick={() => setSelected(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              selected === key
                ? "bg-igris-600 text-white"
                : "bg-white/5 text-white/50 hover:bg-white/10"
            }`}
          >
            <info.icon className="w-4 h-4" />
            {info.name}
          </button>
        ))}
      </div>

      {/* Command */}
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Install Command</h2>
          <Button size="sm" variant="ghost" onClick={copyCommand} disabled={!token}>
            {loading ? (
              <><Loader2 className="w-4 h-4 mr-1 animate-spin" /> Generating</>
            ) : copied ? (
              <><Check className="w-4 h-4 mr-1" /> Copied</>
            ) : (
              <><Copy className="w-4 h-4 mr-1" /> Copy</>
            )}
          </Button>
        </div>
        <div className="bg-black/40 rounded-lg p-4 font-mono text-sm text-igris-300 border border-white/5 overflow-x-auto">
          {token ? command : "Generating your personal install command..."}
        </div>
      </Card>

      {/* Steps */}
      <Card className="p-6">
        <h2 className="font-semibold mb-4">Installation Steps</h2>
        <ol className="space-y-3">
          <li className="flex items-start gap-3 text-sm text-white/70">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-igris-600/20 border border-igris-500/30 flex items-center justify-center text-xs text-igris-400 font-medium">1</span>
            Open {selected === "windows" ? "PowerShell as Administrator" : "Terminal"}
          </li>
          <li className="flex items-start gap-3 text-sm text-white/70">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-igris-600/20 border border-igris-500/30 flex items-center justify-center text-xs text-igris-400 font-medium">2</span>
            Copy and paste the command above
          </li>
          <li className="flex items-start gap-3 text-sm text-white/70">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-igris-600/20 border border-igris-500/30 flex items-center justify-center text-xs text-igris-400 font-medium">3</span>
            Press Enter — installer runs automatically
          </li>
          <li className="flex items-start gap-3 text-sm text-white/70">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-igris-600/20 border border-igris-500/30 flex items-center justify-center text-xs text-igris-400 font-medium">4</span>
            Your AI will greet you at localhost:5743 when ready
          </li>
        </ol>
      </Card>

      {/* What happens */}
      <Card className="p-6 mt-6">
        <h2 className="font-semibold mb-3">What the Installer Does</h2>
        <div className="space-y-2 text-sm text-white/50">
          <p>✓ Installs Ollama (local AI runtime)</p>
          <p>✓ Pulls the base AI model (LLaMA 3.2)</p>
          <p>✓ Injects your personal profile as AI&apos;s DNA</p>
          <p>✓ Sets up local memory database (ChromaDB)</p>
          <p>✓ Starts background AI service on port 5743</p>
          <p>✓ Creates CLI alias: type <code className="text-igris-300">ai &quot;your message&quot;</code></p>
          <p className="text-igris-400 mt-2">→ Your AI will greet you by name when ready.</p>
        </div>
      </Card>
    </div>
  )
}
