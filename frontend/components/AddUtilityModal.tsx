"use client"

import { useState } from "react"
import { X } from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { useAddConsumerAccount } from "@/lib/hooks/useBills"
import { PROVIDER_LABELS } from "@/lib/constants/utility"

const schema = z.object({
  utility_type: z.enum(["electricity", "gas", "water", "internet"]),
  provider_code: z.string().min(1, "Select a provider"),
  consumer_number: z.string().min(3, "Enter your consumer number"),
  account_label: z.string().optional(),
})

type FormData = z.infer<typeof schema>

const UTILITY_OPTIONS = [
  { value: "electricity", label: "Electricity" },
  { value: "gas", label: "Gas" },
  { value: "water", label: "Water" },
  { value: "internet", label: "Internet" },
]

const PROVIDERS_BY_UTILITY: Record<string, string[]> = {
  electricity: ["lesco", "kelectric", "iesco", "gepco", "fesco", "mepco", "pesco", "qesco", "hesco", "sepco"],
  gas: ["sngpl", "ssgc"],
  water: ["wasa_lhr", "kwsb"],
  internet: ["ptcl", "nayatel"],
}

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddUtilityModal({ open, onClose }: Props) {
  const [step, setStep] = useState<"type" | "form">("type")
  const addAccount = useAddConsumerAccount()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { utility_type: "electricity" },
  })

  const utilityType = watch("utility_type")
  const providers = PROVIDERS_BY_UTILITY[utilityType] || []

  const onSubmit = async (data: FormData) => {
    try {
      await addAccount.mutateAsync(data)
      reset()
      setStep("type")
      onClose()
    } catch {
      /* error handled by form */
    }
  }

  const handleClose = () => {
    reset()
    setStep("type")
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center">
      <div className="w-full max-w-md rounded-t-2xl bg-white p-6 sm:rounded-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Add Utility</h2>
          <button onClick={handleClose} className="rounded-lg p-1 hover:bg-gray-100">
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-5 space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-600">Utility Type</label>
            <div className="mt-1.5 grid grid-cols-2 gap-2">
              {UTILITY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    setValue("utility_type", opt.value as FormData["utility_type"])
                    setValue("provider_code", "")
                    setStep("form")
                  }}
                  className={`rounded-lg border px-3 py-2.5 text-sm font-medium transition ${
                    utilityType === opt.value
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {step === "form" && (
            <>
              <div>
                <label className="text-xs font-medium text-gray-600">Provider</label>
                <select
                  {...register("provider_code")}
                  className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
                >
                  <option value="">Select provider</option>
                  {providers.map((p) => (
                    <option key={p} value={p}>
                      {PROVIDER_LABELS[p] || p.toUpperCase()}
                    </option>
                  ))}
                </select>
                {errors.provider_code && (
                  <p className="mt-1 text-xs text-red-500">{errors.provider_code.message}</p>
                )}
              </div>

              <div>
                <label className="text-xs font-medium text-gray-600">Consumer Number</label>
                <input
                  {...register("consumer_number")}
                  placeholder="e.g. 13112621101009"
                  className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
                />
                {errors.consumer_number && (
                  <p className="mt-1 text-xs text-red-500">{errors.consumer_number.message}</p>
                )}
              </div>

              <div>
                <label className="text-xs font-medium text-gray-600">
                  Label <span className="text-gray-400">(optional)</span>
                </label>
                <input
                  {...register("account_label")}
                  placeholder="e.g. Main Meter"
                  className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
                />
              </div>

              {addAccount.isError && (
                <p className="text-xs text-red-500">
                  {addAccount.error?.message || "Failed to add account"}
                </p>
              )}

              <button
                type="submit"
                disabled={addAccount.isPending}
                className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
              >
                {addAccount.isPending ? "Adding..." : "Add Account"}
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  )
}
