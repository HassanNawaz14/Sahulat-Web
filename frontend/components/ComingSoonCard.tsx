"use client"

import { useState } from "react"
import { Clock } from "lucide-react"
import api from "@/lib/api"

interface Props {
  providerCode: string
  providerLabel: string
  utilityType: string
  alreadySignedUp: boolean
}

export default function ComingSoonCard({ providerCode, providerLabel, utilityType, alreadySignedUp }: Props) {
  const [signedUp, setSignedUp] = useState(alreadySignedUp)
  const [loading, setLoading] = useState(false)

  const handleNotify = async () => {
    setLoading(true)
    try {
      await api.post("/coming-soon-signup", { provider_code: providerCode })
      setSignedUp(true)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50/50 p-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-200">
          <Clock className="h-5 w-5 text-gray-500" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-gray-700">{providerLabel} Support</p>
          <p className="text-xs text-gray-500">Coming Soon</p>
        </div>
        <button
          onClick={handleNotify}
          disabled={signedUp || loading}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
            signedUp
              ? "bg-green-100 text-green-700"
              : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          }`}
        >
          {loading ? "..." : signedUp ? "Signed Up" : "Notify me"}
        </button>
      </div>
    </div>
  )
}
