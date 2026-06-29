"use client"

import { Target } from "lucide-react"

const formatNumber = (num: number, suffix: string = "") => {
  return `${num.toLocaleString()}${suffix}`
}

export default function ROICountdown({
  systemCostPkr,
  amountPaidBack,
  roiPercent,
  monthsRemaining,
  commissioningDate,
}: {
  systemCostPkr: number
  amountPaidBack: number
  roiPercent: number
  monthsRemaining: number
  commissioningDate: string
}) {
  const progressPercent = Math.min(roiPercent, 100)

  const formatDate = (date: string) => {
    if (!date) return "Not set"
    const d = new Date(date)
    return d.toLocaleDateString("en-PK", { day: "numeric", month: "short", year: "numeric" })
  }

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">ROI Progress</h3>
        <Target className="h-4 w-4 text-blue-600" />
      </div>

      <div className="text-center mb-4">
        <div className="relative inline-block">
          <svg className="w-24 h-24 transform -rotate-90">
            <circle
              cx="48"
              cy="48"
              r="44"
              stroke="#e5e7eb"
              strokeWidth="6"
              fill="none"
            />
            <circle
              cx="48"
              cy="48"
              r="44"
              stroke="#3b82f6"
              strokeWidth="6"
              fill="none"
              strokeDasharray={`${progressPercent * 2.76} 276`}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-in-out"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-lg font-bold text-gray-900">{formatNumber(roiPercent, "%")}</p>
              <p className="text-xs text-gray-500">paid back</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">System Cost</span>
          <span className="font-medium text-gray-900">{formatNumber(systemCostPkr)}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Amount Paid Back</span>
          <span className="font-medium text-green-600">{formatNumber(amountPaidBack)}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Months Remaining</span>
          <span className="font-medium text-gray-900">
            {monthsRemaining > 0 ? formatNumber(monthsRemaining, " months") : "Completed!"}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Commissioning Date</span>
          <span className="font-medium text-gray-900">{formatDate(commissioningDate)}</span>
        </div>
      </div>

      {roiPercent >= 100 && (
        <div className="mt-4 p-3 bg-green-50 rounded-lg text-center">
          <p className="text-xs font-medium text-green-800">✅ System fully paid off!</p>
          <p className="text-xs text-green-700 mt-1">You're saving money every month</p>
        </div>
      )}

      {monthsRemaining > 0 && monthsRemaining < 12 && (
        <div className="mt-4 p-3 bg-amber-50 rounded-lg text-center">
          <p className="text-xs font-medium text-amber-800">⏰ Near payback time</p>
          <p className="text-xs text-amber-700 mt-1">Only {monthsRemaining} months left to break even</p>
        </div>
      )}
    </div>
  )
}
