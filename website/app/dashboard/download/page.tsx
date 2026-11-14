"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { useState, useEffect } from "react"
import {
  Monitor,
  Apple,
  Terminal,
  Copy,
  Check,
  Usb,
  Play,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Cpu,
  FolderSync
} from "lucide-react"
import { api } from "@/lib/api"

export default function DownloadPage() {
  const [selectedOS, setSelectedOS] = useState<"windows" | "usb" | "unix">("windows")
  const [windowsMode, setWindowsMode] = useState<"powershell" | "cmd" | "network">("powershell")
  const [token, setToken] = useState("")
  const [loading, setLoading] = useState(false)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [serverOrigin, setServerOrigin] = useState("http://localhost:8001")

  useEffect(() => {
    if (typeof window !== "undefined") {
      setServerOrigin(window.location.origin)
    }
  }, [])

  useEffect(() => {
    async function fetchToken() {
      setLoading(true)
      try {
        const res = await api.download.getLink("windows")
        if (res?.token) {
          setToken(res.token)
        }
      } catch {
        // Fallback gracefully without locking the UI
        setToken("")
      } finally {
        setLoading(false)
      }
    }
    fetchToken()
  }, [])

  async function copyToClipboard(text: string, key: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedKey(key)
      setTimeout(() => setCopiedKey(null), 2000)
    } catch {
      // Fallback
    }
  }

  // Windows commands
  const psCommand = `powershell -ExecutionPolicy Bypass -Command "$zip=\\"$HOME\\Downloads\\iris-ai.zip\\"; $dest=\\"$HOME\\Desktop\\IRIS-AI\\"; Write-Host '⬇️ Downloading IRIS AI Package...' -ForegroundColor Cyan; Invoke-WebRequest -Uri '${serverOrigin}/downloads/iris-ai.zip' -OutFile $zip; Write-Host '📦 Extracting to Desktop\\IRIS-AI...' -ForegroundColor Cyan; Expand-Archive -Path $zip -DestinationPath $dest -Force; Remove-Item $zip; Write-Host '🚀 Launching IRIS...' -ForegroundColor Green; Start-Process -FilePath \\"$dest\\run.bat\\""`
  const cmdCommand = `run.bat`
  const networkCommand = token
    ? `powershell -ExecutionPolicy Bypass -Command "irm '${serverOrigin}/api/install/script/windows/${token}' | iex"`
    : `powershell -ExecutionPolicy Bypass -Command "$zip=\\"$HOME\\Downloads\\iris-ai.zip\\"; Invoke-WebRequest -Uri '${serverOrigin}/downloads/iris-ai.zip' -OutFile $zip; Expand-Archive $zip '$HOME\\Desktop\\IRIS-AI' -Force; Start-Process '$HOME\\Desktop\\IRIS-AI\\run.bat'"`

  return (
    <div className="max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous Multi-PC Distribution Engine
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Install IRIS on Another PC</h1>
        <p className="text-white/60 mt-1.5 text-sm max-w-2xl leading-relaxed">
          Deploy IRIS AI to any target Windows computer. The installer handles Python, Node.js, neural models,
          memory migration, and dependencies automatically with zero manual setup.
        </p>
      </div>

      {/* Target Environment Selector */}
      <div className="flex flex-wrap gap-3 mb-8">
        <button
          onClick={() => setSelectedOS("windows")}
          className={`flex items-center gap-2.5 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-75 active:scale-[0.98] select-none cursor-pointer touch-manipulation ${
            selectedOS === "windows"
              ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20 border border-cyan-400/30"
              : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/5"
          }`}
        >
          <Monitor className="w-4 h-4" />
          Windows PC (Recommended)
        </button>

        <button
          onClick={() => setSelectedOS("usb")}
          className={`flex items-center gap-2.5 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-75 active:scale-[0.98] select-none cursor-pointer touch-manipulation ${
            selectedOS === "usb"
              ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20 border border-cyan-400/30"
              : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/5"
          }`}
        >
          <Usb className="w-4 h-4" />
          USB / Pen Drive Transfer (Offline)
        </button>

        <button
          onClick={() => setSelectedOS("unix")}
          className={`flex items-center gap-2.5 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-75 active:scale-[0.98] select-none cursor-pointer touch-manipulation ${
            selectedOS === "unix"
              ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20 border border-cyan-400/30"
              : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/5"
          }`}
        >
          <Terminal className="w-4 h-4" />
          macOS / Linux Terminal
        </button>
      </div>

      {/* WINDOWS INSTALLATION SECTION */}
      {selectedOS === "windows" && (
        <div className="space-y-6">
          {/* DIRECT DOWNLOAD ZIP CARD */}
          <Card className="p-6 border-cyan-500/30 bg-gradient-to-r from-cyan-950/40 via-blue-950/30 to-black/60 relative overflow-hidden">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold mb-2">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Ready for Any Unknown Laptop — No Terminal Required
                </div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  Download IRIS AI Standalone Package
                </h3>
                <p className="text-xs text-white/60 mt-1 max-w-xl">
                  Complete offline-ready package (72 MB) with neural models, desktop overlay, vision engine, and 1-click launcher. Just extract and double-click <strong>run.bat</strong>.
                </p>
              </div>
              <a
                href="/downloads/iris-ai.zip"
                download="iris-ai.zip"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 transition-all duration-150 active:scale-95 shrink-0"
              >
                <FolderSync className="w-4 h-4" />
                Download ZIP (72 MB)
              </a>
            </div>
          </Card>

          {/* Sub-method tabs */}
          <div className="flex gap-2 border-b border-white/10 pb-3">
            <button
              onClick={() => setWindowsMode("powershell")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all duration-75 active:scale-95 select-none cursor-pointer touch-manipulation ${
                windowsMode === "powershell"
                  ? "bg-white/15 text-cyan-300 border border-cyan-500/40"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              PowerShell 1-Click
            </button>
            <button
              onClick={() => setWindowsMode("cmd")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all duration-75 active:scale-95 select-none cursor-pointer touch-manipulation ${
                windowsMode === "cmd"
                  ? "bg-white/15 text-cyan-300 border border-cyan-500/40"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              Direct Double-Click (run.bat)
            </button>
            <button
              onClick={() => setWindowsMode("network")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all duration-75 active:scale-95 select-none cursor-pointer touch-manipulation ${
                windowsMode === "network"
                  ? "bg-white/15 text-cyan-300 border border-cyan-500/40"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              Network / LAN Fetch
            </button>
          </div>

          {/* Active Command Box */}
          <Card className="p-6 border-white/15 bg-black/40">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Play className="w-4 h-4 text-cyan-400 fill-cyan-400/20" />
                  {windowsMode === "powershell" && "PowerShell 1-Click Command for Unknown Laptop"}
                  {windowsMode === "cmd" && "Direct Double-Click Method (No Command Needed)"}
                  {windowsMode === "network" && "Network One-Liner (Remote PC to Host)"}
                </h2>
                <p className="text-xs text-white/50 mt-0.5">
                  {windowsMode === "powershell" && "Paste into PowerShell on ANY target laptop to auto-download, extract, and launch:"}
                  {windowsMode === "cmd" && "Extract iris-ai.zip and simply double-click run.bat (or run in CMD):"}
                  {windowsMode === "network" && "Paste directly into PowerShell on another PC connected to your network:"}
                </p>
              </div>

              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  const cmd =
                    windowsMode === "powershell"
                      ? psCommand
                      : windowsMode === "cmd"
                      ? cmdCommand
                      : networkCommand
                  copyToClipboard(cmd, windowsMode)
                }}
                className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
              >
                {copiedKey === windowsMode ? (
                  <>
                    <Check className="w-4 h-4 mr-1.5 text-emerald-400" />
                    <span className="text-emerald-300 font-medium">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-1.5" />
                    <span>Copy Command</span>
                  </>
                )}
              </Button>
            </div>

            <div className="bg-black/60 rounded-xl p-4 font-mono text-sm text-cyan-200 border border-cyan-500/20 overflow-x-auto flex items-center justify-between shadow-inner">
              <code>
                {windowsMode === "powershell" && psCommand}
                {windowsMode === "cmd" && cmdCommand}
                {windowsMode === "network" && networkCommand}
              </code>
            </div>

            {/* Quick tips */}
            <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap gap-4 text-xs text-white/50">
              <span className="flex items-center gap-1.5 text-white/70">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> No admin rights needed for portable setup
              </span>
              <span className="flex items-center gap-1.5 text-white/70">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Automatically detects missing Python/Node/IRIS Neural Core
              </span>
              <span className="flex items-center gap-1.5 text-white/70">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Preserves memory & profiles in %USERPROFILE%\.iris
              </span>
            </div>
          </Card>

          {/* Step by step */}
          <Card className="p-6">
            <h3 className="font-semibold text-white mb-4 text-base">Simple 3-Step Setup on Any Unknown Laptop</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5">
                <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-sm mb-3">
                  1
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">Download ZIP</h4>
                <p className="text-xs text-white/50 leading-relaxed">
                  Click <strong className="text-cyan-300">Download ZIP</strong> above or run the 1-click PowerShell command.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5">
                <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-sm mb-3">
                  2
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">Extract Folder</h4>
                <p className="text-xs text-white/50 leading-relaxed">
                  Right-click <code className="text-cyan-300">iris-ai.zip</code> ➔ <strong className="text-white">Extract All...</strong> to your Desktop.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5">
                <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-sm mb-3">
                  3
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">Double-Click run.bat</h4>
                <p className="text-xs text-white/50 leading-relaxed">
                  Double-click <code className="text-cyan-300">run.bat</code> inside the extracted folder. Zero terminal typing needed!
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5">
                <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-sm mb-3">
                  4
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">Instant Launch</h4>
                <p className="text-xs text-white/50 leading-relaxed">
                  IRIS boots up automatically! The backend (:5743) and native desktop overlay start running immediately.
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* USB / PEN DRIVE SECTION */}
      {selectedOS === "usb" && (
        <div className="space-y-6">
          <Card className="p-6 border-white/15 bg-black/40">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Usb className="w-4 h-4 text-cyan-400" />
                  Automated USB Pen Drive Transfer Script
                </h2>
                <p className="text-xs text-white/50 mt-0.5">
                  Pre-packages clean files without bloated caches, copies memory backups, and prepares the pen drive in seconds.
                </p>
              </div>

              <Button
                size="sm"
                variant="ghost"
                onClick={() => copyToClipboard("copy_to_pendrive.bat", "usb")}
                className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
              >
                {copiedKey === "usb" ? (
                  <>
                    <Check className="w-4 h-4 mr-1.5 text-emerald-400" />
                    <span className="text-emerald-300 font-medium">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-1.5" />
                    <span>Copy Command</span>
                  </>
                )}
              </Button>
            </div>

            <div className="bg-black/60 rounded-xl p-4 font-mono text-sm text-cyan-200 border border-cyan-500/20 overflow-x-auto shadow-inner">
              <code>copy_to_pendrive.bat</code>
            </div>

            <div className="mt-5 space-y-3">
              <h4 className="text-sm font-semibold text-white">How to Transfer &amp; Run:</h4>
              <ol className="space-y-2 text-xs text-white/70 list-decimal list-inside leading-relaxed">
                <li>Insert your USB pen drive into this PC.</li>
                <li>Double-click <code className="text-cyan-300">copy_to_pendrive.bat</code> in the project folder.</li>
                <li>Safely eject the pen drive and insert it into any target Windows PC.</li>
                <li>Open the <code className="text-cyan-300">IRIS-AI</code> folder on the pen drive.</li>
                <li>Double-click <code className="text-cyan-300">install.bat</code> (or <code className="text-cyan-300">setup_portable_new_pc.bat</code>) and enjoy!</li>
              </ol>
            </div>
          </Card>
        </div>
      )}

      {/* UNIX / LINUX / MAC SECTION */}
      {selectedOS === "unix" && (
        <div className="space-y-6">
          <Card className="p-6 border-white/15 bg-black/40">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-cyan-400" />
                  macOS / Linux Terminal Command
                </h2>
                <p className="text-xs text-white/50 mt-0.5">
                  Runs the shell installer to configure IRIS Neural Core, install python dependencies, and create local services.
                </p>
              </div>

              <Button
                size="sm"
                variant="ghost"
                onClick={() => copyToClipboard("bash installer/linux/install.sh", "unix")}
                className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
              >
                {copiedKey === "unix" ? (
                  <>
                    <Check className="w-4 h-4 mr-1.5 text-emerald-400" />
                    <span className="text-emerald-300 font-medium">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 mr-1.5" />
                    <span>Copy Command</span>
                  </>
                )}
              </Button>
            </div>

            <div className="bg-black/60 rounded-xl p-4 font-mono text-sm text-cyan-200 border border-cyan-500/20 overflow-x-auto shadow-inner">
              <code>chmod +x installer/linux/install.sh &amp;&amp; ./installer/linux/install.sh</code>
            </div>
          </Card>
        </div>
      )}

      {/* Automated Features Checklist */}
      <Card className="p-6 mt-6 border-white/10">
        <h3 className="font-semibold text-white mb-3 text-base flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Autonomous Installation Pipeline Highlights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-white/70">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong>Silent Python 3.11 Installer:</strong> Auto-downloads &amp; adds Python to PATH if missing.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong>Silent Node.js LTS Installer:</strong> Configures npm runtime environment silently.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong>IRIS Neural Core service &amp; Weights:</strong> Auto-pulls LLaMA 3.2 3B for 100% offline local inference.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong>Dynamic Virtual Environment:</strong> Rebuilds machine-bound paths cleanly on new PCs.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong>Memory &amp; Profile Migration:</strong> Restores persistent encrypted vector memory to <code className="text-cyan-300">%USERPROFILE%\.iris</code>.</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong>1-Click Desktop Launcher:</strong> Creates <code className="text-cyan-300">start_all.bat</code> shortcut for daily execution.</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
