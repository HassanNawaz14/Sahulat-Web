"use client"

import type { SlabLine } from "@/types/estimate"

interface Props {
  breakdown: SlabLine[]
  currentUnits: number
}

export default function SlabProgressBar({ breakdown, currentUnits }: Props) {
  const totalUnits = breakdown.reduce((s, l) => s + l.units, 0)
  const maxDisplay = breakdown.length > 0
    ? breakdown[breakdown.length - 1].label.includes("+")
      ? currentUnits * 1.2
      : totalUnits
    : currentUnits

  const pct = Math.min((currentUnits / maxDisplay) * 100, 100)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-500">
          <strong>{currentUnits}</strong> units
        </span>
        <span className="text-gray-500">{Math.round(pct)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex flex-wrap gap-1">
        {breakdown.map((slab) => {
          const slabPct = totalUnits > 0 ? (slab.units / totalUnits) * 100 : 0
          return (
            <div
              key={slab.label}
              className="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600"
            >
              <span className="font-medium">{slab.label}</span>
              <span>{slab.units}u</span>
              <span>@{slab.rate}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
