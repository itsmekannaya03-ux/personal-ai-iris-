import { Navbar } from "@/components/ui/Navbar"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"
import { Check, ArrowRight } from "lucide-react"
import Link from "next/link"

const plans = [
  {
    name: "Free",
    price: "0",
    period: "forever",
    desc: "Try IGRIS with basic features",
    features: [
      "Basic voice assistant",
      "Short-term memory only",
      "3 skill modules",
      "Default blob UI",
      "Limited PC access",
    ],
    cta: "Get Started",
    highlight: false,
  },
  {
    name: "Student Pro",
    price: "99",
    period: "per month",
    desc: "Full AI assistant for students",
    features: [
      "Full 3-tier memory system",
      "All skill modules",
      "Custom AI name & personality",
      "All 6 UI themes",
      "Full PC access",
      "Voice always-on mode",
    ],
    cta: "Subscribe Now",
    highlight: true,
  },
  {
    name: "Lifetime",
    price: "999",
    period: "one time",
    desc: "Everything, forever",
    features: [
      "Everything in Student Pro",
      "Priority model updates",
      "Custom wake word",
      "Beta features first",
      "Lifetime access",
      "Future premium skills",
    ],
    cta: "Get Lifetime",
    highlight: false,
  },
]

const comparisons = [
  { feature: "Runs locally", free: true, pro: true, lifetime: true },
  { feature: "Private data (never leaves PC)", free: true, pro: true, lifetime: true },
  { feature: "Short-term memory", free: true, pro: true, lifetime: true },
  { feature: "Long-term memory", free: false, pro: true, lifetime: true },
  { feature: "Deep memory (permanent)", free: false, pro: true, lifetime: true },
  { feature: "All skill modules", free: false, pro: true, lifetime: true },
  { feature: "Custom AI name & personality", free: false, pro: true, lifetime: true },
  { feature: "All 6 UI themes", free: false, pro: true, lifetime: true },
  { feature: "Full PC access", free: false, pro: true, lifetime: true },
  { feature: "Custom wake word", free: false, pro: false, lifetime: true },
  { feature: "Priority model updates", free: false, pro: false, lifetime: true },
  { feature: "Beta features first", free: false, pro: false, lifetime: true },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen grid-bg">
      <Navbar />

      <section className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Simple Pricing. <span className="gradient-text">Total Privacy.</span>
            </h1>
            <p className="text-white/50 max-w-xl mx-auto">
              No hidden fees. No data mining. Your subscription pays for development, not for your data.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-20">
            {plans.map((plan) => (
              <Card
                key={plan.name}
                variant={plan.highlight ? "glow" : "default"}
                className={`p-8 relative ${plan.highlight ? "border-igris-500/50" : ""}`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-igris-600 rounded-full text-xs font-medium text-white">
                    Most Popular
                  </div>
                )}
                <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                <p className="text-sm text-white/50 mb-6">{plan.desc}</p>
                <div className="mb-6">
                  <span className="text-4xl font-bold">₹{plan.price}</span>
                  <span className="text-white/40 text-sm ml-2">/{plan.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-white/70">
                      <Check className="w-4 h-4 text-igris-400 mt-0.5 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href={`/signup?plan=${plan.name.toLowerCase().replace(" ", "-")}`}>
                  <Button variant={plan.highlight ? "primary" : "outline"} className="w-full">
                    {plan.cta}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </Card>
            ))}
          </div>

          {/* Comparison Table */}
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-center mb-8">Full Feature Comparison</h2>
            <div className="space-y-2">
              {comparisons.map((row) => (
                <div
                  key={row.feature}
                  className="grid grid-cols-4 gap-4 px-4 py-3 rounded-lg bg-white/[0.02] text-sm"
                >
                  <span className="text-white/70">{row.feature}</span>
                  <span className={`text-center ${row.free ? "text-igris-400" : "text-white/20"}`}>
                    {row.free ? "✓" : "—"}
                  </span>
                  <span className={`text-center ${row.pro ? "text-igris-400" : "text-white/20"}`}>
                    {row.pro ? "✓" : "—"}
                  </span>
                  <span className={`text-center ${row.lifetime ? "text-igris-400" : "text-white/20"}`}>
                    {row.lifetime ? "✓" : "—"}
                  </span>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-4 gap-4 px-4 py-2 text-xs text-white/30 mt-2">
              <span />
              <span className="text-center">Free</span>
              <span className="text-center">Pro</span>
              <span className="text-center">Lifetime</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
