"use client"

import React, { useState } from "react"
import Link from "next/link"
import { MessageSquare, Sparkles, Settings as SettingsIcon, ArrowRight, X, Layers, RotateCcw } from "lucide-react"

interface PetalItem {
  id: string
  shortLabel: string
  petalLabel: string
  title: string
  desc: string
  action: string
  href: string
  icon: React.ElementType
  color: string
  glowRgba: string
  bgBadge: string
  borderColor: string
  apexOffsetClass: string
}

const petalItems: PetalItem[] = [
  {
    id: "chat",
    shortLabel: "01 • NEURAL CHAT",
    petalLabel: "UPPER PETAL 01 • NEURAL CORE",
    title: "Local AI Chat",
    desc: "Communicate with your offline neural assistant, send system instructions, and monitor token ratios.",
    action: "Open Chat",
    href: "/dashboard/chat",
    icon: MessageSquare,
    color: "#0eaee8",
    glowRgba: "rgba(14, 174, 232, 0.4)",
    bgBadge: "bg-[#0eaee8]/15 text-[#0eaee8] border-[#0eaee8]/30",
    borderColor: "border-[#0eaee8]/40 hover:border-[#0eaee8]",
    apexOffsetClass: "lg:translate-y-4",
  },
  {
    id: "themes",
    shortLabel: "02 • VISUAL THEMES",
    petalLabel: "UPPER PETAL 02 • VISUAL THEMES",
    title: "Theme Customizer",
    desc: "Choose between 6 visual desktop overlay representations: Blob, Cyber Terminal, Equalizer, and more.",
    action: "Customize Themes",
    href: "/dashboard/settings",
    icon: Sparkles,
    color: "#9a6eb8",
    glowRgba: "rgba(154, 110, 184, 0.4)",
    bgBadge: "bg-[#9a6eb8]/15 text-[#d8b4fe] border-[#9a6eb8]/30",
    borderColor: "border-[#9a6eb8]/40 hover:border-[#9a6eb8]",
    apexOffsetClass: "lg:-translate-y-2", // Center apex sits highest!
  },
  {
    id: "skills",
    shortLabel: "03 • SYSTEM RULES",
    petalLabel: "UPPER PETAL 03 • SYSTEM RULES",
    title: "Skills & System Rules",
    desc: "Manage permissions, autonomous actions, VS Code runner capabilities, and wake word parameters.",
    action: "Manage Skills",
    href: "/dashboard/settings",
    icon: SettingsIcon,
    color: "#34d399",
    glowRgba: "rgba(52, 211, 153, 0.4)",
    bgBadge: "bg-[#34d399]/15 text-[#34d399] border-[#34d399]/30",
    borderColor: "border-[#34d399]/40 hover:border-[#34d399]",
    apexOffsetClass: "lg:translate-y-4",
  },
]

