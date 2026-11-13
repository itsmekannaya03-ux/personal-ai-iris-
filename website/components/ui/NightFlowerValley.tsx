"use client"

import React, { useEffect, useRef, useState } from "react"
import * as THREE from "three"
import Link from "next/link"
import { Check, ArrowRight, Sparkles, Volume2, VolumeX, Layers, Compass, X } from "lucide-react"
import { PlanCheckoutModal } from "@/components/ui/PlanCheckoutModal"

// =======================================================================
// PROCEDURAL BOTANICAL TEXTURE ATLAS GENERATOR
// Creates 6 high-fidelity 512x512 sprite tiles packed into a 3072x512 strip:
// Slot 0: Soft Botanical Forest Foliage & Moss Leaf Cluster (Lush Undergrowth)
// Slot 1: Soft Pastel Lilac / Lavender Wildflower (#9a6eb8)
// Slot 2: Vibrant Light Sky Cyan & Electric Blue Wildflower (#0eaee8)
// Slot 3: Luminous Silver-Mist & Pearlescent White Wildflower (#e5e4eb)
// Slot 4: Light Powder Baby Blue / Celestial Bellflower (Light Sky Blue)
// Slot 5: Soft Periwinkle & Opal Blossom (Light Pastel Harmony)
//
// 100% LIGHT, GLOWING, LUMINOUS COLORS (NO DARK OR HEAVY TONES!)
// =======================================================================
function generateBotanicalAtlasTexture(): THREE.CanvasTexture {
  const tileSize = 512
  const numTiles = 6
  const canvas = document.createElement("canvas")
  canvas.width = tileSize * numTiles
  canvas.height = tileSize
  const ctx = canvas.getContext("2d")!
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const half = tileSize / 2

  // -------------------------------------------------------------
  // TILE 0: Soft Lush Forest Foliage & Shrubbery Leaf Cluster
  // Soft emerald moss with luminous mint/silver veins — no black holes!
  // -------------------------------------------------------------
  ctx.save()
  ctx.translate(0 * tileSize + half, half)

  // Soft atmospheric foliage shadow
  ctx.beginPath()
  ctx.arc(0, 0, half * 0.78, 0, Math.PI * 2)
  const shadowGrad = ctx.createRadialGradient(0, 0, 10, 0, 0, half * 0.76)
  shadowGrad.addColorStop(0, "rgba(4, 20, 14, 0.65)")
  shadowGrad.addColorStop(1, "rgba(4, 20, 14, 0.0)")
  ctx.fillStyle = shadowGrad
  ctx.fill()

  // 6 Soft Botanical Leaves radiating outward
  const leafCount = 6
  for (let i = 0; i < leafCount; i++) {
    const angle = (i * Math.PI * 2) / leafCount + (i % 2 === 0 ? 0.12 : -0.12)
    ctx.save()
    ctx.rotate(angle)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-half * 0.26, half * 0.24, -half * 0.32, half * 0.62, 0, half * 0.86)
    ctx.bezierCurveTo(half * 0.32, half * 0.62, half * 0.26, half * 0.24, 0, 0)

    const leafGrad = ctx.createLinearGradient(0, 0, 0, half * 0.86)
    leafGrad.addColorStop(0, "#0c2e1d") // deep emerald base
    leafGrad.addColorStop(0.4, "#164d30") // lush forest green
    leafGrad.addColorStop(0.8, "#1f6e45") // rich moss green
    leafGrad.addColorStop(1, "#34d399") // luminous soft mint tip
    ctx.fillStyle = leafGrad
    ctx.fill()

    // Central leaf vein
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.quadraticCurveTo(half * 0.02, half * 0.42, 0, half * 0.8)
    ctx.strokeStyle = "rgba(167, 243, 208, 0.45)"
    ctx.lineWidth = 2.4
    ctx.stroke()

    // Fine lateral veins
    ctx.strokeStyle = "rgba(167, 243, 208, 0.22)"
    ctx.lineWidth = 1.1
    for (let v = 1; v <= 4; v++) {
      const vy = half * 0.15 * v
      ctx.beginPath()
      ctx.moveTo(0, vy)
      ctx.lineTo(half * 0.11, vy + half * 0.07)
      ctx.moveTo(0, vy)
      ctx.lineTo(-half * 0.11, vy + half * 0.07)
      ctx.stroke()
    }
    ctx.restore()
  }
  ctx.restore()

  // -------------------------------------------------------------
  // TILE 1: Soft Pastel Lilac / Lavender Wildflower (#9a6eb8)
  // Exact user hex #9a6eb8 with radiant soft pastel petals
  // -------------------------------------------------------------
  ctx.save()
  ctx.translate(1 * tileSize + half, half)

  // 5 Silky Heart-Notched Lilac Petals
  const petalCount1 = 5
  for (let i = 0; i < petalCount1; i++) {
    const angle = (i * Math.PI * 2) / petalCount1
    ctx.save()
    ctx.rotate(angle)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-half * 0.3, half * 0.22, -half * 0.4, half * 0.62, -half * 0.16, half * 0.84)
    ctx.bezierCurveTo(0, half * 0.76, 0, half * 0.76, half * 0.16, half * 0.84)
    ctx.bezierCurveTo(half * 0.4, half * 0.62, half * 0.3, half * 0.22, 0, 0)

    const lilacGrad = ctx.createRadialGradient(0, half * 0.12, 2, 0, half * 0.5, half * 0.5)
    lilacGrad.addColorStop(0, "#f3e8ff") // luminous soft white-lilac glow
    lilacGrad.addColorStop(0.35, "#d8b4fe") // light pastel lavender
    lilacGrad.addColorStop(0.7, "#9a6eb8") // exact user hex: #9a6eb8
    lilacGrad.addColorStop(1, "#7e529d") // soft lilac rim
    ctx.fillStyle = lilacGrad
    ctx.fill()

    // Fine delicate translucent striation
    ctx.strokeStyle = "rgba(243, 232, 255, 0.45)"
    ctx.lineWidth = 1.3
    ctx.beginPath()
    ctx.moveTo(0, half * 0.08)
    ctx.lineTo(0, half * 0.72)
    ctx.stroke()
    ctx.restore()
  }

  // Glowing Ivory-White Center Eye with Light Golden Stamens
  const coreGrad1 = ctx.createRadialGradient(0, 0, 2, 0, 0, half * 0.22)
  coreGrad1.addColorStop(0, "#ffffff")
  coreGrad1.addColorStop(0.4, "#fef08a")
  coreGrad1.addColorStop(0.8, "#e9d5ff")
  coreGrad1.addColorStop(1, "#9a6eb8")
  ctx.beginPath()
  ctx.arc(0, 0, half * 0.2, 0, Math.PI * 2)
  ctx.fillStyle = coreGrad1
  ctx.fill()

  // Ring of tiny stamen pearls
  for (let s = 0; s < 12; s++) {
    const sAng = (s * Math.PI * 2) / 12
    const sx = Math.cos(sAng) * half * 0.14
    const sy = Math.sin(sAng) * half * 0.14
    ctx.beginPath()
    ctx.arc(sx, sy, 3.0, 0, Math.PI * 2)
    ctx.fillStyle = "#ffffff"
    ctx.fill()
  }
  ctx.restore()

  // -------------------------------------------------------------
  // TILE 2: Vibrant Light Sky Cyan & Electric Blue Wildflower (#0eaee8)
  // Exact user hex #0eaee8 with celestial light blue petals
  // -------------------------------------------------------------
  ctx.save()
  ctx.translate(2 * tileSize + half, half)

  // 5 Broad, Gracefully Ruffled Petals
  const petalCount2 = 5
  for (let i = 0; i < petalCount2; i++) {
    const angle = (i * Math.PI * 2) / petalCount2 + 0.15
    ctx.save()
    ctx.rotate(angle)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-half * 0.34, half * 0.2, -half * 0.44, half * 0.58, -half * 0.14, half * 0.86)
    ctx.bezierCurveTo(0, half * 0.9, half * 0.06, half * 0.84, half * 0.2, half * 0.82)
    ctx.bezierCurveTo(half * 0.44, half * 0.58, half * 0.34, half * 0.2, 0, 0)

    const cyanGrad = ctx.createRadialGradient(0, half * 0.1, 2, 0, half * 0.5, half * 0.52)
    cyanGrad.addColorStop(0, "#f0fdfa") // pure shimmering ice glow
    cyanGrad.addColorStop(0.3, "#7dd3fc") // light sky blue
    cyanGrad.addColorStop(0.7, "#0eaee8") // exact user hex: #0eaee8
    cyanGrad.addColorStop(0.92, "#0284c7") // vibrant light cyan-blue
    cyanGrad.addColorStop(1, "#0369a1") // soft edge
    ctx.fillStyle = cyanGrad
    ctx.fill()

    // Delicate translucent fold highlight
    ctx.strokeStyle = "rgba(224, 242, 254, 0.5)"
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(-half * 0.06, half * 0.15)
    ctx.quadraticCurveTo(-half * 0.1, half * 0.45, -half * 0.04, half * 0.72)
    ctx.stroke()
    ctx.restore()
  }

  // Pure Radiant Crystal Core
  const coreGrad2 = ctx.createRadialGradient(0, 0, 2, 0, 0, half * 0.2)
  coreGrad2.addColorStop(0, "#ffffff")
  coreGrad2.addColorStop(0.45, "#67e8f9")
  coreGrad2.addColorStop(0.85, "#0eaee8")
  coreGrad2.addColorStop(1, "#0284c7")
  ctx.beginPath()
  ctx.arc(0, 0, half * 0.18, 0, Math.PI * 2)
  ctx.fillStyle = coreGrad2
  ctx.fill()

  // Ring of glowing cyan-white pearls
  for (let s = 0; s < 14; s++) {
    const sAng = (s * Math.PI * 2) / 14
    const sx = Math.cos(sAng) * half * 0.13
    const sy = Math.sin(sAng) * half * 0.13
    ctx.beginPath()
    ctx.arc(sx, sy, 2.6, 0, Math.PI * 2)
    ctx.fillStyle = "#ffffff"
    ctx.fill()
  }
  ctx.restore()

  // -------------------------------------------------------------
  // TILE 3: Luminous Silver-Mist White Wildflower (#e5e4eb)
  // Exact user hex #e5e4eb with pure starry edelweiss petals
  // -------------------------------------------------------------
  ctx.save()
  ctx.translate(3 * tileSize + half, half)

  // 8 Slender Starry Edelweiss Ray Petals
  const petalCount3 = 8
  for (let i = 0; i < petalCount3; i++) {
    const angle = (i * Math.PI * 2) / petalCount3
    ctx.save()
    ctx.rotate(angle)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-half * 0.16, half * 0.24, -half * 0.2, half * 0.65, 0, half * 0.88)
    ctx.bezierCurveTo(half * 0.2, half * 0.65, half * 0.16, half * 0.24, 0, 0)

    const silverGrad = ctx.createLinearGradient(0, 0, 0, half * 0.88)
    silverGrad.addColorStop(0, "rgba(255, 255, 255, 0.98)")
    silverGrad.addColorStop(0.4, "#e5e4eb") // exact user hex: #e5e4eb
    silverGrad.addColorStop(0.8, "#f1f5f9") // pure silver mist
    silverGrad.addColorStop(1, "#ffffff") // bright star tip
    ctx.fillStyle = silverGrad
    ctx.fill()

    // Fine vein
    ctx.strokeStyle = "rgba(255, 255, 255, 0.7)"
    ctx.lineWidth = 1.2
    ctx.beginPath()
    ctx.moveTo(0, half * 0.08)
    ctx.lineTo(0, half * 0.75)
    ctx.stroke()
    ctx.restore()
  }

  // Soft Golden Sun Dome
  const coreGrad3 = ctx.createRadialGradient(0, 0, 2, 0, 0, half * 0.24)
  coreGrad3.addColorStop(0, "#ffffff")
  coreGrad3.addColorStop(0.35, "#fef08a")
  coreGrad3.addColorStop(0.75, "#facc15")
  coreGrad3.addColorStop(1, "#e5e4eb")
  ctx.beginPath()
  ctx.arc(0, 0, half * 0.21, 0, Math.PI * 2)
  ctx.fillStyle = coreGrad3
  ctx.fill()
  ctx.restore()

  // -------------------------------------------------------------
  // TILE 4: Light Powder Baby Blue / Celestial Bellflower
  // "some blue flowers light bule not dark colors jut light colors ok"
  // -------------------------------------------------------------
  ctx.save()
  ctx.translate(4 * tileSize + half, half)

  // 5 Pointed Celestial Bell Petals
  const petalCount4 = 5
  for (let i = 0; i < petalCount4; i++) {
    const angle = (i * Math.PI * 2) / petalCount4 + 0.1
    ctx.save()
    ctx.rotate(angle)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-half * 0.26, half * 0.24, -half * 0.34, half * 0.65, 0, half * 0.88)
    ctx.bezierCurveTo(half * 0.34, half * 0.65, half * 0.26, half * 0.24, 0, 0)

    const babyBlueGrad = ctx.createRadialGradient(0, half * 0.12, 2, 0, half * 0.5, half * 0.5)
    babyBlueGrad.addColorStop(0, "#f0f9ff") // pale airy sky
    babyBlueGrad.addColorStop(0.35, "#bae6fd") // soft powder blue
    babyBlueGrad.addColorStop(0.7, "#7dd3fc") // light bright baby blue
    babyBlueGrad.addColorStop(1, "#38bdf8") // gentle light azure edge
    ctx.fillStyle = babyBlueGrad
    ctx.fill()

    // Fine striation
    ctx.strokeStyle = "rgba(240, 249, 255, 0.5)"
    ctx.lineWidth = 1.2
    ctx.beginPath()
    ctx.moveTo(0, half * 0.08)
    ctx.lineTo(0, half * 0.76)
    ctx.stroke()
    ctx.restore()
  }

  // Soft Opal Pearl Core
  const coreGrad4 = ctx.createRadialGradient(0, 0, 2, 0, 0, half * 0.19)
  coreGrad4.addColorStop(0, "#ffffff")
  coreGrad4.addColorStop(0.5, "#e0f2fe")
  coreGrad4.addColorStop(1, "#7dd3fc")
  ctx.beginPath()
  ctx.arc(0, 0, half * 0.17, 0, Math.PI * 2)
  ctx.fillStyle = coreGrad4
  ctx.fill()
  ctx.restore()

  // -------------------------------------------------------------
  // TILE 5: Soft Periwinkle & Opal Blossom (Lilac-Blue Harmony)
  // Blends #9a6eb8 and #0eaee8 into a luminous pastel floret
  // -------------------------------------------------------------
  ctx.save()
  ctx.translate(5 * tileSize + half, half)

  // 6 Pointed Star Petals
  const petalCount5 = 6
  for (let i = 0; i < petalCount5; i++) {
    const angle = (i * Math.PI * 2) / petalCount5
    ctx.save()
    ctx.rotate(angle)

    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.bezierCurveTo(-half * 0.2, half * 0.25, -half * 0.26, half * 0.65, 0, half * 0.88)
    ctx.bezierCurveTo(half * 0.26, half * 0.65, half * 0.2, half * 0.25, 0, 0)

    const opalGrad = ctx.createRadialGradient(0, half * 0.12, 2, 0, half * 0.5, half * 0.5)
    opalGrad.addColorStop(0, "#ffffff")
    opalGrad.addColorStop(0.35, "#c7d2fe") // light periwinkle
    opalGrad.addColorStop(0.7, "#a5b4fc") // soft lavender-blue
    opalGrad.addColorStop(1, "#818cf8") // soft indigo-lilac
    ctx.fillStyle = opalGrad
    ctx.fill()
    ctx.restore()
  }

  // Glowing Golden Sunshine Core
  const coreGrad5 = ctx.createRadialGradient(0, 0, 2, 0, 0, half * 0.22)
  coreGrad5.addColorStop(0, "#ffffff")
  coreGrad5.addColorStop(0.4, "#fef08a")
  coreGrad5.addColorStop(0.8, "#facc15")
  coreGrad5.addColorStop(1, "#c7d2fe")
  ctx.beginPath()
  ctx.arc(0, 0, half * 0.2, 0, Math.PI * 2)
  ctx.fillStyle = coreGrad5
  ctx.fill()
  ctx.restore()

  const texture = new THREE.CanvasTexture(canvas)
  texture.generateMipmaps = true
  texture.minFilter = THREE.LinearMipmapLinearFilter
  texture.magFilter = THREE.LinearFilter
  texture.needsUpdate = true
  return texture
}

