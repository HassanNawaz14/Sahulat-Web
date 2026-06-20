"use client"

import { useBillsSummary } from "@/lib/hooks/useBills"
import { UTILITY_ICONS, UTILITY_COLORS } from "@/lib/constants/utility"

export default function DashboardSummaryCard() {
  const { data, isLoading } = useBillsSummary()

  if (isLoading) return null
  if (!data || data.account_count === 0) return null

  return (
    <div className="rounded-xl border bg-gradient-to-br from-blue-600 to-blue-700 p-4 text-white">
      <p className="text-sm text-blue-100">This Month&apos;s Utilities</p>
      <p className="mt-1 text-3xl font-bold">
        Rs. {data.total_this_month.toLocaleString()}
      </p>
      <div className="mt-3 flex flex-wrap gap-3">
        {data.breakdown.map((b) => {
          const Icon = UTILITY_ICONS[b.utility_type] || UTILITY_ICONS.electricity
          return (
            <div key={b.consumer_account_id} className="flex items-center gap-1.5 text-sm text-blue-100">
              <Icon className="h-3.5 w-3.5" />
              <span>{b.label}</span>
              <span className="font-medium text-white">Rs. {b.amount.toLocaleString()}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
