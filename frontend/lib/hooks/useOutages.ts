import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"

export const outageKeys = {
  schedule: (accountId: string) => ["outages", "schedule", accountId] as const,
  community: (city?: string, area?: string) => ["outages", "community", city, area] as const,
  feeders: (providerCode: string, q?: string) => ["outages", "feeders", providerCode, q] as const,
}

export interface ScheduledOutage {
  id: string
  provider_code: string
  feeder_name: string
  start_time: string
  end_time: string
  outage_type: string
  confidence_score: number
  status: "upcoming" | "active" | "expired"
}

export interface ScheduleResponse {
  today: ScheduledOutage[]
  tomorrow: ScheduledOutage[]
  day_after: ScheduledOutage[]
  current_outage: ScheduledOutage | null
  next_outage: ScheduledOutage | null
  feeder_name: string
  feeder_set: boolean
}

export interface CommunityReport {
  id: string
  utility_type: string
  report_type: string
  city: string
  area: string
  severity: string
  status: string
  confidence_score: number
  report_count: number
  created_at: string
  expires_at: string | null
}

export interface FeederItem {
  feeder_code: string
  feeder_name: string
}

export function useScheduledOutages(accountId: string | null) {
  return useQuery({
    queryKey: outageKeys.schedule(accountId ?? ""),
    queryFn: async () => {
      if (!accountId) return null
      const { data } = await api.get<ScheduleResponse>(`/outages/schedule/${accountId}`)
      return data
    },
    enabled: !!accountId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCommunityReports(city?: string, area?: string) {
  return useQuery({
    queryKey: outageKeys.community(city, area),
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (city) params.city = city
      if (area) params.area = area
      const { data } = await api.get<{ reports: CommunityReport[] }>("/outages/community", { params })
      return data.reports
    },
    staleTime: 30 * 1000,
  })
}

export function useReportOutage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      utility_type: string
      provider_code?: string
      home_id?: string
      report_type?: string
      severity?: string
      note?: string
    }) => {
      const { data } = await api.post("/outages/reports", payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outages", "community"] })
    },
  })
}

export function useRestoreOutage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (reportId: string) => {
      const { data } = await api.post(`/outages/reports/${reportId}/restore`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outages", "community"] })
    },
  })
}

export function useSetFeeder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { consumer_account_id: string; feeder_name: string }) => {
      const { data } = await api.patch("/outages/feeder", payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outages"] })
    },
  })
}

export function useFeederSearch(providerCode: string, query: string) {
  return useQuery({
    queryKey: outageKeys.feeders(providerCode, query),
    queryFn: async () => {
      if (!query || query.length < 1) return []
      const { data } = await api.get<{ feeders: FeederItem[] }>("/outages/feeders", {
        params: { provider_code: providerCode, q: query },
      })
      return data.feeders
    },
    enabled: !!providerCode && query.length >= 1,
    staleTime: 60 * 60 * 1000,
  })
}
