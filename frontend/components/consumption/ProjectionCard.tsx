"use client"

interface Props {
  dailyRate: number
  daysRemaining: number
  projectedUnits: number
  estimatedBill: number
  currentSlabRate: number | null
}

export default function ProjectionCard({ dailyRate, daysRemaining, projectedUnits, estimatedBill, currentSlabRate }: Props) {
  return (
    <div className="rounded-xl border bg-gradient-to-br from-blue-50 to-white p-5">
      <h2 className="mb-3 text-sm font-semibold text-gray-700">Projection</h2>
      <p className="text-sm text-gray-600">
        At <strong>{dailyRate.toFixed(1)} kWh/day</strong>, you'll use ~<strong>{projectedUnits.toFixed(0)} kWh</strong>{" "}
        by end of month ({daysRemaining} days remaining).
      </p>
      <div className="mt-3 rounded-lg bg-white/70 px-4 py-3 text-center">
        <p className="text-[10px] text-gray-400 uppercase tracking-wide">Estimated Bill</p>
        <p className="text-2xl font-bold text-blue-600">
          Rs. {estimatedBill.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </p>
        {currentSlabRate && (
          <p className="text-xs text-gray-400">at Rs. {currentSlabRate}/unit avg rate</p>
        )}
      </div>
    </div>
  )
}
