"use client"

import { ChevronRight, AlertCircle, CheckCircle, Clock, Battery, Thermometer, Wrench } from "lucide-react"
import type { SolarInstallation, HealthStatus, AlertType } from "@/types/solar"

const STATUS_CONFIG: Record<HealthStatus, { label: string; color: string; icon: any }> = {
  normal: { label: "Normal", color: "text-green-700", icon: CheckCircle },
  warning: { label: "Warning", color: "text-amber-700", icon: AlertCircle },
  critical: { label: "Critical", color: "text-red-700", icon: AlertCircle },
}

const ALERT_TYPE_CONFIG: Record<AlertType, { icon: any; color: string }> = {
  baseline_drop: { icon: Thermometer, color: "text-amber-600" },
  zero_production: { icon: Battery, color: "text-red-600" },
  inverter_disconnected: { icon: AlertCircle, color: "text-gray-600" },
  cleaning_due: { icon: Wrench, color: "text-blue-600" },
}

export default function InstallationCard({ installation }: { installation: SolarInstallation }) {
  const statusCfg = STATUS_CONFIG[installation.health_status]
  const StatusIcon = statusCfg.icon

  const formatDate = (date: string) => {
    if (!date) return "Not set"
    const d = new Date(date)
    return d.toLocaleDateString("en-PK", { day: "numeric", month: "short", year: "numeric" })
  }

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">
            {installation.inverter_brand.toUpperCase()} Solar
          </h3>
          <p className="text-sm text-gray-500">
            {installation.system_size_kw} kW System • {installation.panel_count || "N/A"} Panels
          </p>
        </div>
        <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusCfg.color} bg-gray-50 flex items-center gap-1`}>
          <StatusIcon className="h-3 w-3" />
          {statusCfg.label}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">System Size</span>
          <span className="font-medium text-gray-900">{installation.system_size_kw} kW</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Capacity</span>
          <span className="font-medium text-gray-900">{installation.panel_wattage ? `${installation.panel_wattage}W` : "N/A"}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Cost</span>
          <span className="font-medium text-gray-900">
            {installation.system_cost_pkr ? `Rs. ${installation.system_cost_pkr.toLocaleString()}` : "N/A"}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Net Metering</span>
          <span className="font-medium text-gray-900">
            {installation.net_metering_enabled ? "Enabled" : "Disabled"}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Last Sync</span>
          <span className="font-medium text-gray-900">
            {installation.last_synced_at ? formatDate(installation.last_synced_at) : "Never"}
          </span>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 rounded-lg bg-blue-50 py-2 text-center text-sm font-medium text-blue-600 hover:bg-blue-100">
          View Details
        </button>
        {!installation.api_username_encrypted && (
          <button className="rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100">
            Connect Inverter
          </button>
        )}
      </div>
    </div>
  )
}
