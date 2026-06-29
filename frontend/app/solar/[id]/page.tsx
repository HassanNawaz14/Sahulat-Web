"use client"

import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Zap, AlertTriangle } from "lucide-react"

import { useSolarDashboard, useSolarAlerts, useMarkAlertRead, useDismissAlert, useMarkMaintenance } from "@/lib/hooks/useSolar"
import SolarSummaryCard from "@/components/solar/SolarSummaryCard"
import ProductionChart from "@/components/solar/ProductionChart"
import SavingsBreakdown from "@/components/solar/SavingsBreakdown"
import ROICountdown from "@/components/solar/ROICountdown"
import HealthAlerts from "@/components/solar/HealthAlerts"
import MaintenanceReminder from "@/components/solar/MaintenanceReminder"
import InstallationCard from "@/components/solar/InstallationCard"

export default function SolarInstallationPage() {
  const params = useParams()
  const router = useRouter()
  const installationId = params.id as string

  const { data: dashboard, isLoading, isError, refetch } = useSolarDashboard(installationId)
  const { data: alerts } = useSolarAlerts(installationId)
  const markAlertRead = useMarkAlertRead()
  const dismissAlert = useDismissAlert()
  const markMaintenance = useMarkMaintenance()

  if (isLoading) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-32 rounded bg-gray-200" />
          <div className="h-40 rounded-xl bg-gray-100" />
          <div className="h-32 rounded-xl bg-gray-100" />
          <div className="h-24 rounded-xl bg-gray-100" />
        </div>
      </main>
    )
  }

  if (isError || !dashboard) {
    return (
      <main className="mx-auto max-w-lg px-4 py-8">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="mb-4 h-12 w-12 text-red-400" />
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Could not load solar data</h2>
          <p className="mb-6 text-sm text-gray-600">Something went wrong. Please try again.</p>
          <button
            onClick={() => refetch()}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </main>
    )
  }

  const { installation } = dashboard

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <div className="mb-6 flex items-center gap-3">
        <Link href="/solar" className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-xl font-bold">{installation.inverter_brand.toUpperCase()} Solar</h1>
        <span className={`ml-auto rounded-full px-3 py-1 text-xs font-medium ${
          dashboard.health_status === "critical" ? "bg-red-100 text-red-700" :
          dashboard.health_status === "warning" ? "bg-amber-100 text-amber-700" :
          "bg-green-100 text-green-700"
        }`}>
          {dashboard.health_status === "critical" ? "Critical" :
           dashboard.health_status === "warning" ? "Warning" :
           "Healthy"}
        </span>
      </div>

      <div className="space-y-4">
        <SolarSummaryCard
          todayKwh={dashboard.today_kwh}
          monthKwh={dashboard.month_kwh}
          savings={dashboard.estimated_monthly_savings}
          exportCredit={dashboard.export_credit}
        />

        <ProductionChart data={dashboard.chart} />

        <SavingsBreakdown
          selfConsumedValue={dashboard.self_consumed_value}
          exportCredit={dashboard.export_credit}
          estimated={!installation.net_metering_enabled}
        />

        <ROICountdown
          systemCostPkr={installation.system_cost_pkr || 0}
          amountPaidBack={dashboard.roi_amount_paid_back}
          roiPercent={dashboard.roi_paid_back_percent}
          monthsRemaining={dashboard.estimated_payback_months_remaining}
          commissioningDate={installation.commissioning_date || ""}
        />

        <HealthAlerts
          alerts={alerts || []}
          onRead={(id) => markAlertRead.mutate(id)}
          onDismiss={(id) => dismissAlert.mutate(id)}
        />

        <MaintenanceReminder
          lastMaintenanceDate={installation.last_maintenance_at}
          systemSizeKw={installation.system_size_kw}
          onMarkDone={() => markMaintenance.mutate({
            installationId,
            lastMaintenanceDate: new Date().toISOString().split("T")[0],
          })}
        />

        {!installation.api_username_encrypted && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
            <div className="flex items-center gap-3">
              <Zap className="h-5 w-5 text-blue-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-900">Connect your inverter</p>
                <p className="text-xs text-blue-700">Link your inverter API for live production data</p>
              </div>
              <button className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700">
                Connect
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
