"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { api } from "@/lib/api"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { ChatInput } from "@/components/chat/ChatInput"
import { TokenBar } from "@/components/chat/TokenBar"
import { Bot, Terminal, Sparkles, HelpCircle, Layers, ArrowRight, ShieldCheck, Cpu, Sliders, Palette } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ConvoStatus {
  tokens_used: number
  max_tokens: number
  ratio: number
  status: "ok" | "warning" | "critical"
  message: string
  message_count: number
}

/**
 * Checks if the user is asking for a command, deployment steps, or installation guidance.
 * Matches keywords including typos like "commend".
 */
function isAskingForCommand(query: string): boolean {
  const q = query.toLowerCase()
  return /commend|command|install|deploy|setup|run in cmd|cmd|terminal|powershell|how to run|how to install|give me (the )?code|download|another pc|other pc|target pc|pendrive|usb|github|git clone|diagnostic|pre-flight/i.test(
    q
  )
}

/**
 * REN's Frontend Modification Engine:
 * Gives REN the superpower to directly change and customize the IRIS frontend
 * (themes, 3D flora canvas, wireframe mode, glow intensity, skills).
 */
function executeFrontendModification(query: string): { modified: boolean; message: string } {
  const q = query.toLowerCase()

  // 1. Visual Themes Modification
  const themeMatches = [
    { match: /terminal|matrix|phosphor|green/i, id: "terminal", name: "Cyber Terminal" },
    { match: /blob|liquid|aura|purple/i, id: "blob", name: "Liquid Blob" },
    { match: /voice(\s+bar)?|spectrum|equalizer|audio bars/i, id: "voice_bar", name: "Voice Spectrum" },
    { match: /drum|ripple|sonic|wave/i, id: "drum_waves", name: "Drum Waves" },
    { match: /hologram|holo|wireframe orb/i, id: "hologram_orb", name: "Hologram Orb" },
    { match: /minimal|dot|clean/i, id: "minimal_dot", name: "Minimal Dot" },
  ]

  if (q.includes("theme") || q.includes("look") || q.includes("style") || q.includes("switch to") || q.includes("change to")) {
    for (const t of themeMatches) {
      if (t.match.test(q)) {
        if (typeof window !== "undefined") {
          localStorage.setItem("iris_theme", t.id)
          window.dispatchEvent(new CustomEvent("iris-theme-change", { detail: { theme: t.id } }))
          api.profile.update({ theme: t.id }).catch(() => {})
        }
        return {
          modified: true,
          message: `✨ **Frontend Theme Updated by REN!**\n\nI have successfully reconfigured IRIS's visual presentation to **${t.name}**.\n\nYour dashboard and desktop overlay are now rendering in this theme. You can ask me to change it anytime (e.g. *"REN, switch to Cyber Terminal"*, *"Change theme to Liquid Blob"*, *"Try Voice Spectrum"*).`,
        }
      }
    }
  }

  // 2. 3D Petal Node Callouts (Expand / Retract)
  if (q.includes("expand") || q.includes("open petal") || q.includes("show petal") || q.includes("retract") || q.includes("close petal")) {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("iris-toggle-petals"))
    }
    const isExpanding = q.includes("expand") || q.includes("open") || q.includes("show")
    return {
      modified: true,
      message: `🌸 **3D Flora Stage ${isExpanding ? "Expanded" : "Retracted"} by REN!**\n\nI have triggered the mechanical expansion of the 3D IRIS petal node callouts on your dashboard. You can inspect Neural Core, Visual Themes, and System Rules directly in 3D space.`,
    }
  }

  // 3. 3D Wireframe Diagnostic Mode
  if (q.includes("wireframe")) {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("iris-wireframe-toggle"))
    }
    return {
      modified: true,
      message: `🕸️ **3D Wireframe Mode Toggled by REN!**\n\nI have toggled the botanical mesh shader between raw vector wireframe topology and bioluminescent surface Fresnel shading. Look at the background 3D flower canvas!`,
    }
  }

  // 4. Bioluminescent Glow Intensity
  if (q.includes("glow") || q.includes("bright") || q.includes("radiance")) {
    const isMax = q.includes("max") || q.includes("more") || q.includes("increase") || q.includes("boost")
    const glowVal = isMax ? 7 : 2
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("iris-glow-change", { detail: { glow: glowVal } }))
    }
    return {
      modified: true,
      message: `✨ **Bioluminescent Radiance ${isMax ? "Boosted" : "Adjusted"} by REN!**\n\nI have updated the ambient Fresnel shader intensity to **${glowVal}x**. The ethereal glow surrounding the 3D flower has been recalibrated.`,
    }
  }

  // 5. Autonomous Skill Toggles
  const skillKeywords = [
    { match: /vision|camera|screen/i, name: "PC Vision & Screen OCR", id: "vision" },
    { match: /voice|wake word|mic|listening/i, name: "Voice & Wake Word Listening", id: "voice_always_on" },
    { match: /code|runner|vs code|script/i, name: "VS Code Program Runner", id: "code_assistant" },
    { match: /pc control|system control|mouse|keyboard/i, name: "PC & System Control", id: "pc_control" },
    { match: /messaging|whatsapp/i, name: "Universal Messaging & WhatsApp", id: "universal_messaging" },
  ]

  if (q.includes("enable") || q.includes("disable") || q.includes("turn on") || q.includes("turn off")) {
    const isEnable = q.includes("enable") || q.includes("turn on")
    for (const s of skillKeywords) {
      if (s.match.test(q)) {
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("iris-skill-toggle", { detail: { skillId: s.id, enabled: isEnable } }))
        }
        return {
          modified: true,
          message: `🦾 **Autonomous Skill Updated by REN!**\n\nI have ${isEnable ? "🟢 **Enabled**" : "🔴 **Disabled**"} the **${s.name}** skill in IRIS's runtime execution matrix.`,
        }
      }
    }
  }

  return { modified: false, message: "" }
}