// =======================================================================
// FLOATING POLLEN / DUST GLOW SPRITE (Soft Cyan & Silver Light)
// =======================================================================
function generateDustMoteTexture(): THREE.CanvasTexture {
  const size = 64
  const canvas = document.createElement("canvas")
  canvas.width = canvas.height = size
  const ctx = canvas.getContext("2d")!
  const half = size / 2

  const grad = ctx.createRadialGradient(half, half, 1, half, half, half)
  grad.addColorStop(0, "rgba(255, 255, 255, 1.0)")
  grad.addColorStop(0.3, "rgba(125, 211, 252, 0.85)") // soft cyan glow
  grad.addColorStop(0.7, "rgba(216, 180, 254, 0.3)") // soft lilac glow
  grad.addColorStop(1, "rgba(216, 180, 254, 0.0)")

  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.arc(half, half, half, 0, Math.PI * 2)
  ctx.fill()

  const tex = new THREE.CanvasTexture(canvas)
  tex.needsUpdate = true
  return tex
}

// =======================================================================
// AMBIENT NIGHT VALLEY AUDIO SYNTHESIZER
// Generates soothing organic nocturnal resonance & chime bells
// =======================================================================
class AmbientNightValleyAudio {
  private ctx: AudioContext | null = null
  private gainNode: GainNode | null = null
  private isPlaying = false
  private timer: number | null = null

