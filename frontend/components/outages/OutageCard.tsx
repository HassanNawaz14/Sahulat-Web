"use client"

import { CircleAlert, CircleCheck, Clock } from "lucide-react"
import type { ScheduledOutage } from "@/lib/hooks/useOutages"

interface OutageCardProps {
  currentOutage: ScheduledOutage | null
  nextOutage: ScheduledOutage | null
  feederName: string
  feederSet: boolean
}

function formatTime(isoStr: string) {
  try {
    const d = new Date(isoStr)
    return d.toLocaleTimeString("en-PK", { hour: "2-digit", minute: "2-digit", hour12: true })
  } catch {
    return isoStr
  }
}

export default function OutageCard({ currentOutage, nextOutage, feederName, feederSet }: OutageCardProps) {
  if (currentOutage) {
    return (
      <div className="rounded-xl border-2 border-red-200 bg-red-50 p-4">
        <div className="flex items-center gap-2">
          <CircleAlert className="h-5 w-5 text-red-600" />
          <p className="text-sm font-semibold text-red-800">Outage ongoing</p>
        </div>
        <p className="mt-1 text-xs text-red-600">
          {feederName} &middot; {formatTime(currentOutage.start_time)} – {formatTime(currentOutage.end_time)}
        </p>
        {nextOutage && (
          <p className="mt-2 text-xs text-gray-500">
            Next: {formatTime(nextOutage.start_time)} – {formatTime(nextOutage.end_time)}
          </p>
        )}
      </div>
    )
  }

  if (nextOutage) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-amber-600" />
          <p className="text-sm font-semibold text-amber-800">Scheduled outage coming</p>
        </div>
        <p className="mt-1 text-xs text-amber-600">
          {feederName} &middot; {formatTime(nextOutage.start_time)} – {formatTime(nextOutage.end_time)}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-green-200 bg-green-50 p-4">
      <div className="flex items-center gap-2">
        <CircleCheck className="h-5 w-5 text-green-600" />
        <p className="text-sm font-semibold text-green-800">No scheduled outage</p>
      </div>
      {!feederSet ? (
        <p className="mt-1 text-xs text-gray-500">Set your feeder for accurate alerts</p>
      ) : (
        <p className="mt-1 text-xs text-green-600">{feederName} &middot; No outages scheduled</p>
      )}
    </div>
  )
}
