"use client"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Card } from "@/components/ui/Card"
import Link from "next/link"
import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import {
  Sparkles,
  ArrowLeft,
  Shield,
  Zap,
  ChevronDown,
  Cpu,
  Lock,
  Layers,
  CheckCircle2,
  Terminal,
  Activity,
  Eye,
  EyeOff
} from "lucide-react"

const interests = [
  "Technology", "Music", "Gaming", "Programming",
  "Design", "Science", "Business", "Art",
  "Sports", "Reading", "Movies", "Education"
]

export default function SignupPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    email: "",
    password: "",
    name: "",
    age: "",
    job: "",
    location: "",
    goals: "",
    interests: [] as string[],
    ai_name: "IRIS",
  })

  // Scroll tracking for fade in/out animation
  const [scrollY, setScrollY] = useState(0)
  const [windowHeight, setWindowHeight] = useState(1000)

  useEffect(() => {
    if (typeof window === "undefined") return

    setWindowHeight(window.innerHeight)

    const handleScroll = () => {
      setScrollY(window.scrollY)
    }

    const handleResize = () => {
      setWindowHeight(window.innerHeight)
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    window.addEventListener("resize", handleResize, { passive: true })
    handleScroll()

    return () => {
      window.removeEventListener("scroll", handleScroll)
      window.removeEventListener("resize", handleResize)
    }
  }, [])

  // Calculate smooth scroll progress (0.0 at top, 1.0 when scrolled ~400px)
  const scrollThreshold = Math.max(300, windowHeight * 0.45)
  const scrollProgress = Math.min(1, Math.max(0, scrollY / scrollThreshold))

  // Fade out hero prompt when scrolling down
  const heroOpacity = Math.max(0, 1 - scrollProgress * 1.8)

  // Fade in signup box when scrolling down, fade out when scrolling up to top
  const formOpacity = Math.min(1, Math.max(0, (scrollProgress - 0.15) / 0.7))
  const formTranslateX = (1 - formOpacity) * 45 // Glides smoothly from 45px right to 0px
  const isFormActive = formOpacity > 0.05

  function scrollToForm() {
    if (typeof window !== "undefined") {
      window.scrollTo({
        top: scrollThreshold + 50,
        behavior: "smooth",
      })
    }
  }

  function scrollToTop() {
    if (typeof window !== "undefined") {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      })
    }
  }

  function toggleInterest(item: string) {
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(item)
        ? f.interests.filter((i) => i !== item)
        : [...f.interests, item],
    }))
  }

  function goToStep(nextStep: number) {
    setError("")
    if (nextStep === 2 && step === 1) {
      if (!form.name.trim()) {
        setError("Please enter your full name.")
        return
      }
      if (!form.email.trim() || !form.email.includes("@")) {
        setError("Please enter a valid email address.")
        return
      }
      if (form.password.length < 8) {
        setError("Password must be at least 8 characters long.")
        return
      }
    }
    setStep(nextStep)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    try {
      const res = await api.auth.signup({
        email: form.email.trim(),
        password: form.password,
        name: form.name.trim(),
      })
      localStorage.setItem("iris_token", res.token)
      localStorage.setItem("iris_refresh", res.refresh_token)

      const parsedAge = form.age.trim() ? parseInt(form.age.trim(), 10) : undefined
      const validAge = !isNaN(parsedAge as number) && (parsedAge as number) > 0 ? parsedAge : undefined

      try {
        await api.profile.update({
          ...(validAge !== undefined ? { age: validAge } : {}),
          job: form.job.trim() || undefined,
          location: form.location.trim() || undefined,
          goals: form.goals.trim() || undefined,
          interests: form.interests,
          ai_name: form.ai_name.trim() || "IRIS",
        })
      } catch (profileErr) {
        console.warn("Non-fatal profile setup issue:", profileErr)
      }

      const params = typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null
      const plan = params?.get("plan")
      const returnUrl = params?.get("return")
      if (returnUrl) {
        router.push(plan ? `${returnUrl}?plan=${plan}` : returnUrl)
      } else if (plan) {
        router.push(`/pricing?plan=${plan}`)
      } else {
        router.push("/pricing")
      }
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-[220vh] bg-slate-950 text-white selection:bg-cyan-500/30 font-sans">
      {/* =========================================================================
          1. FULLSCREEN 4K VIDEO BACKGROUND: BLUE BLOOM AMONG THE RUINS
          ========================================================================= */}
      <div className="fixed inset-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover scale-[1.02] filter brightness-[0.88] contrast-[1.05]"
        >
          <source src="/videos/blue-bloom-among-the-ruins.mp4" type="video/mp4" />
          <source src="/blue-bloom-among-the-ruins.3840x2160.mp4" type="video/mp4" />
        </video>

        {/* Ambient Gradient Overlays for High-Contrast Cinematic Readability */}
        <div className="absolute inset-0 bg-slate-950/45 mix-blend-multiply" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-slate-950/70" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-950/20 via-transparent to-slate-950/80" />
      </div>

      {/* =========================================================================
          2. STICKY VIEWPORT CONTAINER (FIXED AS YOU SCROLL)
          ========================================================================= */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 py-6 max-w-7xl mx-auto z-10 pointer-events-none">
        
        {/* Top Navigation Bar */}
        <header className="relative w-full flex items-center justify-between pointer-events-auto">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-mono text-cyan-200/80 hover:text-white transition-colors px-3.5 py-1.5 rounded-full border border-cyan-500/30 bg-slate-950/60 backdrop-blur-md shadow-lg hover:border-cyan-400"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>

          <div className="flex items-center gap-3">
            {/* Quick jump to signup if not scrolled yet */}
            {formOpacity < 0.8 && (
              <button
                onClick={scrollToForm}
                className="hidden sm:inline-flex items-center gap-2 text-xs font-mono text-cyan-300 hover:text-white px-3.5 py-1.5 rounded-full border border-cyan-500/40 bg-cyan-950/40 backdrop-blur-md transition-all hover:bg-cyan-900/50"
              >
                <span>Jump to Sign Up</span>
                <ChevronDown className="w-3.5 h-3.5 animate-bounce" />
              </button>
            )}

            <div className="flex items-center gap-2 text-xs font-mono text-slate-300 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-700/60 backdrop-blur-sm shadow-md">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span>NEURAL CORE ONLINE</span>
            </div>
          </div>
        </header>

        {/* =========================================================================
            3. MAIN CONTENT STAGE (HERO INTRO & RIGHT-SIDE SIGNUP CARD)
            ========================================================================= */}
        <main className="relative w-full flex-1 flex flex-col lg:flex-row items-center justify-between pointer-events-none my-auto py-4">
          
          {/* -------------------------------------------------------------
              LEFT SIDE: BRAND SHOWCASE & ATMOSPHERIC HEADLINE
              Smoothly adapts as user scrolls
              ------------------------------------------------------------- */}
          <div className="flex flex-col max-w-xl select-none pr-4 lg:pr-8 self-center lg:self-center transition-all duration-500">
            {/* Pill Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-mono bg-cyan-950/70 border border-cyan-400/40 text-cyan-300 mb-4 w-fit shadow-[0_0_15px_rgba(6,182,212,0.2)] backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>AUTONOMOUS AIR-GAPPED INTELLIGENCE</span>
            </div>

            {/* Main Showcase Headline */}
            <h1 className="text-4xl sm:text-5xl xl:text-6xl font-black tracking-tight text-white mb-4 leading-[1.08] filter drop-shadow-[0_4px_24px_rgba(0,0,0,0.8)]">
              Awaken Your <br />
              <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-300 bg-clip-text text-transparent filter drop-shadow-[0_2px_20px_rgba(6,182,212,0.4)]">
                Private Intelligent Iris.
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-slate-300/90 text-sm sm:text-base leading-relaxed mb-6 font-normal max-w-lg drop-shadow-[0_2px_8px_rgba(0,0,0,0.7)]">
              Experience the dawn of self-hosted, private intelligence. Zero cloud surveillance, zero telemetry, and permanent neural memory hosted 100% on your machine.
            </p>

            {/* Feature Badges */}
            <div className="flex flex-wrap items-center gap-2.5 text-xs text-cyan-100 font-mono">
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-950/60 border border-cyan-500/30 shadow-md backdrop-blur-md">
                <Shield className="w-3.5 h-3.5 text-cyan-400" /> 100% Air-Gapped
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-950/60 border border-cyan-500/30 shadow-md backdrop-blur-md">
                <Zap className="w-3.5 h-3.5 text-emerald-400" /> Real-Time Local AI
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-950/60 border border-cyan-500/30 shadow-md backdrop-blur-md">
                <Lock className="w-3.5 h-3.5 text-purple-400" /> Zero Telemetry
              </span>
            </div>

            {/* Centered Scroll Hint (Fades out when scrolling) */}
            <div
              style={{
                opacity: heroOpacity,
                transform: `translateY(${(1 - heroOpacity) * 20}px)`,
                pointerEvents: heroOpacity > 0.2 ? "auto" : "none",
              }}
              className="mt-8 transition-opacity duration-300"
            >
              <button
                onClick={scrollToForm}
                className="group inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-400/40 text-cyan-200 text-xs font-mono backdrop-blur-md transition-all shadow-[0_0_20px_rgba(6,182,212,0.2)] hover:shadow-[0_0_25px_rgba(6,182,212,0.4)]"
              >
                <span>Scroll down slowly to initialize sign up</span>
                <ChevronDown className="w-4 h-4 text-cyan-400 animate-bounce group-hover:translate-y-0.5 transition-transform" />
              </button>
            </div>
          </div>

          {/* -------------------------------------------------------------
              RIGHT SIDE CENTER: THE SIGNUP CARD
              Appears with fade-in animation as you scroll slowly,
              and fades out when you scroll back up to the top!
              ------------------------------------------------------------- */}
          <div
            style={{
              opacity: formOpacity,
              transform: `translateX(${formTranslateX}px) scale(${0.96 + formOpacity * 0.04})`,
              pointerEvents: isFormActive ? "auto" : "none",
              transition: "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
            className="w-full max-w-md lg:ml-auto self-center lg:self-center py-2"
          >
            <Card className="w-full p-6 sm:p-8 border border-cyan-500/30 bg-slate-950/80 backdrop-blur-2xl shadow-[0_20px_60px_-15px_rgba(6,182,212,0.3)] relative overflow-hidden rounded-2xl">
              {/* Glowing cyan top accent line */}
              <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />

              {/* Card Header & Step Indicator */}
              <div className="text-center mb-6">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center mx-auto mb-3 shadow-[0_0_20px_rgba(6,182,212,0.4)]">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-2xl font-black tracking-tight text-white">Create Your AI</h2>
                <p className="text-xs text-cyan-300/80 mt-1 font-mono">
                  Step {step} of 3 — {step === 1 ? "Account Setup" : step === 2 ? "Cognitive Profile" : "AI Persona"}
                </p>

                {/* Progress Bar */}
                <div className="w-full bg-white/10 h-1 rounded-full mt-3 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-300"
                    style={{ width: `${(step / 3) * 100}%` }}
                  />
                </div>
              </div>

              {/* Step Forms */}
              <form onSubmit={handleSubmit}>
                {/* STEP 1: ACCOUNT */}
                {step === 1 && (
                  <div className="space-y-4">
                    <Input
                      label="Full Name"
                      id="name"
                      placeholder="e.g. Alex Hunter"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                      labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                      style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                      className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                    />

                    <Input
                      label="Email Address"
                      type="email"
                      id="email"
                      placeholder="alex@example.com"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      required
                      labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                      style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                      className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                    />

                    <div className="relative">
                      <Input
                        label="Password"
                        type={showPassword ? "text" : "password"}
                        id="password"
                        placeholder="At least 8 characters"
                        value={form.password}
                        onChange={(e) => setForm({ ...form, password: e.target.value })}
                        required
                        minLength={8}
                        labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                        style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                        className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 pl-4 pr-11 font-semibold shadow-inner caret-cyan-400"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        className="absolute right-3.5 top-[32px] p-1 text-cyan-400 hover:text-cyan-200 transition-colors rounded-lg focus:outline-none"
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    {error && (
                      <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-xs text-red-300 font-medium">
                        {error}
                      </div>
                    )}

                    <Button
                      type="button"
                      className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold shadow-lg shadow-cyan-500/25 transition-all py-3 rounded-xl mt-2"
                      onClick={() => goToStep(2)}
                    >
                      Next — Cognitive Profile
                    </Button>
                  </div>
                )}

                {/* STEP 2: PROFILE */}
                {step === 2 && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <Input
                        label="Age"
                        type="number"
                        id="age"
                        placeholder="22"
                        value={form.age}
                        onChange={(e) => setForm({ ...form, age: e.target.value })}
                        labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                        style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                        className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                      />
                      <Input
                        label="Role / Profession"
                        id="job"
                        placeholder="Software Engineer"
                        value={form.job}
                        onChange={(e) => setForm({ ...form, job: e.target.value })}
                        labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                        style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                        className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                      />
                    </div>

                    <Input
                      label="Location"
                      id="location"
                      placeholder="e.g. Hyderabad, India"
                      value={form.location}
                      onChange={(e) => setForm({ ...form, location: e.target.value })}
                      labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                      style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                      className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                    />

                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                        Core Interests &amp; Focus
                      </label>
                      <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
                        {interests.map((item) => (
                          <button
                            key={item}
                            type="button"
                            onClick={() => toggleInterest(item)}
                            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                              form.interests.includes(item)
                                ? "bg-cyan-500 text-slate-950 font-bold shadow-sm"
                                : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
                            }`}
                          >
                            {item}
                          </button>
                        ))}
                      </div>
                    </div>

                    {error && (
                      <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-xs text-red-300 font-medium">
                        {error}
                      </div>
                    )}

                    <div className="flex gap-2.5 pt-2">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => goToStep(1)}
                        className="text-white/70 hover:text-white border border-white/10"
                      >
                        Back
                      </Button>
                      <Button
                        type="button"
                        className="flex-1 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold shadow-lg shadow-cyan-500/25"
                        onClick={() => goToStep(3)}
                      >
                        Next — Customize AI
                      </Button>
                    </div>
                  </div>
                )}

                {/* STEP 3: PERSONA */}
                {step === 3 && (
                  <div className="space-y-4">
                    <Input
                      label="Primary Goals"
                      id="goals"
                      placeholder="Build startups, code, research, automation..."
                      value={form.goals}
                      onChange={(e) => setForm({ ...form, goals: e.target.value })}
                      labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                      style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                      className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                    />

                    <Input
                      label="AI Companion Name"
                      id="ai_name"
                      placeholder="e.g. IRIS, ARIA, NEXUS"
                      value={form.ai_name}
                      onChange={(e) => setForm({ ...form, ai_name: e.target.value })}
                      labelClassName="text-slate-200 text-xs font-bold uppercase tracking-wider mb-1 block"
                      style={{ color: "#67e8f9", WebkitTextFillColor: "#67e8f9" }}
                      className="bg-black/55 backdrop-blur-md text-cyan-300 border border-cyan-500/30 placeholder:text-cyan-200/50 focus:bg-black/70 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/30 rounded-xl py-3 px-4 font-semibold shadow-inner caret-cyan-400"
                    />

                    <p className="text-[11px] text-cyan-200/50 leading-relaxed">
                      Your AI adapts and evolves its memory database automatically as you converse. All parameters can be tuned anytime.
                    </p>

                    {error && (
                      <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-xs text-red-300 font-medium">
                        {error}
                      </div>
                    )}

                    <div className="flex gap-2.5 pt-2">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => goToStep(2)}
                        className="text-white/70 hover:text-white border border-white/10"
                      >
                        Back
                      </Button>
                      <Button
                        type="submit"
                        className="flex-1 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold shadow-lg shadow-cyan-500/25"
                        disabled={loading}
                      >
                        {loading ? "Awakening AI..." : "Awaken My AI"}
                      </Button>
                    </div>
                  </div>
                )}
              </form>

              {/* Footer link to Login */}
              <div className="mt-5 pt-4 border-t border-white/10 text-center">
                <p className="text-xs text-slate-400">
                  Already have an account?{" "}
                  <Link href="/login" className="text-cyan-400 hover:text-cyan-300 hover:underline font-semibold">
                    Sign in
                  </Link>
                </p>
              </div>
            </Card>
          </div>

        </main>

        {/* Footer info bar */}
        <footer className="relative w-full py-2 text-xs text-slate-400 font-mono pointer-events-auto flex flex-col sm:flex-row items-center justify-between gap-2 border-t border-white/5">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span>IRIS AI ENGINE &bull; 100% PRIVATE LOCAL INTELLIGENCE</span>
          </div>
          <div className="text-cyan-300/80">
            {formOpacity > 0.5 ? (
              <button onClick={scrollToTop} className="hover:underline flex items-center gap-1">
                <span>Scroll to top for full video</span> &uarr;
              </button>
            ) : (
              <span>Scroll down slowly to initialize form</span>
            )}
          </div>
        </footer>

      </div>
    </div>
  )
}
