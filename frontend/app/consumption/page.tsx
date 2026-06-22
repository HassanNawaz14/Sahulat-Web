"use client"

import Link from "next/link"
import { useConsumerAccounts } from "@/lib/hooks/useBills"
import { PROVIDER_LABELS, UTILITY_ICONS, UTILITY_COLORS, UTILITY_ORDER } from "@/lib/constants/utility"
import { ArrowLeft } from "lucide-react"

const METER_TYPES = ["electricity", "gas", "water"]

export default function ConsumptionPage() {
  const { data: accounts, isLoading } = useConsumerAccounts()

  const meterAccounts = (accounts ?? []).filter((a) => METER_TYPES.includes(a.utility_type))

  const grouped: Record<string, typeof meterAccounts> = {}
  for (const acc of meterAccounts) {
    if (!grouped[acc.utility_type]) grouped[acc.utility_type] = []
    grouped[acc.utility_type].push(acc)
  }

  const sortedTypes = Object.keys(grouped).sort((a, b) => (UTILITY_ORDER[a] ?? 9) - (UTILITY_ORDER[b] ?? 9))

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard">
          <ArrowLeft className="h-5 w-5 text-gray-500" />
        </Link>
        <h1 className="text-lg font-semibold">Consumption Monitor</h1>
      </div>

      <p className="mb-4 text-sm text-gray-500">
        Track your meter readings, daily usage, and month-end projections.
      </p>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      ) : sortedTypes.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-8 text-center">
          <p className="text-gray-500">No meter-based accounts found.</p>
          <p className="mt-1 text-xs text-gray-400">
            Add an electricity, gas, or water account to start tracking consumption.
          </p>
          <Link
            href="/settings"
            className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white"
          >
            Add Account
          </Link>
        </div>
      ) : (
        sortedTypes.map((type) => {
          const Icon = UTILITY_ICONS[type]
          return (
            <div key={type} className="mb-6">
              <div className="mb-2 flex items-center gap-2">
                {Icon && <Icon className={`h-4 w-4 ${UTILITY_COLORS[type]}`} />}
                <h2 className="text-sm font-medium capitalize text-gray-600">{type}</h2>
              </div>
              <div className="space-y-2">
                {grouped[type].map((acc) => (
                  <Link
                    key={acc.id}
                    href={`/consumption/${acc.id}`}
                    className="flex items-center justify-between rounded-xl border bg-white p-4 transition-colors hover:bg-gray-50"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {acc.account_label || PROVIDER_LABELS[acc.provider_code] || acc.provider_code.toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-400">{acc.consumer_number}</p>
                    </div>
                    <span className="text-xs text-blue-600">&rarr;</span>
                  </Link>
                ))}
              </div>
            </div>
          )
        })
      )}
    </main>
  )
}
