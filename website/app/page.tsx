"use client";

import { Navbar } from "@/components/ui/Navbar"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { SpaceTunnelBackground } from "@/components/ui/SpaceTunnelBackground"
import { SocialCards } from "@/components/ui/card-fan-carousel"
import { CardHandGallery, type FanCardItem } from "@/components/ui/card-hand-gallery"
import {
  ArrowRight,
  Lock,
  Cpu,
  Brain,
  Shield,
  Zap,
  Download,
  Command,
  Mic,
  Eye,
  CheckCircle2,
  Terminal,
  Activity,
  Sparkles,
  WifiOff,
  ServerOff,
  FileCode,
  Volume2
} from "lucide-react"
import Link from "next/link"

const features = [
  {
    icon: Lock,
    tag: "Privacy Core",
    title: "100% Private & Air-Gapped",
    desc: "Everything runs exclusively on your machine. Zero conversations, zero files, and zero telemetry ever leave your hardware.",
    imgUrl: "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80",
    alt: "Privacy Core",
  },
  {
    icon: Cpu,
    tag: "Autonomous Compute",
    title: "Runs Locally on Your PC",
    desc: "No third-party cloud servers or monthly compute surcharges. Powered by local IRIS.1 neural models on your own GPU/CPU.",
    imgUrl: "https://images.unsplash.com/photo-1591488320449-011701bb6704?auto=format&fit=crop&w=800&q=80",
    alt: "Autonomous Compute",
  },
  {
    icon: Brain,
    tag: "Adaptive Intelligence",
    title: "3-Tier Cognitive Memory",
    desc: "Remembers who you are across days, weeks, and months. Short-term scratchpad, working to-dos, and deep permanent knowledge.",
    imgUrl: "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80",
    alt: "Adaptive Intelligence",
  },
  {
    icon: Zap,
    tag: "Desktop Hands",
    title: "Native Desktop Automation",
    desc: "Open apps, organize files, write scripts in VS Code, execute safe terminal commands, and control windows effortlessly.",
    imgUrl: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80",
    alt: "Desktop Hands",
  },
  {
    icon: Mic,
    tag: "Real-Time Audio",
    title: "Natural Neural Voice & Ears",
    desc: "Fast hands-free ambient listening with intelligent noise suppression, sweet conversational cadence, and seamless turn-taking.",
    imgUrl: "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=800&q=80",
    alt: "Real-Time Audio",
  },
  {
    icon: Eye,
    tag: "Computer Vision",
    title: "Multi-Modal Visual Sense",
    desc: "Inspects your screen, reads documents via OCR, understands code windows, and provides contextual help right when you need it.",
    imgUrl: "https://images.unsplash.com/photo-1507499739999-097706ad8914?auto=format&fit=crop&w=800&q=80",
    alt: "Computer Vision",
  },
]

const statCards: FanCardItem[] = [
  {
    id: "zero-bytes",
    src: "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=600&q=80",
    title: "0 Bytes to Cloud",
    description: "Zero external network requests, telemetry, or server prompts. All conversations, code analysis, and document indexing stay strictly inside your physical machine.",
    value: "0 Bytes",
    subtitle: "Data Sent to Cloud",
    tag: "AIR-GAPPED",
    icon: ServerOff,
  },
  {
    id: "voice-latency",
    src: "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
    title: "<200ms Neural Voice",
    description: "Ultra-fast voice response loop featuring streaming sentence-boundary synthesis, ONNX Silero VAD, and instant conversational barge-in.",
    value: "<200ms",
    subtitle: "Voice Response Latency",
    tag: "REAL-TIME",
    icon: Zap,
  },
  {
    id: "three-tier-memory",
    src: "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80",
    title: "3-Tier Permanent Memory",
    description: "Cognitive persistence spanning real-time scratchpad, active task working to-dos, and an encrypted permanent SQLite vector database across all your sessions.",
    value: "3-Tier",
    subtitle: "Permanent Memory",
    tag: "COGNITIVE",
    icon: Brain,
  },
  {
    id: "offline-capability",
    src: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80",
    title: "100% Offline Autonomy",
    description: "Full desktop assistance without an internet connection. Local neural models, high-speed neural TTS, and direct Windows OS automation run uninterrupted anywhere.",
    value: "100%",
    subtitle: "Offline Capability",
    tag: "OFFLINE FIRST",
    icon: WifiOff,
  },
]

