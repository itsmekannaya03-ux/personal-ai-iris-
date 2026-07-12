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
        ai_name: data.ai_name || "IGRIS",
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
    try {
      await api.profile.update({
        name: form.name,
        age: parseInt(form.age) || 0,
        job: form.job,
        location: form.location,
        goals: form.goals,
        interests: form.interests,
        ai_name: form.ai_name,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
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
