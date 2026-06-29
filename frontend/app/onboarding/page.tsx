"use client"

import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"

import { createClient } from "@/lib/supabase/client"
import { CITIES, CITY_DISCO_MAP, DISCO_NAMES } from "@/lib/constants/discoMap"
import FeederSelector from "@/components/outages/FeederSelector"
import PermissionPrompt from "@/components/notifications/PermissionPrompt"

type Step = 1 | 2 | 3 | 4 | 5 | 6

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>(1)
  const [loading, setLoading] = useState(false)
  const [fullName, setFullName] = useState("")
  const [city, setCity] = useState("")
  const [area, setArea] = useState("")
  const [lang, setLang] = useState("en")
  const [consumerNumber, setConsumerNumber] = useState("")
  const [selectedFeeder, setSelectedFeeder] = useState("")
  const [checking, setChecking] = useState(true)
  const userIdRef = useRef<string | null>(null)

  const discoCode = CITY_DISCO_MAP[city.toLowerCase()] ?? ""
  const hasValidDisco = city && !!discoCode
  const canAddConsumer = !!consumerNumber.trim() && hasValidDisco

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

  const steps: Step[] = [1, 2, 3, 4, 5, 6]

  const nextStep = () => {
    if (step < 6) setStep((step + 1) as Step)
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

    if (consumerNumber && discoCode) {
      const insertData: Record<string, unknown> = {
        user_id: uid,
        utility_type: "electricity",
        provider_code: discoCode,
        consumer_number: consumerNumber,
        account_label: "Main Meter",
      }
      if (selectedFeeder) {
        insertData.feeder_name = selectedFeeder
      }
      await supabase.from("consumer_accounts").insert(insertData)
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
              onChange={(e) => { setCity(e.target.value); setArea("") }}
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
            {hasValidDisco && (
              <p className="text-sm text-gray-500">
                {DISCO_NAMES[discoCode]} detected for {city}
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
                onClick={() => {
                  if (canAddConsumer) {
                    nextStep()
                  }
                }}
                disabled={!consumerNumber.trim()}
                className="flex-1 rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
              >
                Add & Continue
              </button>
              <button
                onClick={nextStep}
                className="flex-1 rounded-lg border py-3 text-sm font-medium text-gray-600"
              >
                Skip
              </button>
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Select Feeder</h2>
            <p className="text-sm text-gray-500">
              Choose your area&apos;s feeder for accurate load shedding schedules
            </p>
            <div className="rounded-xl border border-gray-200 bg-white p-3">
              <p className="mb-2 text-xs font-medium text-gray-600">
                Provider: {DISCO_NAMES[discoCode] || discoCode.toUpperCase()}
              </p>
              <FeederSelector
                providerCode={discoCode}
                currentFeeder={selectedFeeder}
                onFeederChange={(name) => setSelectedFeeder(name)}
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={nextStep}
                className="flex-1 rounded-lg bg-blue-600 py-3 text-sm font-medium text-white"
              >
                {selectedFeeder ? "Next" : "Skip"}
              </button>
            </div>
          </div>
        )}

        {step === 6 && (
          <PermissionPrompt
            onComplete={() => {
              setLoading(true)
              completeOnboarding()
            }}
            onSkip={() => {
              setLoading(true)
              completeOnboarding()
            }}
          />
        )}
      </div>
    </main>
  )
}
