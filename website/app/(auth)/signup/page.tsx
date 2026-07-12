"use client"

import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Card } from "@/components/ui/Card"
import Link from "next/link"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"

const interests = [
  "Technology", "Music", "Gaming", "Programming",
  "Design", "Science", "Business", "Art",
  "Sports", "Reading", "Movies", "Education"
]

export default function SignupPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    email: "", password: "", name: "", age: "",
    job: "", location: "", goals: "",
    interests: [] as string[],
    ai_name: "IGRIS",
  })

  function toggleInterest(item: string) {
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(item)
        ? f.interests.filter((i) => i !== item)
        : [...f.interests, item],
    }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    try {
      const res = await api.auth.signup({
        email: form.email,
        password: form.password,
        name: form.name,
      })
      localStorage.setItem("igris_token", res.token)
      await api.profile.update({
        age: parseInt(form.age),
        job: form.job,
        location: form.location,
        goals: form.goals,
        interests: form.interests,
        ai_name: form.ai_name,
      })
      router.push("/pricing")
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid-bg flex items-center justify-center px-6 py-12">
      <Card className="w-full max-w-lg p-8">
        <div className="text-center mb-8">
          <div className="w-10 h-10 rounded-lg bg-igris-600 flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold">I</span>
          </div>
          <h1 className="text-2xl font-bold">Create Your AI</h1>
          <p className="text-sm text-white/50 mt-1">
            Step {step} of 3 — {step === 1 ? "Account" : step === 2 ? "Your Profile" : "Your AI"}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <div className="space-y-4">
              <Input
                label="Full Name"
                id="name"
                placeholder="John Doe"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
              <Input
                label="Email"
                type="email"
                id="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
              <Input
                label="Password"
                type="password"
                id="password"
                placeholder="At least 8 characters"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                minLength={8}
              />
              <Button type="button" className="w-full" onClick={() => setStep(2)}>
                Next — Your Profile
              </Button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <Input
                label="Age"
                type="number"
                id="age"
                placeholder="21"
                value={form.age}
                onChange={(e) => setForm({ ...form, age: e.target.value })}
              />
              <Input
                label="Job / Role"
                id="job"
                placeholder="Computer Science Student"
                value={form.job}
                onChange={(e) => setForm({ ...form, job: e.target.value })}
              />
              <Input
                label="Location"
                id="location"
                placeholder="Hyderabad, India"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
              />
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Interests</label>
                <div className="flex flex-wrap gap-2">
                  {interests.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => toggleInterest(item)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                        form.interests.includes(item)
                          ? "bg-igris-600 text-white"
                          : "bg-white/5 text-white/50 hover:bg-white/10"
                      }`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-3">
                <Button type="button" variant="ghost" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button type="button" className="flex-1" onClick={() => setStep(3)}>
                  Next — Customize AI
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <Input
                label="Your Goals"
                id="goals"
                placeholder="Learn to code, build a startup, stay organized..."
                value={form.goals}
                onChange={(e) => setForm({ ...form, goals: e.target.value })}
              />
              <Input
                label="AI Name"
                id="ai_name"
                placeholder="IGRIS, ARIA, MAX, FRIDAY..."
                value={form.ai_name}
                onChange={(e) => setForm({ ...form, ai_name: e.target.value })}
              />
              <p className="text-xs text-white/30">
                You can change all of this later. Your AI will adapt to you over time.
              </p>

              {error && <p className="text-sm text-red-400">{error}</p>}

              <div className="flex gap-3">
                <Button type="button" variant="ghost" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button type="submit" className="flex-1" disabled={loading}>
                  {loading ? "Creating..." : "Create My AI"}
                </Button>
              </div>
            </div>
          )}
        </form>

        <p className="text-sm text-white/40 text-center mt-6">
          Already have an account?{" "}
           <Link href="/login" className="text-igris-400 hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  )
}
