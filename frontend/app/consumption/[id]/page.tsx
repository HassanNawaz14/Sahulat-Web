"use client"

import { useParams, useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"

import { useConsumerAccounts } from "@/lib/hooks/useBills"
import {
  useConsumptionSummary,
  useReadingHistory,
  useConsumptionTrend,
  useSlabAlerts,
} from "@/lib/hooks/useConsumption"
import { PROVIDER_LABELS, UTILITY_ICONS } from "@/lib/constants/utility"

import ConsumptionSummaryCard from "@/components/consumption/ConsumptionSummaryCard"
import ReadingEntryForm from "@/components/consumption/ReadingEntryForm"
import ConsumptionTrendChart from "@/components/consumption/ConsumptionTrendChart"
import IntraCycleReadingsChart from "@/components/consumption/IntraCycleReadingsChart"
import ProjectionCard from "@/components/consumption/ProjectionCard"
import ApplianceEstimator from "@/components/consumption/ApplianceEstimator"
import ReadingHistory from "@/components/consumption/ReadingHistory"

export default function ConsumptionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const accountId = params.id as string

  const { data: accounts } = useConsumerAccounts()
  const { data: summary, isLoading: summaryLoading } = useConsumptionSummary(accountId)
  const { data: readings } = useReadingHistory(accountId)
  const { data: trend } = useConsumptionTrend(accountId)

  const account = accounts?.find((a) => a.id === accountId)

  if (!account) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <p className="text-gray-500">Account not found</p>
      </main>
    )
  }

  const Icon = UTILITY_ICONS[account.utility_type]

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5 text-gray-500" />
        </button>
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-5 w-5" />}
          <h1 className="text-lg font-semibold">
            {account.account_label || PROVIDER_LABELS[account.provider_code] || account.provider_code.toUpperCase()}
          </h1>
        </div>
        <div className="ml-auto" />
      </div>

      {summaryLoading ? (
        <div className="space-y-4">
          <div className="h-40 animate-pulse rounded-xl bg-gray-100" />
          <div className="h-48 animate-pulse rounded-xl bg-gray-100" />
        </div>
      ) : (
        <>
          <ReadingEntryForm
            consumerAccountId={accountId}
            billUnitsConsumed={summary?.bill_units_consumed ?? null}
            lastReading={summary?.last_reading ?? null}
            consumptionChangePct={summary?.consumption_change_pct ?? null}
            consumptionTrend={summary?.consumption_trend ?? null}
          />

          {summary && (
            <>
              <div className="mt-4">
                <ConsumptionSummaryCard summary={summary} />
              </div>

              <div className="mt-4">
                <ProjectionCard
                  dailyRate={summary.daily_rate}
                  daysRemaining={summary.days_remaining}
                  projectedUnits={summary.projected_units}
                  estimatedBill={summary.estimated_bill}
                  currentSlabRate={summary.current_slab?.rate ?? null}
                />
              </div>

              <div className="mt-4">
                <IntraCycleReadingsChart readings={readings ?? []} cycleStart={summary.cycle_start} />
              </div>

              <div className="mt-4">
                <ConsumptionTrendChart data={trend ?? []} />
              </div>

              <div className="mt-4">
                <ReadingHistory readings={readings ?? []} />
              </div>

              {summary.current_slab && (
                <div className="mt-4">
                  <ApplianceEstimator dailyRatePKR={summary.current_slab.rate} />
                </div>
              )}
            </>
          )}

          {!summary && !summaryLoading && (
            <div className="mt-4 rounded-xl border-2 border-dashed border-gray-300 p-8 text-center">
              <p className="text-sm text-gray-500">Enter your first reading above to start tracking.</p>
            </div>
          )}
        </>
      )}
    </main>
  )
}
