"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { Home, User, Bell, Zap } from "lucide-react"

import { createClient } from "@/lib/supabase/client"
import { DISCO_NAMES } from "@/lib/constants/discoMap"
import FeederSelector from "@/components/outages/FeederSelector"

export default function SettingsPage() {
  const [homes, setHomes] = useState<any[]>([])
  const [accounts, setAccounts] = useState<any[]>([])

  const load = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.user?.id) return
    supabase.from("homes").select("*").eq("user_id", session.user.id).then(({ data }) => {
      if (data) setHomes(data)
    })
    supabase.from("consumer_accounts").select("*").eq("user_id", session.user.id).then(({ data }) => {
      if (data) setAccounts(data)
    })
  }, [])

  useEffect(() => { load() }, [load])

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

      <div className="rounded-lg border bg-white p-4">
        <div className="flex items-center gap-4 mb-3">
          <Zap className="h-5 w-5 text-gray-500" />
          <p className="text-sm font-medium">Consumer Accounts ({accounts.length})</p>
        </div>
        <div className="space-y-3">
          {accounts.map((acc) => (
            <div key={acc.id} className="rounded-md bg-gray-50 p-3">
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  <p className="font-medium">{acc.account_label}</p>
                  <p className="text-xs text-gray-500">
                    {DISCO_NAMES[acc.provider_code] || acc.provider_code.toUpperCase()} &middot; {acc.consumer_number}
                  </p>
                </div>
              </div>
              <div className="mt-2">
                <FeederSelector
                  providerCode={acc.provider_code}
                  consumerAccountId={acc.id}
                  currentFeeder={acc.feeder_name}
                  onSaved={() => load()}
                />
              </div>
            </div>
          ))}
          {!accounts.length && (
            <p className="text-xs text-gray-400">No consumer accounts added yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
