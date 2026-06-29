export type InverterBrand = "growatt" | "solis" | "huawei"
export type AlertSeverity = "info" | "warning" | "critical"
export type AlertType = "baseline_drop" | "zero_production" | "inverter_disconnected" | "cleaning_due"
export type HealthStatus = "normal" | "warning" | "critical"

export interface SolarInstallation {
  id: string
  user_id: string
  home_id: string | null
  inverter_brand: InverterBrand
  inverter_model: string | null
  system_size_kw: number
  panel_count: number | null
  panel_wattage: number | null
  installation_date: string | null
  commissioning_date: string | null
  system_cost_pkr: number | null
  net_metering_enabled: boolean
  net_metering_ref: string | null
  inverter_api_user: string | null
  inverter_plant_id: string | null
  last_synced_at: string | null
  last_maintenance_at: string | null
  health_status: HealthStatus
  created_at: string
  updated_at: string
}

export interface SolarDashboardData {
  installation: SolarInstallation
  today_kwh: number
  month_kwh: number
  estimated_monthly_savings: number
  self_consumed_value: number
  export_credit: number
  roi_paid_back_percent: number
  roi_amount_paid_back: number
  estimated_payback_months_remaining: number
  health_status: HealthStatus
  chart: ProductionDataPoint[]
  alerts: SolarAlert[]
}

export interface ProductionDataPoint {
  date: string
  production_kwh: number
  self_consumed_kwh: number | null
  exported_kwh: number | null
}

export interface SolarAlert {
  id: string
  installation_id: string
  alert_type: AlertType
  severity: AlertSeverity
  title: string
  message: string
  production_kwh: number | null
  baseline_kwh: number | null
  is_read: boolean
  is_dismissed: boolean
  created_at: string
}

export interface InverterConnectPayload {
  api_username: string
  api_password: string
  plant_id?: string
}

export const solarKeys = {
  installations: () => ["solar", "installations"] as const,
  dashboard: (id: string) => ["solar", "dashboard", id] as const,
  production: (id: string, start: string, end: string) =>
    ["solar", "production", id, start, end] as const,
  alerts: (installationId?: string) =>
    ["solar", "alerts", installationId || ""] as const,
}
