"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import { useBudgetSummary, useBudgetCategories, useExpenses, useDeleteExpense } from "@/lib/hooks/useBudget"
import MonthSelector from "@/components/budget/MonthSelector"
import BudgetSummaryCard from "@/components/budget/BudgetSummary"
import CategoryProgress from "@/components/budget/CategoryProgress"
import ExpenseList from "@/components/budget/ExpenseList"
import AddExpenseButton from "@/components/budget/AddExpenseButton"

const now = new Date()
const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`

export default function BudgetPage() {
  const [month, setMonth] = useState(currentMonth)
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()

  const { data: summary, isLoading: summaryLoading } = useBudgetSummary(month)
  const { data: categories } = useBudgetCategories()
  const { data: expenseData } = useExpenses(month, selectedCategory)
  const deleteExpense = useDeleteExpense()

  const handleDelete = async (id: string) => {
    if (confirm("Delete this expense?")) {
      await deleteExpense.mutateAsync(id)
    }
  }

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard" className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-xl font-bold">Budget Manager</h1>
      </div>

      <div className="space-y-4">
        <MonthSelector value={month} onChange={setMonth} />

        {summaryLoading ? (
          <div className="h-32 animate-pulse rounded-xl bg-gray-100" />
        ) : summary ? (
          <BudgetSummaryCard summary={summary} />
        ) : null}

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-600">Categories</p>
            <Link href="/settings" className="text-xs text-blue-600">Manage</Link>
          </div>
          <div className="space-y-2">
            {summary?.categories.map((cat) => (
              <CategoryProgress
                key={cat.code}
                category={cat}
                onTap={() =>
                  setSelectedCategory(selectedCategory === cat.code ? undefined : cat.code)
                }
              />
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-600">
              {selectedCategory
                ? `Expenses - ${summary?.categories.find((c) => c.code === selectedCategory)?.label || ""}`
                : "Recent Expenses"}
            </p>
            <div className="flex items-center gap-2">
              {selectedCategory && (
                <button
                  onClick={() => setSelectedCategory(undefined)}
                  className="text-xs text-blue-600"
                >
                  Clear filter
                </button>
              )}
              <button
                onClick={() => document.querySelector<HTMLButtonElement>('[data-add-expense]')?.click()}
                className="text-xs font-medium text-blue-600 hover:text-blue-800"
              >
                + Add
              </button>
            </div>
          </div>
          <ExpenseList
            items={expenseData?.items || []}
            onDelete={handleDelete}
          />
        </div>
      </div>

      <AddExpenseButton
        categories={categories || []}
        currentMonth={month}
      />

      {(!categories || categories.length === 0) && (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-8 text-center">
          <p className="text-sm text-gray-500">No budget categories yet.</p>
        </div>
      )}
    </main>
  )
}
