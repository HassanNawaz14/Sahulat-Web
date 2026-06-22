"use client"

import { useState } from "react"
import { Plus, X } from "lucide-react"

const DEFAULT_APPLIANCES = [
  { id: "ac_1ton", name: "AC (1 Ton) Inverter", watts: 900, defaultHours: 8 },
  { id: "ac_1_5ton", name: "AC (1.5 Ton) Inverter", watts: 1500, defaultHours: 8 },
  { id: "ac_non", name: "AC (1 Ton) Non-Inverter", watts: 1500, defaultHours: 8 },
  { id: "fridge", name: "Refrigerator", watts: 200, defaultHours: 24 },
  { id: "deep_freezer", name: "Deep Freezer", watts: 350, defaultHours: 24 },
  { id: "geyser", name: "Geyser (Electric)", watts: 2000, defaultHours: 3 },
  { id: "heater", name: "Room Heater (Oil-filled)", watts: 2000, defaultHours: 6 },
  { id: "washing", name: "Washing Machine", watts: 500, defaultHours: 1.5 },
  { id: "water_pump", name: "Water Pump (1 HP)", watts: 750, defaultHours: 2 },
  { id: "fan", name: "Ceiling Fan", watts: 75, defaultHours: 16 },
  { id: "tv", name: "LED TV (43\")", watts: 80, defaultHours: 6 },
  { id: "iron", name: "Iron", watts: 1000, defaultHours: 1 },
  { id: "micro", name: "Microwave Oven", watts: 1200, defaultHours: 0.5 },
  { id: "kettle", name: "Electric Kettle", watts: 1500, defaultHours: 0.5 },
  { id: "rice_cooker", name: "Rice Cooker", watts: 700, defaultHours: 1 },
  { id: "computer", name: "Desktop Computer", watts: 250, defaultHours: 4 },
  { id: "router", name: "WiFi Router", watts: 15, defaultHours: 24 },
  { id: "water_dispenser", name: "Water Dispenser", watts: 500, defaultHours: 8 },
]

interface CustomAppliance {
  id: string
  name: string
  watts: number
  hours: number
}

interface Props {
  dailyRatePKR: number
}