/**
 * Dynamically and autonomously generates the exact installation command based on
 * the current deployed URL (origin/host) and the user's specific target environment.
 */
function generateAutonomousCommand(origin: string, query: string): string {
  const cleanOrigin = origin || "http://localhost:3000"
  let host = "localhost"
  let isHttps = cleanOrigin.startsWith("https://")
  let isLocalhost = cleanOrigin.includes("localhost") || cleanOrigin.includes("127.0.0.1")

  try {
    const url = new URL(cleanOrigin)
    host = url.hostname || "localhost"
  } catch {}

  const q = query.toLowerCase()

  // 1. Another PC / Target PC specific request
  if ((q.includes("another") && q.includes("pc")) || q.includes("other pc") || q.includes("target pc") || q.includes("remote pc")) {
    let wifiCmd = ""

    if (isHttps || (!isLocalhost && !host.startsWith("192.168.") && !host.startsWith("10.") && !host.startsWith("172."))) {
      // Cloud/Web Deployment
      wifiCmd = `powershell -ExecutionPolicy Bypass -Command "irm '${cleanOrigin}/api/install/script/windows/latest' | iex"`
    } else if (host.startsWith("192.168.") || host.startsWith("10.") || host.startsWith("172.")) {
      // Local Network IP
      wifiCmd = `powershell -ExecutionPolicy Bypass -Command "irm http://${host}:8765/install | iex"`
    } else {
      // Localhost fallback
      wifiCmd = `powershell -ExecutionPolicy Bypass -Command "irm http://192.168.29.166:8765/install | iex"`
    }

    return `### 🚀 Autonomous Installation Command for Another PC (Generated by REN)

I have dynamically created the exact command for your deployment:

\`\`\`cmd
${wifiCmd}
\`\`\`

#### Deployment Architecture:
\`\`\`
[Target PC CMD] ──> [Fetch from ${host}] ──> [2s Diagnostic Check] ──> [iris.1 model Setup] ──> [Live :5743]
\`\`\`

#### What will happen automatically on the target PC:
1. **Transfers \`iris.1 model\`**: Downloads the clean 78 MB package directly to \`%USERPROFILE%\\Desktop\\IRIS-AI\`.
2. **2-Second Pre-Flight Check**: Checks Python 3.11+, IRIS Neural Core, and dependencies.
3. **Auto-Install & Self-Healing**: Automatically installs missing tools without prompts.
4. **Desktop Integration**: Creates the **\`IRIS AI\`** Desktop shortcut and global \`iris\` command.
5. **Boots IRIS**: Starts the backend engine and Web UI automatically!`
  }

  // 2. GitHub Deployment
  if (q.includes("github") || q.includes("repo") || q.includes("git clone")) {
    return `### 📦 Deploying via GitHub Repository (Generated by REN)

Here is the exact command to clone and configure **IRIS AI**:

\`\`\`cmd
git clone https://github.com/iris-ai/IRIS-AI.git && cd IRIS-AI && install.bat
\`\`\`

#### What this accomplishes:
1. Clones the clean repository with the **\`iris.1 model\`** folder.
2. Runs the built-in **2-second pre-flight diagnostic** to check Python and IRIS Neural Core.
3. Automatically creates a fresh virtual environment specifically compiled for that PC.
4. Creates the **\`IRIS AI\`** desktop shortcut and launches the application!`
  }

  // 3. USB Pen Drive Offline Transfer
  if (q.includes("usb") || q.includes("pendrive") || q.includes("offline")) {
    return `### 💾 Offline USB Pen Drive Installation (Generated by REN)

Plug your USB drive containing **\`IRIS-AI\`** into the target PC, open **CMD**, and run:

\`\`\`cmd
powershell -ExecutionPolicy Bypass -Command "$f = Get-ChildItem -Path ($HOME, 'D:\\', 'E:\\', 'F:\\', 'G:\\', 'C:\\') -Filter 'install.ps1' -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1; if ($f) { Set-Location $f.DirectoryName; & .\\install.ps1 } else { Write-Host 'Error: Please plug in your USB drive containing IRIS-AI.' -ForegroundColor Red }"
\`\`\`

The script automatically searches all drive letters (\`D:\`, \`E:\`, \`F:\`, etc.), runs the 2-second diagnostic, and configures the environment!`
  }

  // 4. Pre-Flight Diagnostic Check Explanation
  if (q.includes("diagnostic") || q.includes("check") || q.includes("pre-flight")) {
    return `### 🔍 How the 2-Second Pre-Flight Diagnostic Works (by REN)

When you run the installer, it performs an instant 6-point verification before installing:

\`\`\`
>>> RUNNING PRE-FLIGHT HEALTH DIAGNOSTIC...
 [?] 1. Python Runtime (3.11+) .............. [PASS / AUTO-INSTALL]
 [?] 2. IRIS Neural Core Runtime ............ [PASS / AUTO-INSTALL]
 [?] 3. Node.js / npm Environment .......... [PASS / AUTO-INSTALL]
 [?] 4. IRIS.1 Core System Files ............ [PASS / VERIFIED]
 [?] 5. Python Virtual Environment (.venv) .. [PASS / REBUILD IF MACHINE CHANGED]
 [?] 6. Cognitive Memory & Profiles (~/.iris) [PASS / MIGRATED]
\`\`\`

* **Speed**: Runs in **~1.2 seconds**.
* **Zero Redundant Downloads**: If Python or IRIS Neural Core is already present, it skips downloading.
* **Auto-Repair**: If \`.venv\` belongs to another machine's path, it cleanly rebuilds it automatically.`
  }

  // 5. Autonomous Command based on Deployed Origin
  if (isHttps || (!isLocalhost && !host.startsWith("192.168.") && !host.startsWith("10.") && !host.startsWith("172."))) {
    // Cloud Deployed URL
    return `### ⚡ Autonomous Web-Deployment Command (Generated by REN)

Since this dashboard is deployed live at **\`${cleanOrigin}\`**, I have autonomously generated the one-command installer for any Windows PC:

\`\`\`cmd
powershell -ExecutionPolicy Bypass -Command "irm '${cleanOrigin}/api/install/script/windows/latest' | iex"
\`\`\`

#### How it works:
* Open **Command Prompt (CMD)** or **PowerShell** on any target Windows computer.
* Paste the command above and press **Enter**.
* It connects directly to this server, downloads **\`iris.1 model\`**, verifies Python & IRIS Neural Core, and configures everything in under 20 seconds!`
  }

  if (host.startsWith("192.168.") || host.startsWith("10.") || host.startsWith("172.")) {
    // LAN / Wi-Fi Deployed URL
    return `### ⚡ Autonomous Local Network (Wi-Fi) Command (Generated by REN)

Since your dashboard is running on local network IP **\`${host}\`**, here is the 1-click command to install on any PC connected to the same Wi-Fi:

\`\`\`cmd
powershell -ExecutionPolicy Bypass -Command "irm http://${host}:8765/install | iex"
\`\`\`

*(Ensure you have double-clicked \`serve_to_other_pc.bat\` on the host PC so port 8765 is actively serving).*`
  }

  // Default Localhost Environment
  return `### ⚡ Autonomous Universal Windows Command (Generated by REN)

To install and launch **IRIS AI** with **\`iris.1 model\`** on this machine, run this command in **CMD from ANY directory**:

\`\`\`cmd
powershell -ExecutionPolicy Bypass -Command "$f = Get-ChildItem -Path ($HOME, 'D:\\', 'E:\\', 'C:\\') -Filter 'install.ps1' -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1; if ($f) { Set-Location $f.DirectoryName; & .\\install.ps1 } else { Write-Host 'Error: IRIS-AI folder not found.' -ForegroundColor Red }"
\`\`\`

#### Or if you are already inside the project folder:
\`\`\`cmd
install.bat
\`\`\`

*Both commands automatically verify Python 3.11+, IRIS Neural Core, create the Desktop shortcut, and launch the assistant.*`
}

