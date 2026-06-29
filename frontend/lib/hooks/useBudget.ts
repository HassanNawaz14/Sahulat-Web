import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type { AxiosError } from "axios"

export type BudgetStatus = "safe" | "warning" | "exceeded"

export interface CategorySpend {
  code: string
  label: string
  actual: number
  projected: number
  limit: number
  status: BudgetStatus
}

export interface BudgetSummary {
  month: string
  actual_spend: number
  projected_spend: number
  budget_limit: number
  status: BudgetStatus
  categories: CategorySpend[]
}

export interface BudgetCategory {
  id: string
  user_id: string
  code: string
  label: string
  monthly_limit: number | null
  is_custom: boolean
  created_at: string
  updated_at: string
}

export interface ExpenseItem {
  id: string
  category_code: string
  category_label: string
  amount: number
  expense_date: string
  description: string | null
  is_recurring: boolean
}

export interface ExpenseListResponse {
  items: ExpenseItem[]
  next_cursor: string | null
}

export const budgetKeys = {
  summary: (month: string) => ["budget", "summary", month] as const,
  categories: () => ["budget", "categories"] as const,
  expenses: (month?: string, categoryId?: string) =>
    ["budget", "expenses", month ?? "", categoryId ?? ""] as const,
}

export function useBudgetSummary(month: string) {
  return useQuery({
    queryKey: budgetKeys.summary(month),
    queryFn: async () => {
      const { data } = await api.get<BudgetSummary>("/budget/summary", { params: { month } })
      return data
    },
    staleTime: 2 * 60 * 1000,
  })
}

export function useBudgetCategories() {
  return useQuery({
    queryKey: budgetKeys.categories(),
    queryFn: async () => {
      const { data } = await api.get<BudgetCategory[]>("/budget/categories")
      return data
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      code: string
      label: string
      monthly_limit?: number
    }) => {
      const { data } = await api.post("/budget/categories", payload)
      return data as BudgetCategory
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.categories() })
    },
  })
}

export function useUpdateCategoryLimit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      categoryId,
      monthly_limit,
    }: {
      categoryId: string
      monthly_limit: number
    }) => {
      const { data } = await api.put(`/budget/categories/${categoryId}/limit`, { monthly_limit })
      return data as BudgetCategory
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.categories() })
    },
  })
}

export function useCreateExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      category_id: string
      home_id?: string
      amount: number
      expense_date: string
      description?: string
      is_recurring?: boolean
      recurrence_day?: number
    }) => {
      const { data } = await api.post("/budget/expenses", payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget"] })
    },
  })
}

export function useDeleteExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (expenseId: string) => {
      const { data } = await api.delete(`/budget/expenses/${expenseId}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget"] })
    },
  })
}

export function useExpenses(month?: string, categoryId?: string) {
  return useQuery({
    queryKey: budgetKeys.expenses(month, categoryId),
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (month) params.month = month
      if (categoryId) params.category_id = categoryId
      const { data } = await api.get<ExpenseListResponse>("/budget/expenses", { params })
      return data
    },
    staleTime: 1 * 60 * 1000,
  })
}
