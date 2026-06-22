"use client"

interface Props {
  currentUnits: number
  slabMin: number
  slabMax: number | null
  nextThreshold: number | null
  unitsToNext: number | null
}

const SLAB_COLORS = [
  { max: 100, color: "bg-green-500" },
  { max: 200, color: "bg-yellow-500" },
  { max: 300, color: "bg-orange-500" },
  { max: 400, color: "bg-red-500" },
  { max: Infinity, color: "bg-red-700" },
]

function getSlabColor(units: number): string {
  for (const s of SLAB_COLORS) {
    if (units <= s.max) return s.color
  }
  return "bg-gray-400"
}

export default function SlabProgressBar({ currentUnits, slabMin, slabMax, nextThreshold, unitsToNext }: Props) {
  const maxDisplay = nextThreshold ?? slabMax ?? 700
  const pct = Math.min((currentUnits / maxDisplay) * 100, 100)
  const barColor = getSlabColor(currentUnits)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-500">
          <strong>{currentUnits}</strong> / {slabMax ?? `${maxDisplay}+`} units
        </span>
        <span className="text-gray-500">{Math.round(pct)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {unitsToNext !== null && unitsToNext > 0 && (
        <p className="text-xs text-amber-600 font-medium">
          &nbsp;{unitsToNext} units left in current slab
        </p>
      )}
      <div className="flex justify-between text-[10px] text-gray-400">
        <span>{slabMin}</span>
        <span>{slabMax ?? `${slabMin}+`}</span>
      </div>
    </div>
  )
}
