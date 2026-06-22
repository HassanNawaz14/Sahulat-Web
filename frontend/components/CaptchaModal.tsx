"use client"

import { useState } from "react"
import { X } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import { billKeys } from "@/lib/hooks/useBills"

interface Props {
  captchaImage: string
  captchaId: string
  accountId: string
  onClose: () => void
  onCaptchaRefresh?: (captchaId: string, captchaImage: string) => void
}

export default function CaptchaModal({ captchaImage, captchaId, accountId, onClose, onCaptchaRefresh }: Props) {
  const [solution, setSolution] = useState("")
  const [error, setError] = useState("")
  const [currentImage, setCurrentImage] = useState(captchaImage)
  const queryClient = useQueryClient()

  const solveMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/bills/fetch/${accountId}/captcha-solve`, {
        captcha_id: captchaId,
        captcha_solution: solution,
      })
      return data
    },
    onSuccess: (data) => {
      if (data?.status === "no_bill") {
        setError(data.message || "No bill found")
        return
      }
      if (data?.status === "captcha_required") {
        setCurrentImage(data.captcha_image)
        setError("Incorrect captcha. Please try again with the new image.")
        setSolution("")
        if (onCaptchaRefresh) {
          onCaptchaRefresh(data.captcha_id, data.captcha_image)
        }
        return
      }
      queryClient.invalidateQueries({ queryKey: billKeys.latest(accountId) })
      queryClient.invalidateQueries({ queryKey: billKeys.history(accountId) })
      queryClient.invalidateQueries({ queryKey: billKeys.summary() })
      queryClient.invalidateQueries({ queryKey: billKeys.accounts() })
      onClose()
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail || err?.message || "Captcha verification failed")
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!solution.trim()) return
    setError("")
    solveMutation.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Enter Captcha</h3>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-gray-100">
            <X className="h-4 w-4 text-gray-500" />
          </button>
        </div>

        <p className="mt-2 text-xs text-gray-500">
          PTCL requires a captcha to fetch your bill. Please type the digits shown below.
        </p>

        <div className="mt-3 flex justify-center rounded-lg border bg-gray-50 p-3">
          <img
            src={`data:image/jpeg;base64,${currentImage}`}
            alt="Captcha"
            className="h-auto max-w-full rounded"
          />
        </div>

        <form onSubmit={handleSubmit} className="mt-3 space-y-3">
          <input
            value={solution}
            onChange={(e) => setSolution(e.target.value.replace(/[^0-9]/g, ""))}
            placeholder="Enter captcha digits"
            maxLength={6}
            autoFocus
            className="w-full rounded-lg border border-gray-200 p-2.5 text-center text-lg font-mono tracking-widest"
          />

          {error && (
            <p className="text-xs text-red-500">{error}</p>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-200 py-2.5 text-sm font-medium text-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={solveMutation.isPending || !solution.trim()}
              className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {solveMutation.isPending ? "Verifying..." : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
