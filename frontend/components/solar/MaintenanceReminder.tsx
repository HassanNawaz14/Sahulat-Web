"use client"

import { Wrench, CalendarDays, Droplet } from "lucide-react"

const formatDays = (days: number) => {
  if (days === 0) return "Today"
  if (days === 1) return "1 day"
  return `${days} days`
}

const getCleaningDays = (systemSize: number) => {
  if (systemSize >= 15) return 30
  if (systemSize >= 10) return 35
  return 45
}

export default function MaintenanceReminder({
  lastMaintenanceDate,
  systemSizeKw,
  onMarkDone,
}: {
  lastMaintenanceDate?: string | null
  systemSizeKw: number
  onMarkDone?: () => void
}) {
  const daysUntilCleaning = lastMaintenanceDate
    ? Math.ceil(
        (new Date(lastMaintenanceDate).getTime() +
          getCleaningDays(systemSizeKw) * 24 * 60 * 60 * 1000 -
          Date.now()) /
          (24 * 60 * 60 * 1000)
      )
    : getCleaningDays(systemSizeKw)

  const isOverdue = daysUntilCleaning < 0

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-600">Maintenance</h3>
        <Wrench className="h-4 w-4 text-blue-600" />
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 text-gray-500" />
            <span className="text-gray-600">Last Maintenance</span>
          </div>
          <span className="font-medium text-gray-900">
            {lastMaintenanceDate
              ? new Date(lastMaintenanceDate).toLocaleDateString("en-PK", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })
              : "Never"}
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <Droplet className="h-4 w-4 text-blue-500" />
            <span className="text-gray-600">Next Cleaning Due</span>
          </div>
          <span className={`font-medium ${isOverdue ? "text-red-600" : "text-gray-900"}`}>
            {isOverdue ? `Overdue by ${formatDays(Math.abs(daysUntilCleaning))}` : formatDays(daysUntilCleaning)}
          </span>
        </div>

        {lastMaintenanceDate && daysUntilCleaning > 0 && (
          <button
            onClick={() => onMarkDone?.()}
            className="w-full rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100"
          >
            Mark Cleaning Done
          </button>
        )}

        {isOverdue && (
          <div className="mt-4 rounded-lg bg-red-50 p-3">
            <p className="text-xs font-medium text-red-800">Maintenance overdue</p>
            <p className="mt-1 text-xs text-red-700">Schedule cleaning to maintain optimal performance</p>
          </div>
        )}
      </div>
    </div>
  )
}
