"use client"

import Link from "next/link"
import { useAuth } from "@/components/providers"
import { createClient } from "@/lib/supabase/client"
import { useRouter } from "next/navigation"
import { LogOut } from "lucide-react"

export default function Home() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/")
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50">
      <h1 className="text-4xl font-bold text-gray-900">Sahulat</h1>
      <p className="mt-2 text-gray-500">Apni utilities, ek jagah.</p>
      <p className="mt-4 max-w-sm text-center text-sm text-gray-400">
        Track electricity, gas, water, internet &amp; solar bills — all in one place.
      </p>

      <div className="mt-8 flex gap-4">
        {isLoading ? null : user ? (
          <>
            <Link
              href="/dashboard"
              className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white"
            >
              Dashboard
            </Link>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 rounded-lg border px-6 py-3 text-sm font-medium text-gray-600"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </>
        ) : (
          <Link
            href="/auth/login"
            className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white"
          >
            Login / Sign Up
          </Link>
        )}
      </div>
    </main>
  )
}
