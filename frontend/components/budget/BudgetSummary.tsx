import type { BudgetSummary, BudgetStatus } from "@/lib/hooks/useBudget"

const STATUS_CONFIG: Record<BudgetStatus, { label: string; bg: string; text: string }> = {
  safe: { label: "On Track", bg: "bg-green-100", text: "text-green-700" },
  warning: { label: "Warning", bg: "bg-amber-100", text: "text-amber-700" },
  exceeded: { label: "Exceeded", bg: "bg-red-100", text: "text-red-700" },
}

export default function BudgetSummary({ summary }: { summary: BudgetSummary }) {
  const statusCfg = STATUS_CONFIG[summary.status]
  const projectedPct = summary.budget_limit > 0
    ? Math.round((summary.projected_spend / summary.budget_limit) * 100)
    : 0
  const hasTrend = summary.projected_spend > summary.actual_spend
  const trendPct = summary.actual_spend > 0
    ? Math.round(((summary.projected_spend - summary.actual_spend) / summary.actual_spend) * 100)
    : 0

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-gray-600">Monthly Overview</p>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusCfg.bg} ${statusCfg.text}`}>
          {statusCfg.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-500">Spent</p>
          <p className="text-xl font-bold">Rs. {summary.actual_spend.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Budget</p>
          <p className="text-xl font-bold">Rs. {summary.budget_limit.toLocaleString()}</p>
        </div>
      </div>

      {summary.budget_limit > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span>{projectedPct}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-100">
            <div
              className={`h-2 rounded-full transition-all ${
                summary.status === "exceeded" ? "bg-red-500" : summary.status === "warning" ? "bg-amber-500" : "bg-green-500"
              }`}
              style={{ width: `${Math.min(projectedPct, 100)}%` }}
            />
          </div>
        </div>
      )}

      <p className="mt-3 text-xs text-gray-400">
        Projected: Rs. {summary.projected_spend.toLocaleString()}
        {hasTrend && trendPct > 0 && (
          <span className="ml-1 text-amber-500">&uarr; {trendPct}%</span>
        )}
      </p>
    </div>
  )
}
