export interface ElectricityEstimateInput {
  provider_code: string
  units: number
  phase_type: "single_phase" | "three_phase"
  connection_type?: "residential"
  protected_customer?: boolean
  lifeline_customer?: boolean
  include_taxes?: boolean
  arrears?: number
}

export interface GasEstimateInput {
  provider_code: "sngpl" | "ssgc"
  consumption_mmbtu: number
  include_taxes?: boolean
}

export interface WaterEstimateInput {
  provider_code: string
  usage_units?: number | null
  property_type: "residential" | "commercial"
  property_size_marla?: number | null
}

export interface SlabLine {
  label: string
  units: number
  rate: number
  amount: number
}

export interface SlabWarning {
  current_slab: string
  next_slab_threshold: number | null
  units_to_next_slab: number | null
  estimated_extra_cost_if_crossed: number
}

export interface EstimateResult {
  provider_code: string
  utility_type: string
  units: number
  estimated_total: number
  currency: string
  tariff_version: string
  breakdown: SlabLine[]
  taxes: number
  slab_warning?: SlabWarning | null
}
