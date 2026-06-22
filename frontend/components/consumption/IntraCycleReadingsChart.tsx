"use client"

import { useMemo } from "react"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"
import type { MeterReading } from "@/lib/hooks/useConsumption"

interface Props {
  readings: MeterReading[]
  cycleStart: string | null
}

export default function IntraCycleReadingsChart({ readings, cycleStart }: Props) {
  const { chartData, readingMax, rateMax } = useMemo(() => {
    if (!cycleStart || readings.length === 0) return { chartData: [] as any[], readingMax: 350, rateMax: 10 }
    const start = new Date(cycleStart).getTime()
    const sorted = readings
      .filter((r) => new Date(r.reading_date).getTime() >= start)
      .sort((a, b) => new Date(a.reading_date).getTime() - new Date(b.reading_date).getTime())

    let maxReading = 0
    let maxRate = 0
    const data = sorted.map((r) => {
      if (r.reading_value > maxReading) maxReading = r.reading_value
      const rate = r.consumption_rate
      if (rate != null && rate > maxRate) maxRate = rate
      return {
        date: new Date(r.reading_date).toLocaleDateString("en", { day: "numeric", month: "short" }),
        reading: r.reading_value,
        dailyConsumption: rate,
      }
    })
    return {
      chartData: data,
      readingMax: Math.ceil(maxReading * 1.15),
      rateMax: Math.ceil(maxRate * 1.2) || 10,
    }
  }, [readings, cycleStart])

  if (chartData.length < 2) {
    return (
      <div className="rounded-xl border bg-white p-5">
        <h2 className="mb-2 text-sm font-semibold">This Cycle&apos;s Readings</h2>
        <p className="text-xs text-gray-400">Enter at least 2 readings this cycle to see the trend.</p>
      </div>
    )
  }

  const hasRate = chartData.some((d) => d.dailyConsumption != null)

  return (
    <div className="rounded-xl border bg-white p-5">
      <h2 className="mb-1 text-sm font-semibold">This Cycle&apos;s Readings</h2>
      <p className="mb-3 text-[10px] text-gray-400">Meter reading and daily consumption within the billing cycle</p>

      <p className="mb-1 text-xs font-medium text-blue-600">Meter Reading (kWh)</p>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis domain={[0, readingMax]} stroke="#2563eb" tick={{ fontSize: 10, fill: "#2563eb" }} width={50} />
          <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
          <Line
            type="monotone"
            dataKey="reading"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 4, fill: "#2563eb" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <p className="mb-1 mt-4 text-xs font-medium text-green-600">Consumption Rate (kWh/day)</p>
      {hasRate ? (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, rateMax]} stroke="#16a34a" tick={{ fontSize: 10, fill: "#16a34a" }} width={50} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
              formatter={(value: number) => [`${value.toFixed(1)} kWh/day`]}
            />
            <Line
              type="monotone"
              dataKey="dailyConsumption"
              stroke="#16a34a"
              strokeWidth={2}
              dot={{ r: 3, fill: "#16a34a" }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex h-[180px] items-center justify-center rounded-lg bg-gray-50 text-xs text-gray-400">
          Need 3+ readings to show consumption rate
        </div>
      )}
    </div>
  )
}
