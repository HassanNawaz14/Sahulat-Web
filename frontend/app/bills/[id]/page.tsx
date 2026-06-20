"use client"

import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, Share2, RefreshCw } from "lucide-react"

import { useConsumerAccounts, useLatestBill, useBillHistory, useFetchBill } from "@/lib/hooks/useBills"
import { PROVIDER_LABELS, UTILITY_ICONS, STATUS_COLORS } from "@/lib/constants/utility"
import BillTrendChart from "@/components/BillTrendChart"
import MarkPaidButton from "@/components/MarkPaidButton"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"

export default function BillDetailPage() {
  const params = useParams()
  const router = useRouter()
  const accountId = params.id as string

  const { data: accounts } = useConsumerAccounts()
  const { data: bill, isLoading: billLoading } = useLatestBill(accountId)
  const { data: history } = useBillHistory(accountId)
  const fetchBill = useFetchBill()

  const account = accounts?.find((a) => a.id === accountId)

  if (!account) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <p className="text-gray-500">Account not found</p>
      </main>
    )
  }

  const Icon = UTILITY_ICONS[account.utility_type]

  const chartData = (history || [])
    .map((h) => ({
      month: h.billing_month
        ? new Date(h.billing_month + "-01").toLocaleDateString("en", { month: "short", year: "2-digit" })
        : "?",
      amount: h.amount_payable,
    }))
    .reverse()

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5 text-gray-500" />
        </button>
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-5 w-5" />}
          <h1 className="text-lg font-semibold">
            {account.account_label || PROVIDER_LABELS[account.provider_code] || account.provider_code.toUpperCase()}
          </h1>
        </div>
        <div className="ml-auto flex gap-1">
          <button
            onClick={() => fetchBill.mutate(accountId)}
            disabled={fetchBill.isPending}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100"
          >
            <RefreshCw className={`h-4 w-4 ${fetchBill.isPending ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={() => {
              const text = encodeURIComponent(
                `Sahulat Bill - ${PROVIDER_LABELS[account.provider_code] || account.provider_code.toUpperCase()}\n` +
                `Amount: Rs. ${bill?.amount_payable?.toLocaleString() || "N/A"}\n` +
                `Due: ${bill?.due_date || "N/A"}\n` +
                `Track your bills: https://sahulat.pk`
              )
              window.open(`https://wa.me/?text=${text}`, "_blank")
            }}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100"
          >
            <Share2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {billLoading ? (
        <div className="space-y-4">
          <div className="h-40 animate-pulse rounded-xl bg-gray-100" />
          <div className="h-60 animate-pulse rounded-xl bg-gray-100" />
        </div>
      ) : bill ? (
        <>
          <div className="rounded-xl border bg-white p-5">
            <p className="text-xs text-gray-500">
              {bill.billing_month
                ? new Date(bill.billing_month + "-01").toLocaleDateString("en", { month: "long", year: "numeric" })
                : "Current"}{" "}
              Bill
            </p>
            <p className="mt-1 text-3xl font-bold">Rs. {bill.amount_payable.toLocaleString()}</p>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-gray-500">Due Date</p>
                <p className="font-medium">{bill.due_date || "N/A"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[bill.status] || "bg-gray-50 text-gray-600"}`}>
                  {bill.status}
                </span>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <MarkPaidButton billId={bill.id} currentStatus={bill.status} />
            </div>
          </div>

          <div className="mt-4 rounded-xl border bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold">Consumption</h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              {bill.current_reading != null && (
                <div>
                  <p className="text-xs text-gray-500">Current Reading</p>
                  <p className="font-medium">{bill.current_reading}</p>
                </div>
              )}
              {bill.previous_reading != null && (
                <div>
                  <p className="text-xs text-gray-500">Previous Reading</p>
                  <p className="font-medium">{bill.previous_reading}</p>
                </div>
              )}
              {bill.units_consumed != null && (
                <div>
                  <p className="text-xs text-gray-500">Units Consumed</p>
                  <p className="font-medium">{bill.units_consumed} kWh</p>
                </div>
              )}
              {bill.tariff_slab && (
                <div>
                  <p className="text-xs text-gray-500">Tariff Slab</p>
                  <p className="font-medium">{bill.tariff_slab}</p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 rounded-xl border bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold">Charges Breakdown</h2>
            <div className="space-y-2 text-sm">
              <ChargeRow label="Energy Charges" hint="Cost of electricity" amount={bill.amount_payable - bill.taxes - bill.arrears - bill.fc_surcharge - bill.meter_rent - bill.surcharges} />
              {bill.fc_surcharge > 0 && <ChargeRow label="Fuel Cost Adj." amount={bill.fc_surcharge} />}
              {bill.taxes > 0 && <ChargeRow label="Taxes" amount={bill.taxes} />}
              {bill.meter_rent > 0 && <ChargeRow label="Meter Rent" amount={bill.meter_rent} />}
              {bill.surcharges > 0 && <ChargeRow label="Surcharges" amount={bill.surcharges} />}
              {bill.arrears > 0 && <ChargeRow label="Arrears" amount={bill.arrears} />}
              <hr className="border-gray-200" />
              <ChargeRow label="Total Payable" amount={bill.amount_payable} bold />
            </div>
          </div>

          {chartData.length >= 2 && (
            <div className="mt-4 rounded-xl border bg-white p-5">
              <h2 className="mb-3 text-sm font-semibold">6-Month Trend</h2>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ fontSize: 12, borderRadius: 8 }}
                      formatter={(value: number) => [`Rs. ${value.toLocaleString()}`, "Amount"]}
                    />
                    <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-8 text-center">
          <p className="text-gray-500">No bill data found.</p>
          <button
            onClick={() => fetchBill.mutate(accountId)}
            disabled={fetchBill.isPending}
            className="mt-4 rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {fetchBill.isPending ? "Fetching..." : "Fetch Latest Bill"}
          </button>
        </div>
      )}
    </main>
  )
}

function ChargeRow({ label, amount, bold, hint }: { label: string; amount: number; bold?: boolean; hint?: string }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className={bold ? "font-semibold" : "text-gray-700"}>{label}</p>
        {hint && <p className="text-xs text-gray-400">{hint}</p>}
      </div>
      <p className={bold ? "font-bold" : ""}>
        Rs. {Math.max(0, amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </p>
    </div>
  )
}
