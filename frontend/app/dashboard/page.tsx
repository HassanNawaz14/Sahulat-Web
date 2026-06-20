"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { LogOut, Settings } from "lucide-react"

import { useAuth } from "@/components/providers"
import { createClient } from "@/lib/supabase/client"
import { useConsumerAccounts } from "@/lib/hooks/useBills"
import DashboardSummaryCard from "@/components/DashboardSummaryCard"
import ConsumerAccountCard from "@/components/ConsumerAccountCard"
import EmptyStateCTA from "@/components/EmptyStateCTA"
import AddUtilityModal from "@/components/AddUtilityModal"

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [showModal, setShowModal] = useState(false)

  const { data: accounts, isLoading: accountsLoading } = useConsumerAccounts()

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

          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-600">Your Utilities</p>
            <button
              onClick={() => setShowModal(true)}
              className="text-sm font-medium text-blue-600"
            >
              + Add
            </button>
          </div>

          {accounts.map((account) => (
            <ConsumerAccountCard key={account.id} account={account} />
          ))}
        </div>
      ) : (
        <EmptyStateCTA onAddUtility={() => setShowModal(true)} />
      )}

      <AddUtilityModal open={showModal} onClose={() => setShowModal(false)} />
    </main>
  )
}
