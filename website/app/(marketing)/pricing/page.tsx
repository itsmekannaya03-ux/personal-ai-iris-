"use client"

import dynamic from "next/dynamic"

const NightFlowerValley = dynamic(
  () => import("@/components/ui/NightFlowerValley").then((mod) => mod.NightFlowerValley),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-screen bg-[#02040a] flex items-center justify-center text-[#f5efe2]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
          <span className="font-mono text-xs text-white/50 tracking-widest uppercase">
            Entering Night Flower Valley...
          </span>
        </div>
      </div>
    ),
  }
)

export default function PricingPage() {
  return (
    <main className="w-full h-screen overflow-hidden bg-[#02040a]">
      <NightFlowerValley />
    </main>
  )
}
