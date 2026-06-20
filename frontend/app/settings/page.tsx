"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Home, User, Bell } from "lucide-react"

import { createClient } from "@/lib/supabase/client"

export default function SettingsPage() {
  const [homes, setHomes] = useState<any[]>([])

  useEffect(() => {
    const supabase = createClient()
    supabase.from("homes").select("*").then(({ data }) => {
      if (data) setHomes(data)
    })
  }, [])

  return (
    <div className="space-y-4">
      <Link
        href="/settings/profile"
        className="flex items-center gap-4 rounded-lg border bg-white p-4"
      >
        <User className="h-5 w-5 text-gray-500" />
        <div>
          <p className="text-sm font-medium">Profile</p>
          <p className="text-xs text-gray-500">Name, city, language</p>
        </div>
      </Link>

      <Link
        href="/settings/notifications"
        className="flex items-center gap-4 rounded-lg border bg-white p-4"
      >
        <Bell className="h-5 w-5 text-gray-500" />
        <div>
          <p className="text-sm font-medium">Notifications</p>
          <p className="text-xs text-gray-500">Alerts & reminders</p>
        </div>
      </Link>

      <div className="rounded-lg border bg-white p-4">
        <div className="flex items-center gap-4">
          <Home className="h-5 w-5 text-gray-500" />
          <p className="text-sm font-medium">Homes ({homes.length})</p>
        </div>
        <div className="mt-3 space-y-2">
          {homes.map((home) => (
            <div key={home.id} className="rounded-md bg-gray-50 p-3 text-sm">
              <p className="font-medium">{home.name}{home.is_default ? " (Default)" : ""}</p>
              <p className="text-xs text-gray-500">{home.city}{home.area ? `, ${home.area}` : ""}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
