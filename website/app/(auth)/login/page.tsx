"use client"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Card } from "@/components/ui/Card"
import Link from "next/link"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Sparkles, ArrowLeft, Shield, Zap, Eye, EyeOff } from "lucide-react"
import RobotCharacter from "@/components/ui/RobotCharacter"

export default function LoginPage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [form, setForm] = useState({ email: "", password: "" })
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    try {
      const res = await api.auth.login(form)
      localStorage.setItem("iris_token", res.token)
      localStorage.setItem("iris_refresh", res.refresh_token)

      const params = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null
      const returnUrl = params?.get("return")
      const plan = params?.get("plan")
      if (returnUrl) {
        router.push(plan ? `${returnUrl}?plan=${plan}` : returnUrl)
      } else if (plan) {
        router.push(`/pricing?plan=${plan}`)
      } else {
        router.push("/dashboard")
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen bg-white relative overflow-hidden flex flex-col justify-between text-slate-900 selection:bg-cyan-500/20"
      style={{
        backgroundImage:
          "linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
      }}
    >
      {/* =========================================================
          FULL-SCREEN 3D ROBOT LAYER (ON GROUND, UNDER LOGIN CARD)
          Glides seamlessly along the floor across the whole screen.
          When cursor moves right, it passes right under the login card!
          ========================================================= */}
      {mounted && (
        <div className="fixed inset-0 w-full h-full pointer-events-none z-0 overflow-hidden">
          <RobotCharacter
            color="#d4d4d8"
            pantallaColor="#00d4b8"
            pantallaBrillo={1.4}
            scale={1.35}
            theme="light"
            className="w-full h-full"
            isTyping={isTyping}
          />
        </div>
      )}

      {/* Top Navigation Bar */}
      <header className="relative z-20 w-full px-6 py-6 max-w-7xl mx-auto flex items-center justify-between pointer-events-auto">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-mono text-slate-600 hover:text-slate-950 transition-colors px-3.5 py-1.5 rounded-full border border-slate-200 bg-white/80 backdrop-blur-md shadow-sm hover:border-slate-300"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Home</span>
        </Link>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-600 px-3 py-1 rounded-full bg-slate-100/80 border border-slate-200 backdrop-blur-sm shadow-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>IRIS ENGINE ONLINE</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 w-full max-w-7xl mx-auto px-6 pt-4 pb-8 lg:pt-6 lg:pb-12 flex-1 flex flex-col lg:flex-row items-start justify-between pointer-events-none gap-8">
        
        {/* =========================================================
            TOP LEFT: SHOWCASE HEADLINE & BADGES (KEPT ON LEFT TOP)
            ========================================================= */}
        <div className="flex flex-col max-w-lg select-none pointer-events-none pr-4 lg:pr-8 self-start pt-2">
          {/* Pill Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-50 border border-cyan-200/90 text-cyan-800 mb-4 w-fit shadow-sm">
            <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
            <span>AUTONOMOUS NEURAL RIG ACTIVE</span>
          </div>

          {/* Main Title */}
          <h1 className="text-4xl xl:text-5xl font-black tracking-tight text-slate-950 mb-4 leading-[1.1]">
            Your Private <br />
            <span className="bg-gradient-to-r from-cyan-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent filter drop-shadow-[0_2px_15px_rgba(99,102,241,0.2)]">
              Intelligent Iris.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-slate-600 text-sm leading-relaxed mb-6 font-normal">
            Move your cursor anywhere across the entire screen — Iris glides along the ground plane in real time, skating underneath and around your workspace.
          </p>

          {/* Feature Badges */}
          <div className="flex flex-wrap items-center gap-2.5 text-xs text-slate-700 font-mono">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100/90 border border-slate-200 shadow-sm backdrop-blur-sm">
              <Shield className="w-3.5 h-3.5 text-cyan-600" /> 100% Air-Gapped
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100/90 border border-slate-200 shadow-sm backdrop-blur-sm">
              <Zap className="w-3.5 h-3.5 text-emerald-600" /> Real-Time Local AI
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100/90 border border-slate-200 shadow-sm backdrop-blur-sm">
              <Sparkles className="w-3.5 h-3.5 text-purple-600" /> Click Iris for Hearts
            </span>
          </div>
        </div>

        {/* =========================================================
            RIGHT SIDE: MODERN GLASSMORPHIC LOGIN CARD
            When robot skates right, it passes right under / behind this card!
            ========================================================= */}
        <div className="w-full max-w-md pointer-events-auto lg:ml-auto self-center lg:self-start pt-2">
          <Card id="login-card" className="w-full p-8 border border-slate-200/90 bg-white/85 backdrop-blur-2xl shadow-[0_20px_60px_-15px_rgba(15,23,42,0.12)] relative overflow-hidden rounded-2xl">
            {/* Top cyan gradient neon accent */}
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent" />

            <div className="text-center mb-7">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center mx-auto mb-3 shadow-[0_0_20px_rgba(6,182,212,0.3)]">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-black tracking-tight text-slate-900">Welcome Back</h2>
              <p className="text-sm text-slate-500 mt-1">Sign in to your private IRIS workspace</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Email"
                type="email"
                id="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                onFocus={() => setIsTyping(true)}
                onBlur={() => setIsTyping(false)}
                required
                labelClassName="text-slate-800 font-bold text-xs uppercase tracking-wider mb-1.5 block"
                style={{ color: "#f1f5f9", WebkitTextFillColor: "#f1f5f9" }}
                className="bg-[#4b5260] text-slate-100 border border-slate-500/60 placeholder:text-slate-300/60 focus:bg-[#535b6a] focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 rounded-xl py-3.5 px-4 font-semibold shadow-inner caret-slate-100"
              />

              <div className="relative">
                <Input
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  id="password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                  required
                  labelClassName="text-slate-800 font-bold text-xs uppercase tracking-wider mb-1.5 block"
                  style={{ color: "#f1f5f9", WebkitTextFillColor: "#f1f5f9" }}
                  className="bg-[#4b5260] text-slate-100 border border-slate-500/60 placeholder:text-slate-300/60 focus:bg-[#535b6a] focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 rounded-xl py-3.5 pl-4 pr-12 font-semibold shadow-inner caret-slate-100"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3.5 top-[34px] p-1.5 text-slate-300 hover:text-white transition-colors rounded-lg focus:outline-none"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-600 font-medium">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-slate-950 text-white hover:bg-slate-900 font-bold shadow-lg hover:shadow-xl transition-all py-3.5 rounded-xl border border-slate-800 mt-2 tracking-wide"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In to IRIS"}
              </Button>
            </form>

            <div className="mt-6 pt-5 border-t border-slate-100 text-center">
              <p className="text-sm text-slate-500">
                Don&apos;t have an account?{" "}
                <Link href="/signup" className="text-cyan-600 hover:text-cyan-700 hover:underline font-semibold">
                  Sign up
                </Link>
              </p>
            </div>
          </Card>
        </div>

      </main>

      {/* Footer */}
      <footer className="relative z-20 py-4 px-6 text-xs text-slate-500 font-mono pointer-events-auto flex flex-col sm:flex-row items-center justify-between max-w-7xl mx-auto w-full gap-2">
        <span>IRIS AI &bull; Autonomous Desktop Intelligence &bull; 100% Private</span>
        <span className="text-cyan-700 font-medium">Move cursor anywhere &bull; Iris glides on the ground floor</span>
      </footer>
    </div>
  )
}
