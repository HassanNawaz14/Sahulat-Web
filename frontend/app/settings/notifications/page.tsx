"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  useSubscribePush,
  useUnsubscribePush,
  useTestNotification,
  type NotificationPreference,
} from "@/lib/hooks/useNotifications"

const CATEGORY_LABELS: Record<string, string> = {
  bill_due: "Bill Due Reminders",
  outage: "Outage Alerts",
  slab: "Slab Boundary Alerts",
  budget: "Budget Alerts",
  solar: "Solar Alerts",
  community: "Community Outage Reports",
}

export default function NotificationsPage() {
  const { data: preferences, isLoading } = useNotificationPreferences()
  const updatePrefs = useUpdateNotificationPreferences()
  const subscribePush = useSubscribePush()
  const unsubscribePush = useUnsubscribePush()
  const testNotif = useTestNotification()

  if (isLoading) {
    return <p className="text-sm text-gray-500">Loading...</p>
  }

  const toggle = (category: string, enabled: boolean) => {
    if (!preferences) return
    const updated = preferences.map((p) =>
      p.category === category ? { ...p, enabled } : p
    )
    updatePrefs.mutate(updated)
  }

  const handleTest = async () => {
    try {
      await testNotif.mutateAsync()
      alert("Test notification sent!")
    } catch {
      alert("No active push subscription. Enable notifications first.")
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/settings" className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-xl font-bold">Notification Settings</h1>
      </div>
      <div className="space-y-4">
      {preferences?.map((pref: NotificationPreference) => (
        <label
          key={pref.category}
          className="flex items-center justify-between rounded-lg border bg-white p-4"
        >
          <span className="text-sm font-medium">
            {CATEGORY_LABELS[pref.category] ?? pref.category}
          </span>
          <input
            type="checkbox"
            className="h-5 w-5 accent-blue-600"
            checked={pref.enabled}
            onChange={(e) => toggle(pref.category, e.target.checked)}
          />
        </label>
      ))}

      <hr className="my-4" />

      <div className="rounded-lg border bg-white p-4">
        <h3 className="text-sm font-medium mb-2">Push Subscription</h3>
        <div className="flex gap-2">
          <button
            onClick={() => subscribePush.mutate()}
            disabled={subscribePush.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white disabled:opacity-50"
          >
            {subscribePush.isPending ? "Subscribing..." : "Subscribe"}
          </button>
          <button
            onClick={() => unsubscribePush.mutate()}
            disabled={unsubscribePush.isPending}
            className="rounded-lg border px-4 py-2 text-xs font-medium text-gray-600 disabled:opacity-50"
          >
            Unsubscribe
          </button>
        </div>
      </div>

      <button
        onClick={handleTest}
        disabled={testNotif.isPending}
        className="w-full rounded-lg border py-3 text-sm font-medium text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors"
      >
        {testNotif.isPending ? "Sending..." : "Send Test Notification"}
      </button>
      </div>
    </div>
  )
}
