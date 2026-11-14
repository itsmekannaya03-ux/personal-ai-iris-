"use client"

import { useState, useEffect } from "react"
import NightFlowerValley from "@/components/ui/NightFlowerValley"

export default function PricingPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="w-full h-screen bg-[#02040a] flex items-center justify-center text-[#f5efe2]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
          <span className="font-mono text-xs text-white/50 tracking-widest uppercase">
            Entering Night Flower Valley...
          </span>
        </div>
      </div>
    )
  }

  return (
    <main className="w-full h-screen overflow-hidden bg-[#02040a]">
      <NightFlowerValley />
    </main>
  )
}
