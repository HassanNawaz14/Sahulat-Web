"use client"

import type { ConsumptionSummary } from "@/lib/hooks/useConsumption"
import SlabProgressBar from "./SlabProgressBar"

interface Props {
  summary: ConsumptionSummary
}

export default function ConsumptionSummaryCard({ summary }: Props) {
  const snap = summary.latest_reading_snapshot

  return (
    <div className="rounded-xl border bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs text-gray-500">
          Cycle: {summary.cycle_start ? new Date(summary.cycle_start).toLocaleDateString("en", { month: "short", year: "numeric" }) : "N/A"}
        </p>
        <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-600">
          {summary.readings_this_cycle} reading{summary.readings_this_cycle !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-[10px] text-gray-400 uppercase tracking-wide">Current Reading</p>
          <p className="text-xl font-bold">{snap?.reading_value?.toFixed(1) ?? "—"}</p>
          <p className="text-xs text-gray-500">meter reading</p>
        </div>
        <div>
          <p className="text-[10px] text-gray-400 uppercase tracking-wide">Reading Date</p>
          <p className="text-sm font-bold">
            {snap?.reading_date
              ? new Date(snap.reading_date).toLocaleDateString("en", { day: "numeric", month: "short" })
              : "—"}
          </p>
          <p className="text-xs text-gray-500">latest entry</p>
        </div>
        <div>
          <p className="text-[10px] text-gray-400 uppercase tracking-wide">Est. Bill</p>
          <p className="text-xl font-bold text-blue-600">
            Rs. {summary.estimated_bill.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-gray-500">projected</p>
        </div>
      </div>

      {summary.last_reading && (
        <div className="mt-3 text-xs text-gray-400">
          Latest meter reading: <strong>{summary.last_reading.value}</strong> on {summary.last_reading.date}
        </div>
      )}

      {summary.current_slab && (
        <div className="mt-4">
          <p className="mb-1.5 text-xs font-medium text-gray-500">
            Slab {summary.current_slab.min}-{summary.current_slab.max ?? "+"} &middot; Rs. {summary.current_slab.rate}/unit
          </p>
          <SlabProgressBar
            currentUnits={summary.total_units_so_far}
            slabMin={summary.current_slab.min}
            slabMax={summary.current_slab.max}
            nextThreshold={summary.next_slab?.threshold ?? null}
            unitsToNext={summary.next_slab?.units_away ?? null}
          />
        </div>
      )}

      {summary.total_units_so_far > 0 && (
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
          <span>Cycle total: <strong>{summary.total_units_so_far}</strong> kWh</span>
          <span>Daily avg: <strong>{summary.daily_rate}</strong> kWh/day</span>
        </div>
      )}

      <div className="mt-4 border-t pt-3">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1.5">Compared to Last Month</p>
        <div className="flex items-center gap-4">
          {summary.previous_daily_rate != null && (
            <div className="text-center">
              <p className="text-xs text-gray-500">Prev daily rate</p>
              <p className="text-sm font-semibold">{summary.previous_daily_rate.toFixed(1)} kWh/day</p>
            </div>
          )}
          {summary.daily_rate > 0 && (
            <div className="text-center">
              <p className="text-xs text-gray-500">Current daily rate</p>
              <p className="text-sm font-semibold">{summary.daily_rate.toFixed(1)} kWh/day</p>
            </div>
          )}
          {summary.consumption_change_pct != null && (
            <div className="text-center">
              <p className="text-xs text-gray-500">Change</p>
              <p className={`text-sm font-bold ${summary.consumption_trend === "up" ? "text-red-500" : summary.consumption_trend === "down" ? "text-green-500" : "text-gray-500"}`}>
                {summary.consumption_trend === "up" ? "\u2191" : summary.consumption_trend === "down" ? "\u2193" : "\u2192"}{" "}
                {Math.abs(summary.consumption_change_pct)}%
              </p>
            </div>
          )}
        </div>
        {summary.previous_total_units != null && summary.total_units_so_far > 0 && (
          <p className="mt-1.5 text-[10px] text-gray-400">
            {summary.total_units_so_far} kWh this cycle vs {summary.previous_total_units} kWh last month
          </p>
        )}
      </div>
    </div>
  )
}