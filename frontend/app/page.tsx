"use client"

import Link from "next/link"
import { Calculator, Zap, Flame, Droplets, ArrowRight, LayoutDashboard, LogOut } from "lucide-react"
import { useAuth } from "@/components/providers"
import { createClient } from "@/lib/supabase/client"
import { useRouter } from "next/navigation"

const GUEST_FEATURES = [
  { icon: Calculator, label: "Bill Estimator", desc: "Know your bill before it arrives", href: "/estimate" },
  { icon: Zap, label: "Bill Tracker", desc: "All utilities in one dashboard", href: "/auth/login" },
  { icon: Flame, label: "Consumption Monitor", desc: "Slab alerts & daily trends", href: "/auth/login" },
  { icon: Droplets, label: "Outage Alerts", desc: "15-min warning before load shedding", href: "/auth/login" },
]

function GuestView() {
  return (
    <div className="w-full max-w-lg text-center">
      <h1 className="text-4xl font-bold text-gray-900">Sahulat</h1>
      <p className="mt-2 text-gray-500">Apni utilities, ek jagah.</p>
      <p className="mt-4 text-sm text-gray-400">
        Track electricity, gas, water, internet &amp; solar bills — all in one place.
      </p>

      <div className="mt-8">
        <Link
          href="/auth/login"
          className="inline-block rounded-lg bg-blue-600 px-8 py-3 text-sm font-medium text-white"
        >
          Login / Sign Up
        </Link>
      </div>

      <Link
        href="/estimate"
        className="mt-6 flex items-center justify-between rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 text-left transition hover:border-blue-300 hover:from-blue-100 hover:to-indigo-100"
      >
        <div>
          <p className="text-sm font-semibold text-gray-900">Know your bill before it arrives</p>
          <p className="mt-0.5 text-xs text-gray-500">
            Calculate electricity, gas &amp; water bills instantly. No sign-up needed.
          </p>
        </div>
        <ArrowRight className="h-5 w-5 shrink-0 text-blue-500" />
      </Link>

      <div className="mt-8 grid grid-cols-2 gap-3">
        {GUEST_FEATURES.map((f) => {
          const Icon = f.icon
          return (
            <Link
              key={f.label}
              href={f.href}
              className="rounded-xl border border-gray-200 bg-white p-4 text-left transition hover:border-blue-200 hover:shadow-sm"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50">
                <Icon className="h-5 w-5 text-blue-600" />
              </div>
              <p className="mt-3 text-sm font-medium text-gray-900">{f.label}</p>
              <p className="mt-0.5 text-xs text-gray-400">{f.desc}</p>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

function UserView() {
  const supabase = createClient()
  const router = useRouter()

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push("/")
  }

  return (
    <div className="w-full max-w-lg text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 mx-auto">
        <LayoutDashboard className="h-8 w-8 text-blue-600" />
      </div>
      <h1 className="mt-4 text-2xl font-bold text-gray-900">Welcome back</h1>
      <p className="mt-1 text-sm text-gray-500">Your utilities are waiting.</p>

      <div className="mt-8 flex flex-col gap-3">
        <Link
          href="/dashboard"
          className="rounded-lg bg-blue-600 py-3 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          Go to Dashboard
        </Link>
        <button
          onClick={handleSignOut}
          className="flex items-center justify-center gap-2 rounded-lg border py-3 text-sm font-medium text-gray-600 transition hover:bg-gray-100"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  )
}

export default function Home() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 bg-gray-50">
      {user ? <UserView /> : <GuestView />}
    </main>
  )
}