export function PetalCallouts() {
  // Independent open/retract state for each of the 3 upper petal nodes
  const [activePetals, setActivePetals] = useState<Record<string, boolean>>({
    chat: false,
    themes: false,
    skills: false,
  })

  // Toggle individual petal on touch/click:
  // "if i tc tem it will apper and if i tuch them again it will go back same ow it came front"
  const togglePetal = (id: string) => {
    setActivePetals((prev) => ({
      ...prev,
      [id]: !prev[id],
    }))
  }

  const expandAll = () => {
    setActivePetals({ chat: true, themes: true, skills: true })
  }

  const collapseAll = () => {
    setActivePetals({ chat: false, themes: false, skills: false })
  }

  const anyOpen = Object.values(activePetals).some(Boolean)
  const allOpen = Object.values(activePetals).every(Boolean)

  return (
    <section className="relative my-8 select-none">
      {/* Keyframe Styles for Ambient Bioluminescent Waves */}
      <style jsx>{`
        @keyframes petalRadarWave {
          0% {
            transform: scale(0.9);
            opacity: 0.9;
          }
          75% {
            transform: scale(2.2);
            opacity: 0;
          }
          100% {
            transform: scale(2.4);
            opacity: 0;
          }
        }

        @keyframes petalAuraPulse {
          0%, 100% {
            opacity: 0.4;
            transform: scale(1);
          }
          50% {
            opacity: 0.85;
            transform: scale(1.08);
          }
        }
      `}</style>

      {/* Holographic Header Guidance Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 p-3.5 rounded-2xl bg-[#0c0e18]/60 backdrop-blur-xl border border-white/10 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-6 h-6">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping absolute" />
            <span className="w-2 h-2 rounded-full bg-cyan-400 relative" />
          </div>
          <div>
            <h2 className="text-xs font-mono font-bold tracking-widest uppercase text-white/90">
              3D IRIS UPPER PETAL NODES • INTERACTIVE HUD
            </h2>
            <p className="text-[11px] text-white/50">
              Touch any dot on the petals to unfold the indicator. Touch again to retract back.
            </p>
          </div>
        </div>

        {/* Quick Controls */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <button
            onClick={allOpen ? collapseAll : expandAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white/80 bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
          >
            {allOpen ? (
              <>
                <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
                <span>Retract All</span>
              </>
            ) : (
              <>
                <Layers className="w-3.5 h-3.5 text-purple-400" />
                <span>Expand All</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 3 Upper Petal Columns / Interactive Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-5 items-start">
        {petalItems.map((item) => {
          const isOpen = Boolean(activePetals[item.id])

          return (
            <div
              key={item.id}
              className={`flex flex-col transition-transform duration-500 ease-out ${item.apexOffsetClass}`}
            >
              {/* ========================================================= */}
              {/* STEP 1: THE TARGET DOT (◎) ON THE PETAL                   */}
              {/* Sits right on the petal. Click/touch toggles it.          */}
              {/* ========================================================= */}
              <div className="flex flex-col items-center justify-center mb-1">
                <button
                  type="button"
                  onClick={() => togglePetal(item.id)}
                  aria-expanded={isOpen}
                  aria-label={`Toggle ${item.title}`}
                  className="relative group cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 rounded-full p-2"
                >
                  {/* Outer animated radar pulse ring on the petal */}
                  <div
                    className="absolute inset-0 rounded-full pointer-events-none"
                    style={{
                      border: `1.5px solid ${item.color}`,
                      animation: isOpen ? "petalRadarWave 1.4s ease-out infinite" : "petalRadarWave 2.8s ease-out infinite",
                    }}
                  />

                  {/* Ambient Glow Aura */}
                  <div
                    className="absolute -inset-2 rounded-full pointer-events-none blur-md transition-opacity duration-300"
                    style={{
                      backgroundColor: item.color,
                      opacity: isOpen ? 0.6 : 0.2,
                    }}
                  />

                  {/* Double Target Circle (◎) matching user's sketch */}
                  <div
                    className="relative w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300"
                    style={{
                      backgroundColor: isOpen ? `${item.color}25` : "rgba(11, 14, 27, 0.92)",
                      border: `2px solid ${isOpen ? item.color : `${item.color}90`}`,
                      boxShadow: isOpen
                        ? `0 0 24px ${item.color}, inset 0 0 12px ${item.color}`
                        : `0 0 12px ${item.glowRgba}`,
                      transform: isOpen ? "scale(1.1)" : "scale(1)",
                    }}
                  >
                    {/* Inner Target Ring */}
                    <div
                      className="w-6 h-6 rounded-full border flex items-center justify-center transition-colors duration-300"
                      style={{
                        borderColor: isOpen ? "#ffffff" : `${item.color}cc`,
                        backgroundColor: isOpen ? `${item.color}35` : "transparent",
                      }}
                    >
                      {/* Central Glowing Target Core */}
                      <div
                        className="w-2.5 h-2.5 rounded-full transition-all duration-300"
                        style={{
                          backgroundColor: isOpen ? "#ffffff" : item.color,
                          boxShadow: `0 0 8px ${isOpen ? "#ffffff" : item.color}`,
                        }}
                      />
                    </div>
                  </div>
                </button>

                {/* Petal Indicator Pill Button */}
                <button
                  type="button"
                  onClick={() => togglePetal(item.id)}
                  className="mt-1 px-3 py-0.5 rounded-full text-[10px] font-mono tracking-widest uppercase transition-all duration-300 border flex items-center gap-1.5 backdrop-blur-md cursor-pointer hover:scale-105"
                  style={{
                    backgroundColor: isOpen ? `${item.color}25` : "rgba(11, 14, 27, 0.8)",
                    borderColor: isOpen ? item.color : "rgba(255, 255, 255, 0.15)",
                    color: isOpen ? "#ffffff" : "rgba(255, 255, 255, 0.75)",
                    boxShadow: isOpen ? `0 0 14px ${item.glowRgba}` : "none",
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      backgroundColor: item.color,
                      boxShadow: `0 0 6px ${item.color}`,
                    }}
                  />
                  <span>{item.shortLabel}</span>
                  <span className="text-[9px] opacity-60 ml-0.5">
                    {isOpen ? "▲ CLOSE" : "▼ TOUCH"}
                  </span>
                </button>
              </div>

              {/* ========================================================= */}
              {/* STEP 2: ANIMATED POINTER ARROW (PATH + ARROWHEAD)         */}
              {/* Path goes straight diagonally, then turns slight right!   */}
              {/* Retracts backward in exact reverse when closed!          */}
              {/* ========================================================= */}
              <div className="w-full h-12 relative overflow-visible pointer-events-none">
                <svg
                  className="w-full h-12 overflow-visible"
                  viewBox="0 0 280 48"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Arrow Pointer Line: Goes straight up diagonally, then turns right */}
                  <path
                    d="M 140 44 L 168 14 L 255 14"
                    stroke={item.color}
                    strokeWidth={isOpen ? 2.5 : 2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray="260"
                    style={{
                      strokeDashoffset: isOpen ? 0 : 260,
                      transition: isOpen
                        ? "stroke-dashoffset 0.42s cubic-bezier(0.16, 1, 0.3, 1) 0.08s, filter 0.3s"
                        : "stroke-dashoffset 0.32s ease-in 0.14s, filter 0.3s",
                      filter: isOpen
                        ? `drop-shadow(0 0 8px ${item.color}) drop-shadow(0 0 16px ${item.color})`
                        : `drop-shadow(0 0 4px ${item.glowRgba})`,
                    }}
                  />

                  {/* Arrowhead (▶): Appears when line arrives; fades first on reverse */}
                  <polygon
                    points="255,9 265,14 255,19"
                    fill={item.color}
                    style={{
                      opacity: isOpen ? 1 : 0,
                      transform: isOpen ? "scale(1)" : "scale(0)",
                      transformOrigin: "260px 14px",
                      transition: isOpen
                        ? "opacity 0.2s ease 0.44s, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) 0.44s"
                        : "opacity 0.15s ease-in 0.1s, transform 0.15s ease-in 0.1s",
                      filter: `drop-shadow(0 0 6px ${item.color})`,
                    }}
                  />
                </svg>
              </div>

              {/* ========================================================= */}
              {/* STEP 3: THE SLANTED PARALLELOGRAM CALLOUT BOX             */}
              {/* Appears at the arrow; on reverse, disappears first!       */}
              {/* ========================================================= */}
              <div
                className="relative transition-all"
                style={{
                  opacity: isOpen ? 1 : 0,
                  transform: isOpen ? "translateY(0) scale(1)" : "translateY(12px) scale(0.96)",
                  pointerEvents: isOpen ? "auto" : "none",
                  transition: isOpen
                    ? "opacity 0.32s cubic-bezier(0.16, 1, 0.3, 1) 0.46s, transform 0.32s cubic-bezier(0.16, 1, 0.3, 1) 0.46s"
                    : "opacity 0.20s ease-in 0s, transform 0.20s ease-in 0s",
                }}
              >
                {/* Slanted Parallelogram Tech Shell matching user sketch & Image 1 */}
                <div
                  className={`relative p-5 sm:p-6 rounded-2xl bg-[#0b0e1b]/92 backdrop-blur-2xl border ${
                    item.borderColor
                  } shadow-2xl transition-all duration-300 group`}
                  style={{
                    boxShadow: isOpen
                      ? `0 15px 40px -10px ${item.glowRgba}, inset 0 1px 0 rgba(255,255,255,0.25)`
                      : "0 10px 30px -10px rgba(0,0,0,0.8)",
                    transform: "skewX(-3.5deg)",
                  }}
                >
                  {/* Subtle Angled Corner Specular Gradient Line */}
                  <div
                    className="absolute top-0 left-0 right-0 h-[2px] rounded-t-2xl pointer-events-none"
                    style={{
                      background: `linear-gradient(90deg, transparent 0%, ${item.color} 50%, transparent 100%)`,
                      boxShadow: `0 0 10px ${item.color}`,
                    }}
                  />

                  {/* Close button in top-right */}
                  <button
                    type="button"
                    onClick={() => togglePetal(item.id)}
                    aria-label="Close card"
                    className="absolute top-3 right-3 w-6 h-6 rounded-full bg-white/5 hover:bg-white/15 flex items-center justify-center text-white/50 hover:text-white transition-colors cursor-pointer z-20"
                    style={{ transform: "skewX(3.5deg)" }}
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>

                  {/* Inner Content (Counter-skewed so text and icons stay upright & crisp!) */}
                  <div style={{ transform: "skewX(3.5deg)" }}>
                    {/* Top Petal Tag & Icon */}
                    <div className="flex items-center justify-between mb-3.5 pr-6">
                      <span
                        className={`text-[10px] font-mono tracking-widest uppercase px-2.5 py-0.5 rounded-full border ${item.bgBadge}`}
                      >
                        {item.petalLabel}
                      </span>
                      <div
                        className="w-8 h-8 rounded-xl flex items-center justify-center border transition-all duration-300"
                        style={{
                          backgroundColor: `${item.color}15`,
                          borderColor: `${item.color}35`,
                          color: item.color,
                          boxShadow: `0 0 14px ${item.glowRgba}`,
                        }}
                      >
                        <item.icon className="w-4 h-4" />
                      </div>
                    </div>

                    {/* Title */}
                    <h3 className="text-base font-semibold text-white tracking-wide mb-1.5">
                      {item.title}
                    </h3>

                    {/* Description */}
                    <p className="text-xs text-white/60 leading-relaxed mb-4 min-h-[36px]">
                      {item.desc}
                    </p>

                    {/* Action Button */}
                    <Link
                      href={item.href}
                      className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl border text-xs font-semibold tracking-wide transition-all duration-200 group/btn"
                      style={{
                        backgroundColor: `${item.color}20`,
                        borderColor: item.color,
                        color: "#ffffff",
                      }}
                    >
                      <span>{item.action}</span>
                      <ArrowRight
                        className="w-3.5 h-3.5 transition-transform duration-200 group-hover/btn:translate-x-1"
                        style={{ color: item.color }}
                      />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
