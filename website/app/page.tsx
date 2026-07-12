import { Navbar } from "@/components/ui/Navbar"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { ArrowRight, Lock, Cpu, Brain, Shield, Zap, Download, Command, Mic } from "lucide-react"
import Link from "next/link"

const features = [
  {
    icon: Lock,
    title: "100% Private",
    desc: "Everything runs on your machine. Zero data ever leaves your PC. Not even we can see your conversations."
  },
  {
    icon: Cpu,
    title: "Runs Locally",
    desc: "No cloud, no servers, no subscriptions to cloud compute. Your AI runs on your own hardware."
  },
  {
    icon: Brain,
    title: "Learns You",
    desc: "3-tier memory system that truly understands you. Short-term, long-term, and deep permanent memory."
  },
  {
    icon: Zap,
    title: "PC Control",
    desc: "Open apps, manage files, control system settings, browse the web — all by voice or text."
  },
  {
    icon: Command,
    title: "Terminal Native",
    desc: "Full CLI interface for power users. `ai open spotify`, `ai check ram`, `ai remind me`."
  },
  {
    icon: Mic,
    title: "Voice Always-On",
    desc: "Hands-free operation with custom wake word. Works even when the UI is closed."
  }
]

const stats = [
  { value: "100%", label: "Local & Private" },
  { value: "3-Tier", label: "Memory System" },
  { value: "6", label: "UI Themes" },
  { value: "₹99", label: "Starting Price" }
]

export default function HomePage() {
  return (
    <div className="min-h-screen grid-bg">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-igris-500/20 bg-igris-500/5 text-igris-400 text-sm mb-8">
            <Shield className="w-4 h-4" />
            Your AI. Your Machine. Your Data.
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
            Your Own{" "}
            <span className="gradient-text">Private Jarvis</span>
            <br />
            Running on Your PC
          </h1>

          <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-10 leading-relaxed">
            The first truly private, local AI assistant. Knows your life, controls your PC,
            learns you over time — and <span className="text-white/80">never sends a single byte to the cloud.</span>
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link href="/signup">
              <Button size="lg">
                Get Started Free
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg">
                See Pricing
              </Button>
            </Link>
          </div>

          <div className="mt-8 flex items-center justify-center gap-6 text-sm text-white/40">
            <span>No credit card</span>
            <span className="w-1 h-1 rounded-full bg-white/20" />
            <span>Works offline</span>
            <span className="w-1 h-1 rounded-full bg-white/20" />
            <span>Windows / Mac / Linux</span>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-6 border-y border-white/5">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold gradient-text mb-1">{stat.value}</div>
              <div className="text-sm text-white/40">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need.{" "}
              <span className="gradient-text">Nothing You Don&apos;t.</span>
            </h2>
            <p className="text-white/50 max-w-xl mx-auto">
              IGRIS gives you complete control over your AI experience — from deep system access to beautiful visual themes.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <Card key={feature.title} className="p-6">
                <feature.icon className="w-10 h-10 text-igris-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{feature.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-24 px-6 bg-white/[0.01] border-y border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              From Signup to <span className="gradient-text">AI Running</span>
            </h2>
            <p className="text-white/50">It takes about 2 minutes. No technical skills needed.</p>
          </div>

          <div className="space-y-8">
            {[
              { step: "1", title: "Sign Up & Fill Profile", desc: "Tell us about yourself — your name, interests, goals, and preferences. This becomes your AI's DNA." },
              { step: "2", title: "Choose Your Plan", desc: "Free tier to try it out, ₹99/month for full access, or ₹999 for lifetime." },
              { step: "3", title: "Download & Run Installer", desc: "One command in your terminal. We install Ollama, pull the model, and inject your profile." },
              { step: "4", title: "Your AI is Ready", desc: "Dashboard opens at localhost:3000. Your AI greets you by name. Everything is local." },
            ].map((item) => (
              <div key={item.step} className="flex gap-6">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-igris-600/20 border border-igris-500/30 flex items-center justify-center text-igris-400 font-bold">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold mb-1">{item.title}</h3>
                  <p className="text-sm text-white/50">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Meet Your <span className="gradient-text">AI</span>?
          </h2>
          <p className="text-white/50 mb-8">
            Join the privacy-first AI revolution. No data leaks. No cloud. Just you and your AI.
          </p>
          <Link href="/signup">
            <Button size="lg">
              Get Started Free
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/5 text-center text-sm text-white/30">
        IGRIS AI — Private. Local. Yours.
      </footer>
    </div>
  )
}
