"use client"

import { useState, useMemo } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { LogOut, Settings } from "lucide-react"

import { useAuth } from "@/components/providers"
import { createClient } from "@/lib/supabase/client"
import { useConsumerAccounts, useComingSoonSignups } from "@/lib/hooks/useBills"
import DashboardSummaryCard from "@/components/DashboardSummaryCard"
import ConsumerAccountCard from "@/components/ConsumerAccountCard"
import EmptyStateCTA from "@/components/EmptyStateCTA"
import AddUtilityModal from "@/components/AddUtilityModal"
import ComingSoonCard from "@/components/ComingSoonCard"
import { COMING_SOON_V2, PROVIDER_LABELS, UTILITY_ORDER } from "@/lib/constants/utility"
import { Zap, Flame, Droplets, Wifi, type Icon } from "lucide-react"

const SECTION_ICONS: Record<string, Icon> = {
  electricity: Zap,
  gas: Flame,
  water: Droplets,
  internet: Wifi,
}

const UTILITY_TYPES = ["electricity", "gas", "water", "internet"] as const

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [showModal, setShowModal] = useState(false)

  const { data: accounts, isLoading: accountsLoading, isError: accountsError } = useConsumerAccounts()
  const { data: signups } = useComingSoonSignups()

  const grouped = useMemo(() => {
    if (!accounts) return {}
    const groups: Record<string, typeof accounts> = {}
    for (const acc of accounts) {
      const t = acc.utility_type
      if (!groups[t]) groups[t] = []
      groups[t].push(acc)
    }
    return groups
  }, [accounts])

  const sortedTypes = useMemo(() => {
    return [...UTILITY_TYPES].sort((a, b) => (UTILITY_ORDER[a] ?? 99) - (UTILITY_ORDER[b] ?? 99))
  }, [])

  if (authLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </main>
    )
  }

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/auth/login")
  }

  const hasAccounts = accounts && accounts.length > 0
  const showEmpty = (!accountsLoading && !hasAccounts) || accountsError

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-3">
          <Link href="/settings">
            <Settings className="h-5 w-5 text-gray-500" />
          </Link>
          <button onClick={handleSignOut}>
            <LogOut className="h-5 w-5 text-gray-500" />
          </button>
        </div>
      </div>

      {accountsLoading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-32 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      ) : hasAccounts ? (
        <div className="space-y-4">
          <DashboardSummaryCard />

          <Link
            href="/consumption"
            className="flex items-center justify-between rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 transition-colors hover:bg-blue-100"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-blue-700">Consumption Monitor</span>
            </div>
            <span className="text-xs text-blue-400">&rarr;</span>
          </Link>

          <Link
            href="/outages"
            className="flex items-center justify-between rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 transition-colors hover:bg-amber-100"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-amber-700">Outage Tracker</span>
            </div>
            <span className="text-xs text-amber-400">&rarr;</span>
          </Link>

          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-600">Your Utilities</p>
            <button
              onClick={() => setShowModal(true)}
              className="text-sm font-medium text-blue-600"
            >
              + Add
            </button>
          </div>

          {sortedTypes.map((type) => {
            const typeAccounts = grouped[type]
            const comingSoonProviders = COMING_SOON_V2[type] || []
            const Icon = SECTION_ICONS[type]
            if (!typeAccounts && comingSoonProviders.length === 0) return null
            const hasContent = (typeAccounts && typeAccounts.length > 0)

            return (
              <div key={type} className="space-y-2">
                {(hasContent || comingSoonProviders.length > 0) && (
                  <div className="flex items-center gap-2 pt-2">
                    {Icon && <Icon className="h-4 w-4 text-gray-400" />}
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                      {type}
                    </p>
                  </div>
                )}
                {typeAccounts?.map((account) => (
                  <ConsumerAccountCard key={account.id} account={account} />
                ))}
                {comingSoonProviders.map((p) => (
                  <ComingSoonCard
                    key={p}
                    providerCode={p}
                    providerLabel={PROVIDER_LABELS[p] || p.toUpperCase()}
                    utilityType={type}
                    alreadySignedUp={signups?.includes(p) ?? false}
                  />
                ))}
              </div>
            )
          })}
        </div>
      ) : showEmpty ? (
        <EmptyStateCTA onAddUtility={() => setShowModal(true)} />
      ) : null}

      <AddUtilityModal open={showModal} onClose={() => setShowModal(false)} />
    </main>
  )
}
