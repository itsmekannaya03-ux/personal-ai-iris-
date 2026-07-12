import { Navbar } from "@/components/ui/Navbar"
import { Card } from "@/components/ui/Card"
import { Shield, Cpu, Brain, Mic, Command, Eye, Palette, Puzzle, Calendar, Code, BarChart3, Globe, Mail, Music, Folder, Bell } from "lucide-react"

const featureGroups = [
  {
    title: "Privacy & Architecture",
    features: [
      { icon: Shield, title: "Zero-Trust Privacy", desc: "No data ever leaves your machine. Not even we can access your conversations. Encrypted at rest." },
      { icon: Cpu, title: "Local-First Engine", desc: "Runs on Ollama + LLaMA 3. Works completely offline. No cloud dependency whatsoever." },
      { icon: Brain, title: "3-Tier Memory System", desc: "Short-term (RAM), Long-term (ChromaDB), Deep (encrypted JSON). Auto-promotes frequently used memories." },
    ]
  },
  {
    title: "Interaction Modes",
    features: [
      { icon: Eye, title: "Beautiful Web UI", desc: "6 visual themes — Blob, Terminal, Voice Bar, Drum Waves, Hologram Orb, Minimal Dot." },
      { icon: Command, title: "Terminal / CMD", desc: "Type `ai open spotify` or `ai what files did I edit today`. Blazing fast." },
      { icon: Mic, title: "Voice Always-On", desc: "Custom wake word. Works even when UI and terminal are closed. Hands-free." },
      { icon: Palette, title: "Full Visual Customization", desc: "Custom colors, animation speed, glow intensity, particle density, sound effects." },
    ]
  },
  {
    title: "Skill Modules",
    features: [
      { icon: Calendar, title: "Calendar Control", desc: "Schedule management, smart reminders, context-aware alerts." },
      { icon: Code, title: "Code Assistant", desc: "Understands your codebase, GitHub workflow, local repos." },
      { icon: BarChart3, title: "Data Analysis", desc: "Analyze files, generate charts, summarize spreadsheets." },
      { icon: Globe, title: "Web Research", desc: "Browse the web, summarize articles, fetch real-time info." },
      { icon: Mail, title: "Email Drafting", desc: "Read, draft, and send emails through your local client." },
      { icon: Music, title: "Media Control", desc: "Spotify, YouTube, volume control, playlists." },
      { icon: Folder, title: "File Intelligence", desc: "Smart file search, auto-organization, bulk operations." },
      { icon: Bell, title: "Smart Reminders", desc: "Context-aware, learns your schedule, proactive suggestions." },
    ]
  }
]

export default function FeaturesPage() {
  return (
    <div className="min-h-screen grid-bg">
      <Navbar />
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Everything <span className="gradient-text">IGRIS</span> Can Do
            </h1>
            <p className="text-white/50 max-w-xl mx-auto">
              Full PC control, 3-tier memory, 6 themes, voice mode, terminal CLI, skill modules — all running locally.
            </p>
          </div>

          {featureGroups.map((group) => (
            <div key={group.title} className="mb-16">
              <h2 className="text-2xl font-bold mb-8">{group.title}</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {group.features.map((feat) => (
                  <Card key={feat.title} className="p-6">
                    <feat.icon className="w-8 h-8 text-igris-400 mb-4" />
                    <h3 className="font-semibold mb-2">{feat.title}</h3>
                    <p className="text-sm text-white/50 leading-relaxed">{feat.desc}</p>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
