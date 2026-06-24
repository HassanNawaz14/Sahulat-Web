"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"
import type { TrendPoint } from "@/lib/hooks/useConsumption"

interface Props {
  data: TrendPoint[]
  unitLabel?: string
}

function getBarColor(units: number | null): string {
  if (!units) return "#94a3b8"
  if (units <= 200) return "#22c55e"
  if (units <= 300) return "#eab308"
  if (units <= 400) return "#f97316"
  return "#ef4444"
}

export default function ConsumptionTrendChart({ data, unitLabel = "kWh" }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border bg-white p-5 text-center text-sm text-gray-400">
        No consumption data yet
      </div>
    )
  }

  const chartData = data.map((d) => ({
    month: d.billing_month
      ? new Date(d.billing_month).toLocaleDateString("en", { month: "short", year: "2-digit" })
      : "?",
    units: d.units_consumed ?? 0,
    amount: d.amount_payable,
  }))

  return (
    <div className="rounded-xl border bg-white p-5">
      <h2 className="mb-3 text-sm font-semibold">Monthly Consumption</h2>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(0)} ${unitLabel}`,
                name === "units" ? "Units" : "Amount",
              ]}
            />
            <Bar dataKey="units" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={getBarColor(entry.units)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
