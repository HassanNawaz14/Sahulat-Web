"use client"

import { useState } from "react"
import Link from "next/link"
import { RefreshCw, MoreHorizontal, Share2 } from "lucide-react"
// @ts-expect-error Trash missing from types but exists at runtime
import { Trash } from "lucide-react"

import type { ConsumerAccount } from "@/lib/hooks/useBills"
import { useLatestBill, useFetchBill, useDeleteConsumerAccount } from "@/lib/hooks/useBills"
import { UTILITY_ICONS, UTILITY_BG_COLORS, STATUS_COLORS, PROVIDER_LABELS } from "@/lib/constants/utility"
import BillTrendChart from "./BillTrendChart"
import MarkPaidButton from "./MarkPaidButton"
import { buildWhatsAppShareText, openWhatsAppShare } from "@/lib/utils/whatsAppShare"
import CaptchaModal from "./CaptchaModal"

interface Props {
  account: ConsumerAccount
}

export default function ConsumerAccountCard({ account }: Props) {
  const [showMenu, setShowMenu] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [captcha, setCaptcha] = useState<{ id: string; image: string } | null>(null)
  const { data: bill, isLoading: billLoading } = useLatestBill(account.id)
  const fetchBill = useFetchBill()
  const deleteAccount = useDeleteConsumerAccount()
  const Icon = UTILITY_ICONS[account.utility_type]

  const dueDate = bill?.due_date
  let daysLeft: number | null = null
  if (dueDate) {
    const diff = Math.ceil(
      (new Date(dueDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    )
    daysLeft = diff
  }

  const borderClass = UTILITY_BG_COLORS[account.utility_type] || "border-gray-200"

  const handleRefresh = () => {
    setFetchError(null)
    setCaptcha(null)
    fetchBill.mutate(account.id, {
      onSuccess: (data: any) => {
        if (data?.status === "captcha_required") {
          setCaptcha({ id: data.captcha_id, image: data.captcha_image })
        } else if (data?.status === "no_bill" && data?.message) {
          setFetchError(data.message)
          setTimeout(() => setFetchError(null), 8000)
        }
      },
      onError: (err: any) => {
        const msg = err?.response?.data?.detail || err?.message || "Fetch failed"
        setFetchError(msg)
        setTimeout(() => setFetchError(null), 8000)
      },
    })
  }

  const handleDelete = () => {
    if (!window.confirm(`Delete ${account.account_label || account.provider_code.toUpperCase()}? This will remove it from your dashboard.`)) {
      setShowMenu(false)
      return
    }
    setDeleteError(null)
    setShowMenu(false)
    deleteAccount.mutate(account.id, {
      onError: (err: any) => {
        const msg = err?.response?.data?.detail || err?.message || "Delete failed"
        setDeleteError(msg)
        setTimeout(() => setDeleteError(null), 8000)
      },
    })
  }

  const isDeleting = deleteAccount.isPending

  return (
    <div className={`rounded-xl border bg-white p-4 ${borderClass}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">
            {Icon && <Icon className="h-5 w-5" />}
          </div>
          <div>
            <p className="text-sm font-semibold">
              {account.account_label || PROVIDER_LABELS[account.provider_code] || account.provider_code.toUpperCase()}
            </p>
            <p className="text-xs text-gray-500">{account.utility_type}</p>
          </div>
        </div>
        <div className="relative flex items-center gap-1">
          <button
            onClick={handleRefresh}
            disabled={fetchBill.isPending}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <RefreshCw className={`h-4 w-4 ${fetchBill.isPending ? "animate-spin" : ""}`} />
          </button>
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <div className="absolute right-0 z-20 mt-1 w-40 rounded-lg border bg-white py-1 shadow-lg">
                  <Link
                    href={`/bills/${account.id}`}
                    className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => setShowMenu(false)}
                  >
                    View Details
                  </Link>
                  <button
                    onClick={handleDelete}
                    disabled={deleteAccount.isPending}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                  >
                    <Trash className="h-4 w-4" />
                    {deleteAccount.isPending ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {fetchError && (
        <div className="mt-2 rounded-lg bg-red-50 p-2 text-xs text-red-600">
          {fetchError}
        </div>
      )}
      {deleteError && (
        <div className="mt-2 rounded-lg bg-red-50 p-2 text-xs text-red-600">
          {deleteError}
        </div>
      )}

      {billLoading ? (
        <div className="mt-4 h-16 animate-pulse rounded-lg bg-gray-100" />
      ) : bill ? (
        <>
          <div className="mt-4 flex items-end justify-between">
            <div>
              <p className="text-2xl font-bold">Rs. {bill.amount_payable.toLocaleString()}</p>
              {daysLeft !== null && (
                <p className={`mt-0.5 text-xs ${daysLeft <= 3 ? "text-red-500 font-medium" : "text-gray-500"}`}>
                  {daysLeft <= 0
                    ? "Overdue!"
                    : daysLeft === 1
                      ? "Due tomorrow"
                      : `Due in ${daysLeft} days`}
                </p>
              )}
            </div>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[bill.status] || "bg-gray-50 text-gray-600"}`}
            >
              {bill.status}
            </span>
          </div>

          <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
            {bill.units_consumed != null && (
              <span>{bill.units_consumed} kWh</span>
            )}
            {bill.tariff_slab && (
              <span>Slab: {bill.tariff_slab}</span>
            )}
          </div>

          <div className="mt-3">
            <BillTrendChart consumerAccountId={account.id} />
          </div>

          <div className="mt-3 flex gap-2">
            <MarkPaidButton billId={bill.id} currentStatus={bill.status} />
            <button
              onClick={() => {
                const text = buildWhatsAppShareText(
                  PROVIDER_LABELS[account.provider_code] || account.provider_code.toUpperCase(),
                  account.account_label,
                  bill.billing_month,
                  bill.amount_payable,
                  bill.due_date,
                  bill.units_consumed,
                )
                openWhatsAppShare(text)
              }}
              className="flex rounded-lg border border-gray-200 py-2 px-3 text-xs font-medium text-gray-600"
            >
              <Share2 className="h-3.5 w-3.5 mr-1" />
              Share
            </button>
            <Link
              href={`/bills/${account.id}`}
              className="flex-1 rounded-lg border border-gray-200 py-2 text-center text-xs font-medium text-gray-600"
            >
              View Details
            </Link>
          </div>
        </>
      ) : (
        <div className="mt-4 rounded-lg bg-gray-50 p-3 text-center text-xs text-gray-500">
          No bill data yet. Tap refresh to fetch.
        </div>
      )}

      {captcha && (
        <CaptchaModal
          captchaImage={captcha.image}
          captchaId={captcha.id}
          accountId={account.id}
          onClose={() => setCaptcha(null)}
          onCaptchaRefresh={(id, image) => setCaptcha({ id, image })}
        />
      )}
    </div>
  )
}
