"use client"

import Link from "next/link"
import { Button } from "./Button"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { Menu, X, Sparkles } from "lucide-react"

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 20)
    }
    handleScroll()
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled || mobileMenuOpen
          ? "bg-[#0a0a0f]/90 backdrop-blur-xl border-b border-white/10"
          : "bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group" onClick={() => setMobileMenuOpen(false)}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-iris-600 via-purple-600 to-indigo-400 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.5)] group-hover:scale-105 transition-transform">
            <Sparkles className="w-4 h-4 text-cyan-300" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-white tracking-tight">IRIS</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-iris-500/20 text-cyan-300 border border-iris-500/30">
                IRIS
              </span>
            </div>
          </div>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-8">
          <Link href="/pricing" prefetch={true} className="text-sm text-white/60 hover:text-white transition-colors duration-75 active:scale-95 cursor-pointer">
            Pricing
          </Link>
          <Link href="/features" prefetch={true} className="text-sm text-white/60 hover:text-white transition-colors duration-75 active:scale-95 cursor-pointer">
            Features
          </Link>
          <Link href="/login" prefetch={true}>
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link href="/signup" prefetch={true}>
            <Button size="sm">Get Started</Button>
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg bg-white/5 border border-white/10 text-white/70 hover:text-white active:scale-95 cursor-pointer"
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden px-6 pb-6 pt-2 bg-[#0a0a0f]/95 border-b border-white/10 space-y-4">
          <Link
            href="/pricing"
            prefetch={true}
            onClick={() => setMobileMenuOpen(false)}
            className="block text-base text-white/70 hover:text-white py-2 active:scale-95 cursor-pointer"
          >
            Pricing
          </Link>
          <Link
            href="/features"
            prefetch={true}
            onClick={() => setMobileMenuOpen(false)}
            className="block text-base text-white/70 hover:text-white py-2 active:scale-95 cursor-pointer"
          >
            Features
          </Link>
          <div className="pt-2 flex flex-col gap-2">
            <Link href="/login" prefetch={true} onClick={() => setMobileMenuOpen(false)} className="w-full">
              <Button variant="ghost" size="sm" className="w-full justify-center">
                Sign In
              </Button>
            </Link>
            <Link href="/signup" prefetch={true} onClick={() => setMobileMenuOpen(false)} className="w-full">
              <Button size="sm" className="w-full justify-center">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      )}
    </nav>
  )
}
