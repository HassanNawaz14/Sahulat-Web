"use client"

import { useState } from "react"
import { X } from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { useAddConsumerAccount, useFetchBill } from "@/lib/hooks/useBills"
import ProviderSelector from "./ProviderSelector"
import ConsumerNumberInput from "./ConsumerNumberInput"
import { getConsumerNumberPattern } from "@/lib/constants/consumerPatterns"
import CaptchaModal from "./CaptchaModal"

const schema = z.object({
  utility_type: z.enum(["electricity", "gas", "water", "internet"]),
  provider_code: z.string().min(1, "Select a provider"),
  consumer_number: z.string().min(3, "Enter your consumer number"),
  provider_reference: z.string().optional(),
  account_label: z.string().optional(),
})

type FormData = z.infer<typeof schema>

const UTILITY_OPTIONS = [
  { value: "electricity", label: "Electricity" },
  { value: "gas", label: "Gas" },
  { value: "water", label: "Water" },
  { value: "internet", label: "Internet" },
]

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddUtilityModal({ open, onClose }: Props) {
  const [step, setStep] = useState<"type" | "form">("type")
  const [captcha, setCaptcha] = useState<{ id: string; image: string; accountId: string } | null>(null)
  const addAccount = useAddConsumerAccount()
  const fetchBill = useFetchBill()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { utility_type: "electricity" },
  })

  const utilityType = watch("utility_type")
  const providerCode = watch("provider_code")
  const isPtcl = providerCode === "ptcl"

  const onSubmit = async (data: FormData) => {
    const pattern = getConsumerNumberPattern(data.provider_code)
    if (!pattern.pattern.test(data.consumer_number)) {
      setError("consumer_number", {
        message: `Invalid format: ${pattern.hint}`,
      })
      return
    }
    try {
      const result = await addAccount.mutateAsync(data)
      const accountId = (result as any)?.consumer_account?.id
      if (accountId) {
        const fetchResult = await fetchBill.mutateAsync(accountId)
        if (fetchResult?.status === "captcha_required") {
          setCaptcha({
            id: fetchResult.captcha_id,
            image: fetchResult.captcha_image,
            accountId,
          })
          return
        }
      }
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
                    setValue("provider_reference", "")
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
              <ProviderSelector
                utilityType={utilityType}
                value={providerCode}
                onChange={(v) => {
                  setValue("provider_code", v, { shouldValidate: true })
                  if (v !== "ptcl") {
                    setValue("provider_reference", "")
                  }
                }}
                error={errors.provider_code?.message}
              />

              {providerCode && (
                <ConsumerNumberInput
                  providerCode={providerCode}
                  value={watch("consumer_number")}
                  onChange={(v) => setValue("consumer_number", v, { shouldValidate: true })}
                  error={errors.consumer_number?.message}
                />
              )}

              {isPtcl && (
                <div>
                  <label className="text-xs font-medium text-gray-600">PTCL Account ID <span className="text-gray-400">(optional)</span></label>
                  <input
                    {...register("provider_reference")}
                    placeholder="Leave blank if you don’t have it"
                    className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
                  />
                  {errors.provider_reference && (
                    <p className="mt-1 text-xs text-red-500">{errors.provider_reference.message}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">
                    PTCL works with landline number only; Account ID is optional if you know it.
                  </p>
                </div>
              )}

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
                  {(addAccount.error as any)?.response?.data?.detail || addAccount.error?.message || "Failed to add account"}
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

      {captcha && (
        <CaptchaModal
          captchaImage={captcha.image}
          captchaId={captcha.id}
          accountId={captcha.accountId}
          onClose={() => {
            setCaptcha(null)
            handleClose()
          }}
          onCaptchaRefresh={(id, image) => setCaptcha((prev) => prev ? { ...prev, id, image } : prev)}
        />
      )}
    </div>
  )
}
