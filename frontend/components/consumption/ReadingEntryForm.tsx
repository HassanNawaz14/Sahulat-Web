"use client"

import { useState, useEffect } from "react"
import { useSubmitReading } from "@/lib/hooks/useConsumption"

interface TrajectoryShift {
  before: { total_units: number; daily_rate: number; projected_units: number; estimated_bill: number }
  after: { total_units: number; daily_rate: number; projected_units: number; estimated_bill: number }
}

interface Props {
  consumerAccountId: string
  billUnitsConsumed: number | null
  lastReading: { date: string; value: number } | null
  onSuccess?: () => void
  consumptionChangePct?: number | null
  consumptionTrend?: "up" | "down" | "stable" | null
}

export default function ReadingEntryForm({ consumerAccountId, billUnitsConsumed, lastReading, onSuccess, consumptionChangePct, consumptionTrend }: Props) {
  const [value, setValue] = useState("")
  const [date, setDate] = useState(new Date().toISOString().split("T")[0])
  const [showGuide, setShowGuide] = useState(false)
  const [prefilled, setPrefilled] = useState(false)
  const [localError, setLocalError] = useState("")
  const submitReading = useSubmitReading()

  useEffect(() => {
    if (!prefilled && billUnitsConsumed != null && !value) {
      setValue(String(billUnitsConsumed))
      setPrefilled(true)
    }
  }, [billUnitsConsumed, prefilled, value])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError("")
    const parsed = parseFloat(value.replace(/,/g, ""))
    if (isNaN(parsed) || parsed < 0) return

    if (lastReading && parsed < lastReading.value) {
      setLocalError(`Reading (${parsed}) cannot be lower than the previous entry (${lastReading.value}). The meter reading should increase over time.`)
      return
    }

    submitReading.mutate(
      {
        consumer_account_id: consumerAccountId,
        reading_date: date,
        reading_value: parsed,
      },
      {
        onSuccess: () => {
          setValue("")
          setPrefilled(false)
          // Advance date by 1 day to prevent accidental same-date duplicate
          const next = new Date(date)
          next.setDate(next.getDate() + 1)
          setDate(next.toISOString().split("T")[0])
          onSuccess?.()
        },
      }
    )
  }

  const isPrefilled = prefilled && billUnitsConsumed != null

  const trendColor = consumptionTrend === "up" ? "text-red-500" : consumptionTrend === "down" ? "text-green-500" : "text-gray-500"
  const trendArrow = consumptionTrend === "up" ? "\u2191" : consumptionTrend === "down" ? "\u2193" : "\u2192"

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border bg-white p-5">
      <button
        type="button"
        onClick={() => setShowGuide(!showGuide)}
        className="mb-3 flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700"
      >
        <span className="rounded-full border border-blue-300 px-1.5 text-[10px] font-bold">?</span>
        {showGuide ? "Hide guide" : "What should I enter here?"}
      </button>

      {showGuide && (
        <div className="mb-4 rounded-lg bg-blue-50 p-3 text-xs leading-relaxed text-gray-700 space-y-2">
          <p>Enter the <strong>units consumed</strong> since your last entry, or the meter reading shown on your meter.</p>
          <p>The number below is from your latest bill&apos;s <strong>Units Consumed</strong>. Adjust if needed.</p>
        </div>
      )}

      <div className="flex items-end gap-3">
        <div className="flex-1">
          <div className="relative">
            <input
              value={value}
              onChange={(e) => { setValue(e.target.value.replace(/[^0-9.]/g, "")); setLocalError("") }}
              placeholder={billUnitsConsumed ? String(billUnitsConsumed) : "e.g. 282"}
              inputMode="numeric"
              className="w-full rounded-lg border border-gray-200 p-3 text-center text-2xl font-bold tracking-wider"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">kWh</span>
          </div>
        </div>
        <div>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-gray-200 p-2.5 text-sm"
          />
        </div>
      </div>

      {isPrefilled && (
        <p className="mt-1.5 text-[10px] text-green-600 text-center">
          Auto-filled from your latest bill. Adjust if needed.
        </p>
      )}

      {lastReading && (
        <div className="mt-3 flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm">
          <span className="text-gray-500">
            Previous entry: <strong>{lastReading.value}</strong> ({lastReading.date})
          </span>
          {consumptionChangePct != null && (
            <span className={`text-xs font-medium ${trendColor}`}>
              {trendArrow} {Math.abs(consumptionChangePct)}% vs last month
            </span>
          )}
        </div>
      )}

      {submitReading.data && (
        <div className="mt-3 rounded-lg bg-green-50 p-3 text-sm text-green-700">
          <p>
            Saved! Units since last entry: <strong>{submitReading.data.units_since_last}</strong> kWh
          </p>
          {submitReading.data.estimated_bill && (
            <p className="mt-0.5">
              Est. bill at this rate: Rs. <strong>{submitReading.data.estimated_bill.toLocaleString()}</strong>
            </p>
          )}
          {submitReading.data.trajectory_shift && (
            <div className="mt-2 border-t border-green-200 pt-2 text-xs">
              <p className="font-semibold text-green-800">Trajectory Change</p>
              <div className="mt-1 flex items-center gap-3">
                <span className="text-green-600">
                  Before: {submitReading.data.trajectory_shift.before.daily_rate.toFixed(1)} kWh/day &rarr; Rs.{" "}
                  {submitReading.data.trajectory_shift.before.estimated_bill.toLocaleString()}
                </span>
                <span className="text-gray-400">|</span>
                <span className="text-green-600">
                  After: {submitReading.data.trajectory_shift.after.daily_rate.toFixed(1)} kWh/day &rarr; Rs.{" "}
                  {submitReading.data.trajectory_shift.after.estimated_bill.toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {localError && (
        <p className="mt-2 text-xs text-red-500">{localError}</p>
      )}

      {submitReading.isError && (
        <p className="mt-2 text-xs text-red-500">
          {(submitReading.error as any)?.response?.data?.detail || "Could not save reading. Check the value and try again."}
        </p>
      )}

      <button
        type="submit"
        disabled={submitReading.isPending || !value.trim()}
        className="mt-4 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitReading.isPending ? "Saving..." : "Save Reading"}
      </button>
    </form>
  )
}
