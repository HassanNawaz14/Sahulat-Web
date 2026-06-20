"use client"

import { useState, useEffect, useRef, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"

import { createClient } from "@/lib/supabase/client"

function VerifyForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const method = searchParams.get("method") ?? "phone"
  const identifier = searchParams.get("phone") ?? searchParams.get("email") ?? ""

  const [otp, setOtp] = useState(["", "", "", "", "", ""])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [resendTimer, setResendTimer] = useState(60)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    if (resendTimer <= 0) return
    const id = setInterval(() => setResendTimer((t) => t - 1), 1000)
    return () => clearInterval(id)
  }, [resendTimer])

  const handleChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return
    const next = [...otp]
    next[index] = value
    setOtp(next)
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
    if (next.every((d) => d) && value) {
      verifyOtp(next.join(""))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const verifyOtp = async (token: string) => {
    setLoading(true)
    setError("")
    const supabase = createClient()
    const params = method === "phone"
      ? { phone: identifier, token, type: "sms" as const }
      : { email: identifier, token, type: "email" as const }
    const { error: err } = await supabase.auth.verifyOtp(params)
    setLoading(false)
    if (err) {
      setError(err.message)
      setOtp(["", "", "", "", "", ""])
      inputRefs.current[0]?.focus()
      return
    }

    const { data: { session } } = await supabase.auth.getSession()
    const userId = session?.user?.id
    if (!userId) return

    const { data: profile } = await supabase
      .from("profiles")
      .select("city")
      .eq("id", userId)
      .maybeSingle()

    const path = profile?.city ? "/dashboard" : "/onboarding"
    window.location.href = path
  }

  const resendOtp = async () => {
    if (resendTimer > 0) return
    setResendTimer(60)
    const supabase = createClient()
    if (method === "phone") {
      await supabase.auth.signInWithOtp({ phone: identifier })
    } else {
      await supabase.auth.signInWithOtp({ email: identifier })
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-gray-50">
      <div className="w-full max-w-sm text-center">
        <h1 className="text-2xl font-bold text-gray-900">Verify OTP</h1>
        <p className="mt-1 text-sm text-gray-500">
          Code sent to {method === "phone" ? identifier : identifier}
        </p>

        <div className="mt-8 flex justify-center gap-3">
          {otp.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el }}
              className="h-14 w-12 rounded-lg border text-center text-xl font-bold outline-none focus:border-blue-500"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              disabled={loading}
              autoFocus={i === 0}
            />
          ))}
        </div>

        {error && <p className="mt-4 text-sm text-red-500">{error}</p>}

        <button
          onClick={resendOtp}
          disabled={resendTimer > 0}
          className="mt-6 text-sm text-blue-600 disabled:text-gray-400"
        >
          {resendTimer > 0 ? `Resend in ${resendTimer}s` : "Resend OTP"}
        </button>
      </div>
    </main>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-gray-500">Loading...</p></div>}>
      <VerifyForm />
    </Suspense>
  )
}
