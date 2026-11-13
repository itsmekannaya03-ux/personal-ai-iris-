"use client"

import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"

const interests = [
  "Technology", "Music", "Gaming", "Programming",
  "Design", "Science", "Business", "Art",
  "Sports", "Reading", "Movies", "Education"
]

export default function ProfilePage() {
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    name: "", age: "", job: "", location: "", goals: "",
    interests: [] as string[], ai_name: "",
  })

  useEffect(() => {
    api.profile.get().then((data) => {
      setForm({
        name: data.name || "",
        age: data.age?.toString() || "",
        job: data.job || "",
        location: data.location || "",
        goals: data.goals || "",
        interests: data.interests || [],
        ai_name: data.ai_name || "IRIS",
      })
    }).catch(() => {})
  }, [])

  function toggleInterest(item: string) {
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(item)
        ? f.interests.filter((i) => i !== item)
        : [...f.interests, item],
    }))
  }

  async function handleSave() {
    setLoading(true)
    setError("")
    try {
      const parsedAge = form.age.trim() ? parseInt(form.age.trim(), 10) : undefined
      const validAge = !isNaN(parsedAge as number) && (parsedAge as number) > 0 ? parsedAge : undefined

      await api.profile.update({
        name: form.name.trim(),
        age: validAge,
        job: form.job.trim(),
        location: form.location.trim(),
        goals: form.goals.trim(),
        interests: form.interests,
        ai_name: form.ai_name.trim() || "IRIS",
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: any) {
      setError(err?.message || "Failed to save profile changes.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Your Profile</h1>
        <p className="text-white/50 mt-1">
          This information becomes your AI&apos;s DNA. It learns about you from here and builds on it over time.
        </p>
      </div>

      <Card className="p-6 max-w-2xl">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Name" id="name" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input label="Age" type="number" id="age" value={form.age}
              onChange={(e) => setForm({ ...form, age: e.target.value })} />
          </div>
          <Input label="Job / Role" id="job" value={form.job}
            onChange={(e) => setForm({ ...form, job: e.target.value })} />
          <Input label="Location" id="location" value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })} />
          <Input label="Your Goals" id="goals" value={form.goals}
            onChange={(e) => setForm({ ...form, goals: e.target.value })} />
          <Input label="AI Name" id="ai_name" value={form.ai_name}
            onChange={(e) => setForm({ ...form, ai_name: e.target.value })} />

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Interests</label>
            <div className="flex flex-wrap gap-2">
              {interests.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => toggleInterest(item)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-75 active:scale-95 cursor-pointer select-none touch-manipulation ${
                    form.interests.includes(item)
                      ? "bg-iris-600 text-white shadow-md shadow-iris-600/30"
                      : "bg-white/5 text-white/50 hover:bg-white/10"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 p-2.5 rounded-lg">
              {error}
            </p>
          )}

          <div className="pt-4">
            <Button onClick={handleSave} disabled={loading}>
              {loading ? "Saving..." : saved ? "Saved!" : "Save Changes"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
