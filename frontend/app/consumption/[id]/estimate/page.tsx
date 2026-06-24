"use client"

import { useParams, useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"

import { useConsumerAccounts } from "@/lib/hooks/useBills"
import { useEstimateFromConsumption } from "@/lib/hooks/useEstimate"
import { PROVIDER_LABELS, UTILITY_ICONS } from "@/lib/constants/utility"
import EstimateResultCard from "@/components/estimator/EstimateResult"

export default function ConsumptionEstimatePage() {
  const params = useParams()
  const router = useRouter()
  const accountId = params.id as string

  const { data: accounts } = useConsumerAccounts()
  const estimate = useEstimateFromConsumption()

  const account = accounts?.find((a) => a.id === accountId)

  if (!account) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <p className="text-gray-500">Account not found</p>
      </main>
    )
  }

  const Icon = UTILITY_ICONS[account.utility_type]

  const handleEstimate = async () => {
    await estimate.mutateAsync(accountId)
  }

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5 text-gray-500" />
        </button>
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-5 w-5" />}
          <h1 className="text-lg font-semibold">
            Estimate from Readings —{" "}
            {account.account_label || PROVIDER_LABELS[account.provider_code] || account.provider_code.toUpperCase()}
          </h1>
        </div>
      </div>

      <p className="mb-4 text-sm text-gray-500">
        Estimate your current cycle bill based on your latest two meter readings.
      </p>

      <button
        onClick={handleEstimate}
        disabled={estimate.isPending}
        className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
      >
        {estimate.isPending ? "Calculating..." : "Calculate from Readings"}
      </button>

      {estimate.error && (
        <p className="mt-3 text-xs text-red-500">
          {(estimate.error as any)?.response?.data?.detail || (estimate.error as any)?.message || "Failed to estimate"}
        </p>
      )}

      {estimate.data && (
        <div className="mt-6">
          <EstimateResultCard result={estimate.data} />
        </div>
      )}
    </main>
  )
}
