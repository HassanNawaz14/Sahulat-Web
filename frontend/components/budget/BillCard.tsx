import type { Bill } from "@/lib/hooks/useBills"

const STATUS_CONFIG: Record<Bill["status"], { label: string; color: string }> = {
  unpaid: { label: "Unpaid", color: "text-red-700" },
  paid: { label: "Paid", color: "text-green-700" },
  overdue: { label: "Overdue", color: "text-amber-700" },
}

export default function BillCard({ bill, account }: { bill: Bill; account: any }) {
  const statusCfg = STATUS_CONFIG[bill.status || "unpaid"]
  const dueDate = new Date(bill.due_date)
  const daysLeft = Math.max(0, Math.ceil((dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
  const isOverdue = daysLeft === 0 && bill.status === "unpaid"

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">
            {account.account_label || account.provider_code.toUpperCase()}
          </h3>
          <p className="text-xs text-gray-500 capitalize">{account.utility_type}</p>
        </div>
        <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusCfg.color} bg-gray-50`}>{statusCfg.label}</span>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">Amount Due</p>
          <p className="font-semibold text-gray-900">Rs. {bill.amount_payable.toLocaleString()}</p>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">Due Date</p>
          <p className={`text-sm font-medium ${isOverdue ? "text-amber-700" : "text-gray-900"}`}>{daysLeft === 0 && bill.status === "unpaid" ? "Today" : daysLeft > 0 ? `${daysLeft} days` : "Overdue"}</p>
        </div>

        {bill.units_consumed && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">Units</p>
            <p className="text-sm text-gray-900">{bill.units_consumed.toLocaleString()}</p>
          </div>
        )}

        {bill.tariff_slab && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">Rate</p>
            <p className="text-sm text-gray-900">{bill.tariff_slab}</p>
          </div>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <button className="flex-1 rounded-lg bg-blue-50 py-2 text-center text-sm font-medium text-blue-600 hover:bg-blue-100">View Details</button>
        <button className="rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100">Mark Paid</button>
      </div>
    </div>
  )
}
