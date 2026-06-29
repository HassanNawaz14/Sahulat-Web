import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import type { SolarInstallation, SolarDashboardData, SolarAlert, ProductionDataPoint, InverterConnectPayload } from "@/types/solar"
import { solarKeys } from "@/types/solar"

// Hooks for solar installations
export function useSolarInstallations() {
  return useQuery({
    queryKey: solarKeys.installations(),
    queryFn: async () => {
      const { data } = await api.get<SolarInstallation[]>("/solar/installations")
      return data
    },
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateInstallation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      home_id?: string
      inverter_brand: "growatt" | "solis" | "huawei"
      inverter_model?: string
      system_size_kw: number
      panel_count?: number
      panel_wattage?: number
      installation_date?: string
      system_cost_pkr?: number
      net_metering_enabled?: boolean
      net_metering_ref?: string
    }) => {
      const { data } = await api.post("/solar/installations", payload)
      return data as SolarInstallation
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: solarKeys.installations() })
    },
  })
}

export function useConnectInverter() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      installationId,
      credentials,
    }: {
      installationId: string
      credentials: InverterConnectPayload
    }) => {
      const { data } = await api.post(`/solar/installations/${installationId}/connect`, credentials)
      return data
    },
    onSuccess: (_, { installationId }) => {
      queryClient.invalidateQueries({ queryKey: solarKeys.installations() })
      queryClient.invalidateQueries({ queryKey: solarKeys.dashboard(installationId) })
    },
  })
}

export function useSolarDashboard(installationId: string) {
  return useQuery({
    queryKey: solarKeys.dashboard(installationId),
    queryFn: async () => {
      const { data } = await api.get<SolarDashboardData>(`/solar/dashboard/${installationId}`)
      return data
    },
    staleTime: 1 * 60 * 1000,
  })
}

export function useSolarProduction(
  installationId: string,
  startDate: string,
  endDate: string,
) {
  return useQuery({
    queryKey: solarKeys.production(installationId, startDate, endDate),
    queryFn: async () => {
      const { data } = await api.get<ProductionDataPoint>(
        `/solar/installations/${installationId}/production`,
        { params: { start: startDate, end: endDate } }
      )
      return data
    },
    staleTime: 2 * 60 * 1000,
  })
}

export function useSolarAlerts(installationId?: string) {
  return useQuery({
    queryKey: solarKeys.alerts(installationId),
    queryFn: async () => {
      const { data } = await api.get<SolarAlert[]>("/solar/alerts", {
        params: installationId ? { installation_id: installationId } : {},
      })
      return data
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (alertId: string) => {
      const { data } = await api.put(`/solar/alerts/${alertId}/read`, {})
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["solar"] })
    },
  })
}

export function useDismissAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (alertId: string) => {
      const { data } = await api.put(`/solar/alerts/${alertId}/dismiss`, {})
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["solar"] })
    },
  })
}

export function useMarkMaintenance() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      installationId,
      lastMaintenanceDate,
    }: {
      installationId: string
      lastMaintenanceDate: string
    }) => {
      const { data } = await api.put(`/solar/maintenance/${installationId}`, {
        last_maintenance_date: lastMaintenanceDate,
      })
      return data
    },
    onSuccess: (_, { installationId }) => {
      queryClient.invalidateQueries({ queryKey: solarKeys.dashboard(installationId) })
      queryClient.invalidateQueries({ queryKey: solarKeys.alerts(installationId) })
    },
  })
}

export function useDeleteInstallation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (installationId: string) => {
      const { data } = await api.delete(`/solar/installations/${installationId}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["solar"] })
    },
  })
}
