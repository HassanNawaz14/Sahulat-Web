"use client"

import { useState, useMemo } from "react"
import { useAuth } from "@/components/providers"
import { useConsumerAccounts } from "@/lib/hooks/useBills"
import {
  useScheduledOutages,
  useCommunityReports,
  useRestoreOutage,
} from "@/lib/hooks/useOutages"
import OutageCard from "@/components/outages/OutageCard"
import OutageTimeline from "@/components/outages/OutageTimeline"
import CommunityFeed from "@/components/outages/CommunityFeed"
import ReportOutageButton from "@/components/outages/ReportOutageButton"
import FeederSelector from "@/components/outages/FeederSelector"

export default function OutagesPage() {
  const { user, isLoading: authLoading } = useAuth()
  const { data: accounts, isLoading: accountsLoading } = useConsumerAccounts()
  const [refreshFeed, setRefreshFeed] = useState(0)

  // Pick first electricity account for schedule queries
  const electricityAccount = useMemo(() => {
    if (!accounts) return null
    return accounts.find((a) => a.utility_type === "electricity" && a.is_active) ?? null
  }, [accounts])

  const {
    data: schedule,
    isLoading: scheduleLoading,
    refetch: refetchSchedule,
  } = useScheduledOutages(electricityAccount?.id ?? null)

  const {
    data: reports,
    isLoading: feedLoading,
    refetch: refetchFeed,
  } = useCommunityReports()

  const { mutate: restoreOutage } = useRestoreOutage()

  const handleRefreshFeed = () => {
    refetchFeed()
    setRefreshFeed((n) => n + 1)
  }

  if (authLoading || accountsLoading) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="mt-4 space-y-4">
          <div className="h-20 animate-pulse rounded-xl bg-gray-100" />
          <div className="h-32 animate-pulse rounded-xl bg-gray-100" />
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <h1 className="text-2xl font-bold">Outage Tracker</h1>
      <p className="mt-0.5 text-xs text-gray-400">Scheduled & community-reported outages</p>

      {/* Current status card */}
      <div className="mt-4">
        {scheduleLoading ? (
          <div className="h-20 animate-pulse rounded-xl bg-gray-100" />
        ) : (
          <OutageCard
            currentOutage={schedule?.current_outage ?? null}
            nextOutage={schedule?.next_outage ?? null}
            feederName={schedule?.feeder_name ?? ""}
            feederSet={schedule?.feeder_set ?? false}
          />
        )}
      </div>

      {/* Quick actions */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <ReportOutageButton
          homeId={electricityAccount?.home_id ?? undefined}
          consumerAccountId={electricityAccount?.id ?? undefined}
        />
        {electricityAccount && (
          <FeederSelector
            providerCode={electricityAccount.provider_code}
            consumerAccountId={electricityAccount.id}
            currentFeeder={schedule?.feeder_name}
            onSaved={() => refetchSchedule()}
          />
        )}
      </div>

      {/* Today's schedule */}
      <div className="mt-6 space-y-4">
        {scheduleLoading ? (
          <div className="h-32 animate-pulse rounded-xl bg-gray-100" />
        ) : (
          <>
            {schedule?.today && schedule.today.length > 0 && (
              <OutageTimeline outages={schedule.today} label="Today" />
            )}
            {schedule?.tomorrow && schedule.tomorrow.length > 0 && (
              <OutageTimeline outages={schedule.tomorrow} label="Tomorrow" />
            )}
            {schedule?.day_after && schedule.day_after.length > 0 && (
              <OutageTimeline outages={schedule.day_after} label="Day After" />
            )}
          </>
        )}
      </div>

      {/* Community feed */}
      <div className="mt-6">
        <CommunityFeed
          reports={reports ?? []}
          isLoading={feedLoading}
          onRefresh={handleRefreshFeed}
        />
      </div>

      {/* No account warning */}
      {!electricityAccount && !accountsLoading && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-800">No electricity account linked</p>
          <p className="mt-0.5 text-xs text-amber-600">
            Add an electricity consumer account to see scheduled load shedding for your area.
          </p>
        </div>
      )}
    </main>
  )
}
