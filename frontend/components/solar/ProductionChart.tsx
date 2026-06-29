"use client"

import { useState } from "react"

const DAY_OPTIONS = [
  { key: "7", label: "7 days" },
  { key: "14", label: "14 days" },
  { key: "30", label: "30 days" },
] as const

export default function ProductionChart({
  data,
}: {
  data: { date: string; production_kwh: number; self_consumed_kwh?: number | null; exported_kwh?: number | null }[]
}) {
  const [selectedDays, setSelectedDays] = useState("14")

  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - parseInt(selectedDays))

  const filtered = data.filter((item) => new Date(item.date) >= cutoff)

  const maxVal = Math.max(...filtered.map((d) => d.production_kwh), 1)

  const formatDate = (d: string) => {
    const dt = new Date(d)
    return `${dt.getDate()}/${dt.getMonth() + 1}`
  }

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-600">Production History</h3>
        <div className="flex gap-1">
          {DAY_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => setSelectedDays(opt.key)}
              className={`rounded-md px-2 py-1 text-xs ${
                selectedDays === opt.key ? "bg-blue-100 text-blue-700" : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex h-40 items-center justify-center text-sm text-gray-400">
          No production data available
        </div>
      ) : (
        <div className="relative h-48">
          <div className="flex h-full items-end gap-0.5">
            {filtered.map((item, i) => {
              const pct = (item.production_kwh / maxVal) * 100
              return (
                <div key={i} className="group relative flex flex-1 flex-col items-center">
                  <div className="flex h-full w-full flex-col-reverse">
                    <div
                      className="w-full rounded-t bg-blue-500 transition-all group-hover:bg-blue-600"
                      style={{ height: `${Math.max(pct, 2)}%` }}
                      title={`${item.date}: ${item.production_kwh.toFixed(1)} kWh`}
                    />
                  </div>
                  {filtered.length <= 14 && (
                    <span className="mt-1 text-[10px] text-gray-400">{formatDate(item.date)}</span>
                  )}
                </div>
              )
            })}
          </div>
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded bg-blue-500" /> Production
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
