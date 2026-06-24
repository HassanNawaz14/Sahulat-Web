import { useMutation } from "@tanstack/react-query"
import api from "@/lib/api"
import type { ElectricityEstimateInput, GasEstimateInput, WaterEstimateInput, EstimateResult } from "@/types/estimate"

export function useEstimateElectricity() {
  return useMutation({
    mutationFn: async (body: ElectricityEstimateInput) => {
      const { data } = await api.post<EstimateResult>("/estimates/electricity", body)
      return data
    },
  })
}

export function useEstimateGas() {
  return useMutation({
    mutationFn: async (body: GasEstimateInput) => {
      const { data } = await api.post<EstimateResult>("/estimates/gas", body)
      return data
    },
  })
}

export function useEstimateWater() {
  return useMutation({
    mutationFn: async (body: WaterEstimateInput) => {
      const { data } = await api.post<EstimateResult>("/estimates/water", body)
      return data
    },
  })
}

export function useEstimateFromConsumption() {
  return useMutation({
    mutationFn: async (consumerAccountId: string) => {
      const { data } = await api.post<EstimateResult>(`/estimates/from-consumption/${consumerAccountId}`)
      return data
    },
  })
}
