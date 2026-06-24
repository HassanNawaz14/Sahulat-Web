"use client"

import { useState } from "react"
import { Zap, Flame, Droplets, Bell, BarChart3, Wallet, Sun, MapPin, CreditCard } from "lucide-react"
import { PROVIDER_LABELS } from "@/lib/constants/utility"
import ProviderSelector from "@/components/ProviderSelector"
import { useEstimateElectricity, useEstimateGas, useEstimateWater } from "@/lib/hooks/useEstimate"
import EstimateResultCard from "./EstimateResult"

const UTILITY_TABS = [
  { id: "electricity", label: "Electricity", icon: Zap },
  { id: "gas", label: "Gas", icon: Flame },
  { id: "water", label: "Water", icon: Droplets },
] as const

type UtilityType = (typeof UTILITY_TABS)[number]["id"]

const FEATURES = [
  { icon: Bell, title: "Slab crossing alerts", desc: "Push notification at 50, 20, 10 units before next slab", module: "P07" },
  { icon: BarChart3, title: "Live consumption tracking", desc: "Daily usage rate + projected end-of-month bill", module: "P07" },
  { icon: Zap, title: "Auto bill fetch", desc: "LESCO, SNGPL, WASA, etc bills fetched for you daily", module: "P06" },
  { icon: Wallet, title: "Budget manager", desc: "Set limits, get notified at 80% & 100% spend", module: "P10" },
  { icon: MapPin, title: "Outage alerts", desc: "15-min warning before load shedding hits", module: "P09" },
  { icon: Sun, title: "Solar savings", desc: "Personalized solar ROI based on your bill", module: "P16" },
  { icon: CreditCard, title: "One-tap pay", desc: "JazzCash/EasyPaisa with pre-filled details", module: "P15" },
]

export default function EstimatorForm() {
  const [tab, setTab] = useState<UtilityType>("electricity")
  const estElectricity = useEstimateElectricity()
  const estGas = useEstimateGas()
  const estWater = useEstimateWater()

  const [providerCode, setProviderCode] = useState("")
  const [units, setUnits] = useState("")
  const [propertyType, setPropertyType] = useState<"residential" | "commercial">("residential")
  const [marla, setMarla] = useState("")
  const [phaseType, setPhaseType] = useState<"single_phase" | "three_phase">("single_phase")

  const loading = estElectricity.isPending || estGas.isPending || estWater.isPending
  const error = estElectricity.error || estGas.error || estWater.error
  const result = estElectricity.data || estGas.data || estWater.data

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const unitsNum = parseFloat(units)
    if (!providerCode || isNaN(unitsNum) || unitsNum < 0) return

    if (tab === "electricity") {
      await estElectricity.mutateAsync({
        provider_code: providerCode,
        units: unitsNum,
        phase_type: phaseType,
      })
    } else if (tab === "gas") {
      await estGas.mutateAsync({
        provider_code: providerCode as "sngpl" | "ssgc",
        consumption_mmbtu: unitsNum,
      })
    } else if (tab === "water") {
      await estWater.mutateAsync({
        provider_code: providerCode,
        usage_units: null,
        property_type: propertyType,
        property_size_marla: marla ? parseFloat(marla) : null,
      })
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      {/* Utility Tabs */}
      <div className="mb-6 flex rounded-xl bg-gray-100 p-1">
        {UTILITY_TABS.map((t) => {
          const Icon = t.icon
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => { setTab(t.id); setProviderCode(""); setUnits(""); setMarla("") }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition ${
                tab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
              }`}
            >
              <Icon className="h-4 w-4" />
              {t.label}
            </button>
          )
        })}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <ProviderSelector
          utilityType={tab}
          value={providerCode}
          onChange={setProviderCode}
        />

        {tab === "electricity" && (
          <div>
            <label className="text-xs font-medium text-gray-600">Phase Type</label>
            <select
              value={phaseType}
              onChange={(e) => setPhaseType(e.target.value as "single_phase" | "three_phase")}
              className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
            >
              <option value="single_phase">Single Phase</option>
              <option value="three_phase">Three Phase</option>
            </select>
          </div>
        )}

        <div>
          <label className="text-xs font-medium text-gray-600">
            {tab === "electricity" ? "Units (kWh)"
              : tab === "gas" ? "Consumption (MMBtu)"
              : "Property Size (Marla)"}
          </label>
          <input
            type="number"
            value={tab === "water" ? marla : units}
            onChange={(e) => {
              if (tab === "water") setMarla(e.target.value)
              else setUnits(e.target.value)
            }}
            min={0}
            max={tab === "electricity" ? 5000 : tab === "gas" ? 50 : undefined}
            step={tab === "gas" ? "0.1" : "1"}
            placeholder={
              tab === "electricity" ? "e.g. 300"
                : tab === "gas" ? "e.g. 2.5"
                : "e.g. 5"
            }
            className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
            required
          />
          {tab === "water" && (
            <div className="mt-2">
              <label className="text-xs font-medium text-gray-600">Property Type</label>
              <select
                value={propertyType}
                onChange={(e) => setPropertyType(e.target.value as "residential" | "commercial")}
                className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
              >
                <option value="residential">Residential</option>
                <option value="commercial">Commercial</option>
              </select>
            </div>
          )}
        </div>

        {units && parseFloat(units) > 2000 && tab === "electricity" && (
          <p className="text-xs text-amber-600">
            Unusually high consumption (&gt;2000 kWh). Please verify the entered value.
          </p>
        )}

        {error && (
          <p className="text-xs text-red-500">
            {(error as any)?.response?.data?.detail || (error as any)?.message || "Calculation failed"}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !providerCode || !units}
          className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Calculating..." : "Calculate Estimate"}
        </button>
      </form>

      {result && (
        <div className="mt-6">
          <EstimateResultCard result={result} />
        </div>
      )}

      {/* Feature preview — always visible even before calculation */}
      {!result && (
        <div className="mt-10 space-y-4">
          <div className="text-center">
            <p className="text-sm font-semibold text-gray-700">
              Try the demo calculator above (with far less features), then sign up for the full experience
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Every feature below works with your real utility data
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {FEATURES.map((f) => {
              const Icon = f.icon
              return (
                <div
                  key={f.title}
                  className="rounded-lg border border-gray-100 bg-white p-3"
                >
                  <div className="flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-50">
                      <Icon className="h-3.5 w-3.5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{f.title}</p>
                      <p className="text-xs text-gray-400">{f.module}</p>
                    </div>
                  </div>
                  <p className="mt-1.5 text-xs leading-relaxed text-gray-500">
                    {f.desc}
                  </p>
                </div>
              )
            })}
          </div>
          <a
            href="/auth/login"
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-blue-200 bg-blue-50 py-3 text-sm font-medium text-blue-700 transition hover:bg-blue-100"
          >
            Sign up free — One dashboard for all your utilities
          </a>
        </div>
      )}
    </div>
  )
}
