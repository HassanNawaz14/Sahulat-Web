"use client"

import { useState } from "react"
import { Plus, X } from "lucide-react"

import { useCreateExpense } from "@/lib/hooks/useBudget"

interface Props {
  categories: { id: string; code: string; label: string }[]
  currentMonth: string
}

export default function AddExpenseButton({ categories, currentMonth }: Props) {
  const [open, setOpen] = useState(false)
  const [categoryId, setCategoryId] = useState("")
  const [amount, setAmount] = useState("")
  const [date, setDate] = useState(currentMonth + "-01")
  const [description, setDescription] = useState("")
  const [isRecurring, setIsRecurring] = useState(false)
  const [recurrenceDay, setRecurrenceDay] = useState("")
  const createExpense = useCreateExpense()

  const handleSubmit = async () => {
    if (!categoryId || !amount || !date) return
    await createExpense.mutateAsync({
      category_id: categoryId,
      amount: parseFloat(amount),
      expense_date: date,
      description: description || undefined,
      is_recurring: isRecurring,
      recurrence_day: isRecurring ? parseInt(recurrenceDay) || undefined : undefined,
    })
    setOpen(false)
    setCategoryId("")
    setAmount("")
    setDate(currentMonth + "-01")
    setDescription("")
    setIsRecurring(false)
    setRecurrenceDay("")
  }

  return (
    <>
      <button
        data-add-expense
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-colors hover:bg-blue-700"
      >
        <Plus className="h-6 w-6" />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center">
          <div className="w-full max-w-sm rounded-t-2xl bg-white p-5 sm:rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Add Expense</h3>
              <button onClick={() => setOpen(false)} className="rounded-full p-1 text-gray-400 hover:bg-gray-100">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3">
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none"
              >
                <option value="">Select category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>

              <input
                type="number"
                step="0.01"
                placeholder="Amount (Rs.)"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none"
              />

              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none"
              />

              <input
                placeholder="Description (optional)"
                maxLength={100}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none"
              />

              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isRecurring}
                  onChange={(e) => setIsRecurring(e.target.checked)}
                  className="rounded"
                />
                Recurring monthly
              </label>

              {isRecurring && (
                <input
                  type="number"
                  min="1"
                  max="31"
                  placeholder="Day of month (1-31)"
                  value={recurrenceDay}
                  onChange={(e) => setRecurrenceDay(e.target.value)}
                  className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none"
                />
              )}

              <button
                onClick={handleSubmit}
                disabled={!categoryId || !amount || createExpense.isPending}
                className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white disabled:opacity-50"
              >
                {createExpense.isPending ? "Saving..." : "Add Expense"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
