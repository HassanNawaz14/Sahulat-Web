"use client"

import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"

import { createClient } from "@/lib/supabase/client"
import { CITIES, CITY_DISCO_MAP, DISCO_NAMES } from "@/lib/constants/discoMap"

type Step = 1 | 2 | 3 | 4 | 5

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>(1)
  const [loading, setLoading] = useState(false)
  const [fullName, setFullName] = useState("")
  const [city, setCity] = useState("")
  const [area, setArea] = useState("")
  const [lang, setLang] = useState("en")
  const [consumerNumber, setConsumerNumber] = useState("")
  const [checking, setChecking] = useState(true)
  const userIdRef = useRef<string | null>(null)

  useEffect(() => {
    const check = async () => {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const uid = session?.user?.id
      if (!uid) {
        window.location.href = "/auth/login"
        return
      }
      userIdRef.current = uid
      const { data: profile } = await supabase
        .from("profiles")
        .select("city")
        .eq("id", uid)
        .maybeSingle()
      if (profile?.city) {
        window.location.href = "/dashboard"
        return
      }
      setChecking(false)
    }
    check()
  }, [router])

  if (checking) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-sm text-gray-500">Loading...</p>
      </main>
    )
  }

  const steps: Step[] = [1, 2, 3, 4, 5]

  const nextStep = () => {
    if (step < 5) setStep((step + 1) as Step)
  }

  const completeOnboarding = async () => {
    setLoading(true)
    const supabase = createClient()
    const uid = userIdRef.current
    if (!uid) return

    await supabase.from("profiles").update({
      full_name: fullName,
      city: city.toLowerCase(),
      area: area,
      preferred_lang: lang,
    }).eq("id", uid)

    const { data: existingHomes } = await supabase
      .from("homes")
      .select("id")
      .eq("user_id", uid)
      .limit(1)

    if (!existingHomes?.length) {
      await supabase.from("homes").insert({
        user_id: uid,
        name: "Home",
        city: city.toLowerCase(),
        area: area,
        is_default: true,
      })
    }

    if (consumerNumber) {
      const discoCode = CITY_DISCO_MAP[city.toLowerCase()] ?? ""
      if (discoCode) {
        await supabase.from("consumer_accounts").insert({
          user_id: uid,
          utility_type: "electricity",
          provider_code: discoCode,
          consumer_number: consumerNumber,
          account_label: "Main Meter",
        })
      }
    }

    setLoading(false)
    window.location.href = "/dashboard"
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-gray-50">
      <div className="w-full max-w-sm">
        <div className="flex gap-1 mb-6">
          {steps.map((s) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded ${s <= step ? "bg-blue-600" : "bg-gray-200"}`}
            />
          ))}
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Basic Info</h2>
            <input
              className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
              placeholder="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <select
              className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            >
              <option value="">Select City</option>
              {CITIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <input
              className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
              placeholder="Area (e.g. Gulberg)"
              value={area}
              onChange={(e) => setArea(e.target.value)}
            />
            <button
              onClick={nextStep}
              disabled={!fullName || !city}
              className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Preferred Language</h2>
            <div className="flex gap-3">
              <button
                onClick={() => { setLang("en"); nextStep() }}
                className={`flex-1 rounded-lg border py-4 text-sm font-medium ${lang === "en" ? "border-blue-600 bg-blue-50 text-blue-600" : "bg-white text-gray-600"}`}
              >
                English
              </button>
              <button
                onClick={() => { setLang("ur"); nextStep() }}
                className={`flex-1 rounded-lg border py-4 text-sm font-medium ${lang === "ur" ? "border-blue-600 bg-blue-50 text-blue-600" : "bg-white text-gray-600"}`}
              >
                اردو
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Your Home</h2>
            <p className="text-sm text-gray-500">
              We&apos;ll create a home record for <strong>{city}</strong>, {area}
            </p>
            <button
              onClick={nextStep}
              className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white"
            >
              Confirm & Continue
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Add Electricity Bill</h2>
            {city && CITY_DISCO_MAP[city.toLowerCase()] && (
              <p className="text-sm text-gray-500">
                {DISCO_NAMES[CITY_DISCO_MAP[city.toLowerCase()]]} detected for {city}
              </p>
            )}
            <input
              className="w-full rounded-lg border px-4 py-3 text-sm outline-none"
              placeholder="Consumer / Ref Number"
              value={consumerNumber}
              onChange={(e) => setConsumerNumber(e.target.value)}
            />
            <div className="flex gap-3">
              <button
                onClick={completeOnboarding}
                disabled={loading}
                className="flex-1 rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
              >
                {loading ? "Saving..." : "Add & Continue"}
              </button>
              <button
                onClick={() => completeOnboarding()}
                disabled={loading}
                className="flex-1 rounded-lg border py-3 text-sm font-medium text-gray-600 disabled:opacity-50"
              >
                Skip
              </button>
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="space-y-4 text-center">
            <h2 className="text-xl font-bold">Stay Updated</h2>
            <p className="text-sm text-gray-500">
              Get notified before load shedding hits your area
            </p>
            <button
              onClick={async () => {
                setLoading(true)
                await completeOnboarding()
                Notification.requestPermission()
              }}
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
            >
              Enable Notifications
            </button>
            <button
              onClick={completeOnboarding}
              disabled={loading}
              className="w-full rounded-lg border py-3 text-sm font-medium text-gray-600 disabled:opacity-50"
            >
              Not Now
            </button>
          </div>
        )}
      </div>
    </main>
  )
}
