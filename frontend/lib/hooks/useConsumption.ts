import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"

export const consumptionKeys = {
  summary: (id: string) => ["consumption", id, "summary"] as const,
  readings: (id: string) => ["consumption", id, "readings"] as const,
  trend: (id: string) => ["consumption", id, "trend"] as const,
  slabAlerts: (id: string) => ["consumption", id, "slab-alerts"] as const,
}

export interface LatestReadingSnapshot {
  reading_value: number
  units_since_last: number
  reading_date: string
}

export interface TrajectoryPoint {
  total_units: number
  daily_rate: number
  projected_units: number
  estimated_bill: number
}

export interface ConsumptionSummary {
  consumer_account_id: string
  cycle_start: string
  total_units_so_far: number
  daily_rate: number
  days_elapsed: number
  days_remaining: number
  projected_units: number
  current_slab: { min: number; max: number | null; rate: number } | null
  next_slab: { threshold: number; rate: number; units_away: number } | null
  estimated_bill: number
  last_reading: { date: string; value: number } | null
  bill_units_consumed: number | null
  is_protected: boolean
  readings_this_cycle: number
  previous_total_units: number | null
  previous_daily_rate: number | null
  consumption_change_pct: number | null
  consumption_trend: "up" | "down" | "stable" | null
  latest_reading_snapshot: LatestReadingSnapshot | null
}

export interface MeterReading {
  id: string
  consumer_account_id: string
  reading_date: string
  reading_value: number
  units_since_last: number | null
  consumption_rate: number | null
  estimated_bill: number | null
  notes: string | null
  created_at: string
}

export interface TrendPoint {
  billing_month: string
  units_consumed: number | null
  amount_payable: number
  tariff_slab: string | null
}

export interface SlabAlert {
  id: string
  consumer_account_id: string
  billing_period: string
  slab_threshold: number
  units_at_alert: number
  cost_if_crossed: number | null
  alerted_at: string
}

export function useConsumptionSummary(consumerAccountId: string | null) {
  return useQuery({
    queryKey: consumptionKeys.summary(consumerAccountId ?? ""),
    queryFn: async () => {
      if (!consumerAccountId) return null
      const { data } = await api.get<ConsumptionSummary>(
        `/consumption/summary/${consumerAccountId}`
      )
      return data
    },
    enabled: !!consumerAccountId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useReadingHistory(consumerAccountId: string | null) {
  return useQuery({
    queryKey: consumptionKeys.readings(consumerAccountId ?? ""),
    queryFn: async () => {
      if (!consumerAccountId) return []
      const { data } = await api.get<{ readings: MeterReading[] }>(
        `/consumption/readings/${consumerAccountId}?limit=30`
      )
      return data.readings
    },
    enabled: !!consumerAccountId,
    staleTime: 30 * 1000,
  })
}

export function useConsumptionTrend(consumerAccountId: string | null) {
  return useQuery({
    queryKey: consumptionKeys.trend(consumerAccountId ?? ""),
    queryFn: async () => {
      if (!consumerAccountId) return []
      const { data } = await api.get<{ trend: TrendPoint[] }>(
        `/consumption/trend/${consumerAccountId}`
      )
      return data.trend
    },
    enabled: !!consumerAccountId,
    staleTime: 24 * 60 * 60 * 1000,
  })
}

export function useSlabAlerts(consumerAccountId: string | null) {
  return useQuery({
    queryKey: consumptionKeys.slabAlerts(consumerAccountId ?? ""),
    queryFn: async () => {
      if (!consumerAccountId) return []
      const { data } = await api.get<{ alerts: SlabAlert[] }>(
        `/consumption/slab-alerts/${consumerAccountId}`
      )
      return data.alerts
    },
    enabled: !!consumerAccountId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useDeleteReading(consumerAccountId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (readingId: string) => {
      const { data } = await api.delete(`/consumption/readings/${readingId}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consumptionKeys.readings(consumerAccountId) })
      queryClient.invalidateQueries({ queryKey: consumptionKeys.summary(consumerAccountId) })
    },
  })
}

export function useSubmitReading() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      consumer_account_id: string
      reading_date: string
      reading_value: number
      input_mode?: "meter_reading" | "units"
      notes?: string
    }) => {
      const { data } = await api.post("/consumption/readings", payload)
      return data
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: consumptionKeys.summary(variables.consumer_account_id) })
      queryClient.invalidateQueries({ queryKey: consumptionKeys.readings(variables.consumer_account_id) })
      queryClient.invalidateQueries({ queryKey: consumptionKeys.slabAlerts(variables.consumer_account_id) })
    },
  })
}
