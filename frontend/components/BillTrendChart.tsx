"use client"

import { useBillHistory } from "@/lib/hooks/useBills"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"

interface Props {
  consumerAccountId: string
}

export default function BillTrendChart({ consumerAccountId }: Props) {
  const { data: history, isLoading } = useBillHistory(consumerAccountId)

  if (isLoading) {
    return <div className="h-16 animate-pulse rounded bg-gray-100" />
  }

  if (!history || history.length < 1) return null

  const chartData = history
    .map((h) => ({
      month: h.billing_month
        ? new Date(h.billing_month).toLocaleDateString("en", {
            month: "short",
            year: "2-digit",
          })
        : "?",
      amount: h.amount_payable,
    }))
    .reverse()

  return (
    <div className="h-20">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <XAxis dataKey="month" hide />
          <YAxis hide />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(value: number) => [`Rs. ${value.toLocaleString()}`, "Amount"]}
          />
          <Bar dataKey="amount" fill="#3b82f6" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
