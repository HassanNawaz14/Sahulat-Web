import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"

export const billKeys = {
  all: ["bills"] as const,
  summary: () => ["bills", "summary"] as const,
  accounts: () => ["consumer-accounts"] as const,
  latest: (id: string) => ["bills", id, "latest"] as const,
  history: (id: string, months?: number) => ["bills", id, "history", months ?? 6] as const,
}

export interface ConsumerAccount {
  id: string
  home_id: string | null
  utility_type: string
  provider_code: string
  consumer_number: string
  account_label: string
  is_active: boolean
  last_fetched_at: string | null
  created_at: string
}

export interface Bill {
  id: string
  consumer_account_id: string
  billing_month: string
  issue_date: string | null
  due_date: string | null
  amount_payable: number
  units_consumed: number | null
  previous_reading: number | null
  current_reading: number | null
  arrears: number
  taxes: number
  surcharges: number
  meter_rent: number
  fc_surcharge: number
  tariff_slab: string | null
  status: string
  raw_data: Record<string, unknown> | null
}

export interface BillsSummary {
  total_this_month: number
  account_count: number
  breakdown: {
    consumer_account_id: string
    utility_type: string
    provider_code: string
    label: string
    amount: number
    billing_month: string
    status: string
    due_date: string | null
  }[]
}

export function useConsumerAccounts() {
  return useQuery({
    queryKey: billKeys.accounts(),
    queryFn: async () => {
      const { data } = await api.get<{ consumer_accounts: ConsumerAccount[] }>(
        "/consumer-accounts"
      )
      return data.consumer_accounts
    },
    staleTime: 30_000,
  })
}

export function useLatestBill(consumerAccountId: string | null) {
  return useQuery({
    queryKey: billKeys.latest(consumerAccountId ?? ""),
    queryFn: async () => {
      if (!consumerAccountId) return null
      const { data } = await api.get<{ bill: Bill | null }>(
        `/bills/${consumerAccountId}/latest`
      )
      return data.bill
    },
    enabled: !!consumerAccountId,
    staleTime: 30_000,
  })
}

export function useBillHistory(consumerAccountId: string | null, months = 6) {
  return useQuery({
    queryKey: billKeys.history(consumerAccountId ?? "", months),
    queryFn: async () => {
      if (!consumerAccountId) return []
      const { data } = await api.get<{ history: Bill[] }>(
        `/bills/${consumerAccountId}/history?months=${months}`
      )
      return data.history
    },
    enabled: !!consumerAccountId,
    staleTime: 60_000,
  })
}

export function useBillsSummary() {
  return useQuery({
    queryKey: billKeys.summary(),
    queryFn: async () => {
      const { data } = await api.get<BillsSummary>("/bills/summary")
      return data
    },
    staleTime: 15_000,
  })
}

export function useFetchBill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (consumerAccountId: string) => {
      const { data } = await api.post(`/bills/fetch/${consumerAccountId}`)
      return data
    },
    onSuccess: (_data, accountId) => {
      queryClient.invalidateQueries({ queryKey: billKeys.latest(accountId) })
      queryClient.invalidateQueries({ queryKey: billKeys.summary() })
    },
  })
}

export function useUpdateBillStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ billId, status }: { billId: string; status: string }) => {
      const { data } = await api.patch(`/bills/${billId}/status`, { status })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billKeys.all })
    },
  })
}

export function useAddConsumerAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      utility_type: string
      provider_code: string
      consumer_number: string
      account_label?: string
      home_id?: string
    }) => {
      const { data } = await api.post("/consumer-accounts", payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billKeys.accounts() })
    },
  })
}
