import type { CategorySpend } from "@/lib/hooks/useBudget"

const CATEGORY_ICONS: Record<string, string> = {
  electricity: "⚡",
  gas: "🔥",
  water: "💧",
  internet: "🌐",
  cable_tv: "📺",
  mobile_data: "📱",
  solar_maintenance: "☀️",
  groceries: "🛒",
  education: "📚",
  other: "📋",
}

export default function CategoryProgress({
  category,
  onTap,
}: {
  category: CategorySpend
  onTap?: () => void
}) {
  const pct = category.limit > 0 ? Math.min((category.actual / category.limit) * 100, 100) : 0
  const barColor =
    category.status === "exceeded" ? "bg-red-500" : category.status === "warning" ? "bg-amber-500" : "bg-green-500"

  return (
    <button
      onClick={onTap}
      className="w-full rounded-lg border bg-white p-3 text-left transition-colors hover:bg-gray-50"
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-base">{CATEGORY_ICONS[category.code] || "📋"}</span>
          <span className="text-sm font-medium">{category.label}</span>
        </div>
        <span className="text-sm font-semibold">
          Rs. {category.actual.toLocaleString()}
          {category.limit > 0 && (
            <span className="text-xs font-normal text-gray-400">
              {" "}/ {category.limit.toLocaleString()}
            </span>
          )}
        </span>
      </div>

      {category.limit > 0 && (
        <div className="mt-1">
          <div className="h-1.5 w-full rounded-full bg-gray-100">
            <div
              className={`h-1.5 rounded-full transition-all ${barColor}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-0.5 text-xs text-gray-400">
            {category.status === "exceeded" ? "Exceeded" : category.status === "warning" ? "Near limit" : `${Math.round(pct)}% used`}
          </p>
        </div>
      )}
    </button>
  )
}
