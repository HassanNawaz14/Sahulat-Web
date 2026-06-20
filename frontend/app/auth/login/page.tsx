"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Mail, Phone, Chrome } from "lucide-react"

import { createClient } from "@/lib/supabase/client"

export default function LoginPage() {
  const router = useRouter()
  const [phone, setPhone] = useState("+92")
  const [email, setEmail] = useState("")
  const [showEmail, setShowEmail] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handlePhoneOtp = async () => {
    setError("Phone login is under maintenance. Please use Email or Google.")
  }

  const handleEmailOtp = async () => {
    if (!email) return
    setLoading(true)
    setError("")
    const supabase = createClient()
    const { error: err } = await supabase.auth.signInWithOtp({ email })
    setLoading(false)
    if (err) {
      setError(err.message)
    } else {
      router.push(`/auth/verify?method=email&email=${encodeURIComponent(email)}`)
    }
  }

  const handleGoogleOAuth = async () => {
    setLoading(true)
    setError("")
    const supabase = createClient()
    const { error: err } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${location.origin}/auth/callback` },
    })
    setLoading(false)
    if (err) setError(err.message)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-gray-50">
      <div className="w-full max-w-sm text-center">
        <h1 className="text-3xl font-bold text-gray-900">Sahulat</h1>
        <p className="mt-1 text-sm text-gray-500">Apni utilities, ek jagah.</p>

        <div className="mt-8 space-y-4">
          <div className="space-y-2 opacity-50">
            <label className="flex items-center gap-2 rounded-lg border bg-gray-100 px-4 py-3 cursor-not-allowed">
              <Phone className="h-5 w-5 text-gray-400" />
              <input
                className="w-full bg-transparent outline-none text-sm text-gray-400"
                placeholder="+92 3XX XXXXXXX"
                value={phone}
                disabled
                onChange={(e) => setPhone(e.target.value)}
              />
            </label>
            <button
              onClick={handlePhoneOtp}
              className="w-full rounded-lg bg-gray-400 py-3 text-sm font-medium text-white cursor-not-allowed"
            >
              Continue with Phone
            </button>
            <p className="text-xs text-gray-400 text-center">Under maintenance</p>
          </div>

          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span className="flex-1 border-t" />
            or
            <span className="flex-1 border-t" />
          </div>

          <button
            onClick={handleGoogleOAuth}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg border bg-white py-3 text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            <Chrome className="h-5 w-5" />
            Continue with Google
          </button>

          {showEmail ? (
            <div className="space-y-2">
              <label className="flex items-center gap-2 rounded-lg border bg-white px-4 py-3">
                <Mail className="h-5 w-5 text-gray-400" />
                <input
                  className="w-full bg-transparent outline-none text-sm"
                  placeholder="email@example.com"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              <button
                onClick={handleEmailOtp}
                disabled={loading || !email}
                className="w-full rounded-lg border py-3 text-sm font-medium text-gray-600 disabled:opacity-50"
              >
                Send OTP via Email
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowEmail(true)}
              className="text-xs text-blue-600 underline"
            >
              Continue with Email instead
            </button>
          )}
        </div>

        {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      </div>
    </main>
  )
}