  public isSoundPlaying() {
    return this.isPlaying
  }

  public toggle(): boolean {
    if (this.isPlaying) {
      this.stop()
      return false
    } else {
      this.start()
      return true
    }
  }

  private start() {
    try {
      const AudioCtx =
        window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (!this.ctx) {
        this.ctx = new AudioCtx()
      }
      if (this.ctx.state === "suspended") {
        this.ctx.resume()
      }

      this.gainNode = this.ctx.createGain()
      this.gainNode.gain.setValueAtTime(0.001, this.ctx.currentTime)
      this.gainNode.gain.exponentialRampToValueAtTime(0.12, this.ctx.currentTime + 2.5)
      this.gainNode.connect(this.ctx.destination)

      // 1. Deep Earth Drone
      const droneOsc = this.ctx.createOscillator()
      droneOsc.type = "sine"
      droneOsc.frequency.setValueAtTime(54, this.ctx.currentTime)

      const filter = this.ctx.createBiquadFilter()
      filter.type = "lowpass"
      filter.frequency.setValueAtTime(180, this.ctx.currentTime)

      droneOsc.connect(filter)
      filter.connect(this.gainNode)
      droneOsc.start()

      // 2. High Shimmer Chimes (Pentatonic nocturnal bells)
      const scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
      const playChime = () => {
        if (!this.ctx || !this.gainNode || !this.isPlaying) return
        const osc = this.ctx.createOscillator()
        const noteGain = this.ctx.createGain()
        const freq = scale[Math.floor(Math.random() * scale.length)]

        osc.type = "sine"
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime)

        noteGain.gain.setValueAtTime(0.001, this.ctx.currentTime)
        noteGain.gain.linearRampToValueAtTime(0.025, this.ctx.currentTime + 0.1)
        noteGain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 3.0)

        osc.connect(noteGain)
        noteGain.connect(this.gainNode)
        osc.start()
        osc.stop(this.ctx.currentTime + 3.1)

        const nextDelay = 1200 + Math.random() * 2400
        this.timer = window.setTimeout(playChime, nextDelay)
      }

      this.isPlaying = true
      playChime()
    } catch (e) {
      console.warn("AudioContext error:", e)
    }
  }

  public stop() {
    if (this.gainNode && this.ctx) {
      this.gainNode.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.8)
    }
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
    this.isPlaying = false
  }
}

// =======================================================================
// PRICING TIERS DATA
// =======================================================================
const pricingTiers = [
  {
    id: "free",
    tier: "Tier 01",
    name: "Seedling Grove",
    subtitle: "Free Forever",
    price: "0",
    period: "forever",
    desc: "Essential local AI companion. Perfect for exploring private local intelligence without commitments.",
    cta: "Get Started Free",
    highlight: false,
    badge: "100% Free",
    accentColor: "rgba(56, 189, 248, 0.8)",
    features: [
      "Basic voice interaction & commands",
      "Short-term context memory only",
      "3 essential skill modules",
      "Default desktop companion UI",
      "100% Private — Zero cloud telemetry",
      "Works completely offline without network",
    ],
  },
  {
    id: "pro",
    tier: "Tier 02",
    name: "Student Pro",
    subtitle: "Full Cognitive OS",
    price: "99",
    period: "per month",
    desc: "Autonomous cognitive power for daily builders, students, and professionals who demand local supremacy.",
    cta: "Subscribe to Pro",
    highlight: true,
    badge: "Most Popular",
    accentColor: "rgba(192, 132, 252, 0.95)",
    features: [
      "Full 3-Tier persistent memory architecture",
      "All cognitive skill modules unlocked",
      "Custom AI name, voice tone & personality",
      "All 6 companion themes & 3D avatars",
      "Direct desktop execution & window hands",
      "Always-on ambient microphone listening",
      "Priority project notes & workspace mounts",
    ],
  },
  {
    id: "lifetime",
    tier: "Tier 03",
    name: "Lifetime Sovereign",
    subtitle: "Permanent Ownership",
    price: "999",
    period: "one-time payment",
    desc: "The permanent sovereign license. Never pay another subscription — yours forever across all future updates.",
    cta: "Claim Lifetime Sovereign",
    highlight: false,
    badge: "Forever Ownership",
    accentColor: "rgba(251, 191, 36, 0.9)",
    features: [
      "Everything included in Student Pro",
      "Zero recurring fees — permanent lifetime key",
      "Custom wake-word fine-tuning on your voice",
      "Day-one access to beta models & capabilities",
      "Future premium skill expansions included",
      "VIP engineering updates & local fine-tunes",
      "Air-gapped cryptographic ownership token",
    ],
  },
]

const comparisonData = [
  { feature: "Runs 100% Locally on Device", free: "✓", pro: "✓", lifetime: "✓" },
  { feature: "Zero Telemetry / Zero Cloud Storage", free: "✓", pro: "✓", lifetime: "✓" },
  { feature: "Short-Term Working Memory", free: "✓", pro: "✓", lifetime: "✓" },
  { feature: "Episodic Mid-Term Memory", free: "—", pro: "✓", lifetime: "✓" },
  { feature: "Permanent Deep Vault Memory (Layer 3)", free: "—", pro: "✓", lifetime: "✓" },
  { feature: "Autonomous Desktop Hands (Apps, Mouse, Typing)", free: "Basic", pro: "Full", lifetime: "Full" },
  { feature: "Custom AI Personality & Voice Tuning", free: "—", pro: "✓", lifetime: "✓" },
  { feature: "All 6 Companion Avatar Themes", free: "—", pro: "✓", lifetime: "✓" },
  { feature: "Custom Wake Word Training", free: "—", pro: "—", lifetime: "✓" },
  { feature: "Priority Model & Skill Expansions", free: "—", pro: "Monthly", lifetime: "Lifetime VIP" },
]