/**
 * Generates rich, contextual conversational replies to user questions
 * when they are conversing rather than asking for terminal commands.
 */
function generateConversationalReply(query: string, origin: string): string {
  const q = query.toLowerCase().trim()

  // 1. Greetings & Small Talk
  if (/^(hi|hello|hey|greetings|howdy|yo|good morning|good evening|good afternoon)(\s+.*)?$/i.test(q)) {
    return `👋 Hello! I am **REN**. How can I assist you today?`
  }

  // 2. Who is REN / What are your frontend powers
  if (q.includes("who are you") || q.includes("what are your powers") || q.includes("what can you change") || q.includes("frontend") || q.includes("powers")) {
    return `### ⚡ Meet REN • Autonomous Systems Architect

I am **REN**. My role is to help you manage, configure, and operate **IRIS**:

#### 🎨 1. My Superpower to Change the IRIS Frontend:
I have direct architectural control over the IRIS frontend! You can command me directly in chat:
* **Switch Themes**: *"REN, change theme to Cyber Terminal"*, *"Switch to Hologram Orb"*, *"Change to Voice Spectrum"*, *"Switch to Liquid Blob"*.
* **Control the 3D Flora Canvas**: *"REN, expand 3D petals"*, *"Retract petals"*, *"Toggle wireframe mode"*, *"Make flower glow more"*.
* **Toggle Autonomous Skills**: *"REN, enable vision"*, *"Disable voice"*, *"Enable PC control"*, *"Enable code runner"*.

#### 🚀 2. Autonomous Deployment Generator:
Whenever you ask for the command, I generate the exact 1-click terminal command tailored to your live deployment so you can install IRIS on this PC or another machine.

#### 🧠 3. System Guidance:
I can explain any component of IRIS (Voice, Vision, 3-tier Memory, Hands/Automation, Local Neural Core).`
  }

  // 3. What is IRIS
  if (q.includes("what is iris") || q.includes("what can iris do") || q.includes("features")) {
    return `### 🌸 About IRIS AI (Guided by REN)

**IRIS AI** is your autonomous, 100% private personal AI companion designed to run locally on your computer with **zero cloud data leakage**.

#### Key Capabilities of IRIS:
* **🧠 Offline Neural Brain (\`iris.1 model\`)**: Runs high-performance local neural models with zero internet required.
* **👁️ Real-Time Computer Vision**: Understands your screen, reads text (OCR), detects windows, and recognizes user presence.
* **🎙️ Full-Duplex Voice**: Low-latency voice interaction with live interruption (barge-in) and natural emotional tone.
* **💾 Persistent 3-Tier Memory Vault**: Encrypted long-term recall stored locally in \`~/.iris\`.
* **🦾 Autonomous Hands**: Launches apps, interacts with windows, and executes system tasks.

*Tip: As **REN**, I can change IRIS's visual theme or generate your setup command anytime!*`
  }

  // 4. Vision & Camera Questions
  if (q.includes("vision") || q.includes("camera") || q.includes("see") || q.includes("eyes") || q.includes("screen")) {
    return `### 👁️ How IRIS Computer Vision Works

IRIS has a multi-modal perception pipeline that runs locally on your PC:
* **Screen Perception**: Real-time screen capture and OCR to read articles, code, browser windows, and errors.
* **Webcam & Presence**: Detects when you are at your desk, tracks attention, and estimates emotional state.
* **Biometric Security**: Authorizes commands only for registered Commanders and alerts on unauthorized users.

All visual processing is handled locally without uploading images to any third-party servers.`
  }

  // 5. Voice & Speech Questions
  if (q.includes("voice") || q.includes("speak") || q.includes("speech") || q.includes("mic") || q.includes("audio") || q.includes("whisper") || q.includes("tts")) {
    return `### 🎙️ How IRIS Voice Interaction Works

IRIS is engineered for fluid, real-time spoken conversations:
* **Voice Activity Detection (VAD)**: Powered by Silero VAD to detect when you start and stop talking in under 30ms.
* **Speech-to-Text (STT)**: High-accuracy transcription using local Whisper models.
* **Barge-In (Interruption)**: If IRIS is speaking and you start talking, it immediately stops and listens to you.
* **Emotional Speech Synthesis (TTS)**: Modulates pitch, pacing, and tone based on conversation context.`
  }

  // 6. Memory & Privacy Questions
  if (q.includes("memory") || q.includes("remember") || q.includes("privacy") || q.includes("vault") || q.includes("offline")) {
    return `### 💾 IRIS Memory Architecture & Privacy

* **100% Local**: All memories, profiles, and logs are kept strictly on your machine in \`%USERPROFILE%\\.iris\`.
* **3-Tier Hierarchy**:
  1. *Working Memory*: Active session context.
  2. *Episodic Buffer*: Recent daily actions and discussions.
  3. *Semantic Vector Vault*: Long-term facts, preferences, and project insights.
* **Zero Telemetry**: No company server or third-party ever receives your data.`
  }

  // 7. General Contextual Response
  return `I understand! Regarding "${query.trim()}":

As **REN**, I am here to ensure IRIS operates at peak performance for you.

* If you'd like me to **change the frontend of IRIS**, tell me: *"REN, change theme to Cyber Terminal"* or *"REN, expand 3D petals"*.
* If you want to **install IRIS on this PC or another machine**, ask: *"Give me the install command"*.
* What would you like to adjust or explore next?`
}

