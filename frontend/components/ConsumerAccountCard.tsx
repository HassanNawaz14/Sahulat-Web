"use client"

import Link from "next/link"
import { RefreshCw, MoreHorizontal } from "lucide-react"

import type { ConsumerAccount } from "@/lib/hooks/useBills"
import { useLatestBill, useFetchBill } from "@/lib/hooks/useBills"
import { UTILITY_ICONS, UTILITY_BG_COLORS, STATUS_COLORS, PROVIDER_LABELS } from "@/lib/constants/utility"
import BillTrendChart from "./BillTrendChart"
import MarkPaidButton from "./MarkPaidButton"

interface Props {
  account: ConsumerAccount
}

export default function ConsumerAccountCard({ account }: Props) {
  const { data: bill, isLoading: billLoading } = useLatestBill(account.id)
  const fetchBill = useFetchBill()
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
        <div className="flex items-center gap-1">
          <button
            onClick={() => fetchBill.mutate(account.id)}
            disabled={fetchBill.isPending}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <RefreshCw className={`h-4 w-4 ${fetchBill.isPending ? "animate-spin" : ""}`} />
          </button>
          <Link
            href={`/bills/${account.id}`}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Link>
        </div>
      </div>

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
    </div>
  )
}