// =======================================================================
// MAIN NIGHT FLOWER VALLEY COMPONENT
// =======================================================================
export function NightFlowerValley() {
  const mountRef = useRef<HTMLDivElement>(null)
  const [depthProgress, setDepthProgress] = useState(0)
  const [isSoundOn, setIsSoundOn] = useState(false)
  const [showMatrixModal, setShowMatrixModal] = useState(false)
  const [checkoutPlan, setCheckoutPlan] = useState<"student" | "lifetime" | null>(null)

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search)
      const planParam = params.get("plan")
      if (planParam === "pro" || planParam === "student") {
        setCheckoutPlan("student")
      } else if (planParam === "lifetime") {
        setCheckoutPlan("lifetime")
      }
    }
  }, [])

  const audioRef = useRef<AmbientNightValleyAudio | null>(null)
  const targetProgressRef = useRef(0)
  const currentProgressRef = useRef(0)
  const lastInteractionTimeRef = useRef(Date.now())

  // Sound toggle handler
  const handleToggleSound = () => {
    if (!audioRef.current) {
      audioRef.current = new AmbientNightValleyAudio()
    }
    const playing = audioRef.current.toggle()
    setIsSoundOn(playing)
  }

  // Smooth camera depth navigation
  const navigateToDepth = (p: number) => {
    targetProgressRef.current = THREE.MathUtils.clamp(p, 0, 1)
    lastInteractionTimeRef.current = Date.now()
  }

  useEffect(() => {
    const container = mountRef.current
    if (!container) return

    const width = window.innerWidth
    const height = window.innerHeight

    // --- Scene & Perspective Camera ---
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x020710, 0.007)

    const camera = new THREE.PerspectiveCamera(54, width / height, 0.1, 800)
    camera.position.set(0, 0, 16)

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ alpha: false, antialias: true, powerPreference: "high-performance" })
      renderer.setSize(width, height)
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
      renderer.setClearColor(0x01050a, 1.0)
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.2
      container.appendChild(renderer.domElement)
    } catch (e) {
      console.error("WebGL initialization error:", e)
      return
    }

    // --- Texture Atlas ---
    const atlasTexture = generateBotanicalAtlasTexture()
    const dustTexture = generateDustMoteTexture()

    // ===================================================================
    // CANYON TERRAIN & FLOWER MEADOW DISTRIBUTION
    // 36,000 points arranged along a continuous lush botanical valley.
    // Palette:
    // - Lilac (#9a6eb8)
    // - Cyan-Blue (#0eaee8)
    // - Silver-Mist White (#e5e4eb)
    // - Baby Sky Blue
    // - Opal Periwinkle
    // NO DARK COLORS, NO BLACK HOLES!
    // ===================================================================
    const PARTICLE_COUNT = 36000
    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const colors = new Float32Array(PARTICLE_COUNT * 3)
    const texIndices = new Float32Array(PARTICLE_COUNT)
    const sizes = new Float32Array(PARTICLE_COUNT)
    const windScales = new Float32Array(PARTICLE_COUNT)

    // Valley curve down Z
    const pathCenterAtZ = (z: number) => {
      return Math.sin(z * 0.018) * 8.5 + Math.cos(z * 0.042) * 3.5
    }

    const pathHeightAtZ = (z: number) => {
      return -3.4 + Math.sin(z * 0.012) * 1.5
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Z spans from +25 (around/behind camera) down to -340
      const z = 25.0 - Math.random() * 365.0

      // Lateral distribution across canyon banks
      const lateral = (Math.random() - 0.5) * 2.0
      const dx = Math.sign(lateral) * Math.pow(Math.abs(lateral), 0.74) * 36.0
      const centerX = pathCenterAtZ(z)
      const x = centerX + dx

      // Bank elevation: rises sharply as |dx| increases (U-shaped gorge)
      const absDx = Math.abs(dx)
      const bankSlope = Math.pow(absDx / 10.5, 2.15) * 2.05
      const terrainNoise = Math.sin(x * 0.2 + z * 0.14) * 0.8 + Math.cos(x * 0.35 - z * 0.08) * 0.6
      const y = pathHeightAtZ(z) + bankSlope + terrainNoise

      positions[i * 3 + 0] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z

      // Wind sway variation
      windScales[i] = 0.5 + Math.random() * 0.8

      // Species Assignment:
      // 54% Soft Botanical Foliage (Tile 0) — ensures thick, gapless undergrowth
      // 46% Luminous Wildflowers (Tiles 1-5) in the user's light, glowing colors!
      const isFlower = Math.random() < 0.46

      if (!isFlower) {
        // Tile 0: Soft Lush Foliage
        texIndices[i] = 0.0
        // Natural soft green variation with silvery-mint highlights
        const gVar = 0.85 + Math.random() * 0.3
        colors[i * 3 + 0] = 0.9 * gVar
        colors[i * 3 + 1] = 1.05 * gVar
        colors[i * 3 + 2] = 0.95 * gVar
        sizes[i] = 20.0 + Math.random() * 16.0
      } else {
        // Wildflower distribution using ONLY user's light color palette:
        const randChoice = Math.random()

        if (randChoice < 0.28) {
          // Tile 1: Soft Pastel Lilac / Lavender (#9a6eb8)
          texIndices[i] = 1.0
          colors[i * 3 + 0] = 1.0
          colors[i * 3 + 1] = 0.96
          colors[i * 3 + 2] = 1.0
          sizes[i] = 24.0 + Math.random() * 18.0
        } else if (randChoice < 0.54) {
          // Tile 2: Vibrant Light Sky Cyan & Electric Blue (#0eaee8)
          texIndices[i] = 2.0
          colors[i * 3 + 0] = 0.92
          colors[i * 3 + 1] = 0.98
          colors[i * 3 + 2] = 1.0
          sizes[i] = 25.0 + Math.random() * 19.0
        } else if (randChoice < 0.74) {
          // Tile 3: Luminous Silver-Mist White (#e5e4eb)
          texIndices[i] = 3.0
          colors[i * 3 + 0] = 1.0
          colors[i * 3 + 1] = 1.0
          colors[i * 3 + 2] = 1.0
          sizes[i] = 22.0 + Math.random() * 16.0
        } else if (randChoice < 0.88) {
          // Tile 4: Light Powder Baby Blue / Celestial Bellflower
          texIndices[i] = 4.0
          colors[i * 3 + 0] = 0.94
          colors[i * 3 + 1] = 0.98
          colors[i * 3 + 2] = 1.0
          sizes[i] = 23.0 + Math.random() * 17.0
        } else {
          // Tile 5: Soft Periwinkle & Opal Blossom (Lilac-Blue Blend)
          texIndices[i] = 5.0
          colors[i * 3 + 0] = 0.98
          colors[i * 3 + 1] = 0.96
          colors[i * 3 + 2] = 1.0
          sizes[i] = 22.0 + Math.random() * 16.0
        }
      }
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute("aColor", new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute("aTexIndex", new THREE.BufferAttribute(texIndices, 1))
    geometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1))
    geometry.setAttribute("aWindScale", new THREE.BufferAttribute(windScales, 1))

    // ===================================================================
    // THREE.JS SHADER MATERIAL
    // NO BLACK HOLES:
    // - Radial displacement is set to 0.0 (NO crater or void!)
    // - Moving cursor SELECTS and ILLUMINATES flowers underneath
    // - Hovered flowers gently swell by 25% and glow with cyan/lilac radiance
    // ===================================================================
    const meadowUniforms = {
      uTime: { value: 0 },
      uAtlas: { value: atlasTexture },
      uMouse: { value: new THREE.Vector2(-999, -999) },
      uResolution: { value: new THREE.Vector2(width, height) },
      uMouseRadius: { value: 0.28 },
      uFogColor: { value: new THREE.Color(0x01050a) },
    }

    const meadowMaterial = new THREE.ShaderMaterial({
      uniforms: meadowUniforms,
      vertexShader: `
        uniform float uTime;
        uniform vec2 uMouse;
        uniform vec2 uResolution;
        uniform float uMouseRadius;

        attribute vec3 aColor;
        attribute float aTexIndex;
        attribute float aSize;
        attribute float aWindScale;

        varying vec3 vColor;
        varying float vTexIndex;
        varying float vDepth;
        varying float vCursorGlow;

        void main() {
          vColor = aColor;
          vTexIndex = aTexIndex;

          // Gentle natural wind breeze
          vec3 worldPos = position;
          float wind = sin(uTime * 1.5 + position.x * 0.28 + position.z * 0.14) * 0.12 * aWindScale;
          worldPos.x += wind;
          worldPos.y += cos(uTime * 1.1 + position.z * 0.18) * 0.07 * aWindScale;

          vec4 viewPos = viewMatrix * vec4(worldPos, 1.0);
          vDepth = -viewPos.z;

          vec4 clipPos = projectionMatrix * viewPos;

          // Screen-space cursor selection (NO BLACK HOLES!)
          vec2 ndc = clipPos.xy / clipPos.w;
          vec2 mouseDiff = ndc - uMouse;
          mouseDiff.x *= (uResolution.x / uResolution.y);
          float dist = length(mouseDiff);

          // Calculate interactive hover / selection glow
          if (dist < uMouseRadius) {
            vCursorGlow = pow(clamp(1.0 - dist / uMouseRadius, 0.0, 1.0), 1.6);
            // Subtle interactive organic ripple when hovered (NO void push!)
            worldPos.y += sin(uTime * 3.5 + position.x * 2.0) * vCursorGlow * 0.08;
          } else {
            vCursorGlow = 0.0;
          }

          // Point size perspective scaling
          // When hovered by cursor, the flower gently swells up by 25% like a selected bloom!
          float pSize = aSize * (uResolution.y / max(vDepth, 1.0)) * 0.038;
          pSize *= (1.0 + vCursorGlow * 0.28);
          gl_PointSize = clamp(pSize, 2.0, 68.0);

          gl_Position = clipPos;
        }
      `,
      fragmentShader: `
        uniform sampler2D uAtlas;
        uniform vec3 uFogColor;

        varying vec3 vColor;
        varying float vTexIndex;
        varying float vDepth;
        varying float vCursorGlow;

        void main() {
          // Map point coordinates (0..1) to the 6x1 horizontal texture atlas
          float tile = floor(vTexIndex + 0.5);
          vec2 uv = vec2((gl_PointCoord.x + tile) / 6.0, gl_PointCoord.y);

          // Split-RGB Chromatic Aberration & Soft Bokeh dispersion on close foreground petals
          float dispersion = clamp((22.0 - vDepth) * 0.00035, 0.0, 0.0025);
          vec2 dispOffset = (gl_PointCoord - 0.5) * dispersion;

          float r = texture2D(uAtlas, uv + dispOffset).r;
          float g = texture2D(uAtlas, uv).g;
          float b = texture2D(uAtlas, uv - dispOffset).b;
          float a = texture2D(uAtlas, uv).a;

          if (a < 0.035) discard;

          vec3 baseColor = vec3(r, g, b) * vColor;

          // Interactive Selection & Hover Illumination:
          // Flowers under/near cursor gracefully light up in ethereal cyan-blue (#0eaee8) and lilac (#9a6eb8)
          vec3 selectAura = vec3(0.05, 0.72, 0.95) * 0.55 + vec3(0.65, 0.45, 0.85) * 0.45;
          baseColor += vCursorGlow * selectAura * 1.5;
          // Soft radiant center sparkle when selected
          baseColor += pow(vCursorGlow, 2.5) * vec3(1.0, 1.0, 1.0) * 1.2;

          // Depth fog fade into deep night black
          float fogFactor = 1.0 - exp(-vDepth * vDepth * 0.00007);
          vec3 finalColor = mix(baseColor, uFogColor, clamp(fogFactor, 0.0, 1.0));

          gl_FragColor = vec4(finalColor, a);
        }
      `,
      transparent: true,
      depthTest: true,
      depthWrite: false,
    })

    // ===================================================================
    // 3D CONTOURED CANYON GROUND MESH
    // Exactly matches the U-shaped canyon banks & curves of the flowers!
    // ===================================================================
    const groundWidth = 90
    const groundLength = 390
    const segX = 140
    const segZ = 260
    const groundGeo = new THREE.PlaneGeometry(groundWidth, groundLength, segX, segZ)
    groundGeo.rotateX(-Math.PI / 2)
    groundGeo.translate(0, 0, -165) // covers Z from +30 to -360

    const groundPosAttr = groundGeo.attributes.position
    for (let i = 0; i < groundPosAttr.count; i++) {
      const x = groundPosAttr.getX(i)
      const z = groundPosAttr.getZ(i)

      const centerX = pathCenterAtZ(z)
      const dx = x - centerX
      const absDx = Math.abs(dx)

      // Exactly matches flower canyon elevation formula!
      const bankSlope = Math.pow(absDx / 10.5, 2.15) * 2.05
      const terrainNoise = Math.sin(x * 0.2 + z * 0.14) * 0.8 + Math.cos(x * 0.35 - z * 0.08) * 0.6
      // Ground sits just 0.30 below the flowers/leaves
      const y = pathHeightAtZ(z) + bankSlope + terrainNoise - 0.30

      groundPosAttr.setY(i, y)
    }
    groundGeo.computeVertexNormals()

    const groundUniforms = {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(-999, -999) },
      uResolution: { value: new THREE.Vector2(width, height) },
      uMouseRadius: { value: 0.28 },
      uFogColor: { value: new THREE.Color(0x01050a) },
    }

    const groundMat = new THREE.ShaderMaterial({
      uniforms: groundUniforms,
      vertexShader: `
        varying vec3 vWorldPosition;
        varying vec3 vNormal;
        varying vec2 vUv;
        varying float vDepth;

        void main() {
          vUv = uv;
          vec4 worldPos = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPos.xyz;
          vNormal = normalize(normalMatrix * normal);
          vec4 viewPos = viewMatrix * worldPos;
          vDepth = -viewPos.z;
          gl_Position = projectionMatrix * viewPos;
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform vec2 uMouse;
        uniform vec2 uResolution;
        uniform float uMouseRadius;
        uniform vec3 uFogColor;

        varying vec3 vWorldPosition;
        varying vec3 vNormal;
        varying vec2 vUv;
        varying float vDepth;

        // Procedural noise for natural moss & loam texture
        float hash(vec2 p) {
          return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
        }

        float noise(vec2 p) {
          vec2 i = floor(p);
          vec2 f = fract(p);
          f = f * f * (3.0 - 2.0 * f);
          float a = hash(i);
          float b = hash(i + vec2(1.0, 0.0));
          float c = hash(i + vec2(0.0, 1.0));
          float d = hash(i + vec2(1.0, 1.0));
          return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
        }

        void main() {
          vec3 viewDir = normalize(cameraPosition - vWorldPosition);

          // Multi-scale procedural moss & earth texture
          float n1 = noise(vWorldPosition.xz * 0.45);
          float n2 = noise(vWorldPosition.xz * 1.9);
          float n3 = noise(vWorldPosition.xz * 6.5);
          float mossPattern = n1 * 0.5 + n2 * 0.35 + n3 * 0.15;

          // Natural organic earth tones: fertile humus loam & soft velvet moss
          vec3 soilColor = vec3(0.04, 0.09, 0.06); // deep dark earth
          vec3 mossColor1 = vec3(0.09, 0.26, 0.16); // rich emerald moss
          vec3 mossColor2 = vec3(0.16, 0.42, 0.25); // luminous mint-moss highlights

          vec3 baseGround = mix(soilColor, mix(mossColor1, mossColor2, n2), mossPattern);

          // Soft directional moonlight from above
          vec3 lightDir = normalize(vec3(0.18, 0.94, 0.28));
          float diffuse = max(dot(vNormal, lightDir), 0.0);
          vec3 litGround = baseGround * (0.45 + diffuse * 0.65);

          // Subtle dewy sheen on moss
          vec3 halfVec = normalize(lightDir + viewDir);
          float spec = pow(max(dot(vNormal, halfVec), 0.0), 24.0) * 0.2;
          litGround += vec3(0.4, 0.75, 0.55) * spec;

          // Screen-space cursor glow on ground (under flowers)
          vec4 clipPos = projectionMatrix * viewMatrix * vec4(vWorldPosition, 1.0);
          vec2 ndc = clipPos.xy / clipPos.w;
          vec2 mouseDiff = ndc - uMouse;
          mouseDiff.x *= (uResolution.x / uResolution.y);
          float cursorDist = length(mouseDiff);

          if (cursorDist < uMouseRadius) {
            float glow = pow(clamp(1.0 - cursorDist / uMouseRadius, 0.0, 1.0), 1.6);
            // Matches cyan-blue (#0eaee8) and lilac (#9a6eb8) floral aura
            litGround += glow * (vec3(0.05, 0.68, 0.91) * 0.55 + vec3(0.6, 0.43, 0.72) * 0.45) * 0.6;
          }

          // Depth fog fade into deep night black
          float fogFactor = 1.0 - exp(-vDepth * vDepth * 0.00007);
          vec3 finalColor = mix(litGround, uFogColor, clamp(fogFactor, 0.0, 1.0));

          gl_FragColor = vec4(finalColor, 1.0);
        }
      `,
      depthWrite: true,
      depthTest: true,
    })

    const groundMesh = new THREE.Mesh(groundGeo, groundMat)
    scene.add(groundMesh)

    const meadowPoints = new THREE.Points(geometry, meadowMaterial)
    scene.add(meadowPoints)

    // ===================================================================
    // FLOATING BIOLUMINESCENT POLLEN DUST MOTES
    // 700 glowing celestial dust motes swirling in the night breeze
    // ===================================================================
    const DUST_COUNT = 700
    const dustPositions = new Float32Array(DUST_COUNT * 3)
    const dustSpeeds = new Float32Array(DUST_COUNT * 3)

    for (let i = 0; i < DUST_COUNT; i++) {
      dustPositions[i * 3 + 0] = (Math.random() - 0.5) * 50.0
      dustPositions[i * 3 + 1] = -2.0 + Math.random() * 16.0
      dustPositions[i * 3 + 2] = 20.0 - Math.random() * 330.0

      dustSpeeds[i * 3 + 0] = (Math.random() - 0.5) * 0.02
      dustSpeeds[i * 3 + 1] = 0.005 + Math.random() * 0.015
      dustSpeeds[i * 3 + 2] = (Math.random() - 0.5) * 0.02
    }

    const dustGeo = new THREE.BufferGeometry()
    dustGeo.setAttribute("position", new THREE.BufferAttribute(dustPositions, 3))

    const dustMat = new THREE.PointsMaterial({
      size: 4.2,
      map: dustTexture,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      opacity: 0.75,
    })

    const dustPoints = new THREE.Points(dustGeo, dustMat)
    scene.add(dustPoints)

    // ===================================================================
    // EVENT LISTENERS & INTERACTION
    // Mouse movement, wheel scrolling, touch drag, and window resize
    // ===================================================================
    let mouseNdcX = -999
    let mouseNdcY = -999
    let targetTiltX = 0
    let targetTiltY = 0
    let currentTiltX = 0
    let currentTiltY = 0

    const handleMouseMove = (e: MouseEvent) => {
      mouseNdcX = (e.clientX / window.innerWidth) * 2 - 1
      mouseNdcY = -(e.clientY / window.innerHeight) * 2 + 1
      meadowUniforms.uMouse.value.set(mouseNdcX, mouseNdcY)
      groundUniforms.uMouse.value.set(mouseNdcX, mouseNdcY)

      targetTiltX = mouseNdcX * 1.5
      targetTiltY = mouseNdcY * 0.85
      lastInteractionTimeRef.current = Date.now()
    }

    const handleWheel = (e: WheelEvent) => {
      const delta = e.deltaY * 0.00065
      targetProgressRef.current = THREE.MathUtils.clamp(targetProgressRef.current + delta, 0, 1)
      lastInteractionTimeRef.current = Date.now()
    }

    let touchStartY = 0
    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        touchStartY = e.touches[0].clientY
      }
    }

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        const touchY = e.touches[0].clientY
        const delta = (touchStartY - touchY) * 0.002
        touchStartY = touchY
        targetProgressRef.current = THREE.MathUtils.clamp(targetProgressRef.current + delta, 0, 1)
        lastInteractionTimeRef.current = Date.now()
      }
    }

    const handleResize = () => {
      const w = window.innerWidth
      const h = window.innerHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
      meadowUniforms.uResolution.value.set(w, h)
      groundUniforms.uResolution.value.set(w, h)
    }

    window.addEventListener("mousemove", handleMouseMove)
    window.addEventListener("wheel", handleWheel, { passive: true })
    window.addEventListener("touchstart", handleTouchStart, { passive: true })
    window.addEventListener("touchmove", handleTouchMove, { passive: true })
    window.addEventListener("resize", handleResize)

    // ===================================================================
    // RENDER & ANIMATION LOOP
    // ===================================================================
    let animationFrameId: number
    let clock = new THREE.Clock()

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)
      const delta = clock.getDelta()
      const time = clock.getElapsedTime()

      meadowUniforms.uTime.value = time
      groundUniforms.uTime.value = time

      // Subtle idle forward drift if user has not interacted for 2.5 seconds
      if (Date.now() - lastInteractionTimeRef.current > 2500) {
        targetProgressRef.current = (targetProgressRef.current + 0.00028) % 1.0
      }

      // Smooth progress interpolation
      currentProgressRef.current = THREE.MathUtils.lerp(currentProgressRef.current, targetProgressRef.current, 0.065)
      setDepthProgress(currentProgressRef.current)

      // Smooth mouse camera tilt
      currentTiltX = THREE.MathUtils.lerp(currentTiltX, targetTiltX, 0.05)
      currentTiltY = THREE.MathUtils.lerp(currentTiltY, targetTiltY, 0.05)

      // Camera position along the valley path
      const camZ = 14.0 - currentProgressRef.current * 294.0
      const canyonCenterX = pathCenterAtZ(camZ)
      const canyonFloorY = pathHeightAtZ(camZ)

      const camX = canyonCenterX + currentTiltX * 1.8
      const camY = canyonFloorY + 4.2 + currentTiltY * 1.0

      camera.position.set(camX, camY, camZ)

      // Look ahead down the canyon curve
      const lookDist = 26.0
      const lookZ = camZ - lookDist
      const lookX = pathCenterAtZ(lookZ) + currentTiltX * 0.8
      const lookY = pathHeightAtZ(lookZ) + 3.2
      camera.lookAt(lookX, lookY, lookZ)

      // Animate floating pollen dust motes
      const dustPos = dustGeo.attributes.position.array as Float32Array
      for (let i = 0; i < DUST_COUNT; i++) {
        dustPos[i * 3 + 0] += Math.sin(time + i) * 0.015
        dustPos[i * 3 + 1] += Math.cos(time * 0.8 + i) * 0.01
        if (dustPos[i * 3 + 2] > camZ + 15.0) {
          dustPos[i * 3 + 2] = camZ - 200.0
        }
      }
      dustGeo.attributes.position.needsUpdate = true

      renderer.render(scene, camera)
    }

    animate()

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("wheel", handleWheel)
      window.removeEventListener("touchstart", handleTouchStart)
      window.removeEventListener("touchmove", handleTouchMove)
      window.removeEventListener("resize", handleResize)
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement)
      }
      renderer.dispose()
      atlasTexture.dispose()
      dustTexture.dispose()
      geometry.dispose()
      meadowMaterial.dispose()
      groundGeo.dispose()
      groundMat.dispose()
      dustGeo.dispose()
      dustMat.dispose()
      if (audioRef.current) {
        audioRef.current.stop()
      }
    }
  }, [])

  // Milestone depth calculations
  // 0.00 - 0.18: Hero View ("Grown, not built.")
  // 0.22 - 0.46: Plan 1 (Free Plan)
  // 0.48 - 0.74: Plan 2 (Student Pro)
  // 0.76 - 1.00: Plan 3 (Lifetime Sovereign)
  const isHeroVisible = depthProgress < 0.18
  const isFreePlanActive = depthProgress >= 0.19 && depthProgress <= 0.46
  const isProPlanActive = depthProgress >= 0.47 && depthProgress <= 0.74
  const isLifetimePlanActive = depthProgress >= 0.75

  const depthMeters = Math.round(depthProgress * 42)

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#01050a] text-[#f5efe2] font-['Manrope',sans-serif] select-none">
      {/* 3D WebGL Canvas Mount */}
      <div ref={mountRef} className="absolute inset-0 z-0 pointer-events-auto" />

      {/* Subtle Cinematic Vignette */}
      <div className="absolute inset-0 z-1 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_45%,rgba(1,5,10,0.65)_100%)]" />

      {/* ================================================================= */}
      {/* TOP HEADER & DEPTH NAVIGATION PILL */}
      {/* ================================================================= */}
      <header className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 md:px-12 pt-6 pointer-events-none">
        {/* Brand Logo */}
        <Link
          href="/"
          className="pointer-events-auto flex items-center gap-3 transition-opacity duration-200 hover:opacity-80"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-400 to-[#9a6eb8] p-0.5 shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#0a0f18] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-[#0eaee8]" />
            </div>
          </div>
          <span className="font-['Antonio',sans-serif] text-2xl tracking-wider text-white font-medium">IRIS</span>
        </Link>

        {/* Milestone Navigation Floating Pill */}
        <nav className="pointer-events-auto hidden md:flex items-center gap-1.5 p-1 rounded-full bg-white/[0.04] backdrop-blur-2xl border border-white/10 shadow-2xl">
          <button
            onClick={() => navigateToDepth(0.0)}
            className={`px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-wider transition-all duration-300 ${
              isHeroVisible
                ? "bg-[#f5efe2] text-[#0a0f18] shadow-md scale-105"
                : "text-white/60 hover:text-white hover:bg-white/5"
            }`}
          >
            Entrance
          </button>
          <button
            onClick={() => navigateToDepth(0.32)}
            className={`px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-wider transition-all duration-300 ${
              isFreePlanActive
                ? "bg-[#f5efe2] text-[#0a0f18] shadow-md scale-105"
                : "text-white/60 hover:text-white hover:bg-white/5"
            }`}
          >
            Free Plan (₹0)
          </button>
          <button
            onClick={() => navigateToDepth(0.6)}
            className={`px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-wider transition-all duration-300 ${
              isProPlanActive
                ? "bg-[#f5efe2] text-[#0a0f18] shadow-md scale-105"
                : "text-white/60 hover:text-white hover:bg-white/5"
            }`}
          >
            Student Pro (₹99) ★
          </button>
          <button
            onClick={() => navigateToDepth(0.88)}
            className={`px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-wider transition-all duration-300 ${
              isLifetimePlanActive
                ? "bg-[#f5efe2] text-[#0a0f18] shadow-md scale-105"
                : "text-white/60 hover:text-white hover:bg-white/5"
            }`}
          >
            Lifetime (₹999)
          </button>
        </nav>

        {/* Right Actions */}
        <div className="pointer-events-auto flex items-center gap-3">
          <button
            onClick={() => setShowMatrixModal(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.04] backdrop-blur-xl border border-white/10 text-xs font-medium text-white/70 hover:text-white hover:bg-white/10 transition-all"
          >
            <Layers className="w-3.5 h-3.5 text-[#0eaee8]" />
            <span className="hidden sm:inline">Compare</span> Matrix
          </button>
          <Link
            href="/login"
            className="px-4 py-1.5 rounded-full bg-white text-[#0a0f18] text-xs font-semibold hover:bg-[#f5efe2] transition-transform hover:scale-105"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* ================================================================= */}
      {/* 1. HERO VIEW (DEPTH 0.00 - 0.18) */}
      {/* Matches Gladeye's Fernhollow Hero composition */}
      {/* ================================================================= */}
      <div
        className={`absolute inset-0 z-10 flex flex-col items-center justify-center text-center px-4 transition-all duration-700 pointer-events-none ${
          isHeroVisible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-8 pointer-events-none"
        }`}
      >
        {/* Tall Condensed Headline: "Grown, not built." */}
        <h1 className="font-['Antonio',sans-serif] text-7xl sm:text-8xl md:text-9xl lg:text-[148px] leading-[0.92] tracking-[-0.015em] text-[#f5efe2] drop-shadow-2xl">
          Grown, not built.
        </h1>

        {/* Subtitle */}
        <div className="mt-8 text-lg sm:text-xl md:text-2xl text-white/80 font-normal leading-relaxed tracking-wide">
          <p>Rooted in nature.</p>
          <p>Built for what’s next.</p>
        </div>

        {/* Round Arrow Button & Explore CTA */}
        <div className="pointer-events-auto mt-8 flex flex-col items-center gap-4">
          <button
            onClick={() => navigateToDepth(0.32)}
            className="group w-14 h-14 rounded-full border border-[#f5efe2]/60 hover:border-[#f5efe2] hover:bg-[#f5efe2] hover:text-[#0a0f18] flex items-center justify-center transition-all duration-300 shadow-xl cursor-pointer"
            aria-label="Enter valley and explore plans"
          >
            <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
          </button>

          <button
            onClick={() => navigateToDepth(0.32)}
            className="px-6 py-2.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] backdrop-blur-xl border border-white/20 text-xs tracking-wider uppercase font-semibold text-white transition-all shadow-lg hover:scale-105"
          >
            Enter Valley & Explore Plans →
          </button>
        </div>
      </div>

      {/* ================================================================= */}
      {/* 2. INVISIBLE GLASS PRICING PLATES */}
      {/* Seamless liquid glass plates that float right over the glowing flowers */}
      {/* ================================================================= */}

      {/* PLAN 1: FREE PLAN (DEPTH 0.20 - 0.46) */}
      <div
        className={`absolute inset-0 z-10 flex items-center justify-center px-4 transition-all duration-700 pointer-events-none ${
          isFreePlanActive ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
        }`}
      >
        <div className="pointer-events-auto relative w-full max-w-lg rounded-3xl p-8 sm:p-10 backdrop-blur-2xl bg-white/[0.03] border border-white/20 shadow-[0_30px_80px_rgba(0,0,0,0.8)] transition-all">
          <div className="absolute inset-0 rounded-3xl pointer-events-none border-t border-l border-white/30" />

          {/* Badge */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#0eaee8] bg-[#0eaee8]/10 px-3 py-1 rounded-full border border-[#0eaee8]/30">
              Tier 01 • Seedling Grove
            </span>
            <span className="text-xs text-white/50">Depth: 12m</span>
          </div>

          <h2 className="mt-4 text-3xl font-['Antonio',sans-serif] tracking-wide text-white">Seedling Companion</h2>
          <p className="mt-1 text-sm text-white/70">
            Essential private intelligence. Runs 100% locally with zero cloud telemetry.
          </p>

          <div className="mt-6 flex items-baseline gap-2">
            <span className="text-5xl font-['Antonio',sans-serif] tracking-tight text-white">₹0</span>
            <span className="text-sm text-white/50">/ forever free</span>
          </div>

          <ul className="mt-6 space-y-3">
            {pricingTiers[0].features.map((f, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-white/80">
                <Check className="w-4 h-4 text-[#0eaee8] shrink-0 mt-0.5" />
                <span>{f}</span>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex items-center gap-3">
            <Link
              href="/signup"
              className="flex-1 py-3 px-6 rounded-2xl bg-white text-[#0a0f18] text-sm font-semibold text-center hover:bg-[#f5efe2] transition-transform hover:scale-[1.02] shadow-xl"
            >
              Get Started Free
            </Link>
            <button
              onClick={() => navigateToDepth(0.6)}
              className="py-3 px-5 rounded-2xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/20 text-sm text-white font-medium transition-all"
            >
              Next Plan →
            </button>
          </div>
        </div>
      </div>

      {/* PLAN 2: STUDENT PRO (DEPTH 0.48 - 0.74) */}
      <div
        className={`absolute inset-0 z-10 flex items-center justify-center px-4 transition-all duration-700 pointer-events-none ${
          isProPlanActive ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
        }`}
      >
        <div className="pointer-events-auto relative w-full max-w-lg rounded-3xl p-8 sm:p-10 backdrop-blur-2xl bg-white/[0.04] border border-[#9a6eb8]/40 shadow-[0_30px_90px_rgba(154,110,184,0.25)] transition-all">
          <div className="absolute inset-0 rounded-3xl pointer-events-none border-t border-l border-[#9a6eb8]/50" />

          {/* Badge */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#d8b4fe] bg-[#9a6eb8]/15 px-3 py-1 rounded-full border border-[#9a6eb8]/40 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-[#d8b4fe]" /> Tier 02 • Student Pro ★ Most Popular
            </span>
            <span className="text-xs text-white/50">Depth: 25m</span>
          </div>

          <h2 className="mt-4 text-3xl font-['Antonio',sans-serif] tracking-wide text-white">Student Pro</h2>
          <p className="mt-1 text-sm text-white/70">
            Autonomous cognitive OS with 3-tier persistent memory, custom voice & companion themes.
          </p>

          <div className="mt-6 flex items-baseline gap-2">
            <span className="text-5xl font-['Antonio',sans-serif] tracking-tight text-white">₹99</span>
            <span className="text-sm text-white/50">/ per month</span>
          </div>

          <ul className="mt-6 space-y-3">
            {pricingTiers[1].features.map((f, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-white/80">
                <Check className="w-4 h-4 text-[#d8b4fe] shrink-0 mt-0.5" />
                <span>{f}</span>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex items-center gap-3">
            <button
              onClick={() => setCheckoutPlan("student")}
              className="flex-1 py-3 px-6 rounded-2xl bg-gradient-to-r from-[#9a6eb8] to-[#0eaee8] text-white text-sm font-semibold text-center hover:opacity-95 transition-transform hover:scale-[1.02] shadow-xl shadow-[#9a6eb8]/25"
            >
              Subscribe to Pro
            </button>
            <button
              onClick={() => navigateToDepth(0.88)}
              className="py-3 px-5 rounded-2xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/20 text-sm text-white font-medium transition-all"
            >
              Next Plan →
            </button>
          </div>
        </div>
      </div>

      {/* PLAN 3: LIFETIME SOVEREIGN (DEPTH 0.76 - 1.00) */}
      <div
        className={`absolute inset-0 z-10 flex items-center justify-center px-4 transition-all duration-700 pointer-events-none ${
          isLifetimePlanActive ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
        }`}
      >
        <div className="pointer-events-auto relative w-full max-w-lg rounded-3xl p-8 sm:p-10 backdrop-blur-2xl bg-white/[0.04] border border-[#e5e4eb]/40 shadow-[0_30px_90px_rgba(229,228,235,0.2)] transition-all">
          <div className="absolute inset-0 rounded-3xl pointer-events-none border-t border-l border-white/50" />

          {/* Badge */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#e5e4eb] bg-white/10 px-3 py-1 rounded-full border border-white/30 flex items-center gap-1.5">
              <Compass className="w-3 h-3 text-[#0eaee8]" /> Tier 03 • Lifetime Sovereign • Forever Key
            </span>
            <span className="text-xs text-white/50">Depth: 42m</span>
          </div>

          <h2 className="mt-4 text-3xl font-['Antonio',sans-serif] tracking-wide text-white">Lifetime Sovereign</h2>
          <p className="mt-1 text-sm text-white/70">
            Permanent air-gapped license. Zero recurring fees, lifetime model updates & custom wake-words.
          </p>

          <div className="mt-6 flex items-baseline gap-2">
            <span className="text-5xl font-['Antonio',sans-serif] tracking-tight text-white">₹999</span>
            <span className="text-sm text-white/50">/ one-time payment</span>
          </div>

          <ul className="mt-6 space-y-3">
            {pricingTiers[2].features.map((f, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-white/80">
                <Check className="w-4 h-4 text-[#0eaee8] shrink-0 mt-0.5" />
                <span>{f}</span>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex items-center gap-3">
            <button
              onClick={() => setCheckoutPlan("lifetime")}
              className="flex-1 py-3 px-6 rounded-2xl bg-gradient-to-r from-[#0eaee8] via-[#9a6eb8] to-[#e5e4eb] text-[#0a0f18] text-sm font-semibold text-center hover:opacity-95 transition-transform hover:scale-[1.02] shadow-xl shadow-cyan-500/25"
            >
              Claim Lifetime Sovereign
            </button>
            <button
              onClick={() => navigateToDepth(0.0)}
              className="py-3 px-5 rounded-2xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/20 text-sm text-white font-medium transition-all"
            >
              Back to Start ↺
            </button>
          </div>
        </div>
      </div>

      {/* ================================================================= */}
      {/* BOTTOM HUD CONTROLS */}
      {/* ================================================================= */}
      <footer className="absolute bottom-0 left-0 right-0 z-20 flex items-center justify-between px-6 md:px-12 pb-6 pointer-events-none">
        {/* Left: Valley Depth Gauge */}
        <div className="pointer-events-auto flex items-center gap-3 text-xs font-mono text-white/60 tracking-wider">
          <span>DEPTH: {depthMeters}M</span>
          <div className="w-20 h-1 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#0eaee8] to-[#9a6eb8] transition-all duration-150"
              style={{ width: `${Math.round(depthProgress * 100)}%` }}
            />
          </div>
          <span>{Math.round(depthProgress * 100)}%</span>
        </div>

        {/* Center: Scroll Instruction */}
        <div className="hidden sm:block text-[11px] uppercase tracking-[0.2em] text-white/40 font-mono">
          Scroll or touch to wander
        </div>

        {/* Right: Audio Toggle Speaker Button */}
        <div className="pointer-events-auto flex items-center gap-3">
          <button
            onClick={handleToggleSound}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.04] backdrop-blur-xl border border-white/10 text-xs tracking-wider uppercase text-white/70 hover:text-white hover:bg-white/10 transition-all"
            aria-label="Toggle ambient sound"
          >
            {isSoundOn ? (
              <>
                <Volume2 className="w-3.5 h-3.5 text-[#0eaee8]" />
                <span>Sound: On</span>
              </>
            ) : (
              <>
                <VolumeX className="w-3.5 h-3.5 text-white/40" />
                <span>Sound: Off</span>
              </>
            )}
          </button>
        </div>
      </footer>

      {/* ================================================================= */}
      {/* FULL COMPARISON MATRIX MODAL */}
      {/* ================================================================= */}
      {showMatrixModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-2xl">
          <div className="relative w-full max-w-4xl rounded-3xl p-6 sm:p-8 bg-[#0a0f18]/90 border border-white/20 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-6 border-b border-white/10">
              <div>
                <h3 className="text-2xl font-['Antonio',sans-serif] text-white tracking-wide">
                  Complete Capability Matrix
                </h3>
                <p className="text-xs text-white/60">Compare technical local privileges across all three tiers.</p>
              </div>
              <button
                onClick={() => setShowMatrixModal(false)}
                className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-y-auto mt-4 pr-1">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs font-mono uppercase tracking-wider text-white/50">
                    <th className="py-3 px-4">Feature</th>
                    <th className="py-3 px-4 text-center">Free (₹0)</th>
                    <th className="py-3 px-4 text-center text-[#d8b4fe]">Student Pro (₹99)</th>
                    <th className="py-3 px-4 text-center text-[#0eaee8]">Lifetime (₹999)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {comparisonData.map((row, i) => (
                    <tr key={i} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-4 text-white/80 font-medium">{row.feature}</td>
                      <td className="py-3 px-4 text-center text-white/60">{row.free}</td>
                      <td className="py-3 px-4 text-center text-[#d8b4fe] font-semibold">{row.pro}</td>
                      <td className="py-3 px-4 text-center text-[#0eaee8] font-semibold">{row.lifetime}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pt-6 mt-4 border-t border-white/10 flex justify-end">
              <button
                onClick={() => setShowMatrixModal(false)}
                className="px-6 py-2 rounded-xl bg-white text-black text-xs font-semibold hover:bg-white/90"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Plan Checkout & UPI QR Modal */}
      <PlanCheckoutModal
        isOpen={Boolean(checkoutPlan)}
        onClose={() => setCheckoutPlan(null)}
        planId={checkoutPlan || "student"}
      />
    </div>
  )
}
