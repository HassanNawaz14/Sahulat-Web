"use client"

import type { ScheduledOutage } from "@/lib/hooks/useOutages"

interface OutageTimelineProps {
  outages: ScheduledOutage[]
  label: string
}

function formatHour(isoStr: string) {
  try {
    const d = new Date(isoStr)
    return d.toLocaleTimeString("en-PK", { hour: "2-digit", minute: "2-digit", hour12: true })
  } catch {
    return isoStr
  }
}

export default function OutageTimeline({ outages, label }: OutageTimelineProps) {
  if (outages.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</p>
        <p className="mt-2 text-sm text-gray-500">No scheduled outages</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</p>
      <div className="mt-3 space-y-2">
        {outages.map((outage) => {
          const isActive = outage.status === "active"
          const isUpcoming = outage.status === "upcoming"
          return (
            <div
              key={outage.id}
              className={`flex items-center gap-3 rounded-lg border p-3 ${
                isActive
                  ? "border-red-200 bg-red-50"
                  : isUpcoming
                  ? "border-amber-200 bg-amber-50"
                  : "border-gray-100 bg-gray-50"
              }`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                  isActive
                    ? "bg-red-200 text-red-700"
                    : isUpcoming
                    ? "bg-amber-200 text-amber-700"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {formatHour(outage.start_time)}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">
                  {formatHour(outage.start_time)} – {formatHour(outage.end_time)}
                </p>
                <p className="text-xs text-gray-500">{outage.feeder_name}</p>
              </div>
              {isActive && (
                <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                  Ongoing
                </span>
              )}
              {isUpcoming && (
                <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                  Upcoming
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