export default function ChatPage() {
  // Start with empty messages so no card or text floats over the flower on load
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [convoStatus, setConvoStatus] = useState<ConvoStatus | null>(null)
  const [engineOnline, setEngineOnline] = useState(false)
  const [origin, setOrigin] = useState("http://localhost:3000")
  const bottomRef = useRef<HTMLDivElement>(null)

  const quickPrompts = [
    { label: "🎨 REN, change theme to Cyber Terminal", query: "REN, change theme to Cyber Terminal" },
    { label: "🌸 REN, expand 3D petal callouts", query: "REN, expand 3D petals" },
    { label: "🕸️ REN, toggle 3D wireframe mode", query: "REN, toggle wireframe mode" },
    { label: "⚡ Give me the install command", query: "Give me the command to install IRIS on this PC" },
    { label: "🚀 Install on Another PC", query: "Give me the command to install on another PC" },
    { label: "💬 What frontend powers do you have, REN?", query: "What frontend powers do you have, REN?" },
  ]

  const updateStatus = useCallback(async () => {
    if (!engineOnline) return
    try {
      const s = await api.chat.status()
      setConvoStatus(s)
    } catch {
      setEngineOnline(false)
    }
  }, [engineOnline])

  useEffect(() => {
    if (typeof window !== "undefined") {
      setOrigin(window.location.origin)
    }
    fetch("/api/status", { signal: AbortSignal.timeout(1500) })
      .then((r) => {
        if (r.ok) {
          setEngineOnline(true)
          api.chat.status().then(setConvoStatus).catch(() => {})
        }
      })
      .catch(() => setEngineOnline(false))
  }, [])

  useEffect(() => {
    if (!engineOnline) return
    const interval = setInterval(updateStatus, 8000)
    return () => clearInterval(interval)
  }, [engineOnline, updateStatus])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function handleSend(input: string) {
    const trimmed = (input || "").trim()
    if (!trimmed) return

    const userMsg: Message = { role: "user", content: trimmed, timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    // POWER 1: REN's superpower to modify the IRIS frontend live!
    const frontendAction = executeFrontendModification(trimmed)
    if (frontendAction.modified) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: frontendAction.message,
          timestamp: new Date(),
        },
      ])
      setLoading(false)
      return
    }

    // POWER 2: REN's autonomous installation / deployment command generation
    const asksForCommand = isAskingForCommand(trimmed)
    if (asksForCommand) {
      const cmdResponse = generateAutonomousCommand(origin, trimmed)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: cmdResponse,
          timestamp: new Date(),
        },
      ])
      setLoading(false)
      return
    }

    // POWER 3: Regular conversation — if local engine is online, use live LLM backend
    if (engineOnline) {
      try {
        const res = await api.chat.send(trimmed)
        const assistantMsg: Message = {
          role: "assistant",
          content: res.response || "No response received.",
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMsg])
        await updateStatus()
        setLoading(false)
        return
      } catch {
        // Fallback to REN's built-in conversational intelligence
      }
    }

    // POWER 4: REN's Conversational Intelligence Guide (answers user's actual question properly!)
    setTimeout(() => {
      const conversationalResponse = generateConversationalReply(trimmed, origin)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: conversationalResponse,
          timestamp: new Date(),
        },
      ])
      setLoading(false)
    }, 40)
  }

  async function handleNewSession() {
    try {
      await api.chat.newSession()
    } catch {}
    setMessages([])
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] w-full max-w-[460px] lg:max-w-[480px] xl:max-w-[500px] mr-auto bg-[#070914]/85 backdrop-blur-2xl border border-white/10 rounded-3xl p-4 sm:p-5 shadow-2xl relative z-20">
      {/* Compact Left-Corner Header */}
      <div className="flex items-start justify-between gap-2 mb-3 border-b border-white/10 pb-3">
        <div>
          <h1 className="text-sm sm:text-base font-bold flex items-center gap-1.5 text-white">
            <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>REN &bull; Systems Architect</span>
          </h1>
          <p className="text-[11px] text-white/50 mt-0.5 flex flex-wrap items-center gap-1.5 font-mono">
            <span>AI: <strong className="text-cyan-300">REN</strong></span>
            <span>&bull;</span>
            <span>Model: <span className="text-iris-400">iris.1</span></span>
            <span>&bull;</span>
            {engineOnline ? (
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Online
              </span>
            ) : (
              <span className="flex items-center gap-1 text-cyan-300 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                Active
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-cyan-300/90 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-md font-mono shrink-0">
          <Palette className="w-3 h-3 text-cyan-400" />
          <span>Live Control</span>
        </div>
      </div>

      {convoStatus && (
        <div className="mb-2">
          <TokenBar
            tokensUsed={convoStatus.tokens_used}
            maxTokens={convoStatus.max_tokens}
            ratio={convoStatus.ratio}
            status={convoStatus.status}
            message={convoStatus.message}
            messageCount={convoStatus.message_count}
            onNewSession={handleNewSession}
          />
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-white/40">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-2">
              <Bot className="w-5 h-5" />
            </div>
            <span className="text-xs font-medium text-white/70">Chat with REN</span>
            <span className="text-[11px] text-white/40 mt-1 max-w-[260px] leading-relaxed">
              Ask me to customize the frontend, switch themes, or generate your deployment command.
            </span>
          </div>
        ) : (
          messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
          ))
        )}

        {loading && (
          <div className="flex gap-2.5">
            <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-[#0f1322] border border-cyan-500/30 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="flex items-center gap-1.5 px-3 py-2 rounded-2xl bg-[#0b0e1b]/80 border border-white/10">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Quick Action Pills */}
      <div className="pt-2 pb-2 flex flex-wrap gap-1.5">
        {quickPrompts.slice(0, 4).map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p.query)}
            disabled={loading}
            className="text-[11px] px-2.5 py-1 rounded-lg bg-white/[0.04] hover:bg-cyan-500/10 active:bg-cyan-500/20 text-white/70 hover:text-cyan-300 border border-white/10 hover:border-cyan-500/30 transition-all duration-75 active:scale-95 select-none cursor-pointer touch-manipulation flex items-center gap-1"
          >
            <span>{p.label}</span>
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="mt-1">
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  )
}
