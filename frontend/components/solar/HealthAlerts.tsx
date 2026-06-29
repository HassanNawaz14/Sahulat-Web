"use client"

import { AlertCircle, CheckCircle, Clock, Wrench } from "lucide-react"

const STATUS_CONFIG: Record<string, { icon: typeof AlertCircle; color: string; bg: string; label: string }> = {
  critical: { icon: AlertCircle, color: "text-red-700", bg: "bg-red-50", label: "Critical" },
  warning: { icon: AlertCircle, color: "text-amber-700", bg: "bg-amber-50", label: "Warning" },
  info: { icon: Clock, color: "text-blue-700", bg: "bg-blue-50", label: "Info" },
}

const TYPE_CONFIG: Record<string, { icon: typeof AlertCircle; color: string; label: string }> = {
  baseline_drop: { icon: AlertCircle, color: "text-amber-600", label: "Production Drop" },
  zero_production: { icon: AlertCircle, color: "text-red-600", label: "No Production" },
  inverter_disconnected: { icon: AlertCircle, color: "text-gray-600", label: "Inverter Disconnected" },
  cleaning_due: { icon: Wrench, color: "text-blue-600", label: "Maintenance Due" },
}

export default function HealthAlerts({
  alerts,
  onRead,
  onDismiss,
}: {
  alerts: any[]
  onRead?: (id: string) => void
  onDismiss?: (id: string) => void
}) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="rounded-xl bg-white p-4 shadow-sm">
        <div className="py-8 text-center">
          <CheckCircle className="mx-auto mb-2 h-12 w-12 text-green-500" />
          <p className="text-sm text-gray-500">No active alerts</p>
          <p className="mt-1 text-xs text-gray-400">Your solar system is healthy</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const status = STATUS_CONFIG[alert.severity] || STATUS_CONFIG.info
        const type = TYPE_CONFIG[alert.alert_type] || TYPE_CONFIG.cleaning_due
        const StatusIcon = status.icon
        const TypeIcon = type.icon

        return (
          <div
            key={alert.id}
            className={`rounded-lg border-l-4 p-3 ${status.bg} ${status.color} transition-all hover:shadow-sm`}
          >
            <div className="flex items-start justify-between">
              <div className="flex flex-1 items-start gap-3">
                <TypeIcon className="mt-0.5 h-5 w-5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <h4 className="text-sm font-medium">{alert.title}</h4>
                    <span className="rounded-full bg-white px-2 py-0.5 text-xs">{status.label}</span>
                  </div>
                  <p className="mt-1 text-xs">{alert.message}</p>
                  <p className="mt-2 text-xs opacity-75">
                    {new Date(alert.created_at).toLocaleString("en-PK", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
              <div className="ml-3 flex gap-2">
                {!alert.is_read && onRead && (
                  <button
                    onClick={() => onRead(alert.id)}
                    className="rounded bg-white px-2 py-1 text-xs transition-colors hover:bg-gray-100"
                  >
                    Mark Read
                  </button>
                )}
                {!alert.is_dismissed && onDismiss && (
                  <button
                    onClick={() => onDismiss(alert.id)}
                    className="rounded bg-white px-2 py-1 text-xs transition-colors hover:bg-red-100 hover:text-red-700"
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
