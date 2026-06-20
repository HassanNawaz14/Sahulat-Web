"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { createClient } from "@/lib/supabase/client"
import { CITIES } from "@/lib/constants/discoMap"

export default function ProfilePage() {
  const router = useRouter()
  const [fullName, setFullName] = useState("")
  const [city, setCity] = useState("")
  const [area, setArea] = useState("")
  const [lang, setLang] = useState("en")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) return
      supabase.from("profiles").select("*").eq("id", user.id).single().then(({ data }) => {
        if (data) {
          setFullName(data.full_name ?? "")
          setCity(data.city ?? "")
          setArea(data.area ?? "")
          setLang(data.preferred_lang ?? "en")
        }
      })
    })
  }, [])

  const handleSave = async () => {
    setSaving(true)
    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return
    await supabase.from("profiles").update({
      full_name: fullName,
      city: city.toLowerCase(),
      area,
      preferred_lang: lang,
    }).eq("id", user.id)
    setSaving(false)
    router.push("/settings")
  }

  const handleDelete = async () => {
    if (!confirm("Type DELETE to confirm:\n\nThis will permanently delete your account.")) return
    const input = prompt("Type DELETE to confirm account deletion:")
    if (input !== "DELETE") return
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/delete-account`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
    await supabase.auth.signOut()
    router.push("/")
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <input
          className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
          placeholder="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
        <select
          className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
          value={city}
          onChange={(e) => setCity(e.target.value)}
        >
          <option value="">City</option>
          {CITIES.map((c) => (
            <option key={c} value={c.toLowerCase()}>{c}</option>
          ))}
        </select>
        <input
          className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
          placeholder="Area"
          value={area}
          onChange={(e) => setArea(e.target.value)}
        />
        <select
          className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
          value={lang}
          onChange={(e) => setLang(e.target.value)}
        >
          <option value="en">English</option>
          <option value="ur">اردو</option>
        </select>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save"}
      </button>

      <hr className="my-6" />

      <button
        onClick={handleDelete}
        className="w-full rounded-lg border border-red-300 py-3 text-sm font-medium text-red-600"
      >
        Delete Account
      </button>
    </div>
  )
}
