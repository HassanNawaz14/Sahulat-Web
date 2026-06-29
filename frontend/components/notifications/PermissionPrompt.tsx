"use client"

import { useState } from "react"
import { Bell } from "lucide-react"

import { subscribeToPush } from "@/lib/notifications/push"

type Props = {
  onComplete: () => void
  onSkip: () => void
}

export default function PermissionPrompt({ onComplete, onSkip }: Props) {
  const [loading, setLoading] = useState(false)

  const handleEnable = async () => {
    setLoading(true)
    if (!("Notification" in window)) {
      onComplete()
      return
    }
    const permission = await Notification.requestPermission()
    if (permission === "granted") {
      await subscribeToPush()
    }
    onComplete()
  }

  return (
    <div className="space-y-6 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
        <Bell className="h-8 w-8 text-blue-600" />
      </div>
      <h2 className="text-xl font-bold">Stay Informed</h2>
      <p className="text-sm text-gray-500">
        Get notified before load shedding hits your area, when bills are due,
        and when you&apos;re approaching a higher tariff slab.
      </p>
      <div className="space-y-3">
        <button
          onClick={handleEnable}
          disabled={loading}
          className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50 transition-colors hover:bg-blue-700"
        >
          {loading ? "Enabling..." : "Enable Notifications"}
        </button>
        <button
          onClick={onSkip}
          disabled={loading}
          className="w-full rounded-lg border py-3 text-sm font-medium text-gray-600 disabled:opacity-50 transition-colors hover:bg-gray-100"
        >
          Not Now
        </button>
      </div>
    </div>
  )
}
