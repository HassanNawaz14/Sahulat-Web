"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, AlertTriangle, Zap, Loader2 } from "lucide-react"

import { useSolarInstallations } from "@/lib/hooks/useSolar"
import InstallationCard from "@/components/solar/InstallationCard"

export default function SolarPage() {
  const router = useRouter()
  const { data: installations, isLoading, isError, refetch } = useSolarInstallations()

  if (isLoading) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <div className="mb-6 flex items-center gap-3">
          <Link href="/dashboard" className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-xl font-bold">Solar Dashboard</h1>
        </div>
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      </main>
    )
  }

  if (isError) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="mb-4 h-12 w-12 text-red-400" />
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Could not load solar data</h2>
          <p className="mb-6 text-sm text-gray-600">Something went wrong. Please try again.</p>
          <button
            onClick={() => refetch()}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="mb-6 flex items-center gap-3">
        <Link href="/dashboard" className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-xl font-bold">Solar Dashboard</h1>
        <Link
          href="/solar/setup"
          className="ml-auto flex items-center gap-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Add
        </Link>
      </div>

      {!installations || installations.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
            <Zap className="h-8 w-8 text-amber-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-gray-900">No solar installations yet</h3>
          <p className="mb-6 text-sm text-gray-600">
            Add your solar installation to track production, savings, and ROI
          </p>
          <Link
            href="/solar/setup"
            className="inline-block rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700"
          >
            Add Solar Installation
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {installations.map((inst) => (
            <Link key={inst.id} href={`/solar/${inst.id}`}>
              <InstallationCard installation={inst} />
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
