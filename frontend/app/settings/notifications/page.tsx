"use client"

import { useEffect, useState } from "react"

import { createClient } from "@/lib/supabase/client"

export default function NotificationsPage() {
  const [prefs, setPrefs] = useState<any>(null)

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) return
      supabase.from("notification_preferences").select("*").eq("user_id", user.id).single().then(({ data }) => {
        if (data) setPrefs(data)
      })
    })
  }, [])

  const toggle = async (key: string, value: boolean) => {
    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return
    await supabase.from("notification_preferences").update({ [key]: value }).eq("user_id", user.id)
    setPrefs((prev: any) => ({ ...prev, [key]: value }))
  }

  if (!prefs) return <p className="text-sm text-gray-500">Loading...</p>

  const fields = [
    { key: "outage_alert_enabled", label: "Outage Alerts" },
    { key: "bill_due_alert_enabled", label: "Bill Due Reminders" },
    { key: "slab_alert_enabled", label: "Slab Boundary Alerts" },
    { key: "solar_alert_enabled", label: "Solar Alerts" },
    { key: "community_alerts", label: "Community Outage Reports" },
  ]

  return (
    <div className="space-y-4">
      {fields.map(({ key, label }) => (
        <label key={key} className="flex items-center justify-between rounded-lg border bg-white p-4">
          <span className="text-sm font-medium">{label}</span>
          <input
            type="checkbox"
            className="h-5 w-5 accent-blue-600"
            checked={!!prefs[key]}
            onChange={(e) => toggle(key, e.target.checked)}
          />
        </label>
      ))}
    </div>
  )
}
