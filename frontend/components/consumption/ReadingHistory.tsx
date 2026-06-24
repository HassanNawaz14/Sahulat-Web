"use client"

import { useState } from "react"

import type { MeterReading } from "@/lib/hooks/useConsumption"
import { useDeleteReading } from "@/lib/hooks/useConsumption"
import { UNIT_LABELS } from "@/lib/constants/utility"

interface Props {
  readings: MeterReading[]
  utilityType?: string
}

export default function ReadingHistory({ readings, utilityType = "electricity" }: Props) {
  const labels = UNIT_LABELS[utilityType] ?? UNIT_LABELS.electricity
  const [deleting, setDeleting] = useState<string | null>(null)

  const firstReading = readings?.[readings.length - 1]
  const accountId = firstReading?.consumer_account_id ?? ""
  const deleteReading = useDeleteReading(accountId)

  const handleDelete = (r: MeterReading) => {
    setDeleting(r.id)
    deleteReading.mutate(r.id, {
      onSettled: () => setDeleting(null),
    })
  }

  if (!readings || readings.length === 0) {
    return (
      <div className="rounded-xl border bg-white p-5 text-center text-sm text-gray-400">
        No readings saved yet
      </div>
    )
  }

  return (
    <div className="rounded-xl border bg-white p-5">
      <h2 className="mb-3 text-sm font-semibold">Reading History</h2>
      <div className="space-y-1.5">
        {readings.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm"
          >
            <div className="flex items-center gap-3">
              <span className="w-20 text-xs text-gray-400">{r.reading_date}</span>
              <span className="font-medium">{r.reading_value}</span>
            </div>
            <div className="flex items-center gap-3 text-xs">
              {r.units_since_last != null && (
                <span className="font-medium text-blue-600">+{r.units_since_last} {labels.unit}</span>
              )}
              {r.consumption_rate != null && (
                <span className="font-medium text-green-600">{r.consumption_rate} {labels.rate}</span>
              )}
              {r.estimated_bill != null && (
                <span className="text-gray-500">
                  Rs. {r.estimated_bill.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              )}
              <button
                onClick={() => handleDelete(r)}
                disabled={deleteReading.isPending && deleting === r.id}
                className="rounded p-1 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500 disabled:opacity-40"
                title="Delete this reading"
              >
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