export default function ApplianceEstimator({ dailyRatePKR }: Props) {
  const [enabled, setEnabled] = useState<Set<string>>(new Set())
  const [hoursMap, setHoursMap] = useState<Record<string, number>>({})
  const [customs, setCustoms] = useState<CustomAppliance[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState("")
  const [newWatts, setNewWatts] = useState("")
  const [newHours, setNewHours] = useState("4")

  const toggle = (id: string) => {
    const next = new Set(enabled)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setEnabled(next)
  }

  const setHours = (id: string, h: number) => {
    setHoursMap((prev) => ({ ...prev, [id]: h }))
  }

  const getHours = (id: string, defaultHours: number) => hoursMap[id] ?? defaultHours

  const addCustom = () => {
    const w = Number(newWatts)
    const h = Number(newHours)
    if (!newName.trim() || !w || !h) return
    const id = `custom_${Date.now()}`
    setCustoms((prev) => [...prev, { id, name: newName.trim(), watts: w, hours: h }])
    setNewName("")
    setNewWatts("")
    setNewHours("4")
    setShowAdd(false)
  }

  const removeCustom = (id: string) => {
    setCustoms((prev) => prev.filter((c) => c.id !== id))
    const next = new Set(enabled)
    next.delete(id)
    setEnabled(next)
  }

  const allAppliances = [
    ...DEFAULT_APPLIANCES.map((a) => ({ id: a.id, name: a.name, watts: a.watts, hours: getHours(a.id, a.defaultHours) })),
    ...customs,
  ]

  const visible = allAppliances.filter((a) => enabled.has(a.id))
  const sorted = [...visible].sort((a, b) => {
    const kWhA = (a.watts / 1000) * a.hours * 30
    const kWhB = (b.watts / 1000) * b.hours * 30
    return kWhB * dailyRatePKR - kWhA * dailyRatePKR
  })

  const totalKWh = sorted.reduce((sum, a) => sum + (a.watts / 1000) * a.hours * 30, 0)
  const totalCost = totalKWh * dailyRatePKR
  const totalWatts = sorted.reduce((sum, a) => sum + a.watts, 0)

  return (
    <div className="rounded-xl border bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">Appliance Cost Estimator</h2>
          <p className="text-xs text-gray-400">Check appliances to see monthly cost at Rs. {dailyRatePKR}/kWh</p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
        >
          <Plus className="h-3.5 w-3.5" />
          Add
        </button>
      </div>

      {showAdd && (
        <div className="mb-3 rounded-lg border bg-gray-50 p-3">
          <div className="flex flex-wrap items-end gap-2">
            <div className="flex-1">
              <label className="block text-[10px] font-medium text-gray-500">Appliance</label>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Toaster"
                className="mt-0.5 w-full rounded border px-2 py-1.5 text-xs"
              />
            </div>
            <div className="w-16">
              <label className="block text-[10px] font-medium text-gray-500">Watts</label>
              <input
                type="number"
                value={newWatts}
                onChange={(e) => setNewWatts(e.target.value)}
                placeholder="800"
                className="mt-0.5 w-full rounded border px-2 py-1.5 text-xs"
              />
            </div>
            <div className="w-14">
              <label className="block text-[10px] font-medium text-gray-500">Hrs/day</label>
              <input
                type="number"
                value={newHours}
                onChange={(e) => setNewHours(e.target.value)}
                className="mt-0.5 w-full rounded border px-2 py-1.5 text-xs"
              />
            </div>
            <button
              onClick={addCustom}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
            >
              Add
            </button>
          </div>
        </div>
      )}

      <div className="mb-2 rounded-lg bg-amber-50 px-3 py-2">
        <p className="text-[10px] leading-relaxed text-amber-700">
          <span className="font-medium">Manual estimate only</span> — based on typical wattages and hours you enter, not your actual meter readings. Your real bill depends on your meter readings tracked above.
        </p>
      </div>
      <div className="mb-1 flex items-center gap-2 px-3 text-[10px] font-medium text-gray-400">
        <span className="inline-block w-4" />
        <span className="flex-1">Appliance</span>
        <span className="w-12 text-center">Hrs/day</span>
        <span className="w-14 text-right">Watts</span>
        <span className="w-[72px] text-right">Bill</span>
      </div>
      <div className="max-h-60 space-y-0.5 overflow-y-auto">
        {allAppliances.map((a) => {
          const kwhPerMonth = (a.watts / 1000) * a.hours * 30
          const cost = kwhPerMonth * dailyRatePKR
          const isCustom = customs.some((c) => c.id === a.id)
          return (
            <div
              key={a.id}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                enabled.has(a.id) ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <input
                type="checkbox"
                checked={enabled.has(a.id)}
                onChange={() => toggle(a.id)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <span className="flex-1 truncate text-xs">{a.name}</span>
              <input
                type="number"
                value={a.hours}
                onChange={(e) => setHours(a.id, Number(e.target.value))}
                className="w-12 rounded border px-1.5 py-1 text-center text-[11px]"
                min={0}
                max={24}
                step={0.5}
              />
              <span className="w-14 text-right text-[11px] text-gray-500">{a.watts} W</span>
              <span className="w-[72px] text-right text-[11px] text-gray-500">
                Rs. {cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
              {isCustom && (
                <button onClick={() => removeCustom(a.id)} className="text-gray-300 hover:text-red-500">
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          )
        })}
      </div>

      {enabled.size > 0 && (
        <>
          <div className="mt-3 rounded-lg bg-blue-50 p-3">
            <p className="text-xs font-medium text-blue-700">Estimated Monthly Cost</p>
            <p className="text-xl font-bold text-blue-600">
              Rs. {totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
            <div className="mt-1.5 space-y-0.5 text-[11px] text-blue-500">
              <p>{totalKWh.toFixed(0)} kWh/month at Rs. {dailyRatePKR}/kWh</p>
              <p>Total load: {totalWatts >= 1000 ? `${(totalWatts / 1000).toFixed(1)} kW` : `${totalWatts} W`} (simultaneous)</p>
            </div>
          </div>

          <div className="mt-3">
            <p className="mb-1 text-[10px] font-medium text-gray-400">Sorted by cost (most expensive first)</p>
            <div className="space-y-1">
              {sorted.map((a) => {
                const kwhPerMonth = (a.watts / 1000) * a.hours * 30
                const pct = totalKWh > 0 ? (kwhPerMonth / totalKWh) * 100 : 0
                return (
                  <div key={a.id} className="flex items-center gap-2 text-xs">
                    <div className="h-2 w-full flex-1 overflow-hidden rounded-full bg-gray-100">
                      <div
                        className="h-full rounded-full bg-blue-500 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-32 truncate text-gray-500">{a.name}</span>
                    <span className="w-20 text-right text-gray-700">
                      Rs. {(kwhPerMonth * dailyRatePKR).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}

      {enabled.size === 0 && (
        <p className="py-3 text-center text-xs text-gray-400">
          Check appliances above to estimate your monthly electricity cost breakdown.
        </p>
      )}
    </div>
  )
}
