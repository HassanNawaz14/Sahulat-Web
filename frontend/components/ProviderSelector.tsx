"use client"

import { PROVIDER_LABELS } from "@/lib/constants/utility"

const V1_PROVIDERS_BY_TYPE: Record<string, { v1: string[]; comingSoon: string[] }> = {
  electricity: {
    v1: ["lesco", "kelectric"],
    comingSoon: ["iesco", "gepco", "fesco", "mepco", "pesco", "qesco", "hesco", "sepco"],
  },
  gas: {
    v1: ["sngpl", "ssgc"],
    comingSoon: [],
  },
  water: {
    v1: ["wasa_lhr", "kwsb"],
    comingSoon: ["wasa_rwp", "wasa_fsd"],
  },
  internet: {
    v1: ["ptcl", "nayatel"],
    comingSoon: ["stormfiber", "jazz_home", "zong_home"],
  },
}

interface Props {
  utilityType: string
  value: string
  onChange: (value: string) => void
  error?: string
}

export default function ProviderSelector({ utilityType, value, onChange, error }: Props) {
  const config = V1_PROVIDERS_BY_TYPE[utilityType]
  if (!config) return null

  return (
    <div>
      <label className="text-xs font-medium text-gray-600">Provider</label>
      <div className="mt-1.5 space-y-1">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border border-gray-200 p-2.5 text-sm"
        >
          <option value="">Select provider</option>
          {config.v1.map((p) => (
            <option key={p} value={p}>
              {PROVIDER_LABELS[p] || p.toUpperCase()}
            </option>
          ))}
        </select>
        {config.comingSoon.length > 0 && (
          <div className="mt-2 rounded-lg bg-gray-50 p-2.5">
            <p className="text-xs font-medium text-gray-500">Coming Soon</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {config.comingSoon.map((p) => (
                <span
                  key={p}
                  className="inline-block rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-500"
                >
                  {PROVIDER_LABELS[p] || p.toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  )
}

export { V1_PROVIDERS_BY_TYPE }
