"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { 
  Puzzle, 
  MonitorCheck, 
  Mic, 
  Code2, 
  Languages, 
  Send, 
  Music,
  CheckCircle2,
  AlertCircle
} from "lucide-react"

export interface SkillConfig {
  id: string
  name: string
  category: string
  description: string
  icon: typeof Puzzle
  defaultEnabled: boolean
}

export const SKILLS_LIST: SkillConfig[] = [
  {
    id: "pc_control",
    name: "PC & System Control",
    category: "Automation",
    description: "Launch apps, browse local filesystem, manage window focus and hardware volume.",
    icon: MonitorCheck,
    defaultEnabled: true,
  },
  {
    id: "voice_always_on",
    name: "Voice & Wake Word",
    category: "Speech",
    description: "Full-duplex microphone listening, Silero VAD, and barge-in response cancellation.",
    icon: Mic,
    defaultEnabled: true,
  },
  {
    id: "code_assistant",
    name: "VS Code Program Runner",
    category: "Development",
    description: "Open source files, trigger integrated terminal execution, and run scripts in VS Code.",
    icon: Code2,
    defaultEnabled: true,
  },
  {
    id: "multilingual_perception",
    name: "Multilingual & Song Perception",
    category: "Intelligence",
    description: "Auto-detect 90+ languages, sing-along lyric matching for Hindi/Telugu/English hits.",
    icon: Languages,
    defaultEnabled: true,
  },
  {
    id: "universal_messaging",
    name: "Universal Messaging",
    category: "Communication",
    description: "Multi-recipient message delivery and WhatsApp broadcast automation.",
    icon: Send,
    defaultEnabled: true,
  },
  {
    id: "media_control",
    name: "Media & YouTube Control",
    category: "Entertainment",
    description: "Anaphoric song playback, audio queue management, and YouTube music controls.",
    icon: Music,
    defaultEnabled: true,
  },
]

export function SkillToggles() {
  const [enabledSkills, setEnabledSkills] = useState<Record<string, boolean>>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("iris_skills_config")
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch {}
      }
    }
    return Object.fromEntries(SKILLS_LIST.map((s) => [s.id, s.defaultEnabled]))
  })

  const [savedNotification, setSavedNotification] = useState(false)

  function toggleSkill(id: string) {
    setEnabledSkills((prev) => {
      const updated = { ...prev, [id]: !prev[id] }
      if (typeof window !== "undefined") {
        localStorage.setItem("iris_skills_config", JSON.stringify(updated))
      }
      setSavedNotification(true)
      setTimeout(() => setSavedNotification(false), 2000)
      return updated
    })
  }

  function handleToggleAll(enable: boolean) {
    const updated = Object.fromEntries(SKILLS_LIST.map((s) => [s.id, enable]))
    setEnabledSkills(updated)
    if (typeof window !== "undefined") {
      localStorage.setItem("iris_skills_config", JSON.stringify(updated))
    }
    setSavedNotification(true)
    setTimeout(() => setSavedNotification(false), 2000)
  }

  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Puzzle className="w-5 h-5 text-iris-400" />
            Active AI Skills & Capabilities
          </h2>
          <p className="text-sm text-white/50 mt-1">
            Enable or restrict specific autonomous modules running within your local IRIS engine.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {savedNotification && (
            <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 mr-2">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Settings Synced
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={() => handleToggleAll(true)}>
            Enable All
          </Button>
          <Button variant="ghost" size="sm" onClick={() => handleToggleAll(false)}>
            Disable All
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SKILLS_LIST.map((skill) => {
          const isEnabled = enabledSkills[skill.id] ?? true
          const Icon = skill.icon

          return (
            <div
              key={skill.id}
              className={`p-4 rounded-xl border transition-all flex items-start justify-between gap-4 ${
                isEnabled
                  ? "bg-white/[0.03] border-white/10 hover:border-white/20"
                  : "bg-white/[0.01] border-white/5 opacity-60"
              }`}
            >
              <div className="flex items-start gap-3.5">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    isEnabled
                      ? "bg-iris-600/20 text-iris-400 border border-iris-500/30"
                      : "bg-white/5 text-white/30 border border-white/5"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-sm text-white">{skill.name}</h3>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-white/5 text-white/40 border border-white/5">
                      {skill.category}
                    </span>
                  </div>
                  <p className="text-xs text-white/40 leading-relaxed">{skill.description}</p>
                </div>
              </div>

              {/* Accessible Switch Toggle */}
              <button
                type="button"
                role="switch"
                aria-checked={isEnabled}
                onClick={() => toggleSkill(skill.id)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-75 active:scale-95 ease-in-out focus:outline-none select-none touch-manipulation ${
                  isEnabled ? "bg-iris-600" : "bg-white/10"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-75 ease-in-out ${
                    isEnabled ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

