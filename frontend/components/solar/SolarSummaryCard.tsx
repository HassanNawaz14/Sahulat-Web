"use client"

import { TrendingUp, TrendingDown, BarChart3 } from "lucide-react"

const formatNumber = (num: number, type: "currency" | "kwh" | "percent" = "currency") => {
  if (type === "currency") {
    return `Rs. ${num.toLocaleString()}`
  } else if (type === "kwh") {
    return `${num.toLocaleString()} kWh`
  } else if (type === "percent") {
    return `${num}%`
  }
  return num.toString()
}

export default function SolarSummaryCard({
  todayKwh,
  monthKwh,
  savings,
  exportCredit,
}: {
  todayKwh: number
  monthKwh: number
  savings: number
  exportCredit: number
}) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="rounded-xl bg-white p-3 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-500">Today</p>
          <TrendingUp className="h-4 w-4 text-blue-600" />
        </div>
        <p className="text-lg font-bold text-gray-900">{formatNumber(todayKwh, "kwh")}</p>
        <p className="text-xs text-gray-500 mt-1">kWh produced</p>
      </div>

      <div className="rounded-xl bg-white p-3 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-500">This Month</p>
          <BarChart3 className="h-4 w-4 text-green-600" />
        </div>
        <p className="text-lg font-bold text-gray-900">{formatNumber(monthKwh, "kwh")}</p>
        <p className="text-xs text-gray-500 mt-1">Total kWh</p>
      </div>

      <div className="rounded-xl bg-white p-3 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-500">Monthly Savings</p>
          <TrendingUp className="h-4 w-4 text-amber-600" />
        </div>
        <p className="text-lg font-bold text-gray-900">{formatNumber(savings)}</p>
        <p className="text-xs text-gray-500 mt-1">Net savings</p>
      </div>

      <div className="rounded-xl bg-white p-3 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-500">Export Credit</p>
          <TrendingDown className="h-4 w-4 text-purple-600" />
        </div>
        <p className="text-lg font-bold text-gray-900">{formatNumber(exportCredit)}</p>
        <p className="text-xs text-gray-500 mt-1">Exported credits</p>
      </div>
    </div>
  )
}