export default function HomePage() {
  return (
    <div className="relative min-h-screen grid-bg overflow-x-hidden text-white selection:bg-iris-500/30">
      {/* Hyperspace 3D WebGL Space Tunnel Background Animation */}
      <SpaceTunnelBackground opacity={0.88} speed={1.0} rings={4.0} />

      {/* Navigation Header */}
      <Navbar />

      {/* =========================================================
          HERO SECTION (Centered "One Under One" Stacked Layout)
          ========================================================= */}
      <section className="relative z-10 pt-36 sm:pt-44 pb-20 px-6 sm:px-10 lg:px-16 max-w-7xl mx-auto">
        <div className="max-w-4xl mx-auto flex flex-col items-center text-center">
          {/* Main Headline - Stacked "one under one" with cool style (Centered) */}
          <h1 className="flex flex-col items-center text-center font-black tracking-tight mb-8 select-none">
            {/* Line 1 */}
            <span className="text-4xl sm:text-6xl md:text-7xl lg:text-[5.4rem] xl:text-[6.2rem] font-extrabold text-white tracking-tight leading-[0.98] drop-shadow-[0_4px_30px_rgba(0,0,0,0.9)]">
              Your Own
            </span>

            {/* Line 2 - Radiant Cyber Iris in gradient glow */}
            <span className="text-5xl sm:text-7xl md:text-8xl lg:text-[6.8rem] xl:text-[7.6rem] font-black tracking-tighter leading-[0.95] py-1 bg-gradient-to-r from-purple-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent drop-shadow-[0_0_55px_rgba(168,85,247,0.7)] filter brightness-110">
              Private Iris
            </span>

            {/* Line 3 - Sleek Metallic with glowing cyan period dot */}
            <span className="text-3xl sm:text-5xl md:text-6xl lg:text-[4.6rem] xl:text-[5.2rem] font-extrabold tracking-tight text-slate-200 leading-[1.02] drop-shadow-[0_4px_25px_rgba(0,0,0,0.9)] flex items-center justify-center gap-2 sm:gap-3">
              Born on Your PC<span className="text-cyan-400 drop-shadow-[0_0_20px_#22d3ee]">.</span>
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-slate-300/85 max-w-2xl mx-auto mb-10 leading-relaxed font-normal text-center drop-shadow-[0_2px_12px_rgba(0,0,0,0.9)]">
            The first truly private, local personal AI assistant. Knows your life, controls your desktop,
            learns you over time — and{" "}
            <span className="text-white font-medium underline decoration-iris-400/60 underline-offset-4">
              never transmits a single byte to external servers.
            </span>
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10 w-full sm:w-auto">
            <Link href="/signup" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto shadow-[0_0_35px_rgba(99,102,241,0.45)] group">
                <Sparkles className="w-4 h-4 mr-2 text-cyan-300" />
                Get Started Free
                <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-300 group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="/pricing" className="w-full sm:w-auto">
              <Button variant="outline" size="lg" className="w-full sm:w-auto border-white/20 hover:border-iris-400/60 bg-slate-950/50 backdrop-blur-md">
                See Pricing & Plans
              </Button>
            </Link>
          </div>

          {/* Trust Guarantees */}
          <div className="flex flex-wrap items-center justify-center gap-5 sm:gap-6 text-xs md:text-sm text-slate-300/70">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> No credit card required
            </span>
            <span className="w-1 h-1 rounded-full bg-white/20 hidden sm:inline-block" />
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Works 100% offline
            </span>
            <span className="w-1 h-1 rounded-full bg-white/20 hidden sm:inline-block" />
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Windows / macOS / Linux
            </span>
          </div>
        </div>

        {/* =========================================================
            LIVE INTERACTIVE ASSISTANT PREVIEW (HERO SHOWCASE)
            ========================================================= */}
        <div className="max-w-4xl mx-auto mt-20">
          <div className="relative rounded-2xl border border-white/10 bg-[#0d0d14]/85 backdrop-blur-xl shadow-[0_20px_60px_-15px_rgba(99,102,241,0.25)] overflow-hidden">
            {/* Terminal Window Top Bar */}
            <div className="px-4 py-3 bg-white/[0.03] border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="ml-3 text-xs font-mono text-white/40 flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-iris-400" />
                  iris-core:5743 — localhost
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  LOCAL ENGINE ACTIVE
                </span>
              </div>
            </div>

            {/* Conversation Simulation */}
            <div className="p-6 md:p-8 space-y-6 text-sm font-sans">
              {/* User Voice Prompt */}
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center text-white/80 font-semibold text-xs flex-shrink-0">
                  YOU
                </div>
                <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-xs text-iris-400 mb-1 font-mono">
                    <Mic className="w-3.5 h-3.5" /> Spoken via Ambient Microphone:
                  </div>
                  <p className="text-white/90 font-medium">
                    &ldquo;Iris, resume my coding playlist, open my project notes in VS Code, and tell me today&apos;s schedule.&rdquo;
                  </p>
                </div>
              </div>

              {/* Iris Action Execution Pipeline */}
              <div className="pl-12 space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono text-cyan-400/90">
                  <Activity className="w-3.5 h-3.5 animate-spin" />
                  <span>[Cognitive Pipeline] Recalled 2 to-dos from Permanent Memory (Layer 2)</span>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-emerald-400/90">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>[Desktop Hands] Opened VS Code &bull; Mounted workspace notes.txt &bull; Audio Echo Suppressed</span>
                </div>
              </div>

              {/* Iris Response */}
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-iris-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs flex-shrink-0 shadow-[0_0_15px_rgba(99,102,241,0.5)]">
                  <Sparkles className="w-4 h-4 text-cyan-300" />
                </div>
                <div className="flex-1 bg-iris-600/10 border border-iris-500/20 rounded-xl p-4 shadow-[0_0_20px_rgba(99,102,241,0.05)]">
                  <div className="flex items-center justify-between gap-2 text-xs text-iris-300 mb-1">
                    <span className="font-semibold flex items-center gap-1.5">
                      <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
                      Iris Neural Voice (Normal Sweet Pace &bull; 0ms Cloud Latency):
                    </span>
                    <span className="font-mono text-[11px] text-white/40">100% On-Device</span>
                  </div>
                  <p className="text-white/90 leading-relaxed">
                    &ldquo;Right away, Commander! I&apos;ve opened your notes in VS Code and started your music. You have two scheduled milestones today: finishing the project build and reviewing system metrics. I&apos;m right here with you!&rdquo;
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          KEY STATS / PERFORMANCE GUARANTEES (CARD HAND GALLERY)
          ========================================================= */}
      <section className="relative z-10 py-16 px-4 sm:px-6 overflow-hidden">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-6">
            <div className="inline-block px-3 py-1 rounded-full text-xs font-mono bg-iris-500/10 border border-iris-500/20 text-cyan-300 mb-2">
              PERFORMANCE &amp; PRIVACY GUARANTEES
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              Hardware-Accelerated. <span className="gradient-text">Zero Surveillance.</span>
            </h2>
          </div>

          <div className="flex w-full items-center justify-center">
            <CardHandGallery cards={statCards} className="max-w-5xl" />
          </div>
        </div>
      </section>

      {/* =========================================================
          FEATURES SECTION (INTERACTIVE CARD FAN CAROUSEL)
          ========================================================= */}
      <section className="relative z-10 py-24 px-4 sm:px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8 md:mb-12">
            <div className="inline-block px-3 py-1 rounded-full text-xs font-mono bg-iris-500/10 border border-iris-500/20 text-iris-300 mb-3">
              SYSTEM CAPABILITIES
            </div>
            <h2 className="text-3xl md:text-5xl font-extrabold mb-4 tracking-tight">
              Everything You Need.{" "}
              <span className="gradient-text">Zero Compromises.</span>
            </h2>
            <p className="text-white/50 max-w-xl mx-auto text-base md:text-lg">
              IRIS combines multimodal computer vision, permanent 3-tier memory, and native operating system hands into one private engine.
            </p>
          </div>

          <SocialCards cards={features} />
        </div>
      </section>

      {/* =========================================================
          WHY LOCAL MATTERS (CLOUD VS IRIS COMPARISON)
          ========================================================= */}
      <section className="relative z-10 py-20 px-6 bg-white/[0.01] border-y border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-3">
              Why <span className="gradient-text">Local-First AI</span> Matters
            </h2>
            <p className="text-white/50">Stop renting your intelligence from corporations that inspect and train on your personal data.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Standard Cloud AI */}
            <div className="p-6 rounded-2xl border border-red-500/20 bg-red-500/[0.02] space-y-4">
              <div className="flex items-center gap-2 text-red-400 font-semibold text-base">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" /> Traditional Cloud Assistants
              </div>
              <ul className="space-y-3 text-sm text-white/60">
                <li className="flex items-start gap-2.5">
                  <span className="text-red-400 font-bold">&times;</span>
                  Prompts and documents uploaded to remote third-party servers.
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-red-400 font-bold">&times;</span>
                  Unusable during internet blackouts or airplane travel.
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-red-400 font-bold">&times;</span>
                  Recurring monthly subscriptions that increase over time.
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-red-400 font-bold">&times;</span>
                  No ability to click, open local apps, or automate your desktop.
                </li>
              </ul>
            </div>

            {/* IRIS AI */}
            <div className="p-6 rounded-2xl border border-iris-500/40 bg-iris-500/[0.05] space-y-4 shadow-[0_0_30px_rgba(99,102,241,0.1)]">
              <div className="flex items-center gap-2 text-cyan-300 font-semibold text-base">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> IRIS / Iris Engine
              </div>
              <ul className="space-y-3 text-sm text-white/80">
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <strong>100% On-Device:</strong> Zero data ever leaves your computer.
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <strong>Runs Everywhere:</strong> Operates fully offline without internet.
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <strong>Full PC Hands:</strong> Launches software, creates files, writes code.
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <strong>Lifetime Freedom:</strong> Own your AI companion permanently.
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          HOW IT WORKS (2-MINUTE SETUP)
          ========================================================= */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4">
              From Download to <span className="gradient-text">Your AI Running</span>
            </h2>
            <p className="text-white/50 text-base">Setup takes under two minutes. No complex machine learning knowledge required.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                step: "01",
                title: "Create Your AI Profile",
                desc: "Choose your assistant's name, personality, voice tone, and preferred local models.",
              },
              {
                step: "02",
                title: "Run the 1-Click Installer",
                desc: "We configure the IRIS Neural Core, pull optimized quantized neural weights, and set up your workspace.",
              },
              {
                step: "03",
                title: "Connect Desktop Hands",
                desc: "Grant safe execution permissions for launching apps, running code, and reading your screen.",
              },
              {
                step: "04",
                title: "Meet Your Companion",
                desc: "Your floating widget and voice listener launch instantly on your desktop, greeting you by name.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="p-6 rounded-xl border border-white/10 bg-white/[0.02] flex gap-5 items-start hover:border-iris-500/30 transition-colors"
              >
                <div className="text-2xl font-black font-mono text-iris-400/80 bg-iris-600/10 border border-iris-500/20 w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-bold text-base mb-1 text-white/90">{item.title}</h3>
                  <p className="text-sm text-white/50 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================================
          FINAL CALL TO ACTION
          ========================================================= */}
      <section className="relative z-10 py-24 px-6 text-center">
        <div className="max-w-3xl mx-auto p-12 rounded-3xl border border-iris-500/30 bg-gradient-to-b from-iris-500/10 via-purple-600/5 to-transparent backdrop-blur-xl shadow-[0_0_60px_rgba(99,102,241,0.15)]">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-iris-600 to-purple-500 mx-auto flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(99,102,241,0.5)]">
            <Sparkles className="w-8 h-8 text-cyan-300" />
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold mb-4 tracking-tight">
            Ready to Meet Your <span className="gradient-text">Private AI</span>?
          </h2>
          <p className="text-white/60 mb-8 max-w-xl mx-auto text-base">
            Take back control of your privacy and productivity. Zero cloud surveillance. Just you and your intelligent assistant.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" className="w-full sm:w-auto shadow-[0_0_30px_rgba(99,102,241,0.35)]">
                Get Started Free
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Explore Lifetime Plan
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* =========================================================
          FOOTER
          ========================================================= */}
      <footer className="relative z-10 py-8 px-6 border-t border-white/5 bg-[#0a0a0f]/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-white/40">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>IRIS AI &bull; Private. Local. Autonomous.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/features" className="hover:text-white transition-colors">
              Features
            </Link>
            <Link href="/pricing" className="hover:text-white transition-colors">
              Pricing
            </Link>
            <Link href="/login" className="hover:text-white transition-colors">
              Sign In
            </Link>
          </div>
          <div>&copy; {new Date().getFullYear()} IRIS AI Engine. All rights reserved.</div>
        </div>
      </footer>
    </div>
  )
}
