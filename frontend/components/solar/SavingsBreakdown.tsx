"use client"

import { PieChart, Pie, Cell, Legend, Tooltip } from "recharts"

const formatCurrency = (num: number) => `Rs. ${num.toLocaleString()}`

export default function SavingsBreakdown({
  selfConsumedValue,
  exportCredit,
  estimated,
}: {
  selfConsumedValue: number
  exportCredit: number
  estimated?: boolean
}) {
  const data = [
    { name: "Self-Consumed", value: selfConsumedValue, color: "#10b981" },
    { name: "Export Credit", value: exportCredit, color: "#8b5cf6" },
  ].filter(item => item.value > 0)

  if (data.length === 0) {
    return (
      <div className="rounded-xl bg-white p-4 shadow-sm">
        <p className="text-sm text-gray-500 text-center py-8">No savings data available</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <h3 className="text-sm font-medium text-gray-600 mb-4">Savings Breakdown</h3>
      <div className="h-48">
        <PieChart width={280} height={180}>
          <Pie
            data={data}
            cx={140}
            cy={90}
            innerRadius={40}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => formatCurrency(value)}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white p-2 shadow-md rounded-md border border-gray-200">
                    <p className="text-xs font-medium">
                      {payload[0].name}: {formatCurrency(payload[0].value)}
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            formatter={(value: string) => <span className="text-xs text-gray-600">{value}</span>}
          />
        </PieChart>
      </div>

      <div className="mt-4 space-y-2">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.color }} />
              <span className="text-gray-600">{item.name}</span>
            </div>
            <span className="font-medium text-gray-900">{formatCurrency(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
