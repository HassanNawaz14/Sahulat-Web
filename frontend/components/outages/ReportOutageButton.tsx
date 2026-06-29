"use client"

import { useState } from "react"
import { Zap, Flame, Droplets, Wifi, X } from "lucide-react"
import { useReportOutage } from "@/lib/hooks/useOutages"

interface ReportOutageButtonProps {
  homeId?: string
  consumerAccountId?: string
  providerCode?: string
}

const UTILITY_OPTIONS = [
  { value: "electricity", label: "Electricity", icon: Zap, color: "text-yellow-600 bg-yellow-50 border-yellow-200" },
  { value: "gas", label: "Gas", icon: Flame, color: "text-orange-600 bg-orange-50 border-orange-200" },
  { value: "water", label: "Water", icon: Droplets, color: "text-blue-600 bg-blue-50 border-blue-200" },
  { value: "internet", label: "Internet", icon: Wifi, color: "text-purple-600 bg-purple-50 border-purple-200" },
]

export default function ReportOutageButton({ homeId, consumerAccountId, providerCode }: ReportOutageButtonProps) {
  const [open, setOpen] = useState(false)
  const [utilityType, setUtilityType] = useState("electricity")
  const [severity, setSeverity] = useState("medium")
  const [note, setNote] = useState("")
  const { mutate: reportOutage, isPending } = useReportOutage()

  const handleSubmit = () => {
    reportOutage(
      {
        utility_type: utilityType,
        severity,
        note: note || undefined,
        home_id: homeId || undefined,
        provider_code: providerCode || undefined,
      },
      {
        onSuccess: () => {
          setOpen(false)
          setNote("")
          setSeverity("medium")
        },
      }
    )
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
      >
        <Zap className="h-4 w-4" />
        Report Outage
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-end bg-black/40" onClick={() => setOpen(false)}>
          <div
            className="w-full rounded-t-2xl bg-white p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <p className="text-lg font-semibold">Report Outage</p>
              <button onClick={() => setOpen(false)}>
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>

            <p className="mt-1 text-xs text-gray-400">What type of utility issue are you experiencing?</p>

            <div className="mt-4 grid grid-cols-2 gap-2">
              {UTILITY_OPTIONS.map((opt) => {
                const Icon = opt.icon
                const isSelected = utilityType === opt.value
                return (
                  <button
                    key={opt.value}
                    onClick={() => setUtilityType(opt.value)}
                    className={`flex items-center gap-2 rounded-lg border p-3 text-left text-sm transition-colors ${
                      isSelected ? opt.color + " ring-2 ring-blue-400" : "border-gray-200 bg-white text-gray-600"
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{opt.label}</span>
                  </button>
                )
              })}
            </div>

            <div className="mt-3">
              <label className="text-xs font-medium text-gray-600">Severity</label>
              <div className="mt-1 flex gap-2">
                {["low", "medium", "high"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setSeverity(s)}
                    className={`flex-1 rounded-lg border py-1.5 text-xs font-medium capitalize transition-colors ${
                      severity === s
                        ? "bg-blue-100 text-blue-700 border-blue-300"
                        : "border-gray-200 text-gray-500 hover:bg-gray-50"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-3">
              <label className="text-xs font-medium text-gray-600">Note (optional)</label>
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value.slice(0, 200))}
                placeholder="e.g. Power gone in whole street"
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-400"
              />
              <p className="mt-0.5 text-right text-xs text-gray-400">{note.length}/200</p>
            </div>

            <button
              onClick={handleSubmit}
              disabled={isPending}
              className="mt-4 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "Submitting..." : "Submit Report"}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
