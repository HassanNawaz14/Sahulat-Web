// @ts-expect-error Trash missing from types but exists at runtime
import { Trash } from "lucide-react"
import type { ExpenseItem } from "@/lib/hooks/useBudget"

export default function ExpenseList({
  items,
  onDelete,
}: {
  items: ExpenseItem[]
  onDelete?: (id: string) => void
}) {
  if (!items.length) {
    return (
      <div className="rounded-lg border bg-white p-6 text-center">
        <p className="text-sm text-gray-400">No expenses this month</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between rounded-lg bg-white px-3 py-2.5"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 shrink-0">
              {item.category_label}
            </div>
            <div className="min-w-0">
              {item.description && (
                <p className="truncate text-sm text-gray-800">{item.description}</p>
              )}
              <p className="text-xs text-gray-400">
                {item.expense_date}
                {item.is_recurring && <span className="ml-1 text-blue-500">Recurring</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-sm font-medium">Rs. {item.amount.toLocaleString()}</span>
            {onDelete && (
              <button
                onClick={() => onDelete(item.id)}
                className="rounded-full p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
              >
                <Trash className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
