"use client"

import { Zap, Flame, Droplets, Wifi, RefreshCw } from "lucide-react"
import type { CommunityReport } from "@/lib/hooks/useOutages"

const UTILITY_ICONS: Record<string, React.ElementType> = {
  electricity: Zap,
  gas: Flame,
  water: Droplets,
  internet: Wifi,
}

const UTILITY_COLORS: Record<string, string> = {
  electricity: "text-yellow-600 bg-yellow-50 border-yellow-200",
  gas: "text-orange-600 bg-orange-50 border-orange-200",
  water: "text-blue-600 bg-blue-50 border-blue-200",
  internet: "text-purple-600 bg-purple-50 border-purple-200",
}

interface CommunityFeedProps {
  reports: CommunityReport[]
  isLoading: boolean
  onRefresh: () => void
}

function timeAgo(isoStr: string) {
  const now = Date.now()
  const then = new Date(isoStr).getTime()
  const diffMin = Math.floor((now - then) / 60000)
  if (diffMin < 1) return "Just now"
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHrs = Math.floor(diffMin / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  return `${Math.floor(diffHrs / 24)}d ago`
}

function confidenceBadge(score: number) {
  if (score >= 0.8) return "bg-green-100 text-green-700"
  if (score >= 0.6) return "bg-amber-100 text-amber-700"
  return "bg-gray-100 text-gray-500"
}

export default function CommunityFeed({ reports, isLoading, onRefresh }: CommunityFeedProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Community Reports</p>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-1 text-xs text-blue-600 transition-colors hover:text-blue-800"
        >
          <RefreshCw className={`h-3 w-3 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {isLoading && reports.length === 0 ? (
        <div className="mt-3 space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <p className="mt-4 text-center text-sm text-gray-400">No reports in your area yet</p>
      ) : (
        <div className="mt-3 space-y-2">
          {reports.map((report) => {
            const Icon = UTILITY_ICONS[report.utility_type] || Wifi
            const colorClasses = UTILITY_COLORS[report.utility_type] || UTILITY_COLORS.internet
            return (
              <div
                key={report.id}
                className={`flex items-start gap-3 rounded-lg border p-3 ${colorClasses.split(" ").slice(1).join(" ")}`}
              >
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${colorClasses.split(" ")[0]} ${colorClasses.split(" ")[1]}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{report.area}</p>
                  <p className="text-xs text-gray-500">
                    {report.report_count} report{report.report_count !== 1 ? "s" : ""} &middot; {timeAgo(report.created_at)}
                  </p>
                </div>
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${confidenceBadge(report.confidence_score)}`}>
                  {Math.round(report.confidence_score * 100)}%
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
